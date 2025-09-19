#!/usr/bin/env python3
import os
import requests
import phonenumbers
from dotenv import load_dotenv

load_dotenv()

BASE_URL   = os.getenv("CHATWOOT_BASE_URL").rstrip("/")
API_TOKEN  = os.getenv("CHATWOOT_API_TOKEN")
ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID")
INBOX_ID   = os.getenv("CHATWOOT_INBOX_ID")

HEADERS = {
    "api_access_token": API_TOKEN,
    "Content-Type":    "application/json"
}

def to_e164(raw, region="BR"):
    n = phonenumbers.parse(str(raw), region)
    return phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)

def get_or_create_contact(name, email, phone, identifier):
    phone_e = to_e164(phone)
    payload = {
        "name":         name,
        "email":        email,
        "phone_number": phone_e,
        "identifier":   identifier
    }
    url = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts"
    r = requests.post(url, headers=HEADERS, json=payload)
    if r.status_code == 201:
        return r.json()["id"]
    if r.status_code == 422 and "taken" in r.text:
        # busca existente
        resp = requests.get(
            f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/search",
            headers=HEADERS, params={"q": phone_e}
        )
        resp.raise_for_status()
        return resp.json()[0]["id"]
    r.raise_for_status()

def open_conversation(contact_id):
    payload = {
        "source_id":  contact_id,
        "inbox_id":   INBOX_ID,
        "contact_id": contact_id
    }
    url = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations"
    r = requests.post(url, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()["id"]

def send_message(conversation_id, text):
    payload = {
        "content":      text,
        "message_type": "outgoing"
    }
    url = (
        f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}"
        f"/conversations/{conversation_id}/messages"
    )
    r = requests.post(url, headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    # Dados do contato
    name       = "João Example"
    email      = "joao@example.com"
    phone      = "14996126525"
    identifier = "joao-ex"

    # Texto a enviar
    message = "Olá João! Esta é uma mensagem de teste via Chatwoot API."

    # Fluxo mínimo
    contact_id      = get_or_create_contact(name, email, phone, identifier)
    conversation_id = open_conversation(contact_id)
    sent_msg        = send_message(conversation_id, message)

    print(f"Contato ID: {contact_id}")
    print(f"Conversa ID: {conversation_id}")
    print(f"Mensagem enviada, ID: {sent_msg['id']}")
