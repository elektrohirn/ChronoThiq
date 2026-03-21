from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle

class ProgressBar(FloatLayout):
    def __init__(self, progress=0, show_label=True, **kwargs):
        super().__init__(**kwargs)
        self.progress = max(0, min(100, progress))
        self.show_label = show_label
        self.bind(pos=self.redraw, size=self.redraw)

    def redraw(self, *args):
        self.canvas.clear()
        self.clear_widgets()

        with self.canvas:
            # Hintergrund
            Color(0.25, 0.25, 0.25, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[6])

            # Füllstand
            if self.progress > 0:
                fill_width = self.width * (self.progress / 100)
                if self.progress >= 100:
                    Color(0.2, 0.9, 0.2, 1)
                elif self.progress >= 75:
                    Color(0.4, 0.8, 0.2, 1)
                elif self.progress >= 50:
                    Color(0.9, 0.7, 0.1, 1)
                elif self.progress >= 25:
                    Color(0.9, 0.5, 0.1, 1)
                else:
                    Color(0.2, 0.6, 1, 1)
                RoundedRectangle(
                    pos=self.pos,
                    size=(fill_width, self.height),
                    radius=[6]
                )

        if self.show_label:
            lbl = Label(
                text=f"{self.progress}%",
                font_size=11,
                bold=True,
                size_hint=(1, 1),
                pos_hint={"x": 0, "y": 0},
                halign="center",
                valign="middle",
                color=(1, 1, 1, 1)
            )
            lbl.bind(size=lbl.setter("text_size"))
            self.add_widget(lbl)

    def set_progress(self, value):
        self.progress = max(0, min(100, value))
        self.redraw()