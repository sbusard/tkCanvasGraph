"""
Canvas graphs.

This module defines canvas graphs. Such a canvas is a TK canvas on which we
can display graphs.
"""

import tkinter as tk
import random

from .util import ObservableSet
from .mouse import (SelectingMouse, SelectionModifyingMouse,
                    MovingMouse, MouseEvent)
from .layout import ForceBasedLayout, OneStepForceBasedLayout, DotLayout
from .graph import Vertex, Edge


__all__ = ["CanvasGraph", "InteractiveCanvasGraph", "CanvasFrame"]


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
        self.handles = {}

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

    def apply_layout(self, layout):
        """
        Apply the given layout on this canvas.

        :param layout: the layout to apply, must comply with the apply method
                       (see layout.Layout).
        """
        self.layouting.set(False)
        layout.apply(self, self.vertices, self.edges)
        self.refresh()

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

            layout.apply(self, self.vertices, self.edges)
            self.refresh()

            if self.layouting.get():
                self.after(self.layout_interval, iter_layout)

        if not self.layouting.get():
            self.layouting.set(True)
        self.after(self.layout_interval, iter_layout)

    def _current_element(self):
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
        if handle in self.handles:
            return self.handles[handle]
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
        for handle in element.handles:
            self.handles[handle] = element
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
            xo, yo = edge.origin.center
            xe, ye = edge.end.center
            position = ((xo + xe) / 2, (yo + ye) / 2)
        self._add_element(edge, position)
        self.edges.add(edge)

    def delete_element(self, element):
        """
        Delete the given element.

        :param element: the element to delete.
        """

        # Remove edges if element is vertex
        if isinstance(element, Vertex):
            to_delete = {edge for edge in self.edges
                         if edge.origin == element or edge.end == element}
            for edge in to_delete:
                self.delete_element(edge)

        for handle in element.handles:
            self._delete_handle(handle)
        element.delete_handles()

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
        if handle in self.handles:
            del self.handles[handle]

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
        self._update_scrollregion()

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
            event = MouseEvent(self,
                               self._current_element(),
                               (self.canvasx(event.x), self.canvasy(event.y)),
                               (event.x_root, event.y_root),
                               event.num,
                               event.type)
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.pressed(event):
                    break

    def _moved(self, button, modifier, event):
        """
        React to a moved mouse.

        :param button: the button pressed when moving.
        :param modifier: the modifier used when moving.
        :param event: the moving event.
        """
        if (button, modifier) in self.mouses:
            event = MouseEvent(self,
                               self._current_element(),
                               (self.canvasx(event.x), self.canvasy(event.y)),
                               (event.x_root, event.y_root),
                               event.num,
                               event.type)
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.moved(event):
                    break

    def _released(self, button, modifier, event):
        """
        React the a mouse button released.

        :param button: the released button.
        :param modifier: the used modifier.
        :param event: the releasing event.
        """
        if (button, modifier) in self.mouses:
            event = MouseEvent(self,
                               self._current_element(),
                               (self.canvasx(event.x), self.canvasy(event.y)),
                               (event.x_root, event.y_root),
                               event.num,
                               event.type)
            for mouse in self.mouses[(button, modifier)]:
                if not mouse.released(event):
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
                            elements=self.handles.values())
        smm = SelectionModifyingMouse(selection=self.selected,
                                      elements=self.handles.values())
        mm = MovingMouse(self.selected)
        self.register_mouse(sm, "1", "")
        self.register_mouse(smm, "1", "Shift")
        self.register_mouse(mm, "1", "")

    def apply_layout(self, layout):
        self.layouting.set(False)
        layout.apply(self, self.vertices, self.edges, fixed=self.selected)
        self.refresh()

    def apply_interactive_layout(self, layout):
        def iter_layout():
            if not self.layouting.get():
                return

            layout.apply(self, self.vertices, self.edges, fixed=self.selected)
            self.refresh()

            if self.layouting.get():
                self.after(self.layout_interval, iter_layout)

        if not self.layouting.get():
            self.layouting.set(True)
        self.after(self.layout_interval, iter_layout)

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