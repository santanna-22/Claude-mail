# Claude-mail

Sistema de envio massificado e personalizado de e-mails via Gmail/SMTP.

## Funcionalidades

- Envio em massa via Gmail (SMTP com TLS)
- Templates HTML personalizáveis com variáveis Jinja2 (`{{ nome }}`, `{{ empresa }}`, etc.)
- Leitura de contatos de arquivos CSV ou Excel (.xlsx)
- Suporte a anexos (qualquer tipo de arquivo)
- Rate limiting configurável para evitar bloqueio pelo provedor
- Retry automático em caso de falhas de conexão
- Modo dry-run para simulação sem envio real
- Log de envio em CSV com timestamp e status

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

1. Copie o arquivo de exemplo e preencha com seus dados:

```bash
cp .env.example .env
```

2. No Gmail, gere uma **Senha de App**:
   - Acesse https://myaccount.google.com/security
   - Ative a verificação em 2 etapas
   - Vá em "Senhas de app" e gere uma nova senha
   - Cole a senha no arquivo `.env`

## Uso

### Comando básico

```bash
python bulk_send.py \
  --contacts samples/contatos_exemplo.csv \
  --template templates/exemplo.html \
  --subject "Olá {{ nome }}, temos uma proposta para {{ empresa }}"
```

### Com anexos

```bash
python bulk_send.py \
  --contacts contatos.csv \
  --template templates/exemplo.html \
  --subject "Proposta comercial para {{ empresa }}" \
  --attachments "proposta.pdf,catalogo.pdf"
```

### Modo simulação (dry-run)

```bash
python bulk_send.py \
  --contacts contatos.csv \
  --template templates/exemplo.html \
  --subject "Teste {{ nome }}" \
  --dry-run
```

### Limitar quantidade

```bash
python bulk_send.py \
  --contacts contatos.csv \
  --template templates/exemplo.html \
  --subject "Olá {{ nome }}!" \
  --limit 10
```

## Formato do arquivo de contatos

O CSV/Excel deve ter uma coluna `email` (obrigatória). As demais colunas ficam disponíveis como variáveis no template:

| nome | email | empresa | cargo |
|------|-------|---------|-------|
| João | joao@ex.com | Tech Corp | Gerente |

## Monitor de Gmail + Alerta WhatsApp

Monitora seu Gmail e envia uma notificação no WhatsApp quando chega um e-mail de um remetente específico.

### Configuração do CallMeBot (uma única vez)

1. Adicione **+34 644 71 81 99** nos contatos do celular
2. Envie `I allow callmebot to send me messages` para esse número no WhatsApp
3. Anote o **API Key** recebido na resposta

### Configurar no .env

```
WATCH_SENDER=remetente@exemplo.com
WHATSAPP_PHONE=+5531999999999
CALLMEBOT_APIKEY=123456
CHECK_INTERVAL=60
```

### Rodar o monitor

```bash
python gmail_monitor.py
```

O script roda continuamente verificando a cada 60 segundos (configurável).

## Estrutura do projeto

```
Claude-mail/
├── bulk_send.py          # Envio massificado de e-mails (CLI)
├── gmail_monitor.py      # Monitor Gmail + alerta WhatsApp
├── email_sender.py       # Módulo de envio SMTP
├── contacts_reader.py    # Leitor de CSV/Excel
├── template_engine.py    # Motor de templates Jinja2
├── whatsapp_notifier.py  # Notificação via WhatsApp (CallMeBot)
├── requirements.txt      # Dependências Python
├── .env.example          # Exemplo de configuração
├── templates/
│   └── exemplo.html      # Template HTML de exemplo
└── samples/
    └── contatos_exemplo.csv  # CSV de exemplo
```
