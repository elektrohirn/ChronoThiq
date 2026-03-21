import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Line, Rectangle
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from shared.constants import API_BASE_URL
from widgets.node_widget import NodeWidget
from widgets.tooltip_widget import TooltipWidget

CANVAS_COLS = 40
CANVAS_ROWS = 20
CRITICAL_ROW = 6

def get_grid_size(zoom=1.0):
    return max(40, int(max(80, Window.height // 8) * zoom))

class NetworkScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.tooltip = None
        self.tasks = []
        self.parent_task = None
        self.node_widgets = {}
        self.zoom = 1.0
        self.add_widget(self.layout)

    def get_gs(self):
        return get_grid_size(self.zoom)

    def on_enter(self):
        self.layout.clear_widgets()
        self.node_widgets = {}
        app = App.get_running_app()
        project = app.current_project
        self.parent_task = app.current_task

        header = BoxLayout(size_hint=(1, 0.08), padding=10, spacing=10)
        back_btn = Button(text="< Zurück", size_hint=(0.15, 1), background_color=(0.4, 0.4, 0.4, 1))
        if self.parent_task:
            back_btn.bind(on_press=self.go_back)
            title = Label(text=f"Teilaufgaben: {self.parent_task['name']}", font_size=18, bold=True)
        else:
            back_btn.bind(on_press=lambda x: setattr(self.manager, "current", "project"))
            title = Label(text=f"Netzplan: {project['name']}", font_size=18, bold=True)
        add_btn = Button(text="+ Aufgabe", size_hint=(0.15, 1), background_color=(0.2, 0.7, 0.3, 1))
        add_btn.bind(on_press=self.open_task_form)
        png_btn = Button(text="PNG", size_hint=(0.1, 1), background_color=(0.3, 0.5, 0.8, 1))
        png_btn.bind(on_press=self.export_png)
        pdf_btn = Button(text="PDF", size_hint=(0.1, 1), background_color=(0.5, 0.2, 0.8, 1))
        pdf_btn.bind(on_press=self.export_pdf)
        header.add_widget(back_btn)
        header.add_widget(title)
        header.add_widget(add_btn)
        header.add_widget(png_btn)
        header.add_widget(pdf_btn)

        self.canvas_scroll = ScrollView(size_hint=(1, 0.86))
        gs = self.get_gs()
        self.canvas_area = FloatLayout(size_hint=(None, None), size=(CANVAS_COLS * gs, CANVAS_ROWS * gs))
        self.canvas_scroll.add_widget(self.canvas_area)

        zoom_bar = BoxLayout(size_hint=(1, 0.06), padding=(10, 4), spacing=10)
        zoom_out_btn = Button(text="−", size_hint=(None, 1), width=40, background_color=(0.3, 0.3, 0.3, 1))
        zoom_out_btn.bind(on_press=lambda x: self.change_zoom(-0.1))
        self.zoom_slider = Slider(min=0.3, max=2.0, value=self.zoom, size_hint=(1, 1))
        self.zoom_slider.bind(value=self.on_zoom_slider)
        zoom_in_btn = Button(text="+", size_hint=(None, 1), width=40, background_color=(0.3, 0.3, 0.3, 1))
        zoom_in_btn.bind(on_press=lambda x: self.change_zoom(0.1))
        self.zoom_label = Label(text=f"{int(self.zoom * 100)}%", size_hint=(None, 1), width=55, color=(0.7, 0.7, 0.7, 1))
        zoom_bar.add_widget(zoom_out_btn)
        zoom_bar.add_widget(self.zoom_slider)
        zoom_bar.add_widget(zoom_in_btn)
        zoom_bar.add_widget(self.zoom_label)

        self.layout.add_widget(header)
        self.layout.add_widget(self.canvas_scroll)
        self.layout.add_widget(zoom_bar)

        self.load_tasks()

    def change_zoom(self, delta):
        self.zoom = max(0.3, min(2.0, round(self.zoom + delta, 2)))
        self.zoom_slider.value = self.zoom
        self.zoom_label.text = f"{int(self.zoom * 100)}%"
        self.redraw()

    def on_zoom_slider(self, instance, value):
        self.zoom = round(value, 2)
        self.zoom_label.text = f"{int(self.zoom * 100)}%"
        Clock.schedule_once(lambda dt: self.redraw(), 0.05)

    def redraw(self):
        gs = self.get_gs()
        self.canvas_area.size = (CANVAS_COLS * gs, CANVAS_ROWS * gs)
        self.canvas_area.clear_widgets()
        self.node_widgets = {}
        self.draw_grid()
        self.draw_nodes()
        Clock.schedule_once(lambda dt: self.draw_connections(), 0.15)

    def draw_grid(self):
        gs = self.get_gs()
        canvas_width = CANVAS_COLS * gs
        canvas_height = CANVAS_ROWS * gs
        critical_y = canvas_height - CRITICAL_ROW * gs
        self.canvas_area.canvas.before.clear()
        with self.canvas_area.canvas.before:
            Color(0.09, 0.09, 0.13, 1)
            Rectangle(pos=(0, 0), size=(canvas_width, canvas_height))
            Color(0.4, 0.08, 0.08, 0.35)
            Rectangle(pos=(0, critical_y), size=(canvas_width, gs))
            Color(0.2, 0.2, 0.25, 1)
            for i in range(CANVAS_COLS + 1):
                x = i * gs
                Line(points=[x, 0, x, canvas_height], width=0.6)
            for i in range(CANVAS_ROWS + 1):
                y = i * gs
                Line(points=[0, y, canvas_width, y], width=0.6)
        for i in range(CANVAS_COLS):
            x = i * gs
            lbl = Label(
                text=f"T{i}",
                pos=(x + 4, canvas_height - gs + 4),
                size_hint=(None, None),
                size=(gs - 4, gs - 8),
                font_size=max(8, gs // 10),
                bold=True,
                color=(0.45, 0.55, 0.75, 1),
                halign="left",
                valign="middle"
            )
            self.canvas_area.add_widget(lbl)

    def go_back(self, instance):
        app = App.get_running_app()
        if self.parent_task and self.parent_task.get("parent_id"):
            try:
                response = requests.get(
                    f"{API_BASE_URL}/tasks/{self.parent_task['parent_id']}",
                    params={"token": app.token}
                )
                app.current_task = response.json() if response.status_code == 200 else None
            except:
                app.current_task = None
        else:
            app.current_task = None
        self.on_enter()

    def load_tasks(self):
        app = App.get_running_app()
        self.canvas_area.clear_widgets()
        self.node_widgets = {}
        try:
            if self.parent_task:
                response = requests.get(
                    f"{API_BASE_URL}/tasks/{self.parent_task['id']}/subtasks",
                    params={"token": app.token}
                )
            else:
                response = requests.get(
                    f"{API_BASE_URL}/tasks/project/{app.current_project['id']}",
                    params={"token": app.token}
                )
            if response.status_code == 200:
                self.tasks = response.json()
                self.draw_grid()
                self.draw_nodes()
                Clock.schedule_once(lambda dt: self.draw_connections(), 0.15)
            else:
                self.canvas_area.add_widget(Label(text=f"Fehler: {response.status_code}", pos=(100, 300)))
        except Exception as e:
            self.canvas_area.add_widget(Label(text=f"Verbindungsfehler: {str(e)}", pos=(100, 300)))

    def get_subtasks_for_task(self, task_id):
        app = App.get_running_app()
        try:
            response = requests.get(
                f"{API_BASE_URL}/tasks/{task_id}/subtasks",
                params={"token": app.token}
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []

    def draw_nodes(self):
        gs = self.get_gs()
        canvas_height = CANVAS_ROWS * gs
        for i, task in enumerate(self.tasks):
            subtasks = self.get_subtasks_for_task(task["id"])
            node_width = max(gs, int(task["duration"]) * gs)
            grid_col = int(task["pos_x"]) if task["pos_x"] else i + 1
            grid_row = int(task["pos_y"]) if task["pos_y"] else CRITICAL_ROW
            pixel_x = grid_col * gs
            pixel_y = canvas_height - (grid_row + 1) * gs
            node = NodeWidget(
                task=task,
                on_move=self.on_node_moved,
                on_hover=self.show_tooltip,
                on_click=self.open_subtasks,
                on_status=self.on_status_change,
                on_edit=self.open_edit_form,
                on_delete=self.on_delete_task,
                index=i,
                subtasks=subtasks,
                grid_size=gs,
                size_hint=(None, None),
                size=(node_width, gs),
                pos=(pixel_x, pixel_y)
            )
            self.canvas_area.add_widget(node)
            self.node_widgets[task["id"]] = node

    def draw_connections(self, *args):
        self.canvas_area.canvas.after.clear()
        with self.canvas_area.canvas.after:
            for task in self.tasks:
                for pred in task.get("predecessors", []):
                    pred_task = next((t for t in self.tasks if t["id"] == pred.get("predecessor_id")), None)
                    if pred_task:
                        n1 = self.node_widgets.get(pred_task["id"])
                        n2 = self.node_widgets.get(task["id"])
                        if n1 and n2:
                            x1 = n1.x + n1.width
                            y1 = n1.y + n1.height / 2
                            x2 = n2.x
                            y2 = n2.y + n2.height / 2
                            is_critical = task["gp"] == 0 and pred_task["gp"] == 0
                            Color(0.9, 0.2, 0.2, 1) if is_critical else Color(0.4, 0.6, 1, 1)
                            Line(points=[x1, y1, x2, y2], width=1.5)

    def recalculate_cpm(self):
        task_map = {t["id"]: t for t in self.tasks}
        dep_map = {}
        for t in self.tasks:
            for pred in t.get("predecessors", []):
                if t["id"] not in dep_map:
                    dep_map[t["id"]] = []
                dep_map[t["id"]].append(pred["predecessor_id"])
        for task in self.tasks:
            preds = dep_map.get(task["id"], [])
            if not preds:
                task["faz"] = float(task["pos_x"]) if task["pos_x"] else 0.0
            else:
                task["faz"] = max(task_map[p]["fez"] for p in preds if p in task_map)
            task["fez"] = round(task["faz"] + task["duration"], 1)
        max_fez = max((t["fez"] for t in self.tasks), default=0.0)
        for task in reversed(self.tasks):
            successors = [t for t in self.tasks if task["id"] in dep_map.get(t["id"], [])]
            task["sez"] = min(s["saz"] for s in successors) if successors else max_fez
            task["saz"] = round(task["sez"] - task["duration"], 1)
            task["gp"] = round(task["saz"] - task["faz"], 1)
            task["fp"] = 0.0

    def on_node_moved(self, task_id, pixel_x, pixel_y, gs):
        app = App.get_running_app()
        canvas_height = CANVAS_ROWS * gs
        grid_col = round(pixel_x / gs)
        grid_row = round((canvas_height - pixel_y) / gs) - 1
        for t in self.tasks:
            if t["id"] == task_id:
                t["pos_x"] = grid_col
                t["pos_y"] = grid_row
                t["faz"] = float(grid_col)
                t["fez"] = round(t["faz"] + t["duration"], 1)
                break
        self.recalculate_cpm()
        self.draw_connections()
        try:
            requests.put(
                f"{API_BASE_URL}/tasks/{task_id}",
                params={"token": app.token},
                json={"pos_x": float(grid_col), "pos_y": float(grid_row)}
            )
        except Exception:
            pass

    def on_status_change(self, task, new_status):
        app = App.get_running_app()
        try:
            requests.put(
                f"{API_BASE_URL}/tasks/{task['id']}",
                params={"token": app.token},
                json={"status": new_status}
            )
            self.load_tasks()
        except Exception as e:
            print(f"Fehler beim Status-Update: {str(e)}")

    def on_delete_task(self, task):
        app = App.get_running_app()
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        content.add_widget(Label(text=f"'{task['name']}' wirklich löschen?"))
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
                requests.delete(f"{API_BASE_URL}/tasks/{task['id']}", params={"token": app.token})
                self.load_tasks()
            except Exception as e:
                print(f"Fehler beim Löschen: {str(e)}")
        yes_btn.bind(on_press=confirm)
        no_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _build_task_form_content(self, task=None):
        pred_options = ["(kein Vorgänger)"] + [
            f"{i+1} - {t['name']}" for i, t in enumerate(self.tasks)
            if task is None or t["id"] != task["id"]
        ]
        assignee_options = ["(kein Mitarbeiter)"]
        try:
            app = App.get_running_app()
            response = requests.get(f"{API_BASE_URL}/users/", params={"token": app.token})
            if response.status_code == 200:
                assignee_options += [f"{u['id']} - {u['username']}" for u in response.json()]
        except:
            pass

        scroll = ScrollView(size_hint=(1, 1))
        content_inner = BoxLayout(orientation="vertical", padding=10, spacing=8, size_hint_y=None)
        content_inner.bind(minimum_height=content_inner.setter("height"))

        name_input = TextInput(text=task["name"] if task else "", hint_text="Aufgabenname", multiline=False, size_hint=(1, None), height=40)
        desc_input = TextInput(text=task["description"] or "" if task else "", hint_text="Beschreibung", multiline=True, size_hint=(1, None), height=60)
        duration_input = TextInput(text=str(task["duration"]) if task else "", hint_text="Dauer (Tage)", multiline=False, size_hint=(1, None), height=40)

        cpm_label = Label(text="CPM-Werte (manuell):", size_hint=(1, None), height=25, halign="left", color=(0.6, 0.7, 0.9, 1))
        cpm_row1 = BoxLayout(size_hint=(1, None), height=40, spacing=6)
        faz_input = TextInput(text=str(task["faz"]) if task else "0", hint_text="FAZ", multiline=False, size_hint=(1, 1))
        fez_input = TextInput(text=str(task["fez"]) if task else "0", hint_text="FEZ", multiline=False, size_hint=(1, 1))
        saz_input = TextInput(text=str(task["saz"]) if task else "0", hint_text="SAZ", multiline=False, size_hint=(1, 1))
        cpm_row1.add_widget(Label(text="FAZ", size_hint=(None, 1), width=35, color=(0.7, 0.7, 0.7, 1)))
        cpm_row1.add_widget(faz_input)
        cpm_row1.add_widget(Label(text="FEZ", size_hint=(None, 1), width=35, color=(0.7, 0.7, 0.7, 1)))
        cpm_row1.add_widget(fez_input)
        cpm_row1.add_widget(Label(text="SAZ", size_hint=(None, 1), width=35, color=(0.7, 0.7, 0.7, 1)))
        cpm_row1.add_widget(saz_input)

        cpm_row2 = BoxLayout(size_hint=(1, None), height=40, spacing=6)
        sez_input = TextInput(text=str(task["sez"]) if task else "0", hint_text="SEZ", multiline=False, size_hint=(1, 1))
        gp_input = TextInput(text=str(task["gp"]) if task else "0", hint_text="GP", multiline=False, size_hint=(1, 1))
        fp_input = TextInput(text=str(task["fp"]) if task else "0", hint_text="FP", multiline=False, size_hint=(1, 1))
        cpm_row2.add_widget(Label(text="SEZ", size_hint=(None, 1), width=35, color=(0.7, 0.7, 0.7, 1)))
        cpm_row2.add_widget(sez_input)
        cpm_row2.add_widget(Label(text="GP", size_hint=(None, 1), width=35, color=(0.7, 0.7, 0.7, 1)))
        cpm_row2.add_widget(gp_input)
        cpm_row2.add_widget(Label(text="FP", size_hint=(None, 1), width=35, color=(0.7, 0.7, 0.7, 1)))
        cpm_row2.add_widget(fp_input)

        kp_row = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        kp_label = Label(text="Kritischer Pfad:", size_hint=(0.5, 1), halign="left")
        is_critical = task["gp"] == 0 if task else False
        kp_btn = Button(text="Ja" if is_critical else "Nein", size_hint=(0.5, 1), background_color=(0.9, 0.2, 0.2, 1) if is_critical else (0.3, 0.3, 0.3, 1))
        kp_state = [is_critical]

        def toggle_kp(instance):
            kp_state[0] = not kp_state[0]
            kp_btn.text = "Ja" if kp_state[0] else "Nein"
            kp_btn.background_color = (0.9, 0.2, 0.2, 1) if kp_state[0] else (0.3, 0.3, 0.3, 1)

        kp_btn.bind(on_press=toggle_kp)
        kp_row.add_widget(kp_label)
        kp_row.add_widget(kp_btn)

        status_label = Label(text="Status:", size_hint=(1, None), height=25, halign="left")
        status_spinner = Spinner(text=task["status"] if task else "open", values=["open", "in_progress", "review", "done"], size_hint=(1, None), height=40)
        pred_label = Label(text="Vorgänger:", size_hint=(1, None), height=25, halign="left")
        current_pred = "(kein Vorgänger)"
        if task and task.get("predecessors"):
            pred_id = task["predecessors"][0]["predecessor_id"]
            pred_task = next((t for t in self.tasks if t["id"] == pred_id), None)
            if pred_task:
                idx = self.tasks.index(pred_task)
                current_pred = f"{idx+1} - {pred_task['name']}"
        pred_spinner = Spinner(text=current_pred, values=pred_options, size_hint=(1, None), height=40)
        assignee_label = Label(text="Mitarbeiter:", size_hint=(1, None), height=25, halign="left")
        assignee_spinner = Spinner(text="(kein Mitarbeiter)", values=assignee_options, size_hint=(1, None), height=40)
        error_label = Label(text="", color=(1, 0.2, 0.2, 1), size_hint=(1, None), height=30)

        content_inner.add_widget(name_input)
        content_inner.add_widget(desc_input)
        content_inner.add_widget(duration_input)
        content_inner.add_widget(cpm_label)
        content_inner.add_widget(cpm_row1)
        content_inner.add_widget(cpm_row2)
        content_inner.add_widget(kp_row)
        if task:
            content_inner.add_widget(status_label)
            content_inner.add_widget(status_spinner)
        content_inner.add_widget(pred_label)
        content_inner.add_widget(pred_spinner)
        content_inner.add_widget(assignee_label)
        content_inner.add_widget(assignee_spinner)
        content_inner.add_widget(error_label)

        scroll.add_widget(content_inner)

        outer = BoxLayout(orientation="vertical")
        outer.add_widget(scroll)

        return outer, name_input, desc_input, duration_input, status_spinner, pred_spinner, assignee_spinner, error_label, kp_state, faz_input, fez_input, saz_input, sez_input, gp_input, fp_input

    def open_edit_form(self, task):
        app = App.get_running_app()
        content, name_input, desc_input, duration_input, status_spinner, pred_spinner, assignee_spinner, error_label, kp_state, faz_input, fez_input, saz_input, sez_input, gp_input, fp_input = self._build_task_form_content(task)
        btn_row = BoxLayout(size_hint=(1, None), height=44, spacing=10)
        save_btn = Button(text="Speichern", background_color=(0.2, 0.7, 0.3, 1))
        cancel_btn = Button(text="Abbrechen", background_color=(0.4, 0.4, 0.4, 1))
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        popup = Popup(title=f"Bearbeiten: {task['name']}", content=content, size_hint=(0.85, 0.95))

        def save(instance):
            if not name_input.text.strip():
                error_label.text = "Name ist erforderlich"
                return
            try:
                duration = float(duration_input.text.strip())
            except ValueError:
                error_label.text = "Dauer muss eine Zahl sein"
                return
            assignee_id = None
            if assignee_spinner.text != "(kein Mitarbeiter)":
                try:
                    assignee_id = int(assignee_spinner.text.split(" - ")[0])
                except:
                    error_label.text = "Fehler beim Mitarbeiter"
                    return
            try:
                payload = {
                    "name": name_input.text.strip(),
                    "description": desc_input.text.strip(),
                    "duration": duration,
                    "status": status_spinner.text,
                    "assignee_id": assignee_id,
                    "faz": float(faz_input.text) if faz_input.text.strip() else None,
                    "fez": float(fez_input.text) if fez_input.text.strip() else None,
                    "saz": float(saz_input.text) if saz_input.text.strip() else None,
                    "sez": float(sez_input.text) if sez_input.text.strip() else None,
                    "gp": float(gp_input.text) if gp_input.text.strip() else None,
                    "fp": float(fp_input.text) if fp_input.text.strip() else None,
                }
                response = requests.put(f"{API_BASE_URL}/tasks/{task['id']}", params={"token": app.token}, json=payload)
                if response.status_code == 200:
                    popup.dismiss()
                    self.load_tasks()
                else:
                    error_label.text = f"Fehler: {response.status_code}"
            except Exception as e:
                error_label.text = f"Verbindungsfehler: {str(e)}"

        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_tooltip(self, task, widget_pos):
        if self.tooltip:
            self.canvas_area.remove_widget(self.tooltip)
        self.tooltip = TooltipWidget(
            task=task,
            pos=(widget_pos[0] + 130, widget_pos[1] + 60),
            size_hint=(None, None),
            size=(220, 100)
        )
        self.canvas_area.add_widget(self.tooltip)
        Clock.schedule_once(lambda dt: self.hide_tooltip(), 3)

    def hide_tooltip(self):
        if self.tooltip:
            self.canvas_area.remove_widget(self.tooltip)
            self.tooltip = None

    def open_subtasks(self, task):
        app = App.get_running_app()
        app.current_task = task
        self.on_enter()

    def export_png(self, instance):
        try:
            filename = "netzplan_export.png"
            self.canvas_area.export_to_png(filename)
            popup = Popup(title="Export erfolgreich", content=Label(text=f"Gespeichert als {filename}"), size_hint=(0.6, 0.3))
            popup.open()
        except Exception as e:
            popup = Popup(title="Fehler", content=Label(text=str(e)), size_hint=(0.6, 0.3))
            popup.open()

    def export_pdf(self, instance):
        try:
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib.pagesizes import A4, landscape
            png_file = "netzplan_temp.png"
            self.canvas_area.export_to_png(png_file)
            pdf_file = "netzplan_export.pdf"
            page_size = landscape(A4)
            c = pdf_canvas.Canvas(pdf_file, pagesize=page_size)
            c.setTitle("Netzplan Export")
            page_w, page_h = page_size
            img_w = self.canvas_area.width
            img_h = self.canvas_area.height
            scale = min(page_w / img_w, page_h / img_h) * 0.95
            draw_w = img_w * scale
            draw_h = img_h * scale
            x = (page_w - draw_w) / 2
            y = (page_h - draw_h) / 2
            c.drawImage(png_file, x, y, width=draw_w, height=draw_h)
            c.save()
            if os.path.exists(png_file):
                os.remove(png_file)
            popup = Popup(title="Export erfolgreich", content=Label(text=f"Gespeichert als {pdf_file}"), size_hint=(0.6, 0.3))
            popup.open()
        except Exception as e:
            popup = Popup(title="Fehler", content=Label(text=str(e)), size_hint=(0.6, 0.3))
            popup.open()

    def open_task_form(self, instance):
        app = App.get_running_app()
        project = app.current_project
        content, name_input, desc_input, duration_input, status_spinner, pred_spinner, assignee_spinner, error_label, kp_state, faz_input, fez_input, saz_input, sez_input, gp_input, fp_input = self._build_task_form_content()
        btn_row = BoxLayout(size_hint=(1, None), height=44, spacing=10)
        save_btn = Button(text="Speichern", background_color=(0.2, 0.7, 0.3, 1))
        cancel_btn = Button(text="Abbrechen", background_color=(0.8, 0.2, 0.2, 1))
        btn_row.add_widget(save_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(btn_row)
        popup = Popup(title="Neue Aufgabe", content=content, size_hint=(0.85, 0.95))

        def save(instance):
            if not name_input.text.strip():
                error_label.text = "Name ist erforderlich"
                return
            try:
                duration = float(duration_input.text.strip()) if duration_input.text.strip() else 1.0
            except ValueError:
                error_label.text = "Dauer muss eine Zahl sein"
                return
            pred_ids = []
            if pred_spinner.text != "(kein Vorgänger)":
                try:
                    idx = int(pred_spinner.text.split(" - ")[0]) - 1
                    pred_ids = [self.tasks[idx]["id"]]
                except:
                    error_label.text = "Fehler beim Vorgänger"
                    return
            assignee_id = None
            if assignee_spinner.text != "(kein Mitarbeiter)":
                try:
                    assignee_id = int(assignee_spinner.text.split(" - ")[0])
                except:
                    error_label.text = "Fehler beim Mitarbeiter"
                    return
            row = CRITICAL_ROW if kp_state[0] else CRITICAL_ROW - 2
            try:
                payload = {
                    "name": name_input.text.strip(),
                    "description": desc_input.text.strip(),
                    "duration": duration,
                    "project_id": project["id"],
                    "parent_id": self.parent_task["id"] if self.parent_task else None,
                    "predecessor_ids": pred_ids,
                    "assignee_id": assignee_id,
                    "pos_x": float(len(self.tasks) + 1),
                    "pos_y": float(row),
                    "faz": float(faz_input.text) if faz_input.text.strip() else 0.0,
                    "fez": float(fez_input.text) if fez_input.text.strip() else 0.0,
                    "saz": float(saz_input.text) if saz_input.text.strip() else 0.0,
                    "sez": float(sez_input.text) if sez_input.text.strip() else 0.0,
                    "gp": float(gp_input.text) if gp_input.text.strip() else 0.0,
                    "fp": float(fp_input.text) if fp_input.text.strip() else 0.0,
                }
                response = requests.post(f"{API_BASE_URL}/tasks/", params={"token": app.token}, json=payload)
                if response.status_code == 200:
                    popup.dismiss()
                    self.load_tasks()
                else:
                    error_label.text = f"Fehler: {response.status_code}"
            except Exception as e:
                error_label.text = f"Verbindungsfehler: {str(e)}"

        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()