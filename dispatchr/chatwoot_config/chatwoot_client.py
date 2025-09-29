import os
import time
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
    return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)

def whatsapp_jid(phone: str, region: str = "BR") -> str:
    e164 = to_e164(phone, region)
    num  = e164.lstrip("+")
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

def extract_id_from_response(data):
    if not isinstance(data, dict):
        return None
    if "id" in data:
        return data["id"]
    for key in ("payload", "data", "contact"):
        val = data.get(key)
        if isinstance(val, dict) and "id" in val:
            return val["id"]
        if isinstance(val, list) and val and isinstance(val[0], dict) and "id" in val[0]:
            return val[0]["id"]
    return None

def get_or_create_contact(
    name: str,
    email: str,
    phone: str,
    identifier: str,
    cnpj: str,
    max_attempts: int = 4,
    base_delay: float = 0.5
) -> tuple:
    """
    Retorna (contact_id, created)
    - Tenta criar o contato com retries.
    - Em caso de 422, tenta buscar pelo telefone; se não encontrar, espera e tenta novamente.
    - Considera sucesso para qualquer 2xx que contenha o id no body.
    - created == True quando status == 201 ou quando o body indica created_at no contato.
    """
    phone_e = to_e164(phone)
    payload = {
        "name":              name,
        "email":             email,
        "phone_number":      phone_e,
        "identifier":        identifier,
        "custom_attributes": {"cnpj": cnpj}
    }
    url  = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts"

    last_body = None
    for attempt in range(1, max_attempts + 1):
        resp = requests.post(url, headers=HEADERS, json=payload)
        try:
            data = resp.json()
        except Exception:
            data = None
        last_body = data if data is not None else resp.text

        # any 2xx: try extract id
        if 200 <= resp.status_code < 300:
            cid = extract_id_from_response(data)
            if cid is not None:
                created = resp.status_code == 201
                # if not explicit 201, detect created_at inside payload/contact
                if not created and isinstance(data, dict):
                    for key in ("payload", "data", "contact"):
                        val = data.get(key)
                        if isinstance(val, dict) and val.get("created_at"):
                            created = True
                            break
                return cid, created
            # fallback: search by phone
            results = search_contacts(phone_e)
            if results:
                return results[0]["id"], resp.status_code == 201

        # 422: maybe contact already exists but creation endpoint returned unprocessable
        if resp.status_code == 422:
            results = search_contacts(phone_e)
            if results:
                return results[0]["id"], False

        # If not successful yet, wait and retry (exponential backoff)
        if attempt < max_attempts:
            delay = base_delay * (2 ** (attempt - 1))
            time.sleep(delay)

    # after attempts, provide diagnostic
    raise RuntimeError(
        f"Falha ao criar/recuperar contato após {max_attempts} tentativas. "
        f"Último status: {resp.status_code} | Body: {last_body}"
    )

def open_conversation(contact_id: int, source_id: str, max_retries: int = 6, base_delay: float = 0.5) -> int:
    payload = {
        "source_id":  source_id,
        "inbox_id":   INBOX_ID,
        "contact_id": contact_id
    }
    url = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations"

    last_resp = None
    for attempt in range(1, max_retries + 1):
        resp = requests.post(url, headers=HEADERS, json=payload)
        if resp.status_code in (200, 201):
            return resp.json()["id"]
        last_resp = resp
        if attempt == max_retries:
            break
        delay = base_delay * (2 ** (attempt - 1))
        time.sleep(delay)

    msg = (
        f"Falha ao criar conversa. URL: {url} | "
        f"Status: {last_resp.status_code if last_resp is not None else 'nenhum'} | "
        f"Resposta: {last_resp.text if last_resp is not None else 'nenhuma'}"
    )
    raise requests.HTTPError(msg)

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
    content: str,
    max_retries: int = 6,
    base_delay: float = 0.5,
    post_create_delay: float = 0.8
) -> int:
    """
    Fluxo:
      1) Tenta criar/recuperar contato (com retries internos).
      2) Se o contato foi criado agora (detectado), aguarda post_create_delay.
      3) Abre conversa com retry e envia a mensagem.
    """
    jid = whatsapp_jid(phone)
    cid, created = get_or_create_contact(name, email, phone, jid, cnpj)
    if created:
        time.sleep(post_create_delay)
    conv_id = open_conversation(cid, jid, max_retries=max_retries, base_delay=base_delay)
    return send_message(conv_id, content)
