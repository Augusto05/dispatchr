# nav.py
from flet import NavigationBar, NavigationBarDestination, Icons

class AppNavigation:
    def __init__(self, on_change, selected_index: int = 0):
        self.on_change = on_change
        self.selected_index = selected_index

    def build(self):
        return NavigationBar(
            selected_index=self.selected_index,
            destinations=[
                NavigationBarDestination(icon=Icons.HOME, selected_icon=Icons.HOME, label="Início"),
                NavigationBarDestination(icon=Icons.INSIGHTS, selected_icon=Icons.INSIGHTS, label="Relatórios"),
            ],
            on_change=self._handle_change,
        )

    def _handle_change(self, e):
        self.selected_index = e.control.selected_index
        self.on_change(self.selected_index)
