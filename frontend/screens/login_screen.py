import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from shared.constants import API_BASE_URL

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", padding=40, spacing=20)

        title = Label(
            text="Netzplan App",
            font_size=32,
            bold=True,
            size_hint=(1, 0.3)
        )

        self.username_input = TextInput(
            hint_text="Benutzername",
            multiline=False,
            size_hint=(1, 0.1)
        )

        self.password_input = TextInput(
            hint_text="Passwort",
            password=True,
            multiline=False,
            size_hint=(1, 0.1)
        )

        login_btn = Button(
            text="Anmelden",
            size_hint=(1, 0.1),
            background_color=(0.2, 0.6, 1, 1)
        )
        login_btn.bind(on_press=self.do_login)

        self.error_label = Label(
            text="",
            color=(1, 0.2, 0.2, 1),
            size_hint=(1, 0.1)
        )

        layout.add_widget(title)
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(login_btn)
        layout.add_widget(self.error_label)

        self.add_widget(layout)

    def do_login(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        if not username or not password:
            self.error_label.text = "Bitte alle Felder ausfüllen"
            return

        try:
            response = requests.post(
                f"{API_BASE_URL}/login",
                params={"username": username, "password": password}
            )
            print(f"Status: {response.status_code}")
            print(f"Antwort: {response.text}")
            if response.status_code == 200:
                data = response.json()
                app = App.get_running_app()
                app.token = data["access_token"]
                app.current_user = {
                    "id": data["user_id"],
                    "username": data["username"],
                    "role": data["role"]
                }
                self.manager.current = "dashboard"
            else:
                self.error_label.text = f"Fehler {response.status_code}: {response.text}"
        except Exception as e:
            self.error_label.text = f"Verbindungsfehler: {str(e)}"