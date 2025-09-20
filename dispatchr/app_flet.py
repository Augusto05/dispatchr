import flet as ft
from chatwoot_client import dispatch_message

def main(page: ft.Page):
    page.title = "dispatchr"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width  = 400
    page.window_height = 600

    # Agora a imagem vem da pasta assets (veja assets_dir lá embaixo)
    logo = ft.Image(
        src="dispatchr_header.png",  
        width=180,
        fit=ft.ImageFit.CONTAIN
    )

    name_field  = ft.TextField(label="Nome", width=360)
    email_field = ft.TextField(label="E-mail", width=360)
    phone_field = ft.TextField(label="Telefone", width=360)
    cnpj_field  = ft.TextField(label="CNPJ", width=360)
    msg_field   = ft.TextField(label="Mensagem", multiline=True,
                               width=360, height=180)
    status = ft.Text()

    def send_click(e):
        status.value = "Enviando…"
        page.update()
        try:
            msg_id = dispatch_message(
                name    = name_field.value,
                email   = email_field.value,
                phone   = phone_field.value,
                cnpj    = cnpj_field.value,
                content = msg_field.value
            )
            status.value = f"✅ Enviado! ID: {msg_id}"
        except Exception as err:
            status.value = f"❌ Erro: {err}"
        page.update()

    send_btn = ft.ElevatedButton(text="Enviar", on_click=send_click, width=120)

    page.add(
        ft.Column([
            logo,
            name_field,
            email_field,
            phone_field,
            cnpj_field,
            msg_field,
            ft.Row([send_btn, status], alignment="spaceBetween")
        ], spacing=15)
    )

if __name__ == "__main__":
    # Passe assets_dir para expor tudo dentro de ./assets
    ft.app(target=main, assets_dir="assets")
