# pages/reports.py
import flet as ft
import csv
import io
import time
import os
import platform
import subprocess
from typing import List, Dict

def _format_datetime(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

def _reports_summary(reports: List[Dict]) -> ft.Column:
    total_reports = len(reports)
    total_sent = sum(r.get("total", 0) for r in reports)
    total_success = sum(r.get("successes", 0) for r in reports)
    total_fail = sum(r.get("failures", 0) for r in reports)
    return ft.Column([
        ft.Text("Relatórios", size=24, weight="bold"),
        ft.Text(f"Relatórios gerados: {total_reports}"),
        ft.Text(f"Total mensagens: {total_sent}  |  Sucessos: {total_success}  |  Falhas: {total_fail}"),
    ], spacing=6)

def build_reports(state: dict, page):
    """
    Constrói a interface da aba Relatórios.
    - state: dicionário compartilhado do app (state['reports'] = list)
    - page: objeto Page do Flet
    """
    reports = state.setdefault("reports", [])  # lista de relatórios

    selected_report_detail = ft.Column([ft.Text("Selecione um relatório para ver detalhes.")], spacing=6, expand=True)

    def _show_report_detail(original_idx: int, display_id: int):
        # valida índice original
        if original_idx is None or original_idx < 0 or original_idx >= len(reports):
            selected_report_detail.controls = [ft.Text("Relatório não encontrado.")]
            page.update()
            return

        r = reports[original_idx]

        # mensagem visível imediatamente após clicar Exportar
        message_label = ft.Text("", color=ft.Colors.GREEN)

        # Cabeçalho com ID e timestamp
        header = ft.Column([
            ft.Text(f"Relatório ID: {display_id}", weight="bold", size=16),
            ft.Text(f"Gerado em: {_format_datetime(r.get('ts', 0))}"),
        ], spacing=4)

        # construir linhas de detalhe
        detail_rows = []
        for entry in r.get("entries", []):
            detail_rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(entry.get("to", ""))),
                ft.DataCell(ft.Text(entry.get("email", ""))),
                ft.DataCell(ft.Text(entry.get("phone", ""))),
                ft.DataCell(ft.Text(entry.get("cnpj", ""))),
                ft.DataCell(ft.Text(entry.get("status", ""))),
                ft.DataCell(ft.Text(entry.get("time", ""))),
            ]))

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("E-mail")),
                ft.DataColumn(ft.Text("Telefone")),
                ft.DataColumn(ft.Text("CNPJ")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Horário")),
            ],
            rows=detail_rows,
            width=780
        )

        table_scroll = ft.Column([table], scroll=ft.ScrollMode.AUTO, width=800, height=300)

        # Exporta CSV para Z:\DEV, usa display_id no nome do arquivo
        def on_export(_e):
            # exibe mensagem imediata independente do resultado
            message_label.value = "Relatório gerado"
            page.update()

            # prepara CSV em memória
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["nome", "email", "telefone", "cnpj", "status", "time"])
            for ent in r.get("entries", []):
                writer.writerow([
                    ent.get("to", ""),
                    ent.get("email", ""),
                    ent.get("phone", ""),
                    ent.get("cnpj", ""),
                    ent.get("status", ""),
                    ent.get("time", "")
                ])
            csv_data = output.getvalue().encode("utf-8")
            output.close()

            # pasta destino (ajuste se quiser subpasta)
            dest_dir = r"Z:\DEV\dispatchr_reports"
            try:
                os.makedirs(dest_dir, exist_ok=True)
            except Exception as err:
                # tenta também atualizar a mensagem de erro no label
                message_label.value = f"Erro criando pasta: {err}"
                page.update()
                return

            ts = int(r.get("ts", time.time()))
            file_name = f"report_id{display_id}_{ts}.csv"
            file_path = os.path.join(dest_dir, file_name)

            try:
                with open(file_path, "wb") as f:
                    f.write(csv_data)
            except Exception as err:
                message_label.value = f"Erro ao salvar arquivo: {err}"
                page.update()
                return

            # atualiza message_label confirmando sucesso (opcional)
            message_label.value = f"Relatório exportado com sucesso, visite: {file_path} para conferir."
            page.update()

            # se quiser SnackBar também, tenta exibir (pode não ser visível em alguns ambientes)
            try:
                page.snack_bar = ft.SnackBar(ft.Text(f"Relatório exportado com sucesso, visite {dest_dir} para conferir"), open=True, duration=3000)
                page.update()
            except Exception:
                pass

        export_btn = ft.ElevatedButton("Exportar CSV", on_click=on_export, width=160)

        selected_report_detail.controls = [
            # message_label sempre visível quando os detalhes são exibidos
            message_label,
            header,
            ft.Row([export_btn], spacing=10),
            table_scroll
        ]
        page.update()

    # Construir tabela com o mais recente como ID 1
    rows = []
    # iterate over original indices in reverse so display_id 1 = most recent
    for display_id, original_idx in enumerate(range(len(reports) - 1, -1, -1), start=1):
        r = reports[original_idx]
        # capture both original_idx and display_id in defaults to avoid late binding
        view_btn = ft.ElevatedButton("Ver", on_click=lambda e, oi=original_idx, di=display_id: _show_report_detail(oi, di), width=60)
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(str(display_id))),
            ft.DataCell(ft.Text(_format_datetime(r.get("ts", 0)))),
            ft.DataCell(ft.Text(str(r.get("total", 0)))),
            ft.DataCell(ft.Text(str(r.get("successes", 0)))),
            ft.DataCell(ft.Text(str(r.get("failures", 0)))),
            ft.DataCell(view_btn),
        ]))

    reports_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#")),
            ft.DataColumn(ft.Text("Gerado em")),
            ft.DataColumn(ft.Text("Total")),
            ft.DataColumn(ft.Text("Sucessos")),
            ft.DataColumn(ft.Text("Falhas")),
            ft.DataColumn(ft.Text("Ações")),
        ],
        rows=rows,
        width=780,
        height=220,
    )

    reports_table_container = ft.Column([reports_table], scroll=ft.ScrollMode.AUTO, width=800, height=260)

    body = ft.Column(
        [
            _reports_summary(reports),
            ft.Divider(),
            ft.Text("Histórico de relatórios", weight="bold"),
            reports_table_container,
            ft.Divider(),
            ft.Text("Detalhes do relatório", weight="bold"),
            selected_report_detail
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    if not reports:
        body.controls = [
            ft.Text("Relatórios", size=24, weight="bold"),
            ft.Text("Nenhum relatório disponível. As execuções de disparo irão gerar relatórios aqui."),
        ]

    return ft.Container(content=body, padding=20, expand=True)
