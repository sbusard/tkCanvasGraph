import math
import tkinter as tk

# Radius of circles representing vertices
VERTEXRADIUS=10


class AttrDict(dict):
    """A dictionary where keys can be accessed as attributes."""
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
    
def override(first, second):
    """
    Override the values of second dictionary on the first one;
    for every key of second, add this key with the corresponding value
    to the first dictionary.
    """
    for k, v in second.items():
        first[k] = v



class GraphElement:
    """
    An element of a graph.
    """
    
    def handles(self):
        """Return the handles of this element."""
        raise NotImplementedError("Should be implemented by subclasses.")
    
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
            canvas.tag_bind(handle, event, callback, add)
    
    def unbind(self, event):
        """
        Remove all the bindings for event of the element on canvas.
        """
        for handle in self.handles():
            canvas.tag_unbind(handle, event)


class Vertex(GraphElement):
    """
    A vertex of a graph. Owns a label and canvas.
    
    The style of the vertex can be changed at any time by updating vertex.style
    dictionary:
        * style.common is the common style: it is applied to any state
          of the vertex and is overriden by the style for the current state;
        * style.selected is the style of the selected vertex.
    Each of these dictionaries contain two other dictionaries:
        * shape defines the appearance of the shape of the vertex;
        * text defines the appearance of the label of the vertex.
    
    To update the style, just give the wanted value to the attribute of these
    dictionaries. For example, to change the fill color of the vertex when it
    is selected, set:
        style.selected.shape.fill = "yellow"
    
    Note that any style that is not overriden is kept as-is. For example, if
    style.selected changes the width of the border of the vertex, and
    style.common does not define a width, then the width will change when
    selecting the vertex, but will not change back when deselecting it.
    """
    
    def __init__(self, canvas, label="", position=None):
        """
        Create a vertex with label on canvas.
        """
        self._canvas = canvas
        self._label = label
        self._selected = False
        
        # Keep track of handle and handle of labels in canvas
        self._handle = None
        self._labelhandle = None
        
        # Styles
        self.style = AttrDict()
        self.style.common = AttrDict()
        
        # Common style
        self.style.common.shape = AttrDict()
        self.style.common.shape.fill = "white"
        self.style.common.text = AttrDict()
        self.style.common.text.justify = tk.CENTER
        
        # Selected style
        self.style.selected = AttrDict()
        self.style.selected.shape = AttrDict()
        self.style.selected.shape.fill = "yellow"
        self.style.selected.text = AttrDict()
        
        self._canvas.add_vertex(self, position)
    
    def handles(self):
        handles = []
        if self._handle is not None:
            handles.append(self._handle)
        if self._labelhandle is not None:
            handles.append(self._labelhandle)
        return tuple(handles)
    
    def delete(self):
        """Remove this vertex from canvas."""
        self._canvas.delete_element(self)
        self._handle = None
        self._labelhandle = None
    
    def draw(self, x, y):
        self.delete()
        canvas = self._canvas
        
        # When drawing, only apply common style
        self._selected = False
        shapestyle = self.style.common.shape
        textstyle = self.style.common.text
        
        # Add label on canvas and store handle
        if self.label != "":
            self._labelhandle = canvas.create_text(x, y,
                                                   text=self.label,
                                                   **textstyle)
            x0l, y0l, x1l, y1l = canvas.bbox(self._labelhandle)
            
            # Draw on canvas and store handle
            x0e = x - (x1l-x0l)/2 * math.sqrt(2)
            y0e = y - (y1l-y0l)/2 * math.sqrt(2)
            x1e = x + (x1l-x0l)/2 * math.sqrt(2)
            y1e = y + (y1l-y0l)/2 * math.sqrt(2)
            self._handle = canvas.create_oval((x0e, y0e, x1e, y1e),
                                              **shapestyle)
            canvas.tag_raise(self._labelhandle)
        
        else:
            self._labelhandle = None
            self._handle = canvas.create_oval((x - VERTEXRADIUS,
                                               y - VERTEXRADIUS,
                                               x + VERTEXRADIUS,
                                               y + VERTEXRADIUS),
                                              **shapestyle)
    
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
    
    def select(self):
        canvas = self._canvas
        
        # Get style
        shapestyle = self.style.common.shape.copy()
        override(shapestyle, self.style.selected.shape)
        textstyle = self.style.common.text.copy()
        override(textstyle, self.style.selected.text)
            
        canvas.itemconfig(self._handle, **shapestyle)
        if self._labelhandle is not None:
            canvas.itemconfig(self._labelhandle, **textstyle)
        
        self._selected = True
    
    def deselect(self):
        canvas = self._canvas
        
        # Get style
        shapestyle = self.style.common.shape
        textstyle = self.style.common.text
            
        canvas.itemconfig(self._handle, **shapestyle)
        if self._labelhandle is not None:
            canvas.itemconfig(self._labelhandle, **textstyle)
        
        self._selected = False
    
    def center(self):
        x0, y0, x1, y1 = self._canvas.coords(self._handle)
        return ((x0 + x1) / 2, (y0 + y1) / 2)
    
    def bbox(self):
        return self._canvas.bbox(self._handle)
    
    def dimensions(self):
        """Return this vertex width and height."""
        x0, y0, x1, y1 = self.bbox()
        return x1-x0, y1-y0
    
    @property
    def label(self):
        return self._label
    
    @label.setter
    def label(self, value):
        self._label = value
        
        # Get style
        shapestyle = self.style.common.shape.copy()
        textstyle = self.style.common.text.copy()
        if self._selected:
            override(shapestyle, self.style.selected.shape)
            override(textstyle, self.style.selected.text)
        
        canvas = self._canvas
        x, y = self.center(canvas)
        
        if self._label != "":
            if self._labelhandle == None:
                self._labelhandle = canvas.create_text(x, y,
                                                       text=self._label,
                                                       **textstyle)
            else:
                canvas.itemconfig(self._labelhandle,
                                  text=self._label)
        
            x0l, y0l, x1l, y1l = canvas.bbox(self._labelhandle)
        
            # Draw on canvas and store handle
            x0e = x - (x1l-x0l)/2 * math.sqrt(2)
            y0e = y - (y1l-y0l)/2 * math.sqrt(2)
            x1e = x + (x1l-x0l)/2 * math.sqrt(2)
            y1e = y + (y1l-y0l)/2 * math.sqrt(2)
            canvas.coords(self._handle, (x0e, y0e, x1e, y1e))
        
        else:
            if self._labelhandle != None:
                canvas.delete(self._labelhandle)
            canvas.coords(self._handle, (x - VERTEXRADIUS,
                                         y - VERTEXRADIUS,
                                         x + VERTEXRADIUS,
                                         y + VERTEXRADIUS))
        
        canvas.update_vertex(self)
    
    def refresh(self):
        """
        Refresh the appearance of this vertex on canvas.
        """
        canvas = self._canvas
        # Get style
        shapestyle = self.style.common.shape.copy()
        textstyle = self.style.common.text.copy()
        if self._selected:
            override(shapestyle, self.style.selected.shape)
            override(textstyle, self.style.selected.text)
        
        canvas.itemconfig(self._handle, **shapestyle)
        if self._labelhandle is not None:
            canvas.itemconfig(self._labelhandle, **textstyle)



class Edge(GraphElement):
    """
    An edge of a graph. Owns a label and two ends.
    
    The style of the edge can be changed at any time by updating edge.style
    dictionary:
        * style.common is the common style: it is applied to any state
          of the edge and is overriden by the style for the current state.
    This dictionary contains three other dictionaries:
        * shape defines the appearance of the arrow of the edge;
        * text defines the appearance of the label of the edge;
        * textbg defines the appearance of the background rectangle of the
          label of the edge.
    
    To update the style, just give the wanted value to the attribute of these
    dictionaries. For example, to change the line color of the edge, set:
        style.common.shape.fill = "red"
    """
    
    def __init__(self, canvas, origin, end, label=""):
        """
        Create an edge between origin and end.
        """
        self._canvas = canvas
        self.origin = origin
        self.end = end
        self._label = label
        self._handle = None
        self._labelhandle = None
        self._labelbghandle = None
        
        # Styles
        self.style = AttrDict()
        self.style.common = AttrDict()
        
        # Common style
        self.style.common.shape = AttrDict()
        self.style.common.shape.arrow = "last"
        self.style.common.text = AttrDict()
        self.style.common.text.justify = tk.CENTER
        self.style.common.textbg = AttrDict()
        self.style.common.textbg.fill = "white"
        self.style.common.textbg.outline = "white"
        
        self._canvas.add_edge(self)
    
    def handles(self):
        handles = []
        if self._handle is not None:
            handles.append(self._handle)
        if self._labelhandle is not None:
            handles.append(self._labelhandle)
        if self._labelbghandle is not None:
            handles.append(self._labelbghandle)
        return tuple(handles)
    
    def delete(self):
        """Remove this edge from canvas."""
        self._canvas.delete_element(self)
        self._handle = None
        self._labelhandle = None
        self._labelbghandle = None
    
    def draw(self):
        # Draw on canvas and store handle
        canvas = self._canvas
        coords = self._edge_coords_from_ends(self.origin._handle,
                                             self.end._handle)
        
        handle = canvas.create_line(*coords, **self.style.common.shape)
        self._handle = handle
        
        # Add label on canvas and store handle
        if self.label != "":
            x0, y0, x1, y1 = canvas.coords(handle)
            x, y = ((x0 + x1) / 2, (y0 + y1) / 2)
            labelhandle = canvas.create_text(x, y, text=self.label,
                                             **self.style.common.text)
            self._labelhandle = labelhandle
            self._labelbghandle = canvas.create_rectangle(
                                                      *canvas.bbox(labelhandle),
                                                     **self.style.common.textbg)
            canvas.tag_raise(labelhandle)
        else:
            self._labelhandle = self._labelbghandle = None
    
    def _edge_coords_from_ends(self, orig, end):
        xo0, yo0, xo1, yo1 = self._canvas.coords(orig)
        xoc, yoc = (xo1 + xo0) / 2, (yo1 + yo0) / 2
        xe0, ye0, xe1, ye1 = self._canvas.coords(end)
        xec, yec = (xe1 + xe0) / 2, (ye1 + ye0) / 2
        
        ao = xo1 - xoc
        bo = yo1 - yoc
        ae = xe1 - xec
        be = ye1 - yec
        
        if xec != xoc:
            m = (yec - yoc) / (xec - xoc)
            
            dox = (ao * bo) / math.sqrt(ao * ao * m * m + bo * bo)
            dex = (ae * be) / math.sqrt(ae * ae * m * m + be * be)
            doy = (ao * bo * m) / math.sqrt(ao * ao * m * m + bo * bo)
            dey = (ae * be * m) / math.sqrt(ae * ae * m * m + be * be)
        
        else:
            dox = dex = 0
            doy = bo * (-1 if yec > yoc else 1)
            dey = be * (-1 if yec > yoc else 1)
        
        return (xoc + dox if xec >= xoc else xoc - dox,
                yoc + doy if xec > xoc else yoc - doy,
                xec - dex if xec >= xoc else xec + dex,
                yec - dey if xec > xoc else yec + dey)
    
    def length(self):
        x0, y0, x1, y1 = self._edge_coords_from_ends(self.origin._handle,
                                                     self.end._handle)
        dx = x1 - x0
        dy = y1 - y0
        return math.sqrt(dx*dx + dy*dy)
    
    @property
    def label(self):
        return self._label
        
    @label.setter
    def label(self, value):
        self._label = value
        canvas = self._canvas
        
        if self._labelhandle is None:
            if self._label != "":
                x0, y0, x1, y1 = canvas.coords(self._handle)
                x, y = ((x0 + x1) / 2, (y0 + y1) / 2)
                self._labelhandle = canvas.create_text(x, y,
                                                       text=self._label,
                                                       **self.style.common.text)
                self._labelbghandle = canvas.create_rectangle(
                                                *canvas.bbox(self._labelhandle),
                                                **self.style.common.textbg)
                canvas.tag_raise(self._labelhandle)
        else:
            if self._label == "":
                canvas.delete(self._labelhandle)
                canvas.delete(self._labelbghandle)
                self._labelhandle = None
                self._labelbghandle = None
            else:
                canvas.itemconfig(self._labelhandle,
                                  text=self._label)
                canvas.coords(self._labelbghandle,
                              *canvas.bbox(self._labelhandle))
    
    def move(self):
        """
        Move this edge on canvas to fit its ends.
        """
        canvas = self._canvas
        
        canvas.coords(self._handle,
                      self._edge_coords_from_ends(self.origin._handle,
                                                  self.end._handle))
        if self._labelhandle is not None:
            x0, y0, x1, y1 = canvas.coords(self._handle)
            x, y = ((x0 + x1) / 2, (y0 + y1) / 2)
            canvas.coords(self._labelhandle, x, y)
            canvas.coords(self._labelbghandle,
                          *canvas.bbox(self._labelhandle))
    
    def refresh(self):
        """
        Refresh the appearance of this edge on canvas.
        """
        canvas = self._canvas
        canvas.itemconfig(self._handle, **self.style.common.shape)
        if self._labelhandle is not None:
            canvas.itemconfig(self._labelhandle,
                              **self.style.common.text)
            if self._labelbghandle is not None:
                canvas.itemconfig(self._labelbghandle,
                                  **self.style.common.textbg)