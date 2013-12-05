import tkinter as tk
import math

from observable import ObservableSet
from mouse import (SelectingMouse, SelectionModifyingMouse,
                   MovingMouse, CreatingMouse)
from graph import Vertex, Edge

# Padding for scroll region
PADDING=10


class CanvasGraph(tk.Canvas):
    
    def __init__(self, parent, **config):
        tk.Canvas.__init__(self, parent, **config)
        
        # Selected vertices
        self.selected = ObservableSet()
        self.selected.register(self)
        
        # Vertices and edges
        self.vertices = {}
        self.edges = {}
        
        # Populate mouses
        self.mouses = {}
        sm = SelectingMouse(self, selection=self.selected,
                            elements=self.vertices,
                            button="1", modifier="")
        smm = SelectionModifyingMouse(self, selection=self.selected,
                                      elements=self.vertices,
                                      button="1", modifier="Shift")
        mm = MovingMouse(self, self.selected,
                         button="1", modifier="")
        cm = CreatingMouse(self, self.vertices,
                           button="1", modifier="Control")
        
        self.config(scrollregion=self.bbox("all"))
    
    def current_element(self):
        """Return the current element if any, None otherwise."""
        current = self.find_withtag("current")
        if len(current) > 0:
            return current[0]
        else:
            return None
    
    def new_vertex(self, x, y):
        """Add a vertex at (x,y)."""
        v = Vertex(self, x, y)
        
        # Update scrollregion
        self.update_scrollregion()
            
        self.vertices[v.handle] = v
    
    def new_edge(self, orig, end):
        """Add an edge from orig to end, if none exists."""
        if len(list((o, e, n) for (o, e, n) in self.edges
                    if o == orig and n == end)) <= 0:
            # No pre-existing edge, build it
            e = Edge(self, self.vertices[orig], self.vertices[end])
            self.edges[(orig, e.handle, end)] = e
    
    def move_vertices(self, vertices, dx, dy):
        """Move the vertices and the connected edges of (dx,dy)."""
        for v in vertices:
            if v in self.vertices:
                self.vertices[v].move(dx, dy)
                for o, e, n in self.edges:
                    if o == v or n == v:
                        self.edges[(o, e, n)].move(dx, dy)
        
        # Update scrollregion
        self.update_scrollregion()
    
    
    def update(self, observed):
        if observed is self.selected:
            for v in self.vertices:
                if v in self.selected:
                    self.itemconfig(v, fill="yellow")
                else:
                    self.itemconfig(v, fill="white")
    
    
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
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.pressed(event):
                    break
    
    def _moved(self, button, modifier, event):
        if (button, modifier) in self.mouses:
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.moved(event):
                    break
    
    def _released(self, button, modifier, event):
        if (button, modifier) in self.mouses:
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
    
    root.mainloop()