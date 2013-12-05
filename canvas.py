import tkinter as tk
import math

from observable import ObservableSet
from mouse import (SelectingMouse, SelectionModifyingMouse,
                   MovingMouse, CreatingMouse)

# Radius of circles representing states
STATERADIUS=10

# Padding for scroll region
PADDING=10

class CanvasGraph(tk.Canvas):
    
    def __init__(self, parent, **config):
        tk.Canvas.__init__(self, parent, **config)
        
        # Selected vertices
        self.selected = ObservableSet()
        self.selected.register(self)
        
        # Vertices and edges
        self.vertices = set()
        self.edges = set()
        
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


    def _vertex_coords_from_center(self, x, y):
        """Return the coordinates for a vertex centered at (x, y)."""
        return (x-STATERADIUS, y-STATERADIUS, x+STATERADIUS, y+STATERADIUS)
    
    def _edge_coords_from_ends(self, orig, end):
        xo, yo = self._center_from_coords(*self.coords(orig))
        xe, ye = self._center_from_coords(*self.coords(end))
        if xe - xo != 0:
            alpha = math.atan((ye-yo)/(xe-xo))
        else:
            alpha = (-1 if yo < ye else 1) * math.pi / 2
        dx = STATERADIUS * math.cos(alpha)
        dy = STATERADIUS * math.sin(alpha)
        return (xo + dx if xe >= xo else xo - dx,
                yo + dy if xe > xo else yo - dy,
                xe - dx if xe >= xo else xe + dx,
                ye - dy if xe > xo else ye + dy)
    
    def _center_from_coords(self, x0, y0, x1, y1):
        """Return the center of the rectangle given by (x0, y0) and (x1, y1)."""
        return ((x0 + x1) / 2, (y0 + y1) / 2)
    
    
    def current_element(self):
        """Return the current element if any, None otherwise."""
        current = self.find_withtag("current")
        if len(current) > 0:
            return current[0]
        else:
            return None
    
    def new_vertex(self, x, y):
        """Add a vertex at (x,y)."""
        v = self.create_oval(self._vertex_coords_from_center(x, y),
                             fill="white")
        
        # Update scrollregion
        self.update_scrollregion()
            
        self.vertices.add(v)
    
    def new_edge(self, orig, end):
        """Add an edge from orig to end, if none exists."""
        if len(list((o, e, n) for (o, e, n) in self.edges
                    if o == orig and n == end)) <= 0:
            # No pre-existing edge, build it
            coords = self._edge_coords_from_ends(orig, end)
            e = self.create_line(*coords, arrow="last")
            self.edges.add((orig, e, end))
    
    def move_vertices(self, vertices, dx, dy):
        """Move the vertices and the connected edges of (dx,dy)."""
        for v in vertices:
            if v in self.vertices:
                self.move(v, dx, dy)
                for o, e, n in self.edges:
                    if o == v or n == v:
                        self.coords(e,self._edge_coords_from_ends(o, n))
        
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