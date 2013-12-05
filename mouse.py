class Mouse:
    """
    A generic mouse doing nothing.
    """
    
    def __init__(self, canvas, button, modifier):
        """
        Register this mouse to the canvas, for button pressed, moved and
        released events under modifier.
        """
        self.canvas = canvas
        # Register to the canvas
        self.canvas.register_mouse(self, button, modifier)
    
    def pressed(self, event):
        """
        React to mouse button pressed.
        """
        return True # Do nothing, pass the hand
    
    def moved(self, event):
        """
        React to mouse moved.
        """
        return True # Do nothing, pass the hand
        
    def released(self, event):
        """
        React to mouse button released.
        """
        return True # Do nothing, pass the hand


class SelectingMouse(Mouse):
    """
    Add selecting behaviour to a canvas.
    
    The added behaviours are:
        * select individual elements by clicking on them;
        * select several elements by drawing a box around them.
    """
    
    def __init__(self, canvas, selection=None, elements=None, button="1",
                 modifier=""):
        """
        canvas -- the canvas on which operate;
        selection -- the set in which keeping track of selected elements.
                     if None, use an internal set;
        elements -- the set of selectable elements.
                    if None, any element is selectable;
        button -- the button on which react;
        modifier -- the modifier for mouse events.
        """
        super().__init__(canvas, button, modifier)
        
        self.selected = set() if selection is None else selection
        self.elements = elements
        
        self.selecting = None
        self.selection = None
    
    def pressed(self, event):
        element = self.canvas.current_element()
        
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
            self.selecting = (self.canvas.canvasx(event.x),
                              self.canvas.canvasy(event.y))
            self.selection = self.canvas.create_rectangle(self.selecting +
                                                          self.selecting,
                                                          outline="gray")
            return False
        
    
    def moved(self, event):
        if self.selecting is None:
            return True
        else:
            self.canvas.coords(self.selection,
                               self.canvas.canvasx(event.x),
                               self.canvas.canvasy(event.y),
                               *self.selecting)
            return False
    
    def released(self, event):
        if self.selecting is None:
            return True
        else:
            self.selected.clear()
            for e in self.canvas.find_enclosed(
                                           *self.canvas.coords(self.selection)):
                if self.elements is None or e in self.elements:
                    self.selected.add(e)
            self.selecting = None
            self.canvas.delete(self.selection)
            self.selection = None
            return False


class SelectionModifyingMouse(Mouse):
    """
    Add selection modifications to a canvas.
    
    The added behaviour is adding/removing elements from selection when they
    are clicked.
    """
    
    def __init__(self, canvas, selection=None, elements=None,
                 button="1",modifier=""):
        """
        canvas -- the canvas on which operate;
        selection -- the set in which keeping track of selected elements.
                     if None, use an internal set;
        elements -- the set of selectable elements.
                    if None, any element is selectable;
        button -- the button on which react;
        modifier -- the modifier for mouse events.
        """
        super().__init__(canvas, button, modifier)
        
        self.selected = set() if selection is None else selection
        self.elements = elements
    
    def pressed(self, event):
        element = self.canvas.current_element()
        
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
    
    def __init__(self, canvas, selected, button="1", modifier=""):
        """
        canvas -- the canvas on which operate;
        selected -- the set of selected element;
        button -- the button on which react;
        modifier -- the modifier for mouse events.
        """
        super().__init__(canvas, button, modifier)
        self.selected = selected
        self.moving = False
        self.position = None
    
    def pressed(self, event):
        element = self.canvas.current_element()
        
        # if element is in selection, start moving
        if element is not None and element in self.selected:
            self.moving = True
            self.position = (self.canvas.canvasx(event.x),
                             self.canvas.canvasy(event.y))
            return False
        else:
            return True
    
    def moved(self, event):
        if self.moving:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            dx, dy = x - self.position[0], y - self.position[1]
            self.canvas.move_vertices(self.selected, dx, dy)
            self.position = x,y
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
        * creating a vertice when clicking on empty space;
        * creating an edge between two different vertices when dragging
          from one vertice to another.
    """
    
    def __init__(self, canvas, vertices, button="1", modifier=""):
        """
        canvas -- the canvas on which operate;
        vertices -- the set of vertices of the canvas;
        button -- the button on which react;
        modifier -- the modifier for mouse events.
        """
        super().__init__(canvas, button, modifier)
        self.vertices = vertices
        self.starting = None
    
    def pressed(self, event):
        element = self.canvas.current_element()
        
        # if element exists and is a vertice,
        #   start to build an edge
        # otherwise,
        #   build a vertice at position
        
        if (element is not None and element in self.vertices):
            self.starting = element
            return False
        else:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            self.canvas.new_vertice(x, y)
            return False
        
    
    def moved(self, event):
        if self.starting is not None:
            return False
        else:
            return True
    
    def released(self, event):
        if self.starting is not None:
            element = self.canvas.current_element()
            
            # if element exists, is a vertice and is not starting,
            #   add an edge 
            # otherwise,
            #   do nothing
            
            if (element is not None and element in self.vertices and
                element != self.starting):
                self.canvas.new_edge(self.starting, element)
                self.starting = None
                return False
            else:
                return True    