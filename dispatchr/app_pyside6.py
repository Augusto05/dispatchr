#!/usr/bin/env python3
# app_pyside6.py

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QMessageBox, QVBoxLayout,
    QGroupBox, QHBoxLayout, QSpacerItem,
    QSizePolicy
)
from PySide6.QtGui import QIcon, QFont
import qdarkstyle

from chatwoot_client import dispatch_message  # módulo base que já gera o identifier

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chatwoot Sender")
        self.setWindowIcon(QIcon("app_icon.png"))    # opcional: coloque um ícone no diretório
        self.setMinimumSize(450, 550)
        self.setFont(QFont("Segoe UI", 10))

        # Container central
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ─── Grupo: Dados do Contato ─────────────────────
        contact_group = QGroupBox("Dados do Contato")
        form = QFormLayout()

        self.name_input  = QLineEdit(); self.name_input.setPlaceholderText("Ex: João Silva")
        self.email_input = QLineEdit(); self.email_input.setPlaceholderText("joao@exemplo.com")
        self.phone_input = QLineEdit(); self.phone_input.setPlaceholderText("(XX) 9XXXX-XXXX")
        self.cnpj_input  = QLineEdit(); self.cnpj_input.setPlaceholderText("00.000.000/0000-00")

        form.addRow("Nome:",     self.name_input)
        form.addRow("E-mail:",   self.email_input)
        form.addRow("Telefone:", self.phone_input)
        form.addRow("CNPJ:",     self.cnpj_input)

        contact_group.setLayout(form)
        main_layout.addWidget(contact_group)

        # ─── Grupo: Mensagem ─────────────────────────────
        message_group = QGroupBox("Mensagem")
        msg_layout    = QVBoxLayout()
        self.msg_input = QTextEdit()
        self.msg_input.setPlaceholderText("Digite a mensagem aqui...")
        msg_layout.addWidget(self.msg_input)
        message_group.setLayout(msg_layout)
        main_layout.addWidget(message_group)

        # ─── Botão Enviar ───────────────────────────────
        button_layout = QHBoxLayout()
        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.send_btn = QPushButton("Enviar")
        self.send_btn.clicked.connect(self.on_send)
        button_layout.addItem(spacer)
        button_layout.addWidget(self.send_btn)
        main_layout.addLayout(button_layout)

        self.setCentralWidget(central)

    def on_send(self):
        self.send_btn.setEnabled(False)
        try:
            # dispatch_message agora gera o identifier (JID do WhatsApp) internamente
            msg_id = dispatch_message(
                name    = self.name_input.text(),
                email   = self.email_input.text(),
                phone   = self.phone_input.text(),
                cnpj    = self.cnpj_input.text(),
                content = self.msg_input.toPlainText()
            )
            QMessageBox.information(
                self,
                "Sucesso",
                f"Mensagem enviada com sucesso!\nID da mensagem: {msg_id}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao enviar", str(e))
        finally:
            self.send_btn.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # aplica tema Fusion + QDarkStyle
    app.setStyle("Fusion")
    app.setStyleSheet(qdarkstyle.load_stylesheet())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
