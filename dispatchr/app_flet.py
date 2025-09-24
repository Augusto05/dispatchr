import flet as ft
import time, random
from chatwoot_client import dispatch_message

def main(page: ft.Page):
    page.title = "dispatchr"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_width = 900
    page.window_height = 600

    def apply_theme():
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    background=ft.Colors.GREY_900,
                    surface=ft.Colors.GREY_800,
                    primary=ft.Colors.GREY_700,
                    on_primary=ft.Colors.WHITE,
                    secondary=ft.Colors.GREY_600,
                    on_secondary=ft.Colors.WHITE,
                    error=ft.Colors.RED_400,
                    on_error=ft.Colors.WHITE,
                    on_background=ft.Colors.WHITE,
                    on_surface=ft.Colors.WHITE,
                )
            )
        else:
            page.theme = ft.Theme()

    apply_theme()

    theme_button = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        tooltip="Alternar tema",
        on_click=lambda e: toggle_theme(e)
    )

    theme_button_container = ft.Container(
        content=theme_button,
        border_radius=15,
    )

    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Image(src="dispatchr_header.png", width=120, fit=ft.ImageFit.CONTAIN),
                theme_button_container
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        bgcolor=ft.Colors.WHITE,
        padding=10,
        height=60,
        border_radius=10
    )

    # altura fixa padrão para as duas seções
    container_height = 690

    # Campos Disparo Individual
    name_field  = ft.TextField(label="Nome", width=360, border_radius=15)
    email_field = ft.TextField(label="E-mail", width=360, border_radius=15)
    phone_field = ft.TextField(label="Telefone", width=360, border_radius=15)
    cnpj_field  = ft.TextField(label="CNPJ", width=360, border_radius=15)
    msg_field   = ft.TextField(label="Mensagem", multiline=True, width=360, height=180, border_radius=15)
    status = ft.Text()

    use_default_msg = ft.Switch(label="Usar mensagem padrão", value=False)
    example_text = ft.Text(value="", italic=True, size=12, color=ft.Colors.GREY_600)

    def update_message(e=None):
        if use_default_msg.value:
            nome = name_field.value or "[Nome da empresa]"
            cnpj = cnpj_field.value or "[CNPJ]"
            default_msg = f"Olá, {nome}, temos uma oferta para seu CNPJ: {cnpj}. Podemos encaminhar mais informações?"
            msg_field.value = default_msg
            msg_field.read_only = True
            example_text.value = f"Exemplo: {default_msg}"
        else:
            msg_field.read_only = False
            example_text.value = ""
        page.update()

    use_default_msg.on_change = update_message
    name_field.on_change = update_message
    cnpj_field.on_change = update_message

    def send_click(e):
        status.value = "Enviando…"
        page.update()
        try:
            msg_id = dispatch_message(
                name=name_field.value,
                email=email_field.value,
                phone=phone_field.value,
                cnpj=cnpj_field.value,
                content=msg_field.value
            )
            status.value = f"✅ Enviado! ID: {msg_id}"
        except Exception as err:
            status.value = f"❌ Erro: {err}"
        page.update()

    send_btn = ft.ElevatedButton(text="Enviar", on_click=send_click, width=120)

    # Campos Disparo em Lotes
    arquivo_txt = ft.TextField(
        label="Conteúdo do arquivo .txt",
        multiline=True,
        min_lines=5,
        max_lines=15,
        width=360,
        border_radius=15,
        hint_text="Cole aqui o conteúdo do arquivo com cabeçalho e dados separados por ponto e vírgula (;)",
        text_size=12
    )

    lote_msg_template = ft.TextField(
        label="Mensagem padrão para lote",
        multiline=True,
        min_lines=3,
        max_lines=6,
        width=360,
        border_radius=15,
        value="Olá, {nome}, temos uma oferta para seu CNPJ: {cnpj}. Podemos encaminhar mais informações?"
    )

    # Controles novos: pausa e configuração de intervalo
    is_paused = {"value": False}   # flag mutável acessível no loop
    is_running = {"value": False}  # flag para indicar que o loop está rodando

    pause_btn = ft.ElevatedButton(text="Pausar", width=120)
    resume_btn = ft.ElevatedButton(text="Continuar", width=120)
    # Inputs para intervalo mínimo e máximo (segundos)
    min_delay_field = ft.TextField(label="Delay mínimo (s)", value="3", width=140, border_radius=15)
    max_delay_field = ft.TextField(label="Delay máximo (s)", value="7", width=140, border_radius=15)

    # Funções dos botões pausa/continuar
    def on_pause(e):
        is_paused["value"] = True
        page.update()

    def on_resume(e):
        is_paused["value"] = False
        page.update()

    pause_btn.on_click = on_pause
    resume_btn.on_click = on_resume

    # Validação segura dos delays
    def get_delays():
        try:
            mn = float(min_delay_field.value)
        except:
            mn = 3.0
        try:
            mx = float(max_delay_field.value)
        except:
            mx = 7.0
        if mn < 0:
            mn = 0.0
        if mx < mn:
            mx = mn
        return mn, mx

    # Loop de disparo em lote, respeitando pausa e delays configurados
    def disparar_em_lote(e):
        if is_running["value"]:
            # já está rodando; evita múltiplas execuções simultâneas
            status.value = "⚠️ Disparo já em execução."
            page.update()
            return

        linhas = arquivo_txt.value.strip().split("\n")
        if len(linhas) < 2:
            status.value = "❌ Arquivo inválido ou vazio."
            page.update()
            return

        is_running["value"] = True
        status.value = "Iniciando disparo em lote..."
        page.update()

        cabecalho = linhas[0].strip().split(";")
        total = len(linhas) - 1

        for i, linha in enumerate(linhas[1:], start=1):
            # se houve pausa, aguarda até que seja despausado
            while is_paused["value"]:
                status.value = f"⏸️ Pausado em {i-1}/{total}. Aguardando continuar..."
                page.update()
                time.sleep(0.2)  # espera curta para manter UI responsiva

            campos = linha.strip().split(";")
            if len(campos) != len(cabecalho):
                status.value = f"⚠️ Linha {i+1} ignorada: número de campos incorreto."
                page.update()
                continue

            dados = dict(zip(cabecalho, campos))
            try:
                mensagem = lote_msg_template.value.format(**dados)
            except Exception as err:
                status.value = f"❌ Erro ao formatar mensagem na linha {i+1}: {err}"
                page.update()
                continue

            try:
                msg_id = dispatch_message(
                    name=dados.get("nome", ""),
                    email=dados.get("email", ""),
                    phone=dados.get("telefone", ""),
                    cnpj=dados.get("cnpj", ""),
                    content=mensagem
                )
                status.value = f"✅ {i}/{total} enviado: {dados.get('nome','')} (ID: {msg_id})"
            except Exception as err:
                status.value = f"❌ Erro ao enviar para {dados.get('nome','')}: {err}"
            page.update()

            # após cada envio, aguarda intervalo aleatório entre min e max,
            # respeitando pausa se acionada durante a espera
            mn, mx = get_delays()
            wait = random.uniform(mn, mx)
            waited = 0.0
            # subdivide espera em fatias pequenas para permitir pausa rápida
            slice_dt = 0.2
            while waited < wait:
                if is_paused["value"]:
                    status.value = f"⏸️ Pausado após {i}/{total}. Aguardando continuar..."
                    page.update()
                    # esperar enquanto estiver pausado
                    while is_paused["value"]:
                        time.sleep(0.2)
                    # retomou, recalcula mn/mx e ajuste restante
                    mn, mx = get_delays()
                    remaining = wait - waited
                else:
                    time.sleep(slice_dt)
                    waited += slice_dt

        is_running["value"] = False
        status.value = f"✅ Disparo em lote finalizado ({total} linhas processadas)."
        page.update()

    disparar_btn = ft.ElevatedButton("Disparar mensagens em lote", on_click=disparar_em_lote)

    # Containers das duas seções com altura fixa
    individual_container = ft.Container(
        content=ft.Column([
            ft.Text("Disparo Individual", size=18, weight="bold"),
            name_field,
            email_field,
            phone_field,
            cnpj_field,
            use_default_msg,
            ft.Column([msg_field, send_btn], spacing=5, expand=True),
            example_text,
            status
        ], spacing=15, scroll=True, expand=True, alignment=ft.MainAxisAlignment.START),
        expand=True,
        height=container_height,
        padding=10,
        bgcolor=ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_850,
        border_radius=10
    )

    lote_container = ft.Container(
        content=ft.Column([
            ft.Text("Disparo em Lotes", size=18, weight="bold"),
            ft.Text("Como utilizar?", size=12, weight="medium"),
            ft.Text("1. Crie um arquivo em txt, seguindo a lógica desse cabeçalho: nome;email;telefone;cnpj", size=12, weight="regular"),
            ft.Text("2. Cole o arquivo no campo abaixo, e confirme os dados", size=12, weight="regular"),
            ft.Text("3. Configure a mensagem padrão como deseja, adicionando os campos personalisáveis entre chaves", size=12, weight="regular"),
            ft.Text("4. Aperte em Disparar mensagens em lote, e acompanhe o resultado na parte inferior", size=12, weight="regular"),
            arquivo_txt,
            ft.Row([min_delay_field, max_delay_field], spacing=10),
            ft.Row([pause_btn, resume_btn, disparar_btn], spacing=10),
            ft.Text("Editar Mensagem Padrão", size=18, weight="bold"),
            lote_msg_template,
        ], spacing=15, scroll=True, expand=True, alignment=ft.MainAxisAlignment.START),
        expand=True,
        height=container_height,
        padding=10,
        bgcolor=ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_850,
        border_radius=10
    )

    page.add(
        header,
        ft.Row([
            individual_container,
            ft.VerticalDivider(width=1),
            lote_container
        ], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START)
    )

    def toggle_theme(e):
        page.theme_mode = (
            ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        )
        theme_button.icon = (
            ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE
        )
        apply_theme()
        # rebuild containers to apply theme colors correctly (keeps height)
        individual_container.height = container_height
        lote_container.height = container_height
        page.update()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
