"""Módulo de notificação via WhatsApp usando CallMeBot."""

import urllib.parse
import urllib.request


def send_whatsapp(phone, apikey, message):
    """Envia uma mensagem via WhatsApp usando a API CallMeBot.

    Args:
        phone: Número com código do país (ex: +5531996312222)
        apikey: API Key do CallMeBot
        message: Texto da mensagem

    Returns:
        bool: True se enviou com sucesso
    """
    encoded_msg = urllib.parse.quote(message)
    url = (
        f"https://api.callmebot.com/whatsapp.php"
        f"?phone={phone}&text={encoded_msg}&apikey={apikey}"
    )

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                print(f"[OK] WhatsApp enviado para {phone}")
                return True
            else:
                print(f"[ERRO] CallMeBot retornou status {response.status}")
                return False
    except Exception as e:
        print(f"[ERRO] Falha ao enviar WhatsApp: {e}")
        return False
