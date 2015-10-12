from .graph import Vertex, Edge

"""
Mouses.

Mouses handle pressing and releasing a button, with access to the canvas and
its elements, as well as moving the pointer on the canvas.

In addition to the abstract mouse that does nothing, this module gives access
to several pre-defined mouses.
"""

__all__ = ["Mouse", "SelectingMouse", "SelectionModifyingMouse", "MovingMouse",
           "CreatingMouse"]

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

    def pressed(self, canvas, event):
        """
        React to mouse button pressed.

        :param canvas: the canvas on which the event occurred;
        :param event: the tkinter event of the pressed button.
        :return: a True value if the event must be passed to the next mouse,
                 a False value otherwise.
        """
        return True  # Do nothing, pass the hand

    def moved(self, canvas, event):
        """
        React to mouse moved.

        :param canvas: the canvas on which the event occurred;
        :param event: the tkinter event of the moved mouse.
        :return: a True value if the event must be passed to the next mouse,
                 a False value otherwise.
        """
        return True  # Do nothing, pass the hand

    def released(self, canvas, event):
        """
        React to mouse button released.

        :param canvas: the canvas on which the event occurred;
        :param event: the tkinter event of the released button.
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

    def pressed(self, canvas, event):
        element = canvas.current_element()
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
            self.selecting = (canvas.canvasx(event.x),
                              canvas.canvasy(event.y))
            self.selection = canvas.create_rectangle(self.selecting +
                                                     self.selecting,
                                                     outline="gray")
            return False

    def moved(self, canvas, event):
        self.mouse_moved = True
        if self.selecting is None:
            return True
        else:
            canvas.coords(self.selection,
                          canvas.canvasx(event.x),
                          canvas.canvasy(event.y),
                          *self.selecting)
            return False

    def released(self, canvas, event):
        if self.mouse_moved:
            self.mouse_moved = False
            if self.selecting is None:
                return True
            else:
                self.selected.clear()
                for e in canvas.find_enclosed(*canvas.coords(self.selection)):
                    e = canvas.element_by_handle(e)
                    if self.elements is None or e in self.elements:
                        self.selected.add(e)
                self.selecting = None
                canvas.delete(self.selection)
                self.selection = None
                return False
        else:
            element = canvas.current_element()
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

    def pressed(self, canvas, event):
        element = canvas.current_element()

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

    def pressed(self, canvas, event):
        element = canvas.current_element()

        # if element is in selection, start moving
        if element is not None and element in self.selected:
            self.moving = True
            self.position = (canvas.canvasx(event.x),
                             canvas.canvasy(event.y))
            return False
        else:
            return True

    def moved(self, canvas, event):
        if self.moving:
            x = canvas.canvasx(event.x)
            y = canvas.canvasy(event.y)
            dx, dy = x - self.position[0], y - self.position[1]
            canvas.move_elements(self.selected, dx, dy)
            self.position = x, y
            return False
        else:
            return True

    def released(self, canvas, event):
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

    def pressed(self, canvas, event):
        element = canvas.current_element()

        # if element exists and is a vertex,
        #   start to build an edge
        # otherwise,
        #   build a vertex at position

        if element is not None and element in self.vertices:
            self.starting = element
            return False
        else:
            x = canvas.canvasx(event.x)
            y = canvas.canvasy(event.y)
            v = Vertex(canvas)
            canvas.add_vertex(v, position=(x, y))
            return False

    def moved(self, canvas, event):
        if self.starting is not None:
            return False
        else:
            return True

    def released(self, canvas, event):
        if self.starting is not None:
            element = canvas.current_element()

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
