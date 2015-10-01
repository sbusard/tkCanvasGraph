import tkinter as tk
import random
from .canvas import CanvasFrame
from .mouse import CreatingMouse
from .layout import OneStepForceBasedLayout
from .graph import Vertex, Edge

# Start a new window with canvas graph and creating mouse
if __name__ == "__main__":
    root = tk.Tk()

    frame = CanvasFrame(root)

    frame.pack(fill="both", expand=True)

    # Add creating mouse to the canvas
    cm = CreatingMouse(frame.canvas, frame.canvas.vertices,
                       button="1", modifier="Control")

    # TODO Remove this (tests) -----------------------------------------------
    # One step of force-based layout
    frame.canvas.bind("o",
                      lambda e:
                      frame.canvas.layout(OneStepForceBasedLayout()))

    # Random adding
    def addv(_):
        v = Vertex(frame.canvas,
                   str(random.randint(0, 100)) + "\n" +
                   "\n".join(("TEST1=TEST1", "TEST2=TEST2", "TEST3=TEST3""")))
        v.style.common.shape.width = 2
        v.style.selected.shape.outline = "red"
        v.refresh()


    frame.canvas.bind("j", addv)


    def adde(event):
        pairs = [(o, e)
                 for o in frame.canvas.vertices
                 for e in frame.canvas.vertices
                 if o != e
                 if len([edge for edge in frame.canvas.edges
                         if edge.origin == o and edge.end == e]) <= 0]
        if len(pairs) > 0:
            o, e = random.choice(pairs)
            Edge(frame.canvas, o, e, label=str(random.randint(0, 100)))


    frame.canvas.bind("k", adde)
    # -------------------------------------------------------------------------

    root.mainloop()
