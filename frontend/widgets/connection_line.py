from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Triangle
import math

class ConnectionLine(Widget):
    def __init__(self, start_node, end_node, is_critical=False, **kwargs):
        super().__init__(**kwargs)
        self.start_node = start_node
        self.end_node = end_node
        self.is_critical = is_critical
        self.draw()

    def draw(self):
        self.canvas.clear()

        x1 = self.start_node.x + self.start_node.width
        y1 = self.start_node.y + self.start_node.height / 2
        x2 = self.end_node.x
        y2 = self.end_node.y + self.end_node.height / 2

        mid_x = (x1 + x2) / 2

        with self.canvas:
            if self.is_critical:
                Color(1, 0.2, 0.2, 1)
            else:
                Color(0.6, 0.6, 0.6, 1)

            # Linie mit Knick
            Line(
                points=[x1, y1, mid_x, y1, mid_x, y2, x2, y2],
                width=2
            )

            # Pfeilspitze
            self.draw_arrow(x2, y2)

    def draw_arrow(self, x, y):
        arrow_size = 8
        with self.canvas:
            Triangle(points=[
                x, y,
                x - arrow_size, y + arrow_size / 2,
                x - arrow_size, y - arrow_size / 2
            ])

    def update(self):
        self.draw()