"""
Mouses.

Mouses handle pressing and releasing a button, with access to the canvas and
its elements, as well as moving the pointer on the canvas.

In addition to the abstract mouse that does nothing, this module gives access
to several pre-defined mouses.
"""

from .graph import Vertex, Edge

__all__ = ["Mouse", "SelectingMouse", "SelectionModifyingMouse", "MovingMouse",
           "CreatingMouse", "MouseEvent"]


class MouseEvent(object):
    """
    The event captured by a mouse.

    Such an event has:

    * the canvas the event occurred on;
    * the current mouse pointer position on the canvas;
    * the current mouse pointer position relative to the upper left corner of
      the screen;
    * the button number;
    * the type of the event;
    * the element of the graph the mouse pointer is on, if any (None otherwise)

    """

    def __init__(self, canvas, element, position, absolute, number, type_):
        """
        Create a new mouse event.

        :param canvas: the canvas the event occurred on;
        :param element: the element under the mouse pointer on canvas, if any;
                        None otherwise;
        :param position: the current (x, y) position of the mouse pointer;
        :param absolute: the current (x, y) position of the mouse pointer,
                         relative to the upper left corner of the screen;
        :param number: the button number;
        :param type_: the type of the event.
        """
        self.canvas = canvas
        self.element = element
        self.position = position
        self.absolute = absolute
        self.number = number
        self.type_ = type_


class Mouse(object):
    """
    A generic mouse doing nothing.

    Mouses can be registered to canvas. Three events are handled by mouses:

    * pressed button
    * moved pointer
    * released button

    Whenever such an event occurs, the canvas delegates it to the registered
    mouses.
    """

    def pressed(self, event):
        """
        React to mouse button pressed.

        :param event: the mouse event of the pressed button.
        :return: a True value if the event must be passed to the next mouse,
                 a False value otherwise.
        """
        return True  # Do nothing, pass the hand

    def moved(self, event):
        """
        React to mouse moved.

        :param event: the mouse event of the moved mouse.
        :return: a True value if the event must be passed to the next mouse,
                 a False value otherwise.
        """
        return True  # Do nothing, pass the hand

    def released(self, event):
        """
        React to mouse button released.

        :param event: the mouse event of the released button.
        :return: a True value if the event must be passed to the next mouse,
                 a False value otherwise.
        """
        return True  # Do nothing, pass the hand


class SelectingMouse(Mouse):
    """
    Add selecting behaviour to a canvas.
    
    The added behaviours are:
        * select individual elements by clicking on them;
        * select several elements by drawing a box around them.
    """

    def __init__(self, selection=None, elements=None):
        """
        Create a new selecting mouse.

        :param selection: the set in which keeping track of selected elements.
                          if None, use an internal set;
        :param elements: the set of selectable elements.
                         if None, any element is selectable.
        """
        self.selected = set() if selection is None else selection
        self.elements = elements

        self.selecting = None
        self.selection = None

        self.mouse_moved = False

    def pressed(self, event):
        canvas = event.canvas
        element = event.element
        self.mouse_moved = False

        # if element exists,
        #   if element is in elements and not selected,
        #       selection becomes the element
        #   if element is in elements but selected or not in elements,
        #       do nothing, pass the hand
        # if element does not exist,
        #   start selecting box

        if element is not None:
            if ((self.elements is None or element in self.elements) and
                    element not in self.selected):
                self.selected.clear()
                self.selected.add(element)
            return True
        else:
            self.selected.clear()
            self.selecting = event.position
            self.selection = canvas.create_rectangle(self.selecting +
                                                     self.selecting,
                                                     outline="gray")
            return False

    def moved(self, event):
        canvas = event.canvas
        self.mouse_moved = True
        if self.selecting is None:
            return True
        else:
            coords = event.position + self.selecting
            canvas.coords(self.selection, *coords)
            return False

    def released(self, event):
        canvas = event.canvas
        if self.mouse_moved:
            self.mouse_moved = False
            if self.selecting is None:
                return True
            else:
                self.selected.clear()
                to_add = set()
                for handle in canvas.find_enclosed(
                                *canvas.coords(self.selection)):
                    element = canvas.element_by_handle(handle)
                    if self.elements is None or element in self.elements:
                        to_add.add(element)
                self.selected.update(to_add)
                self.selecting = None
                canvas.delete(self.selection)
                self.selection = None
                return False
        else:
            element = event.element
            if self.elements is None or element in self.elements:
                self.selected.clear()
                self.selected.add(element)
            self.mouse_moved = False
            if self.selecting is not None:
                self.selecting = None
                canvas.delete(self.selection)
                self.selection = None
            return False


class SelectionModifyingMouse(Mouse):
    """
    Add selection modifications to a canvas.
    
    The added behaviour is adding/removing elements from selection when they
    are clicked.
    """

    def __init__(self, selection=None, elements=None):
        """
        Create a new selection modifying mouse.

        :param selection: the set in which keeping track of selected elements.
                          if None, use an internal set;
        :param elements: the set of selectable elements.
                         if None, any element is selectable.
        """
        self.selected = set() if selection is None else selection
        self.elements = elements

    def pressed(self, event):
        element = event.element

        if element in self.selected:
            self.selected.remove(element)
            return False

        elif ((self.elements is None or element in self.elements) and
              element not in self.selected):
            self.selected.add(element)
            return False

        return True


class MovingMouse(Mouse):
    """
    Add moving behaviour to a canvas.
    
    The added behaviour is moving the selection when dragged.
    """

    def __init__(self, selected):
        """
        Create a new moving mouse.

        :param selected: the set of selected element.
        """
        self.selected = selected
        self.moving = False
        self.position = None

    def pressed(self, event):
        canvas = event.canvas
        element = event.element

        # if element is in selection, start moving
        if element is not None and element in self.selected:
            self.moving = True
            self.position = event.position
            return False
        else:
            return True

    def moved(self, event):
        canvas = event.canvas
        if self.moving:
            x, y = event.position
            dx, dy = x - self.position[0], y - self.position[1]
            canvas.move_elements(self.selected, dx, dy)
            self.position = x, y
            return False
        else:
            return True

    def released(self, event):
        if self.moving:
            self.moving = False
            self.position = None
            return False
        else:
            return True


class CreatingMouse(Mouse):
    """
    Add creation behaviours to a canvas.
    
    The added behaviours are:
        * creating a vertex when clicking on empty space;
        * creating an edge between two different vertices when dragging
          from one vertex to another.
    """

    def __init__(self, vertices):
        """
        Create a new creating mouse.

        :param vertices: the set of vertices of the canvas.
        """
        self.vertices = vertices
        self.starting = None

    def pressed(self,  event):
        canvas = event.canvas
        element = event.element

        # if element exists and is a vertex,
        #   start to build an edge
        # otherwise,
        #   build a vertex at position

        if element is not None and element in self.vertices:
            self.starting = element
            return False
        else:
            v = Vertex(canvas)
            canvas.add_vertex(v, position=event.position)
            return False

    def moved(self, event):
        if self.starting is not None:
            return False
        else:
            return True

    def released(self, event):
        if self.starting is not None:
            canvas = event.canvas
            element = event.element

            # if element exists, is a vertex and is not starting,
            #   add an edge 
            # otherwise,
            #   do nothing

            if element is not None and element in self.vertices:
                edge = Edge(canvas, self.starting, element)
                canvas.add_edge(edge)
                self.starting = None
                return False
            else:
                self.starting = None
                return True
        return True
