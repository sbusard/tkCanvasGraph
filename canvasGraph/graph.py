"""
Graph elements.

This module defines the elements drawn on canvas graph: vertices and edges.
"""

import tkinter as tk
from .shape import Rectangle, Oval
from .util import ObservableSet, AttrDict, CanvasToolTip

__all__ = ["Vertex", "Edge"]

class GraphElement:
    """
    An element of a graph, composed of a shape and text in it.
    """

    def __init__(self, canvas, shape, label="", tooltip=None):
        """
        Create a graph element with shape, label and tooltip on canvas.
        The element must be added to the canvas after initialisation.

        :param canvas: the canvas on which drawing on;
        :param shape: the shape of the graph element;
        :param label: the label inside the shape of the element;
        :param tooltip: if not None, a string that will be used as a tooltip.
        """
        self._canvas = canvas
        self.tooltip = tooltip

        # Keep track of handle and handle of labels in canvas
        self._handle = None
        self._labelhandle = None

        # Common style
        self.style = AttrDict()
        self.style.shape = shape
        self.style.shape_style = AttrDict()
        self.style.shape_style.fill = "white"
        self.style.label = label
        self.style.label_style = AttrDict()
        self.style.label_style.justify = tk.CENTER

    @property
    def handles(self):
        """
        Return the handles of this element.
        """
        handles = []
        if self._handle is not None:
            handles.append(self._handle)
        if self._labelhandle is not None:
            handles.append(self._labelhandle)
        return tuple(handles)

    @property
    def center(self):
        """
        Return the center point of this element.

        :return: the (x, y) coordinates of the center point.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        x0, y0, x1, y1 = self._canvas.coords(self._handle)
        return (x0 + x1) / 2, (y0 + y1) / 2

    @property
    def bbox(self):
        """
        Return the bounding box of this element.
        :return: the (x0, y0, x1, y1) coordinates of the bounding box.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        return self._canvas.bbox(self._handle)

    @property
    def dimensions(self):
        """
        Return this element width and height.

        :return: the (width, height) pair.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        x0, y0, x1, y1 = self.bbox
        return x1 - x0, y1 - y0

    @property
    def label(self):
        """
        The label of this element.
        """
        return self.style["label"]

    @label.setter
    def label(self, value):
        self.style["label"] = value
        self.refresh()

    @property
    def shape(self):
        """
        The shape of this element.
        """
        return self.style["shape"]

    def intersection(self, end, bbox=None):
        """
        Return the point of intersection between this element if it had the
        given bounding box, and the line segment defined by the center of this
        bounding box and end.
        Return None is such an intersection does not exist.

        :param end: the (x, y) coordinates of the ending point;
        :param bbox: if not None, the tkinter-style bounding box to consider.
        :return: the (x, y) coordinates of the intersection point of this
                 element and the line between its center and end, if any,
                 None otherwise.

        If bbox is None, use the actual element bounding box.
        """
        if bbox is None:
            bbox = self.bbox
        return self.shape.intersection(bbox, end)

    def draw(self, x, y):
        """
        Draw this element on its canvas, centered at position x, y.

        :param x: the horizontal position;
        :param y: the vertical position.
        """
        canvas = self._canvas

        # Add label on canvas and store handle
        if self.style["label"] != "":
            self._labelhandle = canvas.create_text(x, y,
                                                   text=self.style["label"])
            bbox = canvas.bbox(self._labelhandle)
        else:
            self._labelhandle = None
            bbox = (x, y, x, y)

        # Draw on canvas and store handle
        self._handle = self.style["shape"].draw(canvas,
                                                bbox,
                                                self.style.shape_style)

        if self._labelhandle is not None:
            canvas.tag_raise(self._labelhandle)

        if self.tooltip is not None:
            for handle in self.handles:
                CanvasToolTip(canvas, handle, follow_mouse=1,
                              text=self.tooltip)

        self.refresh()

    def refresh(self):
        """
        Refresh the appearance of this element on canvas.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        canvas = self._canvas

        old_label = self.style["label"]
        old_shape = self.style["shape"]

        style = self.style
        for transformer in canvas.transformers:
            transformer(self, style)

        xc, yc = self.center

        if old_label:
            label_bbox = canvas.bbox(self._labelhandle)
        else:
            label_bbox = (xc, yc, xc, yc)

        # Update label
        if style["label"] != old_label:
            new_label = style["label"]
            if new_label == "":
                # Remove labelhandle if needed
                if self._labelhandle is not None:
                    canvas._delete_handle(self._labelhandle)
                    self._labelhandle = None
                # Set bbox as xc, yc, xc, yc
                label_bbox = (xc, yc, xc, yc)
            else:
                # draw labelhandle if needed
                if self._labelhandle is None:
                    self._labelhandle = canvas.create_text(xc,
                                                           yc,
                                                           text=new_label)
                    canvas.handles[self._labelhandle] = self
                # or change text
                else:
                    canvas.itemconfig(self._labelhandle, text=new_label)
                # Set bbox as text bbox
                label_bbox = canvas.bbox(self._labelhandle)
            # Update shape for new bbox
            canvas.coords(self._handle,
                          self.style["shape"].dimension(label_bbox))

        # Update shape
        if style["shape"] != old_shape:
            new_shape = style["shape"]
            canvas._delete_handle(self._handle)
            self._handle = self.style["shape"].draw(canvas,
                                                    label_bbox,
                                                    style["shape_style"])
            canvas.handles[self._handle] = self
            if style["label"]:
                canvas.tag_raise(self._labelhandle)

        # Update style
        canvas.itemconfig(self._handle, **style["shape_style"])
        if self._labelhandle is not None:
            canvas.itemconfig(self._labelhandle, **style["label_style"])
        
        # Raise
        canvas.tag_raise(self._handle)
        if style["label"]:
            canvas.tag_raise(self._labelhandle)

    def move(self, dx, dy):
        """
        Move this vertex on canvas.

        :param dx: the difference to move on x axis;
        :param dy: the difference to move on y axis.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        canvas = self._canvas
        canvas.move(self._handle, dx, dy)
        if self._labelhandle is not None:
            canvas.move(self._labelhandle, dx, dy)
        self.refresh()

    def move_to(self, x, y):
        """
        Move this vertex to x,y on canvas
        and return the corresponding dx,dy.

        :param x: the horizontal position;
        :param y: the vertical position.
        :return: the difference of old and new positions.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        curx, cury = self.center
        dx = x - curx
        dy = y - cury
        self.move(dx, dy)
        return dx, dy

    def delete_handles(self):
        """
        Set the handles of this element to None.
        """
        self._handle = None
        self._labelhandle = None

    def bind(self, event, callback, add=None):
        """
        Add an event binding to this element on canvas.

        :param event: the event specifier;
        :param callback: the function to call when the event occurs.
                         a function taking one argument: the event;
        :param add: if not None and set to "+", the new binding is added to any
                    existing binding.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        for handle in self.handles:
            self._canvas.tag_bind(handle, event, callback, add)

    def unbind(self, event):
        """
        Remove all the bindings for event of the element on canvas.

        :param event: the event specifier to remove the binding on.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        for handle in self.handles:
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

    def __init__(self, canvas, label="", tooltip=None):
        """
        Create a vertex with label on canvas with tooltip.

        :param canvas: the canvas on which drawing on;
        :param label: the label inside the shape of the element;
        :param tooltip: if not None, a string that will be used as a tooltip.
        """
        super(Vertex, self).__init__(canvas, shape=Oval(), label=label,
                                     tooltip=tooltip)


class Edge(GraphElement):
    """
    An edge of a graph.

    In addition to the common style of graph elements, edges define the
    style.common.arrow dictionary for the arrow of the edge.
    """

    def __init__(self, canvas, origin, end, label="", tooltip=None):
        """
        Create an edge between origin and end.

        :param canvas: the canvas on which drawing on;
        :param origin: the origin vertex;
        :param end: the end vertex;
        :param label: the label inside the shape of the element;
        :param tooltip: if not None, a string that will be used as a tooltip.
        """
        super(Edge, self).__init__(canvas, shape=Rectangle(), label=label,
                                   tooltip=tooltip)
        self.origin = origin
        self.end = end
        self._arrowhandle = None

        # Common style
        self.style.arrow_style = AttrDict()
        self.style.arrow_style.arrow = "last"

    @property
    def handles(self):
        """
        Return the handles of this edge.

        :return: the set of handles taking part in this edge.
        """
        if self._arrowhandle is not None:
            return super(Edge, self).handles + (self._arrowhandle,)
        else:
            return super(Edge, self).handles

    def delete_handles(self):
        """
        Set the handles of this edge to None.
        """
        super(Edge, self).delete_handles()
        self._arrowhandle = None

    def _refresh_arrows(self):
        """
        Redraw the arrows of this edge.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        canvas = self._canvas

        # Draw line: from origin to label and from label to end
        xo, yo = self.origin.style["shape"].intersection(self.origin.bbox,
                                                         self.center)
        xol, yol = self.style["shape"].intersection(self.bbox,
                                                    self.origin.center)
        xel, yel = self.style["shape"].intersection(self.bbox,
                                                    self.end.center)
        xe, ye = self.end.style["shape"].intersection(self.end.bbox,
                                                      self.center)

        if self._arrowhandle is not None:
            canvas.coords(self._arrowhandle, *(xo, yo, xol, yol,
                                               xel, yel, xe, ye))
            canvas.itemconfig(self._arrowhandle, **self.style.arrow_style)
        else:
            self._arrowhandle = canvas.create_line((xo, yo, xol, yol,
                                                    xel, yel, xe, ye),
                                                   **self.style.arrow_style)
        canvas.tag_raise(self._handle)
        if self._labelhandle is not None:
            canvas.tag_raise(self._labelhandle)

    def draw(self, x, y):
        super(Edge, self).draw(x, y)
        self._refresh_arrows()

    def refresh(self):
        super(Edge, self).refresh()
        self._refresh_arrows()
