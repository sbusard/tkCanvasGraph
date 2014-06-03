import math
import tkinter as tk
from copy import deepcopy
from .util import AttrDict


# Elements common style
element_style = AttrDict()
element_style.shape = AttrDict()
element_style.shape.fill = "white"
element_style.text = AttrDict()
element_style.text.justify = tk.CENTER


selected_element_style = AttrDict()
selected_element_style.shape = AttrDict()
selected_element_style.shape.fill = "yellow"
selected_element_style.text = AttrDict()

class Shape:
    """
    The shape of a graph element.
    """
    def draw(canvas, bbox, style):
        """
        Draw this shape on canvas, around the given bounding box, with style,
        and return the handle on canvas.
        
        canvas -- the canvas;
        bbox -- the tkinter-style bounding box to draw around;
        style -- the style of the shape.
        """
        raise NotImplementedError("Should be implemented by subclasses.")
    
    def intersection(bbox, end):
        """
        Return the point of intersection between this shape with given bouding
        box, and the line segment defined by the center of this bounding box
        and end.
        Return None is such an intersection does not exist.
        
        bbox -- the tkinter-style bounding box of this shape;
        end -- the coordinates of the ending point.
        """
        raise NotImplementedError("Should be implemented by subclasses.")


class Oval(Shape):
    
    def __init__(self, diameter=20):
        """
        Create a new oval shape with default diameter. Default diameter is used
        to draw a circle when the bounding box to draw around is too small.
        """
        self._diameter = diameter
    
    def draw(self, canvas, bbox, style):
        x0l, y0l, x1l, y1l = bbox
        xc, yc = (x1l + x0l)/2, (y1l + y0l)/2
        
        if x1l-x0l < self._diameter:
            x0e = xc - self._diameter/2
            x1e = xc + self._diameter/2
        else:
            x0e = xc - (x1l-x0l)/2 * math.sqrt(2)
            x1e = xc + (x1l-x0l)/2 * math.sqrt(2)
        
        if y1l-y0l < self._diameter:
            y0e = yc - self._diameter/2
            y1e = yc + self._diameter/2
        else:
            y0e = yc - (y1l-y0l)/2 * math.sqrt(2)
            y1e = yc + (y1l-y0l)/2 * math.sqrt(2)
        
        return canvas.create_oval((x0e, y0e, x1e, y1e),**style)
    
    def intersection(self, bbox, end):
        xo0, yo0, xo1, yo1 = bbox
        xoc, yoc = (xo1 + xo0) / 2, (yo1 + yo0) / 2
        xec, yec = end
        
        ao = xo1 - xoc
        bo = yo1 - yoc
        
        if xec != xoc:
            m = (yec - yoc) / (xec - xoc)
            
            dox = (ao * bo) / math.sqrt(ao * ao * m * m + bo * bo)
            doy = (ao * bo * m) / math.sqrt(ao * ao * m * m + bo * bo)
        
        else:
            dox = 0
            doy = bo * (-1 if yec > yoc else 1)
        
        return (xoc + dox if xec >= xoc else xoc - dox,
                yoc + doy if xec > xoc else yoc - doy)

class Rectangle(Shape):
    
    def __init__(self, size=5):
        """
        Create a new rectangle shape with default size. Default size is used
        to draw a square when the bounding box to draw around is too small.
        """
        self._size = size
    
    def draw(self, canvas, bbox, style):
        x0l, y0l, x1l, y1l = bbox
        xc, yc = (x1l + x0l)/2, (y1l + y0l)/2
        
        if x1l-x0l < self._size:
            x0e = xc - self._size/2
            x1e = xc + self._size/2
        else:
            x0e, x1e = x0l, x1l
        
        if y1l-y0l < self._size:
            y0e = yc - self._size/2
            y1e = yc + self._size/2
        else:
            y0e, y1e = y0l, y1l
        
        return canvas.create_rectangle((x0e, y0e, x1e, y1e),**style)
    
    def intersection(self, bbox, end):
        xo0, yo0, xo1, yo1 = bbox
        xoc, yoc = (xo1 + xo0) / 2, (yo1 + yo0) / 2
        xec, yec = end
        
        if xec != xoc:
            m = abs((yec - yoc) / (xec - xoc))
            
            if m == 0:
                dox = xo1 - xoc
                doy = 0
            else:
                dox = min(xo1 - xoc, (yo1 - yoc) / m)
                doy = min(yo1 - yoc, (xo1 - xoc) * m)
        else:
            dox = 0
            doy = yo1 - yoc
        
        return (xoc + dox if xec > xoc else xoc - dox,
                yoc + doy if yec > yoc else yoc - doy)


class GraphElement:
    """
    An element of a graph, composed of a shape and text in it.
    
    The style of the element can be changed at any time by updating
    element.style.common dictionary:
        * style.common is the common style: it is applied to any state
          of the element and is overriden by the style for the current state.
    This dictionary contains three other dictionaries:
        * shape defines the appearance of the shape of the element;
        * text defines the appearance of the label of the element.
    
    To update the style, just give the wanted value to the attribute of these
    dictionaries. For example, to change the fill color of the element, set:
        style.selected.shape.fill = "yellow"
    """
    
    def __init__(self, canvas, shape, label="", position=None):
        """
        Create a graph element with shape and label on canvas.
        The element must be added to the canvas after initialisation.
        """
        self._canvas = canvas
        self.shape = shape
        self._label = label
        
        # Keep track of handle and handle of labels in canvas
        self._handle = None
        self._labelhandle = None
        
        # Styles
        self.style = AttrDict()
        self.style.common = deepcopy(element_style)
        
        # Start as not selected
        self._selected = False
        self.style.selected = deepcopy(selected_element_style)
    
    def handles(self):
        """Return the handles of this element."""
        handles = []
        if self._handle is not None:
            handles.append(self._handle)
        if self._labelhandle is not None:
            handles.append(self._labelhandle)
        return tuple(handles)
    
    def draw(self, x, y):
        self.delete()
        canvas = self._canvas
        
        # Add label on canvas and store handle
        if self.label != "":
            self._labelhandle = canvas.create_text(x, y,
                                                   text=self.label,
                                                   **self.style.common.text)
            bbox = canvas.bbox(self._labelhandle)
        else:
            self._labelhandle = None
            bbox = (x, y, x, y)
        
        # Draw on canvas and store handle
        self._handle = self.shape.draw(canvas, bbox, self.style.common.shape)            
        
        if self._labelhandle is not None:
             canvas.tag_raise(self._labelhandle)
    
    def move(self, dx, dy):
        """
        Move this vertex on canvas.
        
        dx -- the difference to move on x axis;
        dy -- the difference to move on y axis.
        """
        canvas = self._canvas
        canvas.move(self._handle, dx, dy)
        if self._labelhandle is not None:
            canvas.move(self._labelhandle, dx, dy)
    
    def move_to(self, x, y):
        """
        Move this vertex to x,y on canvas
        and return the corresponding dx,dy.
        """
        curx, cury = self.center()
        dx = x - curx
        dy = y - cury
        self.move(dx, dy)
        return (dx, dy)
    
    def delete(self):
        """Remove this element from canvas."""
        self._canvas.delete_element(self)
        self._handle = None
        self._labelhandle = None
    
    def center(self):
        x0, y0, x1, y1 = self._canvas.coords(self._handle)
        return ((x0 + x1) / 2, (y0 + y1) / 2)
    
    def bbox(self):
        return self._canvas.bbox(self._handle)
    
    def dimensions(self):
        """Return this element width and height."""
        x0, y0, x1, y1 = self.bbox()
        return x1-x0, y1-y0
    
    @property
    def label(self):
        return self._label
    
    @label.setter
    def label(self, value):
        self._label = value
        self.draw(*self.center())
    
    def select(self):
        self._selected = True
        self.refresh()
    
    def deselect(self):
        self._selected = False
        self.refresh()
    
    def refresh(self, style=None):
        """
        Refresh the appearance of this vertex on canvas.
        
        style -- if not None, a dictionary defining the style for shape and text
                 if None, the common style of this element is used.
        """
        canvas = self._canvas
        if style is None:
            style = deepcopy(self.style.common)
        
        if self._selected:
            style.shape.override(self.style.selected.shape)
            style.text.override(self.style.selected.text)
        
        canvas.itemconfig(self._handle, style.shape)
        if self._labelhandle is not None:
            canvas.itemconfig(self._labelhandle, style.text)
    
    def bind(self, event, callback, add=None):
        """
        Add an event binding to this element on canvas.
        
        event -- the event specifier;
        callback -- the function to call when the event occurs.
                    a function taking one argument: the event;
        add -- if present and set to "+", the new binding is added to any
               existing binding.
        """
        for handle in self.handles():
            self._canvas.tag_bind(handle, event, callback, add)
    
    def unbind(self, event):
        """
        Remove all the bindings for event of the element on canvas.
        """
        for handle in self.handles():
            self._canvas.tag_unbind(handle, event)


class Vertex(GraphElement):
    """
    A vertex of a graph.
    
    In addition to the common style of graph elements, vertices define a style
    for their selected states. The style.selected dictionary contains:
        * shape, defining the appearance of the shape of the vertex when
          selected;
        * text, defining the appearance of the label of the vertex when
          selected.
    
    Note that any style that is not overriden is kept as-is. For example, if
    style.selected changes the width of the border of the vertex, and
    style.common does not define a width, then the width will change when
    selecting the vertex, but will not change back when deselecting it.
    """
    
    def __init__(self, canvas, label="", position=None):
        """
        Create a vertex with label on canvas.
        """
        super(Vertex, self).__init__(canvas, shape=Oval(), label=label,
                                             position=position)
        
        self._canvas.add_vertex(self, position)


class Edge(GraphElement):
    """
    An edge of a graph.
    
    In addition to the common style of graph elements, edges define the
    style.common.arrow dictionary for the arrow of the edge.
    """
    
    def __init__(self, canvas, origin, end, label="", position=None):
        """
        Create an edge between origin and end. If position is None, draw the 
        edge between origin and end.
        """
        super(Edge, self).__init__(canvas, shape=Rectangle(), label=label,
                                           position=position)
        self.origin = origin
        self.end = end
        self._arrowhandle = None
        
        # Common style
        self.style.common.arrow = AttrDict()
        self.style.common.arrow.arrow = "last"
        
        # Position
        if position is None:
            xo, yo = origin.center()
            xe, ye = end.center()
            position = ((xo + xe) / 2, (yo + ye) / 2)
        
        self._canvas.add_edge(self, position)
    
    def handles(self):
        if self._arrowhandle is not None:
            return super(Edge, self).handles() + (self._arrowhandle,)
        else:
            return super(Edge, self).handles()
    
    def delete(self):
        """Remove this edge from canvas."""
        super(Edge, self).delete()
        self._arrowhandle = None
    
    def refresh_arrows(self):
        canvas = self._canvas
        if self._arrowhandle is not None:
            canvas.delete(self._arrowhandle)
        # Draw line: from origin to label and from label to end
        xo, yo = self.origin.shape.intersection(self.origin.bbox(),
                                                self.center())
        xol, yol = self.shape.intersection(self.bbox(), self.origin.center())
        xel, yel = self.shape.intersection(self.bbox(), self.end.center())
        xe, ye = self.end.shape.intersection(self.end.bbox(), self.center())
        self._arrowhandle = canvas.create_line((xo, yo, xol, yol,
                                                xel, yel, xe, ye),
                                               **self.style.common.arrow)
        canvas.tag_raise(self._handle)
        if self._labelhandle is not None:
            canvas.tag_raise(self._labelhandle)
    
    def draw(self, x, y):
        super(Edge, self).draw(x, y)
        self.refresh_arrows()
    
    def move(self, dx, dy):
        super(Edge, self).move(dx, dy)
        # Redraw arrow
        self.refresh_arrows()
    
    def refresh(self):
        super(Edge, self).refresh()
        self._canvas.itemconfig(self._arrowhandle, self.style.common.arrow)
        