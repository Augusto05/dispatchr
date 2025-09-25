# reports.py
import flet as ft

def build_reports(state: dict):
    """
    Tela de Relatórios temporariamente vazia.
    Retorna um controle simples com a mensagem "Em breve".
    """
    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Relatórios", size=24, weight="bold"),
                ft.Text("Em breve", size=16),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            expand=True,
        ),
        padding=20,
        expand=True,
    )
