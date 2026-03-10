"""Módulo principal de envio de e-mails via SMTP/Gmail."""

import smtplib
import ssl
import time
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path


class EmailSender:
    """Gerencia conexão SMTP e envio de e-mails."""

    def __init__(self, email_address, email_password, smtp_host="smtp.gmail.com",
                 smtp_port=587, emails_per_minute=20, delay_between_emails=3):
        self.email_address = email_address
        self.email_password = email_password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.emails_per_minute = emails_per_minute
        self.delay_between_emails = delay_between_emails
        self._server = None
        self._sent_count = 0
        self._minute_start = None

    def connect(self):
        """Estabelece conexão SMTP com TLS."""
        context = ssl.create_default_context()
        self._server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30)
        self._server.ehlo()
        self._server.starttls(context=context)
        self._server.ehlo()
        self._server.login(self.email_address, self.email_password)
        self._minute_start = time.time()
        self._sent_count = 0
        print(f"[OK] Conectado ao servidor SMTP {self.smtp_host}:{self.smtp_port}")

    def disconnect(self):
        """Encerra conexão SMTP."""
        if self._server:
            try:
                self._server.quit()
            except smtplib.SMTPServerDisconnected:
                pass
            self._server = None
            print("[OK] Desconectado do servidor SMTP")

    def _apply_rate_limit(self):
        """Aplica rate limiting para evitar bloqueio pelo provedor."""
        now = time.time()
        elapsed = now - self._minute_start

        if elapsed >= 60:
            self._sent_count = 0
            self._minute_start = now
        elif self._sent_count >= self.emails_per_minute:
            wait_time = 60 - elapsed
            print(f"[RATE LIMIT] Limite de {self.emails_per_minute}/min atingido. "
                  f"Aguardando {wait_time:.0f}s...")
            time.sleep(wait_time)
            self._sent_count = 0
            self._minute_start = time.time()

        if self._sent_count > 0:
            time.sleep(self.delay_between_emails)

    def build_message(self, to_email, subject, html_body, attachments=None):
        """Constrói a mensagem de e-mail com HTML e anexos."""
        msg = MIMEMultipart("mixed")
        msg["From"] = self.email_address
        msg["To"] = to_email
        msg["Subject"] = subject

        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        if attachments:
            for filepath in attachments:
                path = Path(filepath)
                if not path.exists():
                    print(f"  [AVISO] Anexo não encontrado: {filepath}")
                    continue

                content_type, _ = mimetypes.guess_type(str(path))
                if content_type is None:
                    content_type = "application/octet-stream"
                main_type, sub_type = content_type.split("/", 1)

                with open(path, "rb") as f:
                    part = MIMEBase(main_type, sub_type)
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=path.name
                    )
                    msg.attach(part)

        return msg

    def send(self, to_email, subject, html_body, attachments=None, max_retries=3):
        """Envia um e-mail com retry automático.

        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        if not self._server:
            raise RuntimeError("Não conectado. Chame connect() primeiro.")

        self._apply_rate_limit()
        msg = self.build_message(to_email, subject, html_body, attachments)

        for attempt in range(1, max_retries + 1):
            try:
                self._server.sendmail(self.email_address, to_email, msg.as_string())
                self._sent_count += 1
                return True, None
            except smtplib.SMTPServerDisconnected:
                print(f"  [RETRY {attempt}/{max_retries}] Conexão perdida. Reconectando...")
                try:
                    self.connect()
                except Exception as e:
                    if attempt == max_retries:
                        return False, f"Falha ao reconectar: {e}"
                    time.sleep(2 ** attempt)
            except smtplib.SMTPRecipientsRefused as e:
                return False, f"Destinatário recusado: {e}"
            except smtplib.SMTPException as e:
                if attempt == max_retries:
                    return False, f"Erro SMTP: {e}"
                time.sleep(2 ** attempt)

        return False, "Número máximo de tentativas excedido"

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
