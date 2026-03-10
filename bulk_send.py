#!/usr/bin/env python3
"""
Claude-mail: Envio massificado e personalizado de e-mails via Gmail.

Uso:
    python bulk_send.py --contacts contatos.csv --template templates/meu_template.html --subject "Olá {{ nome }}!"

Opções:
    --contacts     Arquivo CSV ou Excel com os contatos (obrigatório)
    --template     Arquivo HTML do template do e-mail (obrigatório)
    --subject      Assunto do e-mail, suporta variáveis {{ }} (obrigatório)
    --attachments  Arquivos para anexar (opcional, separados por vírgula)
    --dry-run      Simula o envio sem realmente enviar (opcional)
    --limit        Limita o número de e-mails a enviar (opcional)
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from contacts_reader import read_contacts
from email_sender import EmailSender
from template_engine import render_template, render_subject


def parse_args():
    parser = argparse.ArgumentParser(
        description="Claude-mail: Envio massificado e personalizado de e-mails"
    )
    parser.add_argument(
        "--contacts", required=True,
        help="Caminho para o arquivo CSV ou Excel com os contatos"
    )
    parser.add_argument(
        "--template", required=True,
        help="Caminho para o template HTML do e-mail"
    )
    parser.add_argument(
        "--subject", required=True,
        help="Assunto do e-mail (suporta variáveis Jinja2, ex: 'Olá {{ nome }}!')"
    )
    parser.add_argument(
        "--attachments", default="",
        help="Arquivos para anexar, separados por vírgula"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simula o envio sem realmente enviar os e-mails"
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Limita o número de e-mails enviados (0 = sem limite)"
    )
    return parser.parse_args()


def load_config():
    """Carrega configurações do arquivo .env."""
    load_dotenv()

    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not email_address or not email_password:
        print("[ERRO] Configure EMAIL_ADDRESS e EMAIL_PASSWORD no arquivo .env")
        print("       Copie .env.example para .env e preencha seus dados.")
        sys.exit(1)

    return {
        "email_address": email_address,
        "email_password": email_password,
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "emails_per_minute": int(os.getenv("EMAILS_PER_MINUTE", "20")),
        "delay_between_emails": int(os.getenv("DELAY_BETWEEN_EMAILS", "3")),
    }


def write_log(log_file, row):
    """Escreve uma linha no arquivo de log CSV."""
    file_exists = log_file.exists()
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "email", "status", "error"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    args = parse_args()

    print("=" * 60)
    print("  Claude-mail - Envio Massificado de E-mails")
    print("=" * 60)
    print()

    # Carregar contatos
    contacts = read_contacts(args.contacts)
    if not contacts:
        print("[ERRO] Nenhum contato válido encontrado.")
        sys.exit(1)

    # Verificar template
    template_path = Path(args.template)
    if not template_path.exists():
        print(f"[ERRO] Template não encontrado: {args.template}")
        sys.exit(1)

    # Processar anexos
    attachments = [a.strip() for a in args.attachments.split(",") if a.strip()]

    # Aplicar limite
    if args.limit > 0:
        contacts = contacts[:args.limit]

    # Resumo pré-envio
    print(f"\n{'─' * 40}")
    print(f"  Destinatários: {len(contacts)}")
    print(f"  Template:      {template_path.name}")
    print(f"  Assunto:       {args.subject}")
    print(f"  Anexos:        {len(attachments) if attachments else 'Nenhum'}")
    print(f"  Modo:          {'SIMULAÇÃO (dry-run)' if args.dry_run else 'ENVIO REAL'}")
    print(f"{'─' * 40}\n")

    if not args.dry_run:
        confirm = input("Confirmar envio? (s/N): ").strip().lower()
        if confirm != "s":
            print("Envio cancelado.")
            sys.exit(0)

    # Log de envio
    log_file = Path(f"send_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    # Contadores
    sent_ok = 0
    sent_fail = 0

    if args.dry_run:
        # Modo simulação
        for i, contact in enumerate(contacts, 1):
            subject = render_subject(args.subject, contact)
            html_body = render_template(args.template, contact)
            print(f"  [{i}/{len(contacts)}] [DRY-RUN] {contact['email']} - {subject}")
            write_log(log_file, {
                "timestamp": datetime.now().isoformat(),
                "email": contact["email"],
                "status": "dry-run",
                "error": "",
            })
            sent_ok += 1
    else:
        # Envio real
        config = load_config()
        with EmailSender(**config) as sender:
            for i, contact in enumerate(contacts, 1):
                subject = render_subject(args.subject, contact)
                html_body = render_template(args.template, contact)

                print(f"  [{i}/{len(contacts)}] Enviando para {contact['email']}...", end=" ")

                success, error = sender.send(
                    to_email=contact["email"],
                    subject=subject,
                    html_body=html_body,
                    attachments=attachments or None,
                )

                if success:
                    print("OK")
                    sent_ok += 1
                    status = "ok"
                else:
                    print(f"FALHA - {error}")
                    sent_fail += 1
                    status = "falha"

                write_log(log_file, {
                    "timestamp": datetime.now().isoformat(),
                    "email": contact["email"],
                    "status": status,
                    "error": error or "",
                })

    # Resumo final
    print(f"\n{'=' * 60}")
    print(f"  RESULTADO FINAL")
    print(f"  Enviados com sucesso: {sent_ok}")
    print(f"  Falhas:               {sent_fail}")
    print(f"  Log salvo em:         {log_file}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
