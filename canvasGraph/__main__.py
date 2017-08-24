import tkinter as tk
import random
from .canvas import CanvasFrame
from .graph import Vertex, Edge
from .mouse import Mouse, CreatingMouse
from .layout import OneStepForceBasedLayout
from .shape import Rectangle, Oval

if __name__ == "__main__":
    # Start a new window with canvas graph and creating mouse
    root = tk.Tk()

    frame = CanvasFrame(root)

    frame.pack(fill="both", expand=True)


    # Add predefined creating mouse to the canvas
    cm = CreatingMouse(frame.canvas.vertices)
    frame.canvas.register_mouse(cm, "1", "Control")


    # Define and add deleting mouse to the canvas
    class DeletingMouse(Mouse):
        def released(self, event):
            canvas = event.canvas
            element = event.element
            if element is not None:
                canvas.delete_element(element)
            return False

    frame.canvas.register_mouse(DeletingMouse(), "2", "Control")


    # Define and add new mouse to change labels
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
        def released(self, event):
            canvas = event.canvas
            element = event.element
            if element is not None:
                ChangeLabelDialog(element, canvas)
            return False

    frame.canvas.register_mouse(LabelEditingMouse(), "2", "")


    # Add a transformer to give colors to element edges depending on their
    # relative position
    def rainbow(element, style):
        bbox = frame.canvas.bbox("all")
        if bbox:
            xlu, ylu, xdr, ydr = bbox
            xc, yc = element.center
            # Color border from red to blue, depending on the relative
            # horizontal position; left is red, right is blue
            red = int(255 * (xc - xlu) / (xdr - xlu))
            blue = int(255 * (xdr - xc) / (xdr - xlu))
            style["shape_style"]["outline"] = "#%02x00%02x" % (red, blue)
            style["shape_style"]["width"] = 2
    frame.canvas.register_transformer(rainbow)


    # Add transformer that change the color outline of selected vertices and
    # edges
    def selected_vertex(element, style):
        if element in frame.canvas.selected:
            style["shape_style"]["outline"] = "green"
    frame.canvas.register_transformer(selected_vertex)


    # Add keyboard bindings to apply one step of the force based layout,
    # and to add random vertices and edges
    frame.canvas.bind("o",
                      lambda e:
                      frame.canvas.apply_layout(OneStepForceBasedLayout()))

    def add_vertex(_):
        v = Vertex(frame.canvas)
        frame.canvas.add_vertex(v)

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
            edge = Edge(frame.canvas, o, e)
            frame.canvas.add_edge(edge)

    frame.canvas.bind("k", add_edge)


    root.mainloop()
