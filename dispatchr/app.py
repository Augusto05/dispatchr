#!/usr/bin/env python3
import os
import requests
import phonenumbers
from dotenv import load_dotenv

load_dotenv()

# Configurações do Chatwoot (defina no .env)
BASE_URL   = os.getenv("CHATWOOT_BASE_URL").rstrip("/")
API_TOKEN  = os.getenv("CHATWOOT_API_TOKEN")
ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID")
INBOX_ID   = os.getenv("CHATWOOT_INBOX_ID")

HEADERS = {
    "api_access_token": API_TOKEN,
    "Content-Type":    "application/json"
}

def to_e164(raw, region="BR"):
    """Formata número em E.164 (ex: +5514996126525)."""
    num = phonenumbers.parse(str(raw), region)
    return phonenumbers.format_number(
        num, phonenumbers.PhoneNumberFormat.E164
    )

def search_contacts(query):
    """
    Busca contatos via `/contacts/search`.
    Retorna sempre uma lista (mesmo que vazia).
    """
    url = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/search"
    resp = requests.get(url, headers=HEADERS, params={"q": query})
    resp.raise_for_status()
    data = resp.json()

    # Se vier dict com lista aninhada
    if isinstance(data, dict):
        for key in ("payload", "data", "contacts"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return []

    return data if isinstance(data, list) else []

def get_or_create_contact(name, email, phone, identifier):
    """
    Tenta criar um contato; se der 422 (já existe), busca pelo telefone.
    Retorna o contact_id.
    """
    phone_e = to_e164(phone)
    payload = {
        "name":         name,
        "email":        email,
        "phone_number": phone_e,
        "identifier":   identifier
    }
    url = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts"
    resp = requests.post(url, headers=HEADERS, json=payload)

    if resp.status_code == 201:
        return resp.json()["id"]

    if resp.status_code == 422:
        contacts = search_contacts(phone_e)
        if contacts:
            return contacts[0]["id"]
        raise RuntimeError(f"Contato não encontrado após erro 422 para {phone_e}")

    resp.raise_for_status()

def open_conversation(contact_id):
    """
    Abre uma nova conversa (ou retorna a existente) para o contato.
    """
    payload = {
        "source_id":  contact_id,
        "inbox_id":   INBOX_ID,
        "contact_id": contact_id
    }
    url = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations"
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()["id"]

def send_message(conversation_id, text):
    """
    Envia mensagem de saída (outgoing) para a conversa.
    """
    payload = {
        "content":      text,
        "message_type": "outgoing"
    }
    url = (
        f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}"
        f"/conversations/{conversation_id}/messages"
    )
    resp = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    # Exemplo de dados e texto
    name       = "João Example"
    email      = "joao@example.com"
    phone      = "14996126525"
    identifier = "joao-ex"
    message    = "Olá João! Esta é uma mensagem de teste via Chatwoot API."

    # Fluxo mínimo
    contact_id      = get_or_create_contact(name, email, phone, identifier)
    conversation_id = open_conversation(contact_id)
    sent_msg        = send_message(conversation_id, message)

    print(f"Contato ID: {contact_id}")
    print(f"Conversa ID: {conversation_id}")
    print(f"Mensagem enviada, ID: {sent_msg['id']}")
