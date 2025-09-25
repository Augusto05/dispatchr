# app_flet.py
import flet as ft
import time, random, threading
from chatwoot_config.chatwoot_client import dispatch_message

# importa componentes modulares
from pages.nav import AppNavigation
from pages.reports import build_reports

def main(page: ft.Page):
    page.title = "dispatchr"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window.width = 890
    page.window.height = 830

    # estado compartilhado entre views e worker
    state = {
        "nav_index": 0,
        "is_running": False,
        "is_paused": False,
        "progress": 0.0,
        "total_sent": 0,
        "successes": 0,
        "failures": 0,
        "recent_logs": [],
        "reports": [],  # lista de relatórios
    }

    def safe_update():
        try:
            page.update()
        except Exception:
            # em algumas versões/ambientes atualizar a UI a partir da thread pode falhar;
            # ignoramos erros aqui para não interromper o worker
            pass

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
    msg_field   = ft.TextField(label="Mensagem", multiline=True, min_lines=6, width=360, height=180, border_radius=15,)
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
        safe_update()

    use_default_msg.on_change = update_message
    name_field.on_change = update_message
    cnpj_field.on_change = update_message

    def _make_entry_from_fields(name, email, phone, cnpj, status_text):
        return {
            "to": name or "",
            "email": email or "",
            "phone": phone or "",
            "cnpj": cnpj or "",
            "status": status_text,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def _persist_reports():
        try:
            page.client_storage.set("dispatchr_reports", state["reports"])
        except Exception:
            pass

    def send_click(e):
        status.value = "Enviando…"
        safe_update()
        sent_ok = False
        entry = None
        try:
            msg_id = dispatch_message(
                name=name_field.value,
                email=email_field.value,
                phone=phone_field.value,
                cnpj=cnpj_field.value,
                content=msg_field.value
            )
            status.value = f"✅ Enviado! ID: {msg_id}"
            sent_ok = True
            # atualiza métricas básicas
            state["total_sent"] += 1
            state["successes"] += 1
            entry = _make_entry_from_fields(name_field.value, email_field.value, phone_field.value, cnpj_field.value, "sucesso")
            state["recent_logs"].insert(0, entry)
            state["recent_logs"] = state["recent_logs"][:200]
        except Exception as err:
            status.value = f"❌ Erro: {err}"
            state["total_sent"] += 1
            state["failures"] += 1
            entry = _make_entry_from_fields(name_field.value, email_field.value, phone_field.value, cnpj_field.value, "falha")
            state["recent_logs"].insert(0, entry)
            state["recent_logs"] = state["recent_logs"][:200]
        finally:
            # gerar relatório individual de envio (cada disparo vira um relatório único)
            if entry is None:
                entry = _make_entry_from_fields(name_field.value, email_field.value, phone_field.value, cnpj_field.value, "desconhecido")
            report = {
                "ts": time.time(),
                "total": 1,
                "successes": 1 if sent_ok else 0,
                "failures": 0 if sent_ok else 1,
                "entries": [entry],
            }
            state["reports"].insert(0, report)
            # limitar número de relatórios mantidos
            state["reports"] = state["reports"][:500]
            _persist_reports()
            safe_update()

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
        min_lines=2,
        max_lines=6,
        width=360,
        border_radius=15,
        value="Olá, {nome}, temos uma oferta para seu CNPJ: {cnpj}. Podemos encaminhar mais informações?",
        text_size=12
    )

    # Controles novos: pausa e configuração de intervalo
    # mantemos as variáveis locais por compatibilidade, mas as ligamos ao state
    is_paused = {"value": False}   # compat layer; sincronizado com state
    is_running = {"value": False}  # compat layer; sincronizado with state

    pause_btn = ft.ElevatedButton(text="Pausar", width=175)
    resume_btn = ft.ElevatedButton(text="Continuar", width=175)
    # Inputs para intervalo mínimo e máximo (segundos)
    min_delay_field = ft.TextField(label="Delay mínimo (s)", value="3", width=175, border_radius=15)
    max_delay_field = ft.TextField(label="Delay máximo (s)", value="7", width=175, border_radius=15)

    # Funções dos botões pausa/continuar (agora atualizam state também)
    def on_pause(e):
        state["is_paused"] = True
        is_paused["value"] = True
        safe_update()

    def on_resume(e):
        state["is_paused"] = False
        is_paused["value"] = False
        safe_update()

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
        # sincroniza camada compatível
        if state["is_running"]:
            status.value = "⚠️ Disparo já em execução."
            safe_update()
            return

        linhas = arquivo_txt.value.strip().split("\n")
        if len(linhas) < 2:
            status.value = "❌ Arquivo inválido ou vazio."
            safe_update()
            return

        # marca execução no state e na compat layer
        state["is_running"] = True
        is_running["value"] = True
        state["is_paused"] = False
        is_paused["value"] = False

        status.value = "Iniciando disparo em lote..."
        safe_update()

        cabecalho = [h.strip() for h in linhas[0].strip().split(";")]
        total = len(linhas) - 1

        def worker():
            # variáveis locais para construir o relatório desta execução
            successes_before = state.get("successes", 0)
            failures_before = state.get("failures", 0)
            current_entries = []
            try:
                for i, linha in enumerate(linhas[1:], start=1):
                    # se houve pausa, aguarda até que seja despausado
                    while state["is_paused"]:
                        status.value = f"⏸️ Pausado em {i-1}/{total}. Aguardando continuar..."
                        safe_update()
                        time.sleep(0.2)  # espera curta para permitir reatividade

                    if not linha.strip():
                        # linha vazia
                        status.value = f"⚠️ Linha {i+1} ignorada: vazia."
                        safe_update()
                        continue

                    campos = [c.strip() for c in linha.strip().split(";")]
                    if len(campos) != len(cabecalho):
                        status.value = f"⚠️ Linha {i+1} ignorada: número de campos incorreto."
                        safe_update()
                        continue

                    dados = dict(zip(cabecalho, campos))
                    try:
                        mensagem = lote_msg_template.value.format(**dados)
                    except Exception as err:
                        status.value = f"❌ Erro ao formatar mensagem na linha {i+1}: {err}"
                        safe_update()
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
                        entry_status = "sucesso"
                        # atualiza estado de relatórios
                        state["total_sent"] += 1
                        state["successes"] += 1
                    except Exception as err:
                        status.value = f"❌ Erro ao enviar para {dados.get('nome','')}: {err}"
                        entry_status = "falha"
                        state["total_sent"] += 1
                        state["failures"] += 1

                    entry = {
                        "to": dados.get("nome", ""),
                        "email": dados.get("email", ""),
                        "phone": dados.get("telefone", ""),
                        "cnpj": dados.get("cnpj", ""),
                        "status": entry_status,
                        "time": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    state["recent_logs"].insert(0, entry)
                    state["recent_logs"] = state["recent_logs"][:200]
                    current_entries.append(entry)

                    # limita tamanho do log
                    state["recent_logs"] = state["recent_logs"][:200]
                    safe_update()

                    # após cada envio, aguarda intervalo aleatório entre min e max,
                    # respeitando pausa se acionada durante a espera
                    mn, mx = get_delays()
                    wait = random.uniform(mn, mx)
                    waited = 0.0
                    # subdivide espera em fatias pequenas para permitir pausa rápida
                    slice_dt = 0.2
                    while waited < wait:
                        if state["is_paused"]:
                            status.value = f"⏸️ Pausado após {i}/{total}. Aguardando continuar..."
                            safe_update()
                            # esperar enquanto estiver pausado
                            while state["is_paused"]:
                                time.sleep(0.2)
                        else:
                            time.sleep(slice_dt)
                            waited += slice_dt

            finally:
                # monta relatório desta execução
                successes_delta = state.get("successes", 0) - successes_before
                failures_delta = state.get("failures", 0) - failures_before
                report = {
                    "ts": time.time(),
                    "total": len(current_entries),
                    "successes": successes_delta,
                    "failures": failures_delta,
                    "entries": current_entries
                }
                state["reports"].insert(0, report)
                state["reports"] = state["reports"][:500]  # limitar
                _persist_reports()

                state["is_running"] = False
                is_running["value"] = False
                state["is_paused"] = False
                is_paused["value"] = False
                status.value = f"✅ Disparo em lote finalizado ({total} linhas processadas)."
                safe_update()

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    disparar_btn = ft.ElevatedButton("Disparar mensagens em lote", on_click=disparar_em_lote, width=360)

    # Containers das duas seções com altura fixa
    # Ajuste: Columns internas usam scroll=ft.ScrollMode.AUTO para rolagem independente
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
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True, alignment=ft.MainAxisAlignment.START),
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
            ft.Row([pause_btn, resume_btn], spacing=10),
            ft.Row([disparar_btn], spacing=10),
            ft.Text("Editar Mensagem Padrão", size=18, weight="bold"),
            lote_msg_template,
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True, alignment=ft.MainAxisAlignment.START),
        expand=True,
        height=container_height,
        padding=10,
        bgcolor=ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_850,
        border_radius=10
    )

    # monta a view Home (reutiliza containers existentes)
    def home_view():
        # header fica fixo; abaixo, a Row com as duas colunas roláveis
        return ft.Container(
            content=ft.Column([
                header,
                ft.Row([
                    individual_container,
                    ft.VerticalDivider(width=1),
                    lote_container
                ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
            ], spacing=10, expand=True),
            expand=True
        )

    # Navigation: callback que altera o state e reconstrói o body
    def on_nav_change(new_index: int):
        state["nav_index"] = new_index
        nav_component.selected_index = new_index
        build_body()

    nav_component = AppNavigation(on_change=on_nav_change, selected_index=state["nav_index"])

    # função que monta o conteúdo principal (Home ou Relatórios) e adiciona a NavigationBar
    def build_body():
        page.controls.clear()
        # header deixamos dentro de home_view para manter exatamente o layout atual na tela inicial
        if state["nav_index"] == 0:
            page.controls.append(home_view())
        else:
            # chama reports.build_reports, que lê o state para mostrar métricas
            page.controls.append(build_reports(state, page))
        # adiciona a navigation bar fixa embaixo
        page.controls.append(nav_component.build())
        safe_update()

    def toggle_theme(e):
        page.theme_mode = (
            ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        )
        theme_button.icon = (
            ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE
        )
        apply_theme()
        # rebuild body para aplicar cores corretamente
        build_body()

    # tenta carregar relatórios persistidos (se houver)
    try:
        saved = page.client_storage.get("dispatchr_reports")
        if saved:
            state["reports"] = saved
    except Exception:
        pass

    # inicializa a UI
    build_body()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
