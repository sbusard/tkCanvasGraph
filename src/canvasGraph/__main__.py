import tkinter as tk
import random
from .canvas import CanvasFrame
from .mouse import Mouse, CreatingMouse
from .layout import OneStepForceBasedLayout
from .graph import Vertex, Edge, Rectangle, Oval

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
            style["shape_style"]["width"] = 4
    frame.canvas.register_transformer(added_vertex)

    def selected_vertex(element, style):
        if element.label and element in frame.canvas.selected:
            style["shape_style"]["outline"] = "red"
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


    class ChangeLabelDialog(tk.Toplevel):
        def __init__(self, element, parent, **config):
            super().__init__(parent, **config)
            self.title = "Change label"
            self.lift()
            self.resizable(False, False)

            mainframe = tk.Frame(self)
            mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
            mainframe.columnconfigure(0, weight=1)
            mainframe.rowconfigure(0, weight=1)

            label_var = tk.StringVar()
            label_var.set(element.label)

            tk.Label(mainframe, text="Label").grid(column=1,
                                                   row=1,
                                                   sticky=tk.W)

            label_entry = tk.Entry(mainframe, width=7, textvariable=label_var)
            label_entry.grid(column=2, row=1, sticky=tk.E)

            def replace_label(*args):
                element.label = label_var.get()
                frame.canvas.refresh()
                self.destroy()

            tk.Button(mainframe,
                      text="Calculate",
                      command=replace_label).grid(column=2,
                                                  row=2,
                                                  sticky=(tk.W, tk.E))

            for child in mainframe.winfo_children():
                child.grid_configure(padx=5, pady=5)

            label_entry.focus()


    class LabelEditingMouse(Mouse):
        def released(self, canvas, event):
            element = canvas.current_element()
            if element is not None:
                ChangeLabelDialog(element, canvas)
            return False

    frame.canvas.register_mouse(LabelEditingMouse(), "2", "")


    def random_label(_, style):
        style["label"] = str(random.randint(0, 100))
    frame.canvas.register_transformer(random_label)


    def random_shape(_, style):
        style["shape"] = random.choice([Rectangle(), Oval()])
    frame.canvas.register_transformer(random_shape)


    def rainbow(element, style):
        bbox = frame.canvas.bbox("all")
        if bbox:
            xlu, ylu, xdr, ydr = bbox
            xc, yc = element.center()
            # Color border from red to blue, depending on the relative
            # horizontal position; left is red, right is blue
            red = int(255 * (xc - xlu) / (xdr - xlu))
            blue = int(255 * (xdr - xc) / (xdr - xlu))
            style["shape_style"]["outline"] = "#%02x00%02x" % (red, blue)
            style["shape_style"]["width"] = 2
    frame.canvas.register_transformer(rainbow)
    # -------------------------------------------------------------------------

    root.mainloop()
