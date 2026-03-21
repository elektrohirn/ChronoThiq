from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.clock import Clock
from kivy.core.window import Window

DRAG_THRESHOLD = 10

COLOR_OPEN = (0.95, 0.95, 0.95, 1)
COLOR_DONE = (0.2, 0.78, 0.35, 1)
COLOR_REVIEW = (1.0, 0.85, 0.1, 1)

def get_task_color(task):
    if task["status"] == "done":
        return COLOR_DONE
    if task["status"] == "review":
        return COLOR_REVIEW
    return COLOR_OPEN

def get_text_color(task):
    if task["status"] == "done":
        return (1, 1, 1, 1)
    return (0.1, 0.1, 0.1, 1)


class NodeWidget(FloatLayout):
    def __init__(self, task, on_move, on_hover, on_click, on_status, on_edit, on_delete, index=0, subtasks=None, grid_size=80, **kwargs):
        super().__init__(**kwargs)
        self.task = task
        self.on_move_cb = on_move
        self.on_hover_cb = on_hover
        self.on_click_cb = on_click
        self.on_status_cb = on_status
        self.on_edit_cb = on_edit
        self.on_delete_cb = on_delete
        self.index = index
        self.subtasks = subtasks or []
        self.grid_size = grid_size
        self._touch_start = None
        self._dragging = False
        self._drag_offset = (0, 0)
        self._hover_clock = None
        self._mouse_inside = False
        Window.bind(mouse_pos=self.on_mouse_pos)
        self.draw_node()

    def on_mouse_pos(self, window, pos):
        inside = self.collide_point(*self.to_widget(*pos))
        if inside and not self._mouse_inside:
            self._mouse_inside = True
            if self._hover_clock:
                self._hover_clock.cancel()
            self._hover_clock = Clock.schedule_once(
                lambda dt: self.on_hover_cb(self.task, self.pos), 0.9
            )
        elif not inside and self._mouse_inside:
            self._mouse_inside = False
            if self._hover_clock:
                self._hover_clock.cancel()

    def draw_node(self):
        self.canvas.before.clear()
        self.clear_widgets()
        task = self.task
        node_color = get_task_color(task)
        text_color = get_text_color(task)
        has_subtasks = len(self.subtasks) > 0

        with self.canvas.before:
            Color(*node_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
            Color(0.35, 0.35, 0.35, 1)
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 8], width=1.5)

        layout = BoxLayout(orientation="vertical", padding=6, spacing=2, size_hint=(1, 1), pos_hint={"x": 0, "y": 0})

        # Titelzeile mit Kreuz-Symbol wenn Teilaufgaben vorhanden
        title_row = BoxLayout(size_hint=(1, 0.25), spacing=4)
        name_text = f"[{self.index + 1}] {task['name']}"
        name_lbl = Label(text=name_text, bold=True, font_size=12, size_hint=(1, 1), halign="center", valign="middle", color=text_color)
        name_lbl.bind(size=name_lbl.setter("text_size"))
        title_row.add_widget(name_lbl)

        if has_subtasks:
            subtask_count = len(self.subtasks)
            cross_lbl = Label(
                text=f"✛{subtask_count}",
                bold=True,
                font_size=14,
                size_hint=(None, 1),
                width=36,
                color=(0.9, 0.4, 0.1, 1)
            )
            title_row.add_widget(cross_lbl)

        row1 = BoxLayout(size_hint=(1, 0.25), spacing=2)
        row1.add_widget(self._small_label(f"FAZ\n{task['faz']}", text_color))
        row1.add_widget(self._small_label(f"D\n{task['duration']}", text_color, bold=True))
        row1.add_widget(self._small_label(f"FEZ\n{task['fez']}", text_color))

        row2 = BoxLayout(size_hint=(1, 0.25), spacing=2)
        row2.add_widget(self._small_label(f"SAZ\n{task['saz']}", text_color))
        row2.add_widget(self._small_label(f"GP\n{task['gp']}", text_color))
        row2.add_widget(self._small_label(f"SEZ\n{task['sez']}", text_color))

        progress_lbl = Label(text=f"Fortschritt: {task['progress']}%", font_size=10, size_hint=(1, 0.25), color=text_color)

        layout.add_widget(title_row)
        layout.add_widget(row1)
        layout.add_widget(row2)
        layout.add_widget(progress_lbl)
        self.add_widget(layout)
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def _small_label(self, text, color, bold=False):
        lbl = Label(text=text, font_size=10, bold=bold, halign="center", valign="middle", color=color)
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def update_graphics(self, *args):
        node_color = get_task_color(self.task)
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*node_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
            Color(0.35, 0.35, 0.35, 1)
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 8], width=1.5)

    def show_context_menu(self):
        content = BoxLayout(orientation="vertical", padding=8, spacing=6)
        nicht_btn = Button(text="Nicht erledigt", size_hint=(1, None), height=44, background_color=(0.5, 0.5, 0.5, 1))
        prufen_btn = Button(text="Prüfen", size_hint=(1, None), height=44, background_color=(1, 0.85, 0.1, 1))
        erledigt_btn = Button(text="Erledigt", size_hint=(1, None), height=44, background_color=(0.2, 0.8, 0.2, 1))
        bearbeiten_btn = Button(text="Bearbeiten", size_hint=(1, None), height=44, background_color=(0.2, 0.6, 1, 1))
        loschen_btn = Button(text="Löschen", size_hint=(1, None), height=44, background_color=(0.8, 0.2, 0.2, 1))
        abbrechen_btn = Button(text="Abbrechen", size_hint=(1, None), height=44, background_color=(0.4, 0.4, 0.4, 1))
        content.add_widget(nicht_btn)
        content.add_widget(prufen_btn)
        content.add_widget(erledigt_btn)
        content.add_widget(bearbeiten_btn)
        content.add_widget(loschen_btn)
        content.add_widget(abbrechen_btn)
        popup = Popup(title=self.task['name'], content=content, size_hint=(0.5, 0.6))
        nicht_btn.bind(on_press=lambda x: (popup.dismiss(), self.on_status_cb(self.task, "open")))
        prufen_btn.bind(on_press=lambda x: (popup.dismiss(), self.on_status_cb(self.task, "review")))
        erledigt_btn.bind(on_press=lambda x: (popup.dismiss(), self.on_status_cb(self.task, "done")))
        bearbeiten_btn.bind(on_press=lambda x: (popup.dismiss(), self.on_edit_cb(self.task)))
        loschen_btn.bind(on_press=lambda x: (popup.dismiss(), self.on_delete_cb(self.task)))
        abbrechen_btn.bind(on_press=popup.dismiss)
        popup.open()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        self._touch_start = (touch.x, touch.y)
        self._dragging = False
        self._drag_offset = (self.x - touch.x, self.y - touch.y)
        if touch.button == "right":
            self.show_context_menu()
            return True
        if touch.is_double_tap:
            if self._hover_clock:
                self._hover_clock.cancel()
            self.on_click_cb(self.task)
            return True
        return True

    def on_touch_move(self, touch):
        if self._touch_start is None:
            return False
        if touch.button == "right":
            return False
        dx = abs(touch.x - self._touch_start[0])
        dy = abs(touch.y - self._touch_start[1])
        if dx > DRAG_THRESHOLD or dy > DRAG_THRESHOLD:
            self._dragging = True
            if self._hover_clock:
                self._hover_clock.cancel()
            gs = self.grid_size
            new_x = round((touch.x + self._drag_offset[0]) / gs) * gs
            new_y = round((touch.y + self._drag_offset[1]) / gs) * gs
            self.pos = (new_x, new_y)
            self.on_move_cb(self.task["id"], new_x, new_y, gs)
        return True

    def on_touch_up(self, touch):
        if self._touch_start is None:
            return False
        if touch.button == "right":
            self._touch_start = None
            return True
        if self._dragging:
            self._dragging = False
            self._touch_start = None
            gs = self.grid_size
            final_x = round(self.x / gs) * gs
            final_y = round(self.y / gs) * gs
            self.pos = (final_x, final_y)
            self.on_move_cb(self.task["id"], final_x, final_y, gs)
            return True
        self._touch_start = None
        return True