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
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Line
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from shared.constants import API_BASE_URL

class GanttScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.add_widget(self.layout)
        self.tasks = []
        self._resize_trigger = None

    def on_enter(self):
        self.layout.clear_widgets()
        app = App.get_running_app()
        project = app.current_project

        header = BoxLayout(size_hint=(1, 0.07), padding=10, spacing=10)
        back_btn = Button(text="< Zurück", size_hint=(0.15, 1), background_color=(0.4, 0.4, 0.4, 1))
        back_btn.bind(on_press=lambda x: setattr(self.manager, "current", "project"))
        title = Label(text=f"Gantt: {project['name']}", font_size=18, bold=True)
        png_btn = Button(text="Export PNG", size_hint=(0.15, 1), background_color=(0.3, 0.5, 0.8, 1))
        png_btn.bind(on_press=self.export_png)
        pdf_btn = Button(text="Export PDF", size_hint=(0.15, 1), background_color=(0.5, 0.2, 0.8, 1))
        pdf_btn.bind(on_press=self.export_pdf)
        header.add_widget(back_btn)
        header.add_widget(title)
        header.add_widget(png_btn)
        header.add_widget(pdf_btn)

        self.scroll = ScrollView(size_hint=(1, 0.93))
        self.gantt_area = FloatLayout(size_hint=(None, None))
        self.scroll.add_widget(self.gantt_area)

        self.layout.add_widget(header)
        self.layout.add_widget(self.scroll)

        Window.bind(on_resize=self.on_window_resize)
        self.load_and_draw()

    def on_leave(self):
        Window.unbind(on_resize=self.on_window_resize)

    def on_window_resize(self, window, width, height):
        if self._resize_trigger:
            self._resize_trigger.cancel()
        self._resize_trigger = Clock.schedule_once(lambda dt: self.draw_gantt(), 0.2)

    def load_and_draw(self):
        app = App.get_running_app()
        project = app.current_project
        try:
            response = requests.get(
                f"{API_BASE_URL}/tasks/project/{project['id']}",
                params={"token": app.token}
            )
            if response.status_code == 200:
                self.tasks = response.json()
                self.draw_gantt()
        except Exception as e:
            self.gantt_area.clear_widgets()
            self.gantt_area.add_widget(Label(text=f"Fehler: {str(e)}", pos=(100, 100)))

    def draw_gantt(self):
        self.gantt_area.clear_widgets()
        self.gantt_area.canvas.clear()
        self.gantt_area.canvas.before.clear()

        tasks = self.tasks
        if not tasks:
            self.gantt_area.size = (Window.width, Window.height)
            self.gantt_area.add_widget(Label(text="Keine Aufgaben vorhanden", pos=(200, 200)))
            return

        available_width = Window.width - 20
        available_height = Window.height * 0.86

        label_width = max(150, available_width * 0.2)
        max_fez = max((t["fez"] for t in tasks), default=10)
        col_width = max(40, (available_width - label_width) / (max_fez + 1))
        row_height = max(35, min(60, available_height / (len(tasks) + 2)))
        header_height = row_height
        total_width = max(label_width + (max_fez + 2) * col_width, available_width)
        total_height = max((len(tasks) + 2) * row_height, available_height)

        self.gantt_area.size = (total_width, total_height)
        canvas_height = total_height

        with self.gantt_area.canvas.before:
            Color(0.09, 0.09, 0.13, 1)
            Rectangle(pos=(0, 0), size=(total_width, total_height))

        with self.gantt_area.canvas:
            Color(0.2, 0.2, 0.25, 1)
            for day in range(int(max_fez) + 2):
                x = label_width + day * col_width
                Line(points=[x, 0, x, canvas_height], width=0.5)

        for day in range(int(max_fez) + 2):
            x = label_width + day * col_width
            lbl = Label(
                text=str(day),
                pos=(x - col_width / 2, canvas_height - header_height),
                size_hint=(None, None),
                size=(col_width, header_height),
                font_size=max(9, int(col_width * 0.25)),
                color=(0.6, 0.7, 0.9, 1),
                halign="center",
                valign="middle"
            )
            lbl.bind(size=lbl.setter("text_size"))
            self.gantt_area.add_widget(lbl)

        for i, task in enumerate(tasks):
            y = canvas_height - header_height - (i + 1) * row_height

            with self.gantt_area.canvas:
                Color(0.2, 0.2, 0.25, 1)
                Line(points=[0, y, total_width, y], width=0.5)

            name_lbl = Label(
                text=task["name"],
                pos=(0, y),
                size_hint=(None, None),
                size=(label_width - 8, row_height),
                font_size=max(9, int(row_height * 0.28)),
                halign="right",
                valign="middle",
                color=(0.9, 0.9, 0.9, 1)
            )
            name_lbl.bind(size=name_lbl.setter("text_size"))
            self.gantt_area.add_widget(name_lbl)

            if task["status"] == "done":
                bar_color = (0.2, 0.78, 0.35, 1)
            elif task["status"] == "review":
                bar_color = (1.0, 0.85, 0.1, 1)
            elif task["gp"] == 0:
                bar_color = (0.85, 0.15, 0.15, 1)
            else:
                bar_color = (0.2, 0.5, 0.9, 1)

            bar_x = label_width + task["faz"] * col_width
            bar_w = max(4, task["duration"] * col_width)
            bar_h = row_height * 0.6
            bar_y = y + row_height * 0.2

            with self.gantt_area.canvas:
                Color(*bar_color)
                Rectangle(pos=(bar_x, bar_y), size=(bar_w, bar_h))
                Color(1, 1, 1, 0.3)
                Rectangle(pos=(bar_x, bar_y), size=(bar_w * task["progress"] / 100, bar_h))
                if task["gp"] > 0:
                    Color(0.4, 0.4, 0.4, 0.4)
                    Rectangle(pos=(bar_x + bar_w, bar_y), size=(task["gp"] * col_width, bar_h))

            pct_lbl = Label(
                text=f"{int(task['progress'])}%",
                pos=(bar_x + bar_w + task["gp"] * col_width + 4, y),
                size_hint=(None, None),
                size=(50, row_height),
                font_size=max(9, int(row_height * 0.25)),
                color=(0.8, 0.8, 0.8, 1)
            )
            self.gantt_area.add_widget(pct_lbl)

    def export_png(self, instance):
        try:
            filename = "gantt_export.png"
            self.gantt_area.export_to_png(filename)
            popup = Popup(title="Export erfolgreich", content=Label(text=f"Gespeichert als {filename}"), size_hint=(0.6, 0.3))
            popup.open()
        except Exception as e:
            popup = Popup(title="Fehler", content=Label(text=str(e)), size_hint=(0.6, 0.3))
            popup.open()

    def export_pdf(self, instance):
        try:
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib.pagesizes import A4, landscape

            png_file = "gantt_temp.png"
            self.gantt_area.export_to_png(png_file)

            pdf_file = "gantt_export.pdf"
            page_size = landscape(A4)
            c = pdf_canvas.Canvas(pdf_file, pagesize=page_size)
            c.setTitle("Gantt Export")
            page_w, page_h = page_size
            img_w = self.gantt_area.width
            img_h = self.gantt_area.height
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