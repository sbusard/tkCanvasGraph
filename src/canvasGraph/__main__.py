import tkinter as tk
import random
from .canvas import CanvasFrame
from .mouse import CreatingMouse
from .layout import OneStepForceBasedLayout
from .graph import Vertex, Edge

if __name__ == "__main__":
    # Start a new window with canvas graph and creating mouse
    root = tk.Tk()

    frame = CanvasFrame(root)

    frame.pack(fill="both", expand=True)

    # Add creating mouse to the canvas
    cm = CreatingMouse(frame.canvas.vertices)
    frame.canvas.register_mouse(cm, "1", "Control")

    # TODO Remove this (tests) -----------------------------------------------
    # One step of force-based layout
    frame.canvas.bind("o",
                      lambda e:
                      frame.canvas.apply_layout(OneStepForceBasedLayout()))

    # Random adding
    def add_vertex(_):
        v = Vertex(frame.canvas,
                   str(random.randint(0, 100)) + "\n" +
                   "\n".join("TEST" +
                             str(random.randint(0, 100)) +
                             "=" +
                             "TEST" +
                             str(random.randint(0, 100))
                             for _ in range(3)))
        v.style.common.shape.width = 2
        v.style.selected.shape.outline = "red"
        v.refresh()


    frame.canvas.bind("j", add_vertex)


    def add_edge(_):
        pairs = [(o, e)
                 for o in frame.canvas.vertices
                 for e in frame.canvas.vertices
                 if o != e
                 if len([edge for edge in frame.canvas.edges
                         if edge.origin == o and edge.end == e]) <= 0]
        if len(pairs) > 0:
            o, e = random.choice(pairs)
            Edge(frame.canvas, o, e, label=str(random.randint(0, 100)))


    frame.canvas.bind("k", add_edge)
    # -------------------------------------------------------------------------

    root.mainloop()
