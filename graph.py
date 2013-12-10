import math
import tkinter as tk

# Radius of circles representing vertices
VERTEXRADIUS=10


class Vertex:
    """
    A vertex of a graph.
    
    A vertex has:
        * a handle linking the vertex to its drawn shape;
        * a label;
        * a handle linking the vertex to its displayed label.
    """
    
    def __init__(self, canvas, x, y, label=""):
        """
        Create a vertex and draw it on canvas.
        """
        
        self.canvas = canvas
        self._label = label
        
        # Add label on canvas and store handle
        if self.label != "":
            self.labelhandle = self.canvas.create_text(x, y, text=label,
                                                       justify=tk.CENTER)
            x0l, y0l, x1l, y1l = self.canvas.bbox(self.labelhandle)
            
            # Draw on canvas and store handle
            x0e = x - (x1l-x0l)/2 * math.sqrt(2)
            y0e = y - (y1l-y0l)/2 * math.sqrt(2)
            x1e = x + (x1l-x0l)/2 * math.sqrt(2)
            y1e = y + (y1l-y0l)/2 * math.sqrt(2)
            self.handle = self.canvas.create_oval((x0e, y0e, x1e, y1e),
                                                  fill="white")
            self.canvas.tag_raise(self.labelhandle)
        
        else:
            self.labelhandle = None
            self.handle = self.canvas.create_oval((x - VERTEXRADIUS,
                                                   y - VERTEXRADIUS,
                                                   x + VERTEXRADIUS,
                                                   y + VERTEXRADIUS),
                                                  fill="white")
    
    def move(self, dx, dy):
        """
        Move this vertex.
        
        dx -- the difference to move on x axis;
        dy -- the difference to move on y axis.
        """
        self.canvas.move(self.handle, dx, dy)
        if self.labelhandle is not None:
            self.canvas.move(self.labelhandle, dx, dy)
    
    def move_to(self, x, y):
        """Move this vertex to x,y and return the corresponding dx,dy."""
        curx, cury = self.center
        dx = x - curx
        dy = y - cury
        self.move(dx, dy)
        return (dx, dy)
    
    def select(self):
        self.canvas.itemconfig(self.handle, fill="yellow")
    
    def deselect(self):
        self.canvas.itemconfig(self.handle, fill="white")
    
    @property
    def center(self):
        return self._center_from_coords(*self.canvas.coords(self.handle))
    
    def distance_vector_from(self, end):
        """
        Return the distance vector (x,y) from the end vertex.
        """
        xo0, yo0, xo1, yo1 = self.canvas.bbox(self.handle)
        xoc, yoc = (xo1 + xo0) / 2, (yo1 + yo0) / 2
        xe0, ye0, xe1, ye1 = self.canvas.bbox(end.handle)
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

        dbbox = (xoc + dox if xec >= xoc else xoc - dox,
                 yoc + doy if xec > xoc else yoc - doy,
                 xec - dex if xec >= xoc else xec + dex,
                 yec - dey if xec > xoc else yec + dey)
        
        if xoc < xec:
            dx = dbbox[2] - dbbox[0]
        else:
            dx = dbbox[0] - dbbox[2]
        if yoc < yec:
            dy = dbbox[3] - dbbox[1]
        else:
            dy = dbbox[1] - dbbox[3]
        dx = dbbox[2] - dbbox[0]
        dy = dbbox[3] - dbbox[1]
        return dx, dy
    
    def _center_from_coords(self, x0, y0, x1, y1):
        """Return the center of the rectangle given by (x0, y0) and (x1, y1)."""
        return ((x0 + x1) / 2, (y0 + y1) / 2)
    
    @property
    def label(self):
        return self._label
    
    @label.setter
    def label(self, value):
        self._label = value
        
        x, y = self._center_from_coords(*self.canvas.coords(self.handle))
        
        if self._label != "":
            if self.labelhandle == None:
                self.labelhandle = self.canvas.create_text(x, y,
                                                           text=self._label,
                                                           justify=tk.CENTER)
            else:
                self.canvas.itemconfig(self.labelhandle, text=self._label)
            
            x0l, y0l, x1l, y1l = self.canvas.bbox(self.labelhandle)
            
            # Draw on canvas and store handle
            x0e = x - (x1l-x0l)/2 * math.sqrt(2)
            y0e = y - (y1l-y0l)/2 * math.sqrt(2)
            x1e = x + (x1l-x0l)/2 * math.sqrt(2)
            y1e = y + (y1l-y0l)/2 * math.sqrt(2)
            self.canvas.coords(self.handle, (x0e, y0e, x1e, y1e))
        
        else:
            if self.labelhandle != None:
                self.canvas.delete(self.labelhandle)
            self.canvas.coords(self.handle, (x - VERTEXRADIUS,
                                             y - VERTEXRADIUS,
                                             x + VERTEXRADIUS,
                                             y + VERTEXRADIUS))
        
        self.canvas.update(self)



class Edge:
    """
    An edge of a graph.
    
    An edge has:
        * a handle linking the edge to its drawn arrow;
        * two vertices, the origin and the end of this the edge;
        * a label;
        * a handle linking the edge to its displayed label.
    """
    
    def __init__(self, canvas, origin, end, label=""):
        """
        Create an edge between origin and end and draw it on canvas.
        """
        self.canvas = canvas
        self.origin = origin
        self.end = end
        self.label = label
        
        # Draw on canvas and store handle
        coords = self._edge_coords_from_ends(origin.handle, end.handle)
        self.handle = canvas.create_line(*coords, arrow="last")
        
        # Add label on canvas and store handle
        if label != "":
            x, y = self._center_from_coords(*canvas.coords(self.handle))
            self.labelhandle = self.canvas.create_text(x, y, text=label,
                                                       justify=tk.CENTER)
            self.labelbghandle = self.canvas.create_rectangle(
                                    *canvas.bbox(self.labelhandle),
                                    fill="white", outline="white")
            canvas.tag_raise(self.labelhandle)
        else:
            self.labelhandle = self.labelbghandle = None
    
    def _edge_coords_from_ends(self, orig, end):
        xo0, yo0, xo1, yo1 = self.canvas.coords(orig)
        xoc, yoc = (xo1 + xo0) / 2, (yo1 + yo0) / 2
        xe0, ye0, xe1, ye1 = self.canvas.coords(end)
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
    
    def _center_from_coords(self, x0, y0, x1, y1):
        """Return the center of the rectangle given by (x0, y0) and (x1, y1)."""
        return ((x0 + x1) / 2, (y0 + y1) / 2)
    
    @property
    def length(self):
        x0, y0, x1, y1 = self._edge_coords_from_ends(self.origin.handle,
                                                     self.end.handle)
        dx = x1 - x0
        dy = y1 - y0
        return math.sqrt(dx*dx + dy*dy)
    
    @property
    def ends_coordinates(self):
        """
        Return (xo, yo), (xe, ye), the coordinates of the ends of this edge,
        connected to origin and end, respectively.
        """
        x0, y0, x1, y1 = self.canvas.coords(self.handle)
        ox, oy = self.origin.center
        ex, ey = self.end.center
        
        odist = math.sqrt((ox-x0)*(ox-x0) + (oy-y0)*(oy-y0))
        edist = math.sqrt((ex-x0)*(ex-x0) + (ey-y0)*(ey-y0))
        if odist < edist: # The x0, y0 is closer to origin
            opos = x0, y0
            epos = x1, y1
        else:
            opos = x1, y1
            epos = x0, y0
        
        return opos, epos
    
    def move(self):
        """
        Move this edge on canvas to fit its ends.
        """
        self.canvas.coords(self.handle,
                           self._edge_coords_from_ends(self.origin.handle,
                                                       self.end.handle))
        if self.labelhandle is not None:
            x, y = self._center_from_coords(*self.canvas.coords(self.handle))
            self.canvas.coords(self.labelhandle, x, y)
            self.canvas.coords(self.labelbghandle,
                               *self.canvas.bbox(self.labelhandle))
            self.canvas.itemconfig(self.labelhandle, text=str(int(self.length)))