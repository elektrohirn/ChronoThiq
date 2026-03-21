from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.app import App
import requests
from shared.constants import API_BASE_URL, STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_REVIEW, STATUS_DONE

class TaskFormScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.add_widget(self.layout)
        self.edit_mode = False
        self.task_id = None

    def on_enter(self):
        self.layout.clear_widgets()
        app = App.get_running_app()
        task = app.current_task

        self.edit_mode = task is not None
        self.task_id = task["id"] if task else None

        # Header
        header = BoxLayout(size_hint=(1, 0.08), spacing=10)
        back_btn = Button(
            text="< Zurück",
            size_hint=(0.2, 1),
            background_color=(0.4, 0.4, 0.4, 1)
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, "current", "network"))
        title = Label(
            text="Aufgabe bearbeiten" if self.edit_mode else "Neue Aufgabe",
            font_size=20,
            bold=True
        )
        header.add_widget(back_btn)
        header.add_widget(title)

        # Formular
        scroll = ScrollView(size_hint=(1, 0.84))
        form = GridLayout(
            cols=2,
            spacing=10,
            padding=10,
            size_hint_y=None
        )
        form.bind(minimum_height=form.setter("height"))

        # Name
        form.add_widget(Label(text="Name *", size_hint_y=None, height=40, halign="right"))
        self.name_input = TextInput(
            text=task["name"] if task else "",
            multiline=False,
            size_hint_y=None,
            height=40
        )
        form.add_widget(self.name_input)

        # Beschreibung
        form.add_widget(Label(text="Beschreibung", size_hint_y=None, height=80, halign="right"))
        self.desc_input = TextInput(
            text=task["description"] if task and task["description"] else "",
            multiline=True,
            size_hint_y=None,
            height=80
        )
        form.add_widget(self.desc_input)

        # Dauer
        form.add_widget(Label(text="Dauer (Tage) *", size_hint_y=None, height=40, halign="right"))
        self.duration_input = TextInput(
            text=str(task["duration"]) if task else "1",
            multiline=False,
            size_hint_y=None,
            height=40
        )
        form.add_widget(self.duration_input)

        # Status (nur im Edit-Modus)
        if self.edit_mode:
            form.add_widget(Label(text="Status", size_hint_y=None, height=40, halign="right"))
            self.status_spinner = Spinner(
                text=task["status"] if task else STATUS_OPEN,
                values=[STATUS_OPEN, STATUS_IN_PROGRESS, STATUS_REVIEW, STATUS_DONE],
                size_hint_y=None,
                height=40
            )
            form.add_widget(self.status_spinner)

        # Vorgänger IDs
        form.add_widget(Label(text="Vorgänger IDs\n(kommagetrennt)", size_hint_y=None, height=60, halign="right"))
        self.pred_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=40
        )
        form.add_widget(self.pred_input)

        # FAZ manuell
        form.add_widget(Label(text="FAZ (manuell)", size_hint_y=None, height=40, halign="right"))
        self.faz_input = TextInput(
            text=str(task["faz"]) if task else "0",
            multiline=False,
            size_hint_y=None,
            height=40
        )
        form.add_widget(self.faz_input)

        # SAZ manuell
        form.add_widget(Label(text="SAZ (manuell)", size_hint_y=None, height=40, halign="right"))
        self.saz_input = TextInput(
            text=str(task["saz"]) if task else "0",
            multiline=False,
            size_hint_y=None,
            height=40
        )
        form.add_widget(self.saz_input)

        scroll.add_widget(form)

        # Fehleranzeige
        self.error_label = Label(
            text="",
            color=(1, 0.2, 0.2, 1),
            size_hint=(1, 0.04)
        )

        # Buttons
        btn_row = BoxLayout(size_hint=(1, 0.08), spacing=10)
        save_btn = Button(
            text="Speichern",
            background_color=(0.2, 0.7, 0.3, 1)
        )
        save_btn.bind(on_press=self.save_task)

        if self.edit_mode:
            delete_btn = Button(
                text="Löschen",
                background_color=(0.8, 0.2, 0.2, 1)
            )
            delete_btn.bind(on_press=self.delete_task)
            btn_row.add_widget(delete_btn)

        btn_row.add_widget(save_btn)

        self.layout.add_widget(header)
        self.layout.add_widget(scroll)
        self.layout.add_widget(self.error_label)
        self.layout.add_widget(btn_row)

    def save_task(self, instance):
        app = App.get_running_app()
        project = app.current_project

        name = self.name_input.text.strip()
        if not name:
            self.error_label.text = "Name ist erforderlich"
            return

        try:
            duration = float(self.duration_input.text.strip())
        except ValueError:
            self.error_label.text = "Dauer muss eine Zahl sein"
            return

        pred_ids = []
        if self.pred_input.text.strip():
            try:
                pred_ids = [int(x.strip()) for x in self.pred_input.text.split(",")]
            except ValueError:
                self.error_label.text = "Ungültige Vorgänger IDs"
                return

        try:
            if self.edit_mode:
                payload = {
                    "name": name,
                    "description": self.desc_input.text.strip(),
                    "duration": duration,
                    "status": self.status_spinner.text
                }
                response = requests.put(
                    f"{API_BASE_URL}/tasks/{self.task_id}",
                    params={"token": app.token},
                    json=payload
                )
            else:
                payload = {
                    "name": name,
                    "description": self.desc_input.text.strip(),
                    "duration": duration,
                    "project_id": project["id"],
                    "predecessor_ids": pred_ids
                }
                response = requests.post(
                    f"{API_BASE_URL}/tasks/",
                    params={"token": app.token},
                    json=payload
                )

            if response.status_code == 200:
                app.current_task = None
                self.manager.current = "network"
            else:
                self.error_label.text = f"Fehler: {response.status_code}"
        except Exception as e:
            self.error_label.text = f"Verbindungsfehler: {str(e)}"

    def delete_task(self, instance):
        app = App.get_running_app()
        try:
            response = requests.delete(
                f"{API_BASE_URL}/tasks/{self.task_id}",
                params={"token": app.token}
            )
            if response.status_code == 200:
                app.current_task = None
                self.manager.current = "network"
            else:
                self.error_label.text = f"Fehler: {response.status_code}"
        except Exception as e:
            self.error_label.text = f"Verbindungsfehler: {str(e)}"