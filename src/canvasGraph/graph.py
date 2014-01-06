import math
import tkinter as tk

from .exception import UnknownCanvasError

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
    
    def handles(self, canvas):
        """Return the handles in canvas."""
        handles = []
        for handlesset in self._handlessets:
            if canvas in handlesset and handlesset[canvas] is not None:
                handles.append(handlesset[canvas])
        return tuple(handles)
    
    def bind_on(self, canvas, event, callback, add=None):
        """
        Add an event binding to this element on canvas.
        
        canvas -- the canvas on which operate;
        event -- the event specifier;
        callback -- the function to call when the event occurs.
                    a function taking one argument: the event;
        add -- if present and set to "+", the new binding is added to any
               existing binding.
        """
        for handle in self.handles(canvas):
            canvas.tag_bind(handle, event, callback, add)
    
    def unbind_on(self, canvas, event):
        """
        Remove all the bindings for event of the element on canvas.
        """
        for handle in self.handles(canvas):
            canvas.tag_unbind(handle, event)


class Vertex(GraphElement):
    """
    A vertex of a graph. Owns a label and canvas be drawn on several canvas.
    
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
    
    def __init__(self, label=""):
        """
        Create a vertex with label.
        """
        self._label = label
        self._selected = False
        
        # Keep track of handles and handles of labels in each canvas
        self._handles = {}
        self._labelhandles = {}
        self._handlessets = [self._handles, self._labelhandles]
        
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
    
    def delete_from(self, canvas):
        """Remove this vertex from canvas, if it is drawn on it."""
        if canvas in self._handles:
            if self._handles[canvas] is not None:
                canvas.delete(self._handles[canvas])
            del self._handles[canvas]
        if canvas in self._labelhandles:
            if self._labelhandles[canvas] is not None:
                canvas.delete(self._labelhandles[canvas])
            del self._handles[canvas]
    
    def draw(self, canvas, x, y):
        self.delete_from(canvas)
        
        # When drawing, only apply common style
        self._selected = False
        shapestyle = self.style.common.shape
        textstyle = self.style.common.text
        
        # Add label on canvas and store handle
        if self.label != "":
            self._labelhandles[canvas] = canvas.create_text(x, y,
                                                            text=self.label,
                                                            **textstyle)
            x0l, y0l, x1l, y1l = canvas.bbox(self._labelhandles[canvas])
            
            # Draw on canvas and store handle
            x0e = x - (x1l-x0l)/2 * math.sqrt(2)
            y0e = y - (y1l-y0l)/2 * math.sqrt(2)
            x1e = x + (x1l-x0l)/2 * math.sqrt(2)
            y1e = y + (y1l-y0l)/2 * math.sqrt(2)
            self._handles[canvas] = canvas.create_oval((x0e, y0e, x1e, y1e),
                                                       **shapestyle)
            canvas.tag_raise(self._labelhandles[canvas])
        
        else:
            self._labelhandles[canvas] = None
            self._handles[canvas] = canvas.create_oval((x - VERTEXRADIUS,
                                                        y - VERTEXRADIUS,
                                                        x + VERTEXRADIUS,
                                                        y + VERTEXRADIUS),
                                                       **shapestyle)
    
    def move(self, canvas, dx, dy):
        """
        Move this vertex on canvas.
        
        dx -- the difference to move on x axis;
        dy -- the difference to move on y axis.
        """
        if canvas not in self._handles:
            raise UnknownCanvasError("Unknown canvas ({}), "
                                     "cannot move.".format(canvas))
        canvas.move(self._handles[canvas], dx, dy)
        if (canvas in self._labelhandles
            and self._labelhandles[canvas] is not None):
            canvas.move(self._labelhandles[canvas], dx, dy)
    
    def move_to(self, canvas, x, y):
        """
        Move this vertex to x,y on canvas
        and return the corresponding dx,dy.
        """
        curx, cury = self.center(canvas)
        dx = x - curx
        dy = y - cury
        self.move(canvas, dx, dy)
        return (dx, dy)
    
    def select(self, canvas):
        if canvas not in self._handles:
            raise UnknownCanvasError("Unknown canvas ({}), "
                                     "cannot select vertex.".format(canvas))
        
        # Get style
        shapestyle = self.style.common.shape.copy()
        override(shapestyle, self.style.selected.shape)
        textstyle = self.style.common.text.copy()
        override(textstyle, self.style.selected.text)
            
        canvas.itemconfig(self._handles[canvas], **shapestyle)
        if (canvas is self._labelhandles and
            self._labelhandles[canvas] is not None):
            canvas.itemconfig(self._labelhandles[canvas], **textstyle)
        
        self._selected = True
    
    def deselect(self, canvas):
        if canvas not in self._handles:
            raise UnknownCanvasError("Unknown canvas ({}), "
                                     "cannot deselect vertex.".format(canvas))
        
        # Get style
        shapestyle = self.style.common.shape
        textstyle = self.style.common.text
            
        canvas.itemconfig(self._handles[canvas], **shapestyle)
        if (canvas is self._labelhandles and
            self._labelhandles[canvas] is not None):
            canvas.itemconfig(self._labelhandles[canvas], **textstyle)
        
        self._selected = False
    
    def center(self, canvas):
        if canvas not in self._handles:
            raise UnknownCanvasError("Unknown canvas ({}), "
                                     "cannot find center.".format(canvas))
        x0, y0, x1, y1 = canvas.coords(self._handles[canvas])
        return ((x0 + x1) / 2, (y0 + y1) / 2)
    
    def bbox(self, canvas):
        if canvas not in self._handles:
            raise UnknownCanvasError("Unknown canvas ({}), "
                                     "cannot find bounding box.".format(canvas))
        return canvas.bbox(self._handles[canvas])
    
    def dimensions(self, canvas):
        """Return this vertex width and height."""
        x0, y0, x1, y1 = self.bbox(canvas)
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
        
        for canvas in self._handles:
            x, y = self.center(canvas)
        
            if self._label != "":
                if self._labelhandles[canvas] == None:
                    self._labelhandles[canvas] = canvas.create_text(x, y,
                                                               text=self._label,
                                                               **textstyle)
                else:
                    canvas.itemconfig(self._labelhandles[canvas],
                                      text=self._label)
            
                x0l, y0l, x1l, y1l = canvas.bbox(self._labelhandles[canvas])
            
                # Draw on canvas and store handle
                x0e = x - (x1l-x0l)/2 * math.sqrt(2)
                y0e = y - (y1l-y0l)/2 * math.sqrt(2)
                x1e = x + (x1l-x0l)/2 * math.sqrt(2)
                y1e = y + (y1l-y0l)/2 * math.sqrt(2)
                canvas.coords(self._handles[canvas], (x0e, y0e, x1e, y1e))
        
            else:
                if self._labelhandles[canvas] != None:
                    canvas.delete(self._labelhandles[canvas])
                canvas.coords(self._handles[canvas], (x - VERTEXRADIUS,
                                                      y - VERTEXRADIUS,
                                                      x + VERTEXRADIUS,
                                                      y + VERTEXRADIUS))
        
            canvas.update_vertex(self)
    
    def refresh(self, canvas):
        """
        Refresh the appearance of this vertex on canvas.
        """
        if canvas not in self._handles:
            raise UnknownCanvasError("Unknown canvas ({}), "
                                     "cannot refresh vertex.".format(canvas))
        # Get style
        shapestyle = self.style.common.shape.copy()
        textstyle = self.style.common.text.copy()
        if self._selected:
            override(shapestyle, self.style.selected.shape)
            override(textstyle, self.style.selected.text)
        
        canvas.itemconfig(self._handles[canvas], **shapestyle)
        if (canvas in self._labelhandles and
            self._labelhandles[canvas] is not None):
            canvas.itemconfig(self._labelhandles[canvas], **textstyle)



class Edge(GraphElement):
    """
    An edge of a graph. Owns a label and two ends
    and can be drawn on different canvas.
    
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
    
    def __init__(self, origin, end, label=""):
        """
        Create an edge between origin and end.
        """
        self.origin = origin
        self.end = end
        self._label = label
        self._handles = {}
        self._labelhandles = {}
        self._labelbghandles = {}
        self._handlessets = [self._handles, self._labelhandles,
                             self._labelbghandles]
        
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
    
    def draw(self, canvas):
        # Draw on canvas and store handle
        try:
            coords = self._edge_coords_from_ends(canvas, 
                                                self.origin._handles[canvas],
                                                self.end._handles[canvas])
        except KeyError:
            raise UnknownCanvasError("Edge ends are not in canvas.")
        
        handle = canvas.create_line(*coords, **self.style.common.shape)
        self._handles[canvas] = handle
        
        # Add label on canvas and store handle
        if self.label != "":
            x0, y0, x1, y1 = canvas.coords(handle)
            x, y = ((x0 + x1) / 2, (y0 + y1) / 2)
            labelhandle = canvas.create_text(x, y, text=self.label,
                                             **self.style.common.text)
            self._labelhandles[canvas] = labelhandle
            self._labelbghandles[canvas] = canvas.create_rectangle(
                                    *canvas.bbox(labelhandle),
                                    **self.style.common.textbg)
            canvas.tag_raise(labelhandle)
        else:
            self._labelhandles[canvas] = self._labelbghandles[canvas] = None
    
    def _edge_coords_from_ends(self, canvas, orig, end):
        xo0, yo0, xo1, yo1 = canvas.coords(orig)
        xoc, yoc = (xo1 + xo0) / 2, (yo1 + yo0) / 2
        xe0, ye0, xe1, ye1 = canvas.coords(end)
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
    
    def length(self, canvas):
        x0, y0, x1, y1 = self._edge_coords_from_ends(canvas,
                                                     self.origin.handle,
                                                     self.end.handle)
        dx = x1 - x0
        dy = y1 - y0
        return math.sqrt(dx*dx + dy*dy)
    
    @property
    def label(self):
        return self._label
        
    @label.setter
    def label(self, value):
        self._label = value
        
        for canvas in self._handles:
        
            if (canvas in self._labelhandles
                and self._labelhandles[canvas] is None):
                if self._label != "":
                    x0, y0, x1, y1 = canvas.coords(self._handles[canvas])
                    x, y = ((x0 + x1) / 2, (y0 + y1) / 2)
                    self._labelhandles[canvas] = canvas.create_text(x, y,
                                                              text=self._label,
                                                       **self.style.common.text)
                    self._labelbghandles[canvas] = self.canvas.create_rectangle(
                                    *canvas.bbox(self._labelhandles[canvas]),
                                    **self.style.common.textbg)
                    canvas.tag_raise(self._labelhandles[canvas])
            else:
                if self._label == "":
                    canvas.delete(self._labelhandles[canvas])
                    canvas.delete(self._labelbghandles[canvas])
                    del self._labelhandles[canvas]
                    del self._labelbghandles[canvas]
                else:
                    self.canvas.itemconfig(self._labelhandles[canvas],
                                           text=self._label)
                    self.canvas.coords(self._labelbghandles[canvas],
                                       *canvas.bbox(self._labelhandles[canvas]))
    
    def move(self, canvas):
        """
        Move this edge on canvas to fit its ends.
        """
        if canvas not in self._handles:
            raise UnknownCanvasError("Unknown canvas ({}), "
                                     "cannot move edge.".format(canvas))
        
        canvas.coords(self._handles[canvas],
                      self._edge_coords_from_ends(canvas,
                                                  self.origin._handles[canvas],
                                                  self.end._handles[canvas]))
        if (canvas in self._labelhandles
            and self._labelhandles[canvas] is not None):
            x0, y0, x1, y1 = canvas.coords(self._handles[canvas])
            x, y = ((x0 + x1) / 2, (y0 + y1) / 2)
            canvas.coords(self._labelhandles[canvas], x, y)
            canvas.coords(self._labelbghandles[canvas],
                               *canvas.bbox(self._labelhandles[canvas]))
    
    def refresh(self, canvas):
        """
        Refresh the appearance of this edge on canvas.
        """
        if canvas not in self._handles:
            raise UnknownCanvasError("Unknown canvas ({}), "
                                     "cannot refresh edge.".format(canvas))
        
        canvas.itemconfig(self._handles[canvas], **self.style.common.shape)
        if (canvas in self._labelhandles and
            self._labelhandles[canvas] is not None):
            canvas.itemconfig(self._labelhandles[canvas],
                              **self.style.common.text)
            if (canvas in self._labelbghandles and
                self._labelbghandles[canvas] is not None):
                canvas.itemconfig(self._labelbghandles[canvas],
                                  **self.style.common.textbg)