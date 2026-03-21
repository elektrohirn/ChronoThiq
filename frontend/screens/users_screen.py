import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.app import App
from shared.constants import API_BASE_URL, ROLE_ADMIN, ROLE_MANAGER, ROLE_MEMBER

class UsersScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        app = App.get_running_app()

        header = BoxLayout(size_hint=(1, 0.08), spacing=10)
        back_btn = Button(text="< Zurück", size_hint=(0.2, 1), background_color=(0.4, 0.4, 0.4, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, "current", "dashboard"))
        title = Label(text="Nutzerverwaltung", font_size=22, bold=True)
        add_btn = Button(text="+ Nutzer", size_hint=(0.2, 1), background_color=(0.2, 0.7, 0.3, 1))
        add_btn.bind(on_press=self.open_add_user_form)
        header.add_widget(back_btn)
        header.add_widget(title)
        header.add_widget(add_btn)

        scroll = ScrollView(size_hint=(1, 0.92))
        self.users_grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.users_grid.bind(minimum_height=self.users_grid.setter("height"))
        scroll.add_widget(self.users_grid)

        self.layout.add_widget(header)
        self.layout.add_widget(scroll)

        self.load_users()

    def load_users(self):
        app = App.get_running_app()
        self.users_grid.clear_widgets()
        try:
            response = requests.get(
                f"{API_BASE_URL}/users/",
                params={"token": app.token}
            )
            if response.status_code == 200:
                users = response.json()
                if not users:
                    self.users_grid.add_widget(Label(text="Keine Nutzer vorhanden", size_hint_y=None, height=50))
                for user in users:
                    row = BoxLayout(size_hint_y=None, height=60, spacing=8)
                    info = Label(
                        text=f"{user['username']}  |  {user['email']}  |  {user['role']}",
                        size_hint=(1, 1),
                        halign="left",
                        valign="middle"
                    )
                    info.bind(size=info.setter("text_size"))
                    delete_btn = Button(
                        text="Löschen",
                        size_hint=(None, 1),
                        width=100,
                        background_color=(0.8, 0.2, 0.2, 1)
                    )
                    delete_btn.bind(on_press=lambda instance, u=user: self.confirm_delete(u))
                    row.add_widget(info)
                    row.add_widget(delete_btn)
                    self.users_grid.add_widget(row)
            else:
                self.users_grid.add_widget(Label(text=f"Fehler: {response.status_code}", size_hint_y=None, height=50))
        except Exception as e:
            self.users_grid.add_widget(Label(text=f"Verbindungsfehler: {str(e)}", size_hint_y=None, height=50))

    def open_add_user_form(self, instance):
        app = App.get_running_app()
        content = BoxLayout(orientation="vertical", padding=10, spacing=8)
        username_input = TextInput(hint_text="Benutzername", multiline=False, size_hint=(1, None), height=40)
        email_input = TextInput(hint_text="E-Mail", multiline=False, size_hint=(1, None), height=40)
        password_input = TextInput(hint_text="Passwort", password=True, multiline=False, size_hint=(1, None), height=40)
        role_label = Label(text="Rolle:", size_hint=(1, None), height=25, halign="left")
        role_spinner = Spinner(
            text=ROLE_MEMBER,
            values=[ROLE_ADMIN, ROLE_MANAGER, ROLE_MEMBER],
            size_hint=(1, None),
            height=40
        )
        error_label = Label(text="", color=(1, 0.2, 0.2, 1), size_hint=(1, None), height=30)
        btn_row = BoxLayout(size_hint=(1, None), height=44, spacing=10)
        save_btn = Button(text="Erstellen", background_color=(0.2, 0.7, 0.3, 1))
        cancel_btn = Button(text="Abbrechen", background_color=(0.4, 0.4, 0.4, 1))
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(username_input)
        content.add_widget(email_input)
        content.add_widget(password_input)
        content.add_widget(role_label)
        content.add_widget(role_spinner)
        content.add_widget(error_label)
        content.add_widget(btn_row)
        popup = Popup(title="Neuen Nutzer anlegen", content=content, size_hint=(0.8, 0.7))

        def save(instance):
            if not username_input.text.strip() or not email_input.text.strip() or not password_input.text.strip():
                error_label.text = "Alle Felder ausfüllen"
                return
            try:
                response = requests.post(
                    f"{API_BASE_URL}/users/",
                    json={
                        "username": username_input.text.strip(),
                        "email": email_input.text.strip(),
                        "password": password_input.text.strip(),
                        "role": role_spinner.text
                    }
                )
                if response.status_code == 200:
                    popup.dismiss()
                    self.load_users()
                else:
                    error_label.text = f"Fehler: {response.json().get('detail', response.status_code)}"
            except Exception as e:
                error_label.text = f"Verbindungsfehler: {str(e)}"

        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def confirm_delete(self, user):
        app = App.get_running_app()
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(Label(text=f"'{user['username']}' wirklich löschen?"))
        btn_row = BoxLayout(size_hint=(1, None), height=44, spacing=10)
        yes_btn = Button(text="Ja, löschen", background_color=(0.8, 0.2, 0.2, 1))
        no_btn = Button(text="Abbrechen", background_color=(0.4, 0.4, 0.4, 1))
        btn_row.add_widget(yes_btn)
        btn_row.add_widget(no_btn)
        content.add_widget(btn_row)
        popup = Popup(title="Löschen bestätigen", content=content, size_hint=(0.6, 0.3))

        def confirm(instance):
            popup.dismiss()
            try:
                requests.delete(
                    f"{API_BASE_URL}/users/{user['id']}",
                    params={"token": app.token}
                )
                self.load_users()
            except Exception as e:
                print(f"Fehler: {str(e)}")

        yes_btn.bind(on_press=confirm)
        no_btn.bind(on_press=popup.dismiss)
        popup.open()