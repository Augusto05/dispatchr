# chatwoot_client.py

import os
import requests
import phonenumbers
from dotenv import load_dotenv

load_dotenv()

BASE_URL   = os.getenv("CHATWOOT_BASE_URL", "").rstrip("/")
API_TOKEN  = os.getenv("CHATWOOT_API_TOKEN", "")
ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID", "")
INBOX_ID   = os.getenv("CHATWOOT_INBOX_ID", "")

HEADERS = {
    "api_access_token": API_TOKEN,
    "Content-Type":    "application/json"
}

def to_e164(raw: str, region: str = "BR") -> str:
    num = phonenumbers.parse(str(raw), region)
    return phonenumbers.format_number(
        num, phonenumbers.PhoneNumberFormat.E164
    )

def whatsapp_jid(phone: str, region: str = "BR") -> str:
    """
    Gera o JID de WhatsApp Business API a partir do telefone.
    Ex: '14996126525' → '5514996126525@s.whatsapp.net'
    """
    e164 = to_e164(phone, region)       # '+5514996126525'
    num  = e164.lstrip("+")             # '5514996126525'
    return f"{num}@s.whatsapp.net"

def search_contacts(query: str) -> list:
    url  = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/search"
    resp = requests.get(url, headers=HEADERS, params={"q": query})
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, dict):
        for key in ("payload", "data", "contacts"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return []

    return data if isinstance(data, list) else []

def get_or_create_contact(
    name: str,
    email: str,
    phone: str,
    identifier: str,
    cnpj: str
) -> int:
    phone_e = to_e164(phone)
    payload = {
        "name":              name,
        "email":             email,
        "phone_number":      phone_e,
        "identifier":        identifier,
        "custom_attributes": {"cnpj": cnpj}
    }
    url  = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts"
    resp = requests.post(url, headers=HEADERS, json=payload)

    if resp.status_code == 201:
        return resp.json()["id"]

    if resp.status_code == 422:
        results = search_contacts(phone_e)
        if results:
            return results[0]["id"]
        raise RuntimeError(f"Contato não encontrado após erro 422 para {phone_e}")

    resp.raise_for_status()

def open_conversation(contact_id: int, source_id: str) -> int:
    payload = {
        "source_id":  source_id,
        "inbox_id":   INBOX_ID,
        "contact_id": contact_id
    }
    url = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations"
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()["id"]

def send_message(conversation_id: int, content: str) -> int:
    payload = {
        "content":      content,
        "message_type": "outgoing"
    }
    url = (
        f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}"
        f"/conversations/{conversation_id}/messages"
    )
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()["id"]

def dispatch_message(
    name: str,
    email: str,
    phone: str,
    cnpj: str,
    content: str
) -> int:
    """
    Fluxo completo sem precisar do identifier:
      1) Gera JID via whatsapp_jid()
      2) Cria/recupera contato
      3) Abre conversa usando o JID como source_id
      4) Envia mensagem
    """
    jid = whatsapp_jid(phone)
    cid = get_or_create_contact(name, email, phone, jid, cnpj)
    conv_id = open_conversation(cid, jid)
    return send_message(conv_id, content)
