import math
import tkinter as tk

from .exception import UnknownCanvasError

# Radius of circles representing vertices
VERTEXRADIUS=10


class Vertex:
    """
    A vertex of a graph. Owns a label and canvas be drawn on several canvas.
    """
    
    def __init__(self, label=""):
        """
        Create a vertex with label.
        """
        self._label = label
        
        # Keep track of handles and handles of labels in each canvas
        self._handles = {}
        self._labelhandles = {}
    
    def handles(self, canvas):
        """Return the handles in canvas."""
        handles = []
        if canvas in self._handles:
            handles.append(self._handles[canvas])
        if canvas in self._labelhandles:
            handles.append(self._labelhandles[canvas])
        return tuple(handles)
    
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
        
        # Add label on canvas and store handle
        if self.label != "":
            self._labelhandles[canvas] = canvas.create_text(x, y,
                                                            text=self.label,
                                                            justify=tk.CENTER)
            x0l, y0l, x1l, y1l = canvas.bbox(self._labelhandles[canvas])
            
            # Draw on canvas and store handle
            x0e = x - (x1l-x0l)/2 * math.sqrt(2)
            y0e = y - (y1l-y0l)/2 * math.sqrt(2)
            x1e = x + (x1l-x0l)/2 * math.sqrt(2)
            y1e = y + (y1l-y0l)/2 * math.sqrt(2)
            self._handles[canvas] = canvas.create_oval((x0e, y0e, x1e, y1e),
                                                       fill="white")
            canvas.tag_raise(self._labelhandles[canvas])
        
        else:
            self._labelhandles[canvas] = None
            self._handles[canvas] = canvas.create_oval((x - VERTEXRADIUS,
                                                        y - VERTEXRADIUS,
                                                        x + VERTEXRADIUS,
                                                        y + VERTEXRADIUS),
                                                       fill="white")
    
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
        canvas.itemconfig(self._handles[canvas], fill="yellow")
    
    def deselect(self, canvas):
        if canvas not in self._handles:
            raise UnknownCanvasError("Unknown canvas ({}), "
                                     "cannot deselect vertex.".format(canvas))
        canvas.itemconfig(self._handles[canvas], fill="white")
    
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
        
        for canvas in self._handles:
            x, y = self.center(canvas)
        
            if self._label != "":
                if self._labelhandles[canvas] == None:
                    self._labelhandles[canvas] = canvas.create_text(x, y,
                                                               text=self._label,
                                                              justify=tk.CENTER)
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



class Edge:
    """
    An edge of a graph. Owns a label and two ends
    and can be drawn on different canvas.
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
    
    def draw(self, canvas):
        # Draw on canvas and store handle
        coords = self._edge_coords_from_ends(canvas, 
                                             self.origin._handles[canvas],
                                             self.end._handles[canvas])
        handle = canvas.create_line(*coords, arrow="last")
        self._handles[canvas] = handle
        
        # Add label on canvas and store handle
        if self.label != "":
            x, y = self._center_from_coords(*canvas.coords(handle))
            labelhandle = canvas.create_text(x, y, text=label,
                                             justify=tk.CENTER)
            self._labelhandles[canvas] = labelhandle
            self._labelbghandle[canvas] = canvas.create_rectangle(
                                    *canvas.bbox(labelhandle),
                                    fill="white", outline="white")
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
                                                              justify=tk.CENTER)
                    self._labelbghandles[canvas] = self.canvas.create_rectangle(
                                    *canvas.bbox(self._labelhandles[canvas]),
                                    fill="white", outline="white")
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