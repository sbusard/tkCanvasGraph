canvasGraph is a Python library that implements a tkinter canvas on which users
can display and manipulate graphs.

A small example of its usage:

.. code:: python

    import tkinter
    from canvasGraph import CanvasFrame, Vertex, Edge
    root = tkinter.Tk()
    frame = CanvasFrame(root)
    frame.pack(fill="both", expand=True)
    v1 = Vertex(frame.canvas, label="vertex1")
    frame.canvas.add_vertex(v1)
    v2 = Vertex(frame.canvas, label="vertex2")
    frame.canvas.add_vertex(v2)
    edge = Edge(frame.canvas, v1, v2, label="edge")
    frame.canvas.add_edge(edge)
    root.mainloop()

It creates a new tkinter window, fills it with a `CanvasFrame` (a tkinter
frame containing a canvasGraph `frame.canvas`, but also buttons to apply
layouts, and scrollbars), then add two vertices and one edge.


Another example is the `canvasGraph/__main__.py` file:

.. code::

    python -m canvasGraph

It opens a similar window with additional functionalities:

* new vertices can be created with CTRL + left click,
* new edges by maintaining CTRL and dragging and dropping the mouse from
  one vertex to another,
* elements can be deleted with CTRL + right click,
* labels can be modified by right-clicking on any element,
* "j" key will create a new vertex in a random position,
* "k" key will create a new edge between two vertices without an edge,
* "o" key will apply one step of the force based layout.

Look at the code to get more insight on how to use the library.