import tkinter as tk
import math

from observable import ObservableSet
from mouse import (SelectingMouse, SelectionModifyingMouse,
                   MovingMouse, CreatingMouse)
from graph import Vertex, Edge
from layout import force_based_layout

# Padding for scroll region
PADDING=10


class CanvasGraph(tk.Canvas):
    
    def __init__(self, parent, **config):
        tk.Canvas.__init__(self, parent, **config)
        
        # Selected vertices
        self.selected = ObservableSet()
        self.selected.register(self)
        
        self.elements = {}
        
        # Vertices and edges
        self.vertices = set()
        self.edges = set()
        
        self.mouses = {}
        
        self.config(scrollregion=self.bbox("all"))
        
        self.focus_set()
        self.bind("r", self.start_layout)
    
    def start_layout(self, event):
        vertices = {vertice:vertice.center for vertice in self.vertices}
        nps = force_based_layout(vertices, self.edges)
        
        def layout():
            if self.new_event:
                return
            try:
                np = nps.__next__()
                
                for vertex in np:
                    vertex.move_to(*np[vertex])
                for e in self.edges:
                    e.move()

                self.update_scrollregion()
                
                self.after(10, layout)
                
            except StopIteration:
                pass
        
        self.new_event = False
        self.after(10, layout)
    
    def current_element(self):
        """Return the current element if any, None otherwise."""
        current = self.find_withtag("current")
        if len(current) > 0:
            return self.element_by_handle(current[0])
        else:
            return None
    
    def element_by_handle(self, handle):
        if handle in self.elements:
            return self.elements[handle]
        else:
            return None
    
    def new_vertex(self, x, y, label=""):
        """Add a vertex at (x,y)."""
        v = Vertex(self, x, y, label)
        
        # Update scrollregion
        self.update_scrollregion()
            
        self.vertices.add(v)
        
        # Update elements
        self.elements[v.handle] = v
        if v.labelhandle is not None:
            self.elements[v.labelhandle] = v
    
    def new_edge(self, orig, end, label=""):
        """Add an edge from orig to end, if none exists."""
        if len(list(e for e in self.edges
                    if e.origin == orig and e.end == end)) <= 0:
            # No pre-existing edge, build it
            e = Edge(self, orig, end, label)
            self.edges.add(e)
    
    def move_vertices(self, vertices, dx, dy):
        """Move the vertices and the connected edges of (dx,dy)."""
        for v in vertices:
            v.move(dx, dy)
            for e in self.edges:
                if e.origin == v or e.end == v:
                    e.move()
        
        # Update scrollregion
        self.update_scrollregion()
    
    
    def update(self, observed):
        if observed is self.selected:
            for v in self.vertices:
                if v in self.selected:
                    v.select()
                else:
                    v.deselect()
        
        if observed in self.elements.values():
            keys = {k for k in self.elements if self.elements[k] == observed}
            for key in keys:
                del self.elements[key]
            self.elements[observed.handle] = observed
            if observed.labelhandle != None:
                self.elements[observed.labelhandle] = observed
            for e in self.edges:
                if e.origin == observed or e.end == observed:
                    e.move()
    
    
    def update_scrollregion(self):
        minx, miny, maxx, maxy = self.bbox("all")
        self.config(scrollregion=(minx-PADDING, miny-PADDING,
                                  maxx+PADDING, maxy+PADDING))
    
    def register_mouse(self, mouse, button, modifier):
        """Register a new mouse for button pressed with modifier."""
        
        modifier = modifier + "-" if modifier != "" else modifier
        
        if (button, modifier) not in self.mouses:
            self.mouses[(button, modifier)] = []
            self.bind("<" + modifier + "ButtonPress-" + button + ">",
                      lambda e: self._pressed(button, modifier, e))
            self.bind("<" + modifier + "B" + button + "-Motion>",
                      lambda e: self._moved(button, modifier, e))
            self.bind("<" + modifier + "ButtonRelease-" + button + ">",
                      lambda e: self._released(button, modifier, e))
        
        self.mouses[(button, modifier)].append(mouse)
    
    
    def _pressed(self, button, modifier, event):
        if (button, modifier) in self.mouses:
            self.new_event = True
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.pressed(event):
                    break
    
    def _moved(self, button, modifier, event):
        if (button, modifier) in self.mouses:
            self.new_event = True
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.moved(event):
                    break
    
    def _released(self, button, modifier, event):
        if (button, modifier) in self.mouses:
            self.new_event = True
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.released(event):
                    break



if __name__ == "__main__":
    root = tk.Tk()
    
    frame = tk.Frame(root)

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    xscrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
    xscrollbar.grid(row=1, column=0, sticky=tk.E+tk.W)

    yscrollbar = tk.Scrollbar(frame)
    yscrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)

    canvas = CanvasGraph(frame, xscrollcommand=xscrollbar.set,
                                yscrollcommand=yscrollbar.set)

    canvas.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

    xscrollbar.config(command=canvas.xview)
    yscrollbar.config(command=canvas.yview)
    
    frame.pack(fill="both", expand=True)
    
    # Mouses for the canvas
    sm = SelectingMouse(canvas, selection=canvas.selected,
                        elements=canvas.vertices,
                        button="1", modifier="")
    smm = SelectionModifyingMouse(canvas, selection=canvas.selected,
                                  elements=canvas.vertices,
                                  button="1", modifier="Shift")
    mm = MovingMouse(canvas, canvas.selected,
                     button="1", modifier="")
    cm = CreatingMouse(canvas, canvas.vertices,
                       button="1", modifier="Control")
    
    root.mainloop()