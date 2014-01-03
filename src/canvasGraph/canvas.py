import tkinter as tk
import math
import random

from .observable import ObservableSet
from .mouse import (SelectingMouse, SelectionModifyingMouse,
                   MovingMouse, CreatingMouse)
from .graph import Vertex, Edge
from .layout import ForceBasedLayout, OneStepForceBasedLayout, DotLayout

# Padding for scroll region
PADDING=10


class CanvasGraph(tk.Canvas):
    
    def __init__(self, parent, **config):
        super(CanvasGraph, self).__init__(parent, **config)
        
        self.event_handled = False
        
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
        
        
        menu = tk.Menu(self, tearoff=0)
        
        # Interactive layout
        osfbl = OneStepForceBasedLayout()
        self.layouting = tk.BooleanVar()
        self.layouting.set(False)
        self.layouting.trace("w", lambda *args: self.interactive_layout(osfbl))
        menu.add_checkbutton(label="Interactive layout",
                             onvalue=True, offvalue=False, 
                             variable=self.layouting,
                             accelerator="Ctrl+i")
        
        self.bind("<Control-i>",
                  lambda e: self.layouting.set(not self.layouting.get()))
        
        # Force-based layout
        fbl = ForceBasedLayout()
        menu.add_command(label="Force-based layout",
                         command=lambda : self.layout(fbl),
                         accelerator="Ctrl+l")
        
        self.bind("<Control-l>", lambda e: self.layout(fbl))
        
        # Dot layout
        dl = DotLayout()
        menu.add_command(label="Dot layout",
                         command=lambda : self.layout(dl),
                         accelerator="Ctrl+d")
        
        self.bind("<Control-d>", lambda e: self.layout(dl))

        def popup(event):
            menu.post(event.x_root, event.y_root)

        self.bind("<Button-2>", popup)
        
        
        # TODO REMOVE THIS -----
        
        # One step of force-based layout
        self.bind("o", lambda e: self.layout(OneStepForceBasedLayout()))
        
        # Random adding
        def addv(event):
            v = Vertex(str(random.randint(0,100)) +
"""
TEST1=TEST1
TEST2=TEST2
TEST3=TEST3""")
            self.add_vertex(v)
        self.bind("j", addv)
        def adde(event):
            pairs = [(o, e) for o in self.vertices
                            for e in self.vertices
                            if o != e
                            if len([edge for edge in self.edges
                                         if edge.origin == o
                                            and edge.end == e]) <= 0]
            if len(pairs) > 0:
                o, e = random.choice(pairs)
                edge = Edge(o, e)
                self.add_edge(edge)
        self.bind("k", adde)
        
        # ----------------------
    
    
    def layout(self, layout):
        self.layouting.set(False)
        vertices = {vertex:vertex.center(self) for vertex in self.vertices}
        edges = set()
        for edge in self.edges:
            # Add edge in edges if no edge in edges already share
            # the extremities
            if (len([e for e in edges
                       if (e.origin == edge.origin and e.end == edge.end)
                       or (e.origin == edge.end and e.end == edge.origin)])
                    <= 0):
                edges.add(edge)
        np = layout.apply(self, vertices, edges)
        
        try:
            self.apply_positions(np[0])
        except KeyError:
            self.apply_positions(np)
    
    def apply_positions(self, positions):
        """
        Move all vertices of positions at their new position.
        
        positions -- a vertex -> x,y position dictionary.
        """
        for vertex in positions:
            vertex.move_to(self, *positions[vertex])
        for e in self.edges:
            e.move(self)
        
        self.update_scrollregion()
    
    def interactive_layout(self, layout):
        def iter_layout():
            if not self.layouting.get():
                return
            
            vertices = {vertex:vertex.center(self)
                        for vertex in self.vertices}
            
            edges = set()
            for edge in self.edges:
                # Add edge in edges if no edge in edges already share
                # the extremities
                if len([e for e in edges
                         if (e.origin == edge.origin and e.end == edge.end)
                      or (e.origin == edge.end and e.end == edge.origin)]) <= 0:
                    edges.add(edge)
            np, sf = layout.apply(self, vertices, edges, fixed=self.selected)
            
            self.apply_positions(np)
            
            if self.layouting.get():
                self.after(25, iter_layout)
        
        if self.layouting.get():
            self.after(25, iter_layout)
    
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
    
    def add_vertex(self, vertex, position=None):
        """
        Add the given vertex on this canvas at position, if specified.
        
        vertex -- the vertex to add and draw;
        position -- if not None, an x,y tuple.
        """
        # Compute position if not specified;
        # The vertex is added at random in the scroll region, if it is
        # large enough.
        if position is None:
            if self.bbox("all") is None:
                position = 0,0
            else:
                x0, y0, x1, y1 = self.bbox("all")
                dx = x1-x0 if x1-x0 > 100 else 100
                dy = y1-y0 if y1-y0 > 100 else 100
                x, y = random.randint(0,dx), random.randint(0, dy)
                position = x0 + x, y0 + y
        
        vertex.draw(self, *position)
        self.update_scrollregion()
        self.vertices.add(vertex)
        for handle in vertex.handles(self):
            self.elements[handle] = vertex
    
    def add_edge(self, edge):
        """
        Add the given edge on this canvas and draw it.
        
        edge -- the edge to add.
        """
        edge.draw(self)
        self.edges.add(edge)
    
    def move_vertices(self, vertices, dx, dy):
        """Move the vertices and the connected edges of (dx,dy)."""
        for v in vertices:
            v.move(self, dx, dy)
            for e in self.edges:
                if e.origin == v or e.end == v:
                    e.move(self)
        
        # Update scrollregion
        self.update_scrollregion()
    
    
    def update(self, observed):
        if observed is self.selected:
            for v in self.vertices:
                if v in self.selected:
                    v.select(self)
                else:
                    v.deselect(self)
    
    def update_vertex(self, vertex):
        if vertex in self.elements.values():
            keys = {k for k in self.elements if self.elements[k] == vertex}
            for key in keys:
                del self.elements[key]
            for handle in vertex.handles(self):
                self.elements[handle] = vertex
            for e in self.edges:
                if e.origin == vertex or e.end == vertex:
                    e.move()
    
    def update_scrollregion(self):
        bbox = self.bbox("all")
        if bbox is not None:
            minx, miny, maxx, maxy = bbox
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
    
    
    def bind(self, event, func, add=None):
        def newfunc(event):
            if self.event_handled:
                self.event_handled = False
            else:
                return func(event)
        super(CanvasGraph, self).bind(event, newfunc, add)
        
    
    def tag_bind(self, item, event, func, add=None):
        def newfunc(event):
            if func(event) == "break":
                self.event_handled = True
        super(CanvasGraph, self).tag_bind(item, event, newfunc, add)


class CanvasFrame(tk.Frame):
    """
    A frame containing a canvas graph in which one can display any graph.
    """
    
    def __init__(self, parent, **config):
        super(CanvasFrame, self).__init__(parent, **config)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        xscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        xscrollbar.grid(row=1, column=0, sticky=tk.E+tk.W)

        yscrollbar = tk.Scrollbar(self)
        yscrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)

        self.canvas = CanvasGraph(self, xscrollcommand=xscrollbar.set,
                                        yscrollcommand=yscrollbar.set)

        self.canvas.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

        xscrollbar.config(command=self.canvas.xview)
        yscrollbar.config(command=self.canvas.yview)

        # Mouses for the canvas
        sm = SelectingMouse(self.canvas,
                            selection=self.canvas.selected, 
                            elements=self.canvas.vertices,
                            button="1", modifier="")
        smm = SelectionModifyingMouse(self.canvas,
                                      selection=self.canvas.selected,
                                      elements=self.canvas.vertices,
                                      button="1", modifier="Shift")
        mm = MovingMouse(self.canvas, self.canvas.selected,
                         button="1", modifier="")
    
    
    def add_vertices(self, vertices):
        """
        Add the given set of vertices to the canvas of this frame.
        
        vertices -- a set of vertices.
        """
        for vertex in vertices:
            self.canvas.add_vertex(vertex)
    
    
    def add_edges(self, edges):
        """
        Add the given set of edges to the canvas of this frame.
        
        edges -- a set of edges.
        """
        for edge in edges:
            self.canvas.add_edge(edge)


def show_graph_in_canvas(vertices, edges):
    """
    Create a new window with a canvas and add all given vertices and edges.
    """
    root = tk.Tk()
    
    cframe = CanvasFrame(root)
    
    cframe.pack(fill="both", expand=True)
    
    # Add vertices and edges
    for vertex in vertices:
        cframe.add_vertex(vertex)
    for edge in edges:
        cframe.add_edge(edge)
    
    root.mainloop()