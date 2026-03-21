from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle

class TooltipWidget(FloatLayout):
    def __init__(self, task, **kwargs):
        super().__init__(**kwargs)
        self.task = task
        self.draw_tooltip()

    def draw_tooltip(self):
        self.canvas.before.clear()
        self.clear_widgets()

        with self.canvas.before:
            Color(0.1, 0.1, 0.15, 0.95)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
            Color(0.4, 0.4, 0.5, 1)

        layout = BoxLayout(
            orientation="vertical",
            padding=8,
            spacing=4,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0}
        )

        # Beschreibungstext
        desc = self.task.get("description") or "Keine Beschreibung"
        if len(desc) > 80:
            desc = desc[:77] + "..."

        desc_lbl = Label(
            text=desc,
            font_size=11,
            size_hint=(1, 0.5),
            halign="left",
            valign="top",
            color=(0.9, 0.9, 0.9, 1)
        )
        desc_lbl.bind(size=desc_lbl.setter("text_size"))

        # Fortschrittsbalken
        progress = self.task.get("progress", 0)
        progress_label = Label(
            text=f"Fortschritt: {progress}%",
            font_size=11,
            size_hint=(1, 0.2),
            color=(0.7, 1, 0.7, 1)
        )

        bar_layout = BoxLayout(size_hint=(1, 0.3), spacing=2)
        bar_bg = FloatLayout(size_hint=(1, 1))

        with bar_bg.canvas:
            Color(0.3, 0.3, 0.3, 1)
            RoundedRectangle(
                pos=bar_bg.pos,
                size=bar_bg.size,
                radius=[4]
            )
            if progress > 0:
                fill_width = bar_bg.width * (progress / 100)
                if progress >= 100:
                    Color(0.2, 0.9, 0.2, 1)
                elif progress >= 50:
                    Color(0.9, 0.7, 0.1, 1)
                else:
                    Color(0.2, 0.6, 1, 1)
                RoundedRectangle(
                    pos=bar_bg.pos,
                    size=(fill_width, bar_bg.height),
                    radius=[4]
                )

        bar_bg.bind(pos=self.update_bar, size=self.update_bar)
        self._bar_bg = bar_bg
        self._progress = progress

        bar_layout.add_widget(bar_bg)

        layout.add_widget(desc_lbl)
        layout.add_widget(progress_label)
        layout.add_widget(bar_layout)

        self.add_widget(layout)
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.1, 0.1, 0.15, 0.95)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])

    def update_bar(self, instance, value):
        instance.canvas.clear()
        with instance.canvas:
            Color(0.3, 0.3, 0.3, 1)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[4])
            if self._progress > 0:
                fill_width = instance.width * (self._progress / 100)
                if self._progress >= 100:
                    Color(0.2, 0.9, 0.2, 1)
                elif self._progress >= 50:
                    Color(0.9, 0.7, 0.1, 1)
                else:
                    Color(0.2, 0.6, 1, 1)
                RoundedRectangle(
                    pos=instance.pos,
                    size=(fill_width, instance.height),
                    radius=[4]
                )