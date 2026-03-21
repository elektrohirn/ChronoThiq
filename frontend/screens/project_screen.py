from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App
import requests
from shared.constants import API_BASE_URL, ROLE_ADMIN, ROLE_MANAGER

class ProjectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.add_widget(self.layout)

    def on_enter(self):
        self.layout.clear_widgets()
        app = App.get_running_app()
        project = app.current_project

        # Header
        header = BoxLayout(size_hint=(1, 0.1), spacing=10)
        back_btn = Button(
            text="< Zurück",
            size_hint=(0.2, 1),
            background_color=(0.4, 0.4, 0.4, 1)
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, "current", "dashboard"))
        title = Label(
            text=project["name"],
            font_size=22,
            bold=True
        )
        header.add_widget(back_btn)
        header.add_widget(title)

        # Beschreibung
        desc = Label(
            text=project.get("description") or "Keine Beschreibung",
            size_hint=(1, 0.06),
            color=(0.7, 0.7, 0.7, 1)
        )

        # Aktionsbuttons
        btn_row = BoxLayout(size_hint=(1, 0.08), spacing=10)
        netzplan_btn = Button(
            text="Netzplan",
            background_color=(0.2, 0.6, 1, 1)
        )
        netzplan_btn.bind(on_press=lambda x: setattr(self.manager, "current", "network"))

        gantt_btn = Button(
            text="Gantt-Diagramm",
            background_color=(0.5, 0.2, 0.8, 1)
        )
        gantt_btn.bind(on_press=lambda x: setattr(self.manager, "current", "gantt"))

        btn_row.add_widget(netzplan_btn)
        btn_row.add_widget(gantt_btn)

        # Aufgabenliste
        tasks_label = Label(
            text="Aufgaben",
            font_size=18,
            bold=True,
            size_hint=(1, 0.06)
        )

        scroll = ScrollView(size_hint=(1, 0.7))
        self.tasks_grid = GridLayout(
            cols=1,
            spacing=8,
            size_hint_y=None
        )
        self.tasks_grid.bind(minimum_height=self.tasks_grid.setter("height"))
        scroll.add_widget(self.tasks_grid)

        self.layout.add_widget(header)
        self.layout.add_widget(desc)
        self.layout.add_widget(btn_row)
        self.layout.add_widget(tasks_label)
        self.layout.add_widget(scroll)

        self.load_tasks()

    def load_tasks(self):
        app = App.get_running_app()
        project = app.current_project
        self.tasks_grid.clear_widgets()
        try:
            response = requests.get(
                f"{API_BASE_URL}/tasks/project/{project['id']}",
                params={"token": app.token}
            )
            if response.status_code == 200:
                tasks = response.json()
                if not tasks:
                    self.tasks_grid.add_widget(
                        Label(text="Noch keine Aufgaben vorhanden", size_hint_y=None, height=50)
                    )
                for task in tasks:
                    row = BoxLayout(size_hint_y=None, height=60, spacing=5)
                    name_btn = Button(
                        text=f"{task['name']} | Dauer: {task['duration']} | Status: {task['status']}",
                        background_color=(0.15, 0.15, 0.2, 1)
                    )
                    progress_label = Label(
                        text=f"{task['progress']}%",
                        size_hint=(0.15, 1),
                        color=(0.2, 0.8, 0.2, 1)
                    )
                    row.add_widget(name_btn)
                    row.add_widget(progress_label)
                    self.tasks_grid.add_widget(row)
        except Exception as e:
            self.tasks_grid.add_widget(
                Label(text=f"Fehler: {str(e)}", size_hint_y=None, height=50)
            )