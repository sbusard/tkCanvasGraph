"""
Canvas graphs.

This module defines canvas graphs. Such a canvas is a TK canvas on which we
can display graphs.
"""

import tkinter as tk
import random

from .util import ObservableSet, AttrDict, CanvasToolTip
from .mouse import (SelectingMouse, SelectionModifyingMouse,
                    MovingMouse)
from .layout import ForceBasedLayout, OneStepForceBasedLayout, DotLayout
from .shape import Rectangle, Oval


__all__ = ["CanvasGraph", "InteractiveCanvasGraph", "CanvasFrame"]


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

    def draw(self, x, y):
        """
        Draw this element on its canvas, centered at position x, y.

        :param x: the horizontal position;
        :param y: the vertical position.
        """
        self.delete()
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
            for handle in self.handles():
                CanvasToolTip(canvas, handle, follow_mouse=1,
                              text=self.tooltip)

        self.refresh()

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
        curx, cury = self.center()
        dx = x - curx
        dy = y - cury
        self.move(dx, dy)
        return dx, dy

    def delete(self):
        """
        Remove this element from canvas, if it is already drawn.
        """
        self._canvas.delete_element(self)
        self._handle = None
        self._labelhandle = None

    def center(self):
        """
        Return the center point of this element.

        :return: the (x, y) coordinates of the center point.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        x0, y0, x1, y1 = self._canvas.coords(self._handle)
        return (x0 + x1) / 2, (y0 + y1) / 2

    def bbox(self):
        """
        Return the bounding box of this element.
        :return: the (x0, y0, x1, y1) coordinates of the bounding box.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        return self._canvas.bbox(self._handle)

    def dimensions(self):
        """
        Return this element width and height.

        :return: the (width, height) pair.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        x0, y0, x1, y1 = self.bbox()
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

        xc, yc = self.center()

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
                # Set bbox as xc, yc, xc, yc
                label_bbox = (xc, yc, xc, yc)
            else:
                # draw labelhandle if needed
                if self._labelhandle is None:
                    self._labelhandle = canvas.create_text(xc,
                                                           yc,
                                                           text=new_label)
                    canvas.elements[self._labelhandle] = self
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
            canvas.elements[self._handle] = self
            if style["label"]:
                canvas.tag_raise(self._labelhandle)

        # Update style
        canvas.itemconfig(self._handle, style["shape_style"])
        if self._labelhandle is not None:
            canvas.itemconfig(self._labelhandle, style["label_style"])

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
        for handle in self.handles():
            self._canvas.tag_bind(handle, event, callback, add)

    def unbind(self, event):
        """
        Remove all the bindings for event of the element on canvas.

        :param event: the event specifier to remove the binding on.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
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

    def handles(self):
        """
        Return the handles of this edge.

        :return: the set of handles taking part in this edge.
        """
        if self._arrowhandle is not None:
            return super(Edge, self).handles() + (self._arrowhandle,)
        else:
            return super(Edge, self).handles()

    def delete(self):
        """
        Remove this edge from canvas.

        This element must be already drawn on its canvas.
        """
        super(Edge, self).delete()
        self._arrowhandle = None

    def _refresh_arrows(self):
        """
        Redraw the arrows of this edge.

        This element must be already drawn on its canvas.
        """
        assert self._handle is not None, "The element is not drawn yet"
        canvas = self._canvas

        # Draw line: from origin to label and from label to end
        xo, yo = self.origin.style["shape"].intersection(self.origin.bbox(),
                                                         self.center())
        xol, yol = self.style["shape"].intersection(self.bbox(),
                                                    self.origin.center())
        xel, yel = self.style["shape"].intersection(self.bbox(),
                                                    self.end.center())
        xe, ye = self.end.style["shape"].intersection(self.end.bbox(),
                                                      self.center())

        if self._arrowhandle is not None:
            canvas.coords(self._arrowhandle, *(xo, yo, xol, yol,
                                               xel, yel, xe, ye))
            canvas.itemconfig(self._arrowhandle, self.style.arrow_style)
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


class CanvasGraph(tk.Canvas):
    """
    A canvas graph is a TK canvas on which you can display graphs.
    """
    def __init__(self, parent, **config):
        """
        Create a new canvas graph with parent and configured with config.

        :param parent: the TK parent of this canvas.
        :param config: the config of this canvas (see TK documentation).
        """
        super(CanvasGraph, self).__init__(parent, **config)

        # Elements indexed by their handles
        self.elements = {}

        self.vertices = set()
        self.edges = set()

        # Transformers
        self.transformers = []

        # Mouses indexed by their binding button
        self.mouses = {}

        self.config(scrollregion=self.bbox("all"))
        self.focus_set()

        # Layout variable to stop and start interactive layouts
        self.layouting = tk.BooleanVar()
        self.layouting.set(False)
        self.layout_interval = 25

    def _get_positions(self, layout, vertices, edges):
        """
        Return the positions resulting of applying layout on vertices and
        edges.

        :param layout: the layout to apply;
        :param vertices: the vertices and their center position;
        :param edges: the edges couples (origin, end);
        :return: the new positions of vertices.
        """
        return layout.apply(self, vertices, edges)

    def _apply_positions(self, positions):
        """
        Move all elements of positions at their new position.

        :param positions: a dictionary of element -> x,y positions.
        """
        for element in positions.keys() & self.vertices:
            element.move_to(*positions[element])
        for element in positions.keys() & self.edges:
            element.move_to(*positions[element])
        self._update_scrollregion()

    def apply_layout(self, layout):
        """
        Apply the given layout on this canvas.

        :param layout: the layout to apply, must comply with the apply method
                       (see layout.Layout).
        """
        self.layouting.set(False)
        vertices = {element: element.center()
                    for element in self.elements.values()}
        edges = set()
        for edge in self.edges:
            edges.add((edge.origin, edge))
            edges.add((edge, edge.end))
        np = self._get_positions(layout, vertices, edges)
        self._apply_positions(np)

    def apply_interactive_layout(self, layout):
        """
        Apply the given interactive layout.

        :param layout: the layout to apply now and then. The interval the
                       layout is applied is self.layout_interval.

        The self.layouting variable is set to True to tell that interactive
        layouting is enabled. Then every layout_interval milliseconds, the
        given layout is applied on the current graph.
        The process is stopped as soon as layouting is set to False.
        """
        def iter_layout():
            if not self.layouting.get():
                return

            vertices = {element: element.center()
                        for element in self.elements.values()}
            edges = set()
            for edge in self.edges:
                edges.add((edge.origin, edge))
                edges.add((edge, edge.end))

            np = self._get_positions(layout, vertices, edges)

            self._apply_positions(np)

            if self.layouting.get():
                self.after(self.layout_interval, iter_layout)

        if not self.layouting.get():
            self.layouting.set(True)
        self.after(self.layout_interval, iter_layout)

    def current_element(self):
        """
        Return the element under the mouse pointer, if any; None otherwise.

        :return: the element under the mouse pointer, or None if no element is
                 under the pointer.
        """
        current = self.find_withtag("current")
        if len(current) > 0:
            return self.element_by_handle(current[0])
        else:
            return None

    def element_by_handle(self, handle):
        """
        Return the element attached to the given handle, if any; None
        otherwise.

        :param handle: the handle to get.
        :return: the element corresponding to the given handle, if any,
                 otherwise None.
        """
        if handle in self.elements:
            return self.elements[handle]
        else:
            return None

    def _add_element(self, element, position=None):
        """
        Add the given element on this canvas at position, if specified.
        If position is None, set it at random in the frame defined by the
        existing elements, or in the (0,0), (100, 100) rectangle if there are
        no elements.
        
        :param element: the element to add and draw;
        :param position: if not None, an x,y tuple.
        """
        # Compute position if not specified;
        # The vertex is added at random in the scroll region, if it is
        # large enough.
        if position is None:
            if self.bbox("all") is None:
                position = 0, 0
            else:
                x0, y0, x1, y1 = self.bbox("all")
                dx = x1 - x0 if x1 - x0 > 100 else 100
                dy = y1 - y0 if y1 - y0 > 100 else 100
                x, y = random.randint(0, dx), random.randint(0, dy)
                position = x0 + x, y0 + y

        element.draw(*position)
        for handle in element.handles():
            self.elements[handle] = element
        self._update_scrollregion()
        self.refresh()

    def add_vertex(self, vertex, position=None):
        """
        Add the given vertex on this canvas at position, if specified.
        If position is None, set it at random in the frame defined by the
        existing elements, or in the (0,0), (100, 100) rectangle if there are
        no elements.
        
        :param vertex: the vertex to add and draw;
        :param position: if not None, an x,y tuple.
        """
        self._add_element(vertex, position)
        self.vertices.add(vertex)

    def add_edge(self, edge, position=None):
        """
        Add the given edge on this canvas at position, if specified.
        If position is None, set the label at the middle position between
        its origin and end vertices.
        
        :param edge: the edge to add and draw;
        :param position: if not None, an x,y tuple.
        """
        if position is None:
            xo, yo = edge.origin.center()
            xe, ye = edge.end.center()
            position = ((xo + xe) / 2, (yo + ye) / 2)
        self._add_element(edge, position)
        self.edges.add(edge)

    def delete_element(self, element):
        """
        Delete the given element.

        :param element: the element to delete.
        """
        for handle in element.handles():
            self._delete_handle(handle)

        # Discard from other sets
        self.vertices.discard(element)
        self.edges.discard(element)

        self.refresh()

    def _delete_handle(self, handle):
        """
        Delete the given handle.

        :param handle: the handle to delete.
        """
        self.delete(handle)
        if handle in self.elements:
            del self.elements[handle]

    def move_elements(self, elements, dx, dy):
        """
        Move the given elements of (dx,dy) offset.

        :param elements: the iterable of elements to move.
        :param dx: the horizontal offset.
        :param dy: the vertical offset.
        """
        for e in elements:
            e.move(dx, dy)
        for edge in self.edges:
            if edge.origin in elements or edge.end in elements:
                edge.refresh()
        self.refresh()

        # Update scrollregion
        self._update_scrollregion()

    def _update_scrollregion(self):
        """
        Update the scrollregion of this canvas to match the drawn elements.
        """
        # Padding for scroll region
        PADDING = 10
        bbox = self.bbox("all")
        if bbox is not None:
            minx, miny, maxx, maxy = bbox
            self.config(scrollregion=(minx - PADDING, miny - PADDING,
                                      maxx + PADDING, maxy + PADDING))

    def refresh(self):
        """
        Refresh all elements of this canvas.
        """
        for vertex in self.vertices:
            vertex.refresh()
        for edge in self.edges:
            edge.refresh()

    def register_mouse(self, mouse, button, modifier):
        """
        Register a new mouse for button pressed with modifier.

        :param mouse: the mouse to register. Must comply with the mouse.Mouse
                      methods.
        :param button: the button to react to.
        :param modifier: the modifier to activate the mouse for.
        """

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
        """
        Unregister a registered mouse for button pressed with modifier.

        :param mouse: the mouse to unregister.
        :param button: the button for which the mouse was registered.
        :param modifier: the modifier for which the mouse was registered.
        """

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
        """
        React to a mouse button pressed.

        :param button: the pressed button.
        :param modifier: the used modifier.
        :param event: the pressing event.
        """
        if (button, modifier) in self.mouses:
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.pressed(self, event):
                    break

    def _moved(self, button, modifier, event):
        """
        React to a moved mouse.

        :param button: the button pressed when moving.
        :param modifier: the modifier used when moving.
        :param event: the moving event.
        """
        if (button, modifier) in self.mouses:
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.moved(self, event):
                    break

    def _released(self, button, modifier, event):
        """
        React the a mouse button released.

        :param button: the released button.
        :param modifier: the used modifier.
        :param event: the releasing event.
        """
        if (button, modifier) in self.mouses:
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.released(self, event):
                    break

    def register_transformer(self, transformer):
        """
        Register the given transformer.
        The transformer must be a function taking an element (vertex or edge)
        and a style as arguments and updating the style.

        :param transformer: the transformer to register.

        The transformer has access to and can change:
        * the label of the element: style["label"].
          The transformer should not delete the "label" key and its value
          should be a string.
        * the shape of the element: style["shape"].
          The transformer should not delete the "shape" key and its value
          should be a valid shape (sub-class of graph.Shape).
        * the style of label: style["label_style"].
          The style of the label should be a dictionary of valid tkinter canvas
          text configurations.
        * the style of the shape: style["shape_style"].
          The style of the shape should be a dictionary of valid tkinter canvas
          shape configurations.
        """
        self.transformers.append(transformer)

    def unregister_transformer(self, transformer):
        """
        Unregister the given transformer.

        :param transformer: the transformer to unregister.
        """
        while transformer in self.transformers:
            self.transformers.remove(transformer)


class InteractiveCanvasGraph(CanvasGraph):
    """
    A selectable canvas graph is a TK canvas on which you can display graphs.
    In addition, such a canvas graph embeds the necessary mouses to select
    and move around elements of the displayed graph.

    Interactive canvas graphs have an observable set of selected elements
    (canvas.selected) that can be observed to be notified when its content
    changes.
    """
    def __init__(self, parent, **config):
        """
        Create a new interactive canvas graph with parent and config.

        :param parent: the TK parent of this canvas.
        :param config: the configuration of the canvas.
        """
        super(InteractiveCanvasGraph, self).__init__(parent, **config)
        # Selected vertices
        self.selected = ObservableSet()

        # Selected vertices transformer and observer
        def selected(element, style):
            if element in self.selected:
                style["shape_style"]["fill"] = "yellow"
            if element not in self.selected:
                style["shape_style"]["fill"] = "white"
        self.register_transformer(selected)

        class SelectionObserver:
            def __init__(self, canvas):
                self.canvas = canvas

            def update(self, _):
                self.canvas.refresh()

        observer = SelectionObserver(self)
        self.selected.register(observer)

        # Mouses for the canvas
        sm = SelectingMouse(selection=self.selected,
                            elements=self.elements.values())
        smm = SelectionModifyingMouse(selection=self.selected,
                                      elements=self.elements.values())
        mm = MovingMouse(self.selected)
        self.register_mouse(sm, "1", "")
        self.register_mouse(smm, "1", "Shift")
        self.register_mouse(mm, "1", "")

    def _get_positions(self, layout, vertices, edges):
        return layout.apply(self, vertices, edges, fixed=self.selected)

    def delete_element(self, element):
        super(InteractiveCanvasGraph, self).delete_element(element)
        self.selected.discard(element)


class CanvasFrame(tk.Frame):
    """
    A frame containing a canvas graph in which one can display a graph.
    The frame also includes buttons to apply layouts (interactive, force-based
    and dot layouts), as well as scrollbars and mouse wheel scroll.
    The canvas graph is selectable, in the sense that it contains necessary
    mechanisms to select and move elements.
    """

    def __init__(self, parent, **config):
        """
        Create a new CanvasFrame.

        :param parent: the TK parent of the new frame.
        :param config: the TK config of the new frame.
        """
        super(CanvasFrame, self).__init__(parent, **config)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        xscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        xscrollbar.grid(row=2, column=0, sticky=tk.E + tk.W)

        yscrollbar = tk.Scrollbar(self)
        yscrollbar.grid(row=1, column=1, sticky=tk.N + tk.S)

        self.canvas = InteractiveCanvasGraph(self,
                                             xscrollcommand=xscrollbar.set,
                                             yscrollcommand=yscrollbar.set)

        self.canvas.grid(row=1, column=0, sticky=tk.N + tk.S + tk.E + tk.W)

        xscrollbar.config(command=self.canvas.xview)
        yscrollbar.config(command=self.canvas.yview)

        # Toolbar
        frame = tk.Frame(self)
        frame.grid(row=0, sticky=tk.W + tk.E)
        self.toolbar = tk.Frame(frame)
        self.toolbar.pack(fill=tk.BOTH, expand=True)

        # Interactive layout
        osfbl = OneStepForceBasedLayout()
        self.canvas.layouting.trace("w",
                                    lambda *args:
                                    self.canvas.layouting.get() and
                                    self.canvas.apply_interactive_layout(osfbl)
                                    )
        ilbutton = tk.Checkbutton(self.toolbar,
                                  text="Interactive layout",
                                  onvalue=True, offvalue=False,
                                  variable=self.canvas.layouting)
        ilbutton.grid(row=0, sticky=tk.W)

        self.canvas.bind("<Control-i>",
                         lambda e: self.canvas.layouting.set(
                             not self.canvas.layouting.get()))

        # Force-based layout
        fbl = ForceBasedLayout()
        fblbutton = tk.Button(self.toolbar,
                              text="Force-based layout",
                              command=lambda: self.canvas.apply_layout(fbl))
        fblbutton.config()
        fblbutton.grid(row=0, column=1, sticky=tk.W)

        self.canvas.bind("<Control-l>",
                         lambda e: self.canvas.apply_layout(fbl))

        # Dot layout
        try:
            import pydot

            dl = DotLayout()
            dlbutton = tk.Button(self.toolbar,
                                 text="Dot layout",
                                 command=lambda: self.canvas.apply_layout(dl))
            dlbutton.grid(row=0, column=2, sticky=tk.W)

            self.canvas.bind("<Control-d>",
                             lambda e: self.canvas.apply_layout(dl))
        except ImportError:
            pass

        # Scroll with mouse
        def on_mousewheel(event):
            self.canvas.yview_scroll(-1 * event.delta, "units")

        self.canvas.bind("<MouseWheel>", on_mousewheel)


