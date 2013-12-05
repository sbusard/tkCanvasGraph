import math

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
        self.label = label
        
        # Draw on canvas and store handle
        self.handle = self.canvas.create_oval((x-VERTEXRADIUS, y-VERTEXRADIUS,
                                               x+VERTEXRADIUS, y+VERTEXRADIUS),
                                               fill="white")
        
        # TODO Add label on canvas and store handle
        self.labelhandle = None
    
    def move(self, dx, dy):
        """
        Move this vertex.
        
        dx -- the difference to move on x axis;
        dy -- the difference to move on y axis.
        """
        self.canvas.move(self.handle, dx, dy)
        if self.labelhandle is not None:
            self.canvas.move(self.labelhandle, dx, dy)


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
        
        # TODO Add label on canvas and store handle
    
    def _edge_coords_from_ends(self, orig, end):
        xo, yo = self._center_from_coords(*self.canvas.coords(orig))
        xe, ye = self._center_from_coords(*self.canvas.coords(end))
        if xe - xo != 0:
            alpha = math.atan((ye-yo)/(xe-xo))
        else:
            alpha = (-1 if yo < ye else 1) * math.pi / 2
        dx = VERTEXRADIUS * math.cos(alpha)
        dy = VERTEXRADIUS * math.sin(alpha)
        return (xo + dx if xe >= xo else xo - dx,
                yo + dy if xe > xo else yo - dy,
                xe - dx if xe >= xo else xe + dx,
                ye - dy if xe > xo else ye + dy)
    
    def _center_from_coords(self, x0, y0, x1, y1):
        """Return the center of the rectangle given by (x0, y0) and (x1, y1)."""
        return ((x0 + x1) / 2, (y0 + y1) / 2)
    
    def move(self, dx, dy):
        """
        Move this edge on canvas.
        
        dx -- the difference to move on x axis;
        dy -- the difference to move on y axis.
        """
        self.canvas.coords(self.handle,
                           self._edge_coords_from_ends(self.origin.handle,
                                                       self.end.handle))