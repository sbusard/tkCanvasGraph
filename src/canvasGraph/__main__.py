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
    added = set()

    def add_vertex(_):
        v = Vertex(frame.canvas,
                   str(random.randint(0, 100)) + "\n" +
                   "\n".join("TEST" +
                             str(random.randint(0, 100)) +
                             "=" +
                             "TEST" +
                             str(random.randint(0, 100))
                             for _ in range(3)))
        frame.canvas.add_vertex(v)
        added.add(v)

    def added_vertex(element, style):
        if element.label and isinstance(element, Vertex):
            style["shape"]["width"] = 4
    frame.canvas.register_transformer(added_vertex)

    def selected_vertex(element, style):
        if element.label and element in frame.canvas.selected:
            style["shape"]["outline"] = "red"
    frame.canvas.register_transformer(selected_vertex)

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
            edge = Edge(frame.canvas, o, e, label=str(random.randint(0, 100)))
            frame.canvas.add_edge(edge)


    frame.canvas.bind("k", add_edge)
    # -------------------------------------------------------------------------

    root.mainloop()
