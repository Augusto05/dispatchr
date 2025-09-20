# app_simplegui.py

import PySimpleGUI as sg
from chatwoot_client import dispatch_message

try:
    sg.theme("DarkBlue3")
except AttributeError:
    sg.change_look_and_feel("DarkBlue3")


layout = [
    [sg.Text("Nome:"),     sg.Input(key="-NAME-", size=(30,1))],
    [sg.Text("E-mail:"),   sg.Input(key="-EMAIL-", size=(30,1))],
    [sg.Text("Telefone:"), sg.Input(key="-PHONE-", size=(30,1))],
    [sg.Text("CNPJ:"),     sg.Input(key="-CNPJ-", size=(30,1))],
    [sg.Text("Mensagem:")],
    [sg.Multiline(key="-MSG-", size=(50,5))],
    [sg.Button("Enviar"), sg.Button("Sair")],
    [sg.StatusBar("", size=(60,1), key="-STATUS-")]
]

window = sg.Window("Chatwoot Sender", layout)

while True:
    event, vals = window.read()
    if event in (sg.WIN_CLOSED, "Sair"):
        break
    if event == "Enviar":
        window["-STATUS-"].update("Enviando…")
        try:
            msg_id = dispatch_message(
                name    = vals["-NAME-"],
                email   = vals["-EMAIL-"],
                phone   = vals["-PHONE-"],
                cnpj    = vals["-CNPJ-"],
                content = vals["-MSG-"]
            )
            window["-STATUS-"].update(f"✅ Enviado! ID: {msg_id}")
        except Exception as e:
            window["-STATUS-"].update(f"❌ Erro: {e}")

window.close()
