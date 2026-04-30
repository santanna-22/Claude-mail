#!/usr/bin/env python3
"""
Monitor de Gmail — envia alerta no WhatsApp quando recebe e-mail de um remetente específico.

Uso:
    python gmail_monitor.py

Configuração no .env:
    EMAIL_ADDRESS, EMAIL_PASSWORD (mesmos do bulk_send)
    WATCH_SENDER         - remetente para monitorar
    WHATSAPP_PHONE       - número do WhatsApp com código do país
    CALLMEBOT_APIKEY     - API Key do CallMeBot
    CHECK_INTERVAL       - intervalo de verificação em segundos (padrão: 60)
"""

import imaplib
import email
import email.header
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

from whatsapp_notifier import send_whatsapp


def decode_header_value(raw):
    """Decodifica cabeçalhos de e-mail que podem estar em diferentes encodings."""
    parts = email.header.decode_header(raw)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def check_new_emails(imap, sender_filter, seen_uids):
    """Verifica novos e-mails de um remetente específico.

    Returns:
        list[dict]: Lista de novos e-mails encontrados
    """
    new_emails = []

    imap.select("INBOX")
    _, data = imap.search(None, f'(FROM "{sender_filter}" UNSEEN)')

    if not data[0]:
        return new_emails

    uids = data[0].split()

    for uid in uids:
        uid_str = uid.decode()
        if uid_str in seen_uids:
            continue

        _, msg_data = imap.fetch(uid, "(RFC822)")
        if not msg_data or not msg_data[0]:
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject = decode_header_value(msg.get("Subject", "(sem assunto)"))
        from_addr = decode_header_value(msg.get("From", ""))
        date = msg.get("Date", "")

        new_emails.append({
            "uid": uid_str,
            "from": from_addr,
            "subject": subject,
            "date": date,
        })

        seen_uids.add(uid_str)

    return new_emails


def connect_imap(email_address, email_password, host="imap.gmail.com"):
    """Conecta ao servidor IMAP do Gmail."""
    imap = imaplib.IMAP4_SSL(host)
    imap.login(email_address, email_password)
    print(f"[OK] Conectado ao IMAP como {email_address}")
    return imap


def main():
    load_dotenv()

    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    watch_sender = os.getenv("WATCH_SENDER")
    whatsapp_phone = os.getenv("WHATSAPP_PHONE")
    callmebot_apikey = os.getenv("CALLMEBOT_APIKEY")
    check_interval = int(os.getenv("CHECK_INTERVAL", "60"))

    missing = []
    if not email_address:
        missing.append("EMAIL_ADDRESS")
    if not email_password:
        missing.append("EMAIL_PASSWORD")
    if not watch_sender:
        missing.append("WATCH_SENDER")
    if not whatsapp_phone:
        missing.append("WHATSAPP_PHONE")
    if not callmebot_apikey:
        missing.append("CALLMEBOT_APIKEY")

    if missing:
        print(f"[ERRO] Variáveis não configuradas no .env: {', '.join(missing)}")
        sys.exit(1)

    print("=" * 60)
    print("  Gmail Monitor + WhatsApp Alert")
    print("=" * 60)
    print(f"  Monitorando:  {email_address}")
    print(f"  Remetente:    {watch_sender}")
    print(f"  WhatsApp:     {whatsapp_phone}")
    print(f"  Intervalo:    {check_interval}s")
    print("=" * 60)
    print()

    seen_uids = set()

    while True:
        try:
            imap = connect_imap(email_address, email_password)

            while True:
                now = datetime.now().strftime("%H:%M:%S")
                print(f"[{now}] Verificando e-mails...", end=" ")

                new_emails = check_new_emails(imap, watch_sender, seen_uids)

                if new_emails:
                    print(f"{len(new_emails)} novo(s)!")
                    for em in new_emails:
                        msg_text = (
                            f"📧 Novo e-mail de {watch_sender}!\n\n"
                            f"Assunto: {em['subject']}\n"
                            f"De: {em['from']}\n"
                            f"Data: {em['date']}"
                        )
                        print(f"  → {em['subject']}")
                        send_whatsapp(whatsapp_phone, callmebot_apikey, msg_text)
                else:
                    print("nenhum novo.")

                time.sleep(check_interval)

        except imaplib.IMAP4.abort:
            print("[AVISO] Conexão IMAP perdida. Reconectando em 10s...")
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n[OK] Monitor encerrado.")
            sys.exit(0)
        except Exception as e:
            print(f"[ERRO] {e}. Tentando novamente em 30s...")
            time.sleep(30)


if __name__ == "__main__":
    main()
