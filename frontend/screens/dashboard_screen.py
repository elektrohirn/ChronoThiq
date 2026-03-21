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
from kivy.uix.popup import Popup
from kivy.app import App
from shared.constants import API_BASE_URL

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        app = App.get_running_app()

        header = BoxLayout(size_hint=(1, 0.1), spacing=10)
        title = Label(text=f"Willkommen, {app.current_user['username']}", font_size=24, bold=True)
        logout_btn = Button(text="Abmelden", size_hint=(0.2, 1), background_color=(0.8, 0.2, 0.2, 1))
        logout_btn.bind(on_press=self.do_logout)
        header.add_widget(title)
        header.add_widget(logout_btn)

        btn_row = BoxLayout(size_hint=(1, 0.08), spacing=10)
        new_project_btn = Button(text="+ Neues Projekt", background_color=(0.2, 0.7, 0.3, 1))
        new_project_btn.bind(on_press=self.open_new_project_form)
        btn_row.add_widget(new_project_btn)

        if app.current_user.get("role") == "admin":
            users_btn = Button(text="Nutzerverwaltung", background_color=(0.2, 0.4, 0.8, 1))
            users_btn.bind(on_press=lambda x: setattr(self.manager, "current", "users"))
            btn_row.add_widget(users_btn)

        projects_label = Label(text="Meine Projekte", font_size=18, bold=True, size_hint=(1, 0.06))

        scroll = ScrollView(size_hint=(1, 0.76))
        self.projects_grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.projects_grid.bind(minimum_height=self.projects_grid.setter("height"))
        scroll.add_widget(self.projects_grid)

        self.layout.add_widget(header)
        self.layout.add_widget(btn_row)
        self.layout.add_widget(projects_label)
        self.layout.add_widget(scroll)

        self.load_projects()

    def load_projects(self):
        app = App.get_running_app()
        self.projects_grid.clear_widgets()
        try:
            response = requests.get(
                f"{API_BASE_URL}/projects/",
                params={"token": app.token}
            )
            if response.status_code == 200:
                projects = response.json()
                if not projects:
                    self.projects_grid.add_widget(
                        Label(text="Noch keine Projekte vorhanden", size_hint_y=None, height=50)
                    )
                for project in projects:
                    btn = Button(
                        text=project["name"],
                        size_hint_y=None,
                        height=60,
                        background_color=(0.15, 0.15, 0.2, 1)
                    )
                    btn.bind(on_press=lambda instance, p=project: self.open_project(p))
                    self.projects_grid.add_widget(btn)
        except Exception as e:
            self.projects_grid.add_widget(
                Label(text=f"Fehler: {str(e)}", size_hint_y=None, height=50)
            )

    def open_project(self, project):
        app = App.get_running_app()
        app.current_project = project
        self.manager.current = "project"

    def open_new_project_form(self, instance):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        name_input = TextInput(hint_text="Projektname", multiline=False, size_hint=(1, None), height=40)
        desc_input = TextInput(hint_text="Beschreibung", multiline=True, size_hint=(1, None), height=80)
        error_label = Label(text="", color=(1, 0.2, 0.2, 1), size_hint=(1, None), height=30)
        btn_row = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        save_btn = Button(text="Erstellen", background_color=(0.2, 0.7, 0.3, 1))
        cancel_btn = Button(text="Abbrechen", background_color=(0.8, 0.2, 0.2, 1))
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(name_input)
        content.add_widget(desc_input)
        content.add_widget(error_label)
        content.add_widget(btn_row)
        popup = Popup(title="Neues Projekt", content=content, size_hint=(0.8, 0.5))

        def save(instance):
            if not name_input.text.strip():
                error_label.text = "Bitte einen Projektnamen eingeben"
                return
            app = App.get_running_app()
            try:
                response = requests.post(
                    f"{API_BASE_URL}/projects/",
                    params={"token": app.token},
                    json={"name": name_input.text.strip(), "description": desc_input.text.strip()}
                )
                if response.status_code == 200:
                    popup.dismiss()
                    self.load_projects()
                else:
                    error_label.text = "Fehler beim Erstellen"
            except Exception as e:
                error_label.text = f"Verbindungsfehler: {str(e)}"

        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def do_logout(self, instance):
        app = App.get_running_app()
        app.token = None
        app.current_user = None
        app.current_project = None
        self.manager.current = "login"