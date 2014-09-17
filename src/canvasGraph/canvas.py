import tkinter as tk
import math
import random

from .util import ObservableSet
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
        self.vertices = set()
        self.edges = set()
        
        self.mouses = {}
        
        self.config(scrollregion=self.bbox("all"))
        
        self.focus_set()
        
        
        # TODO REMOVE THIS -----
        
        # One step of force-based layout
        self.bind("o", lambda e: self.layout(OneStepForceBasedLayout()))
        
        # Random adding
        def addv(event):
            v = Vertex(self, str(random.randint(0,100)) +
"""
TEST1=TEST1
TEST2=TEST2
TEST3=TEST3""")
            v.style.common.shape.width = 2
            v.style.selected.shape.outline = "red"
            v.refresh()
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
                edge = Edge(self, o, e, label=str(random.randint(0,100)))
        self.bind("k", adde)
        
        # ----------------------
    
    
    def layout(self, layout):
        self.layouting.set(False)
        vertices = {element:element.center()
                    for element in self.elements.values()}
        edges = set()
        for edge in self.edges:
            edges.add((edge.origin, edge))
            edges.add((edge, edge.end))
        np = layout.apply(vertices, edges)
        
        try:
            self.apply_positions(np[0])
        except KeyError:
            self.apply_positions(np)
    
    def apply_positions(self, positions):
        """
        Move all vertices of positions at their new position.
        
        positions -- a vertex -> x,y position dictionary.
        """
        for element in positions.keys() & self.vertices:
            element.move_to(*positions[element])
        for element in positions.keys() & self.edges:
            element.move_to(*positions[element])
        self.update_scrollregion()
    
    def interactive_layout(self, layout):
        def iter_layout():
            if not self.layouting.get():
                return
            
            vertices = {element:element.center()
                        for element in self.elements.values()}
            edges = set()
            for edge in self.edges:
                edges.add((edge.origin, edge))
                edges.add((edge, edge.end))
            
            np, sf = layout.apply(vertices, edges, fixed=self.selected)
            
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
    
    def add_element(self, element, position=None):
        """
        Add the given element on this canvas at position, if specified.
        If position is None, set it at random.
        
        element -- the element to add and draw;
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
        
        element.draw(*position)
        self.update_scrollregion()
        for handle in element.handles():
            self.elements[handle] = element
    
    def add_vertex(self, vertex, position=None):
        """
        Add the given vertex on this canvas at position, if specified.
        If position is None, set it at random.
        
        vertex -- the vertex to add and draw;
        position -- if not None, an x,y tuple.
        """
        self.add_element(vertex, position)
        self.vertices.add(vertex)
    
    def add_edge(self, edge, position=None):
        """
        Add the given edge on this canvas at position, if specified.
        If position is None, set it at random.
        
        edge -- the edge to add and draw;
        position -- if not None, an x,y tuple.
        """
        self.add_element(edge, position)
        self.edges.add(edge)
    
    
    def delete_element(self, element):
        """Delete a given element."""
        
        for handle in element.handles():
            self.delete_handle(handle)
                
        # Discard from other sets (such as selected)
        self.selected.discard(element)
        self.vertices.discard(element)
        self.edges.discard(element)
    
    def delete_handle(self, handle):
        """Delete the given handle."""
        self.delete(handle)
        if handle in self.elements:
            del self.elements[handle]
    
    def move_elements(self, elements, dx, dy):
        """Move the given elements of (dx,dy)."""
        for e in elements:
            e.move(dx, dy)
        for edge in self.edges:
            if edge.origin in elements or edge.end in elements:
                edge.refresh_arrows()
        
        # Update scrollregion
        self.update_scrollregion()
    
    
    def update(self, observed):
        if observed is self.selected:
            for e in self.elements.values():
                if e in self.selected:
                    e.select()
                else:
                    e.deselect()
    
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
    
    def unregister_mouse(self, mouse, button, modifier):
        """Unregister a registered mouse for button pressed with modifier."""
        
        modifier = modifier + "-" if modifier != "" else modifier
        
        if (button, modifier) in self.mouses:
            if mouse in self.mouses[(button, modifier)]:
                self.mouses[(button, modifier)].remove(mouse)
        
            if len(self.mouses[(button, modifier)]) <= 0:
                del self.mouses[(button, modifier)]
                self.unbind("<" + modifier + "ButtonPress-" + button + ">")
                self.unbind("<" + modifier + "B" + button + "-Motion>")
                self.unbind("<" + modifier + "ButtonRelease-" + button + ">")
    
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
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        xscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        xscrollbar.grid(row=2, column=0, sticky=tk.E+tk.W)

        yscrollbar = tk.Scrollbar(self)
        yscrollbar.grid(row=1, column=1, sticky=tk.N+tk.S)

        self.canvas = CanvasGraph(self, xscrollcommand=xscrollbar.set,
                                        yscrollcommand=yscrollbar.set)

        self.canvas.grid(row=1, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

        xscrollbar.config(command=self.canvas.xview)
        yscrollbar.config(command=self.canvas.yview)
        
        # Toolbar
        frame = tk.Frame(self)
        frame.grid(row=0, sticky=tk.W+tk.E)
        
        # Interactive layout
        osfbl = OneStepForceBasedLayout()
        self.canvas.layouting = tk.BooleanVar()
        self.canvas.layouting.set(False)
        self.canvas.layouting.trace("w",
                            lambda *args: self.canvas.interactive_layout(osfbl))
        ilbutton = tk.Checkbutton(frame,
                                  text="Interactive layout",
                                  onvalue=True, offvalue=False,
                                  variable=self.canvas.layouting)
        ilbutton.grid(row=0, sticky=tk.W)
        
        self.canvas.bind("<Control-i>",
           lambda e: self.canvas.layouting.set(not self.canvas.layouting.get()))
        
        
        # Force-based layout
        fbl = ForceBasedLayout()
        fblbutton = tk.Button(frame,
                              text="Force-based layout",
                              command=lambda : self.canvas.layout(fbl))
        fblbutton.config()
        fblbutton.grid(row=0, column=1, sticky=tk.W)
        
        self.canvas.bind("<Control-l>", lambda e: self.canvas.layout(fbl))
        
        
        # Dot layout
        try:
            import pydot
            
            dl = DotLayout()
            dlbutton = tk.Button(frame,
                                 text="Dot layout",
                                 command=lambda : self.canvas.layout(dl))
            dlbutton.grid(row=0, column=2, sticky=tk.W)
            
            self.canvas.bind("<Control-d>", lambda e: self.canvas.layout(dl))
        except ImportError:
            pass
        
        
        # Scroll with mouse
        def on_mousewheel(event):
            self.canvas.yview_scroll(-1 * event.delta, "units")
        self.canvas.bind("<MouseWheel>", on_mousewheel)
        
        
        # Mouses for the canvas
        sm = SelectingMouse(self.canvas,
                            selection=self.canvas.selected, 
                            elements=self.canvas.elements.values(),
                            button="1", modifier="")
        smm = SelectionModifyingMouse(self.canvas,
                                      selection=self.canvas.selected,
                                      elements=self.canvas.elements.values(),
                                      button="1", modifier="Shift")
        mm = MovingMouse(self.canvas, self.canvas.selected,
                         button="1", modifier="")