import math

"""
Layouts.

This module provides layouts to organize a graph on a canvas. In addition to
the abstract layout class, this module provides several pre-defined layouts.
"""

__all__ = ["Layout", "OneStepForceBasedLayout", "ForceBasedLayout",
           "DotLayout"]


class Layout:
    """
    A graph layout.
    """

    def apply(self, canvas, positions, edges, fixed=None):
        """
        Apply this layout on canvas, with positions of elements.
        
        :param canvas: the canvas on which operate;
        :param positions: a dictionary of elements -> x,y positions;
        :param edges: a list of couples representing the edges;
        :param fixed: a set of elements that must remain at given position.
        :return: a dictionary of new positions for elements of positions.
        """
        raise NotImplementedError("Should be implemented by subclasses.")


class OneStepForceBasedLayout(Layout):
    """
    A force-based layout. Applying only cause one step of the computation
    of the layout. Useful for interactive layout, each application
    giving the new positions to draw.
    """

    def __init__(self):
        self.minSpringLength = 30
        self.springStiffness = 0.3
        self.electricalRepulsion = 250
        self.maxForce = 10

    def _distance_vector_from(self, positions, vertex, other):
        """
        Return the distance vector from vertex to the other vertex.
        If vertex is at greater position than other,
        the distance vector is negative.

        :param positions: the positions of all vertices;
        :param vertex: a vertex of positions;
        :param other: another vertex of positions.
        :return the distance vector between vertex and other.
    
        Warning: if vertices overlap, the vector is directed towards vertex.
    
                |               ____
                |      dv      /
          v     /____________>/
               /             /      o
        ______/             |
                            |
        """

        xvc, yvc = positions[vertex]
        vw, vh = vertex.dimensions()
        xoc, yoc = positions[other]
        ow, oh = other.dimensions()

        xv0, yv0, xv1, yv1 = (
            xvc - vw / 2, yvc - vh / 2, xvc + vw / 2, yvc + vh / 2)
        xo0, yo0, xo1, yo1 = (
            xoc - ow / 2, yoc - oh / 2, xoc + ow / 2, yoc + oh / 2)

        xvi, yvi = vertex.shape.intersection((xv0, yv0, xv1, yv1), (xoc, yoc))
        xoi, yoi = other.shape.intersection((xo0, yo0, xo1, yo1), (xvc, yvc))

        return xvi, yvi, xoi, yoi

    def _hooke_attraction(self, positions, vertex, other):
        """
        Return the force produced by the spring between vertex and other,
        applied on vertex.

        :param positions: the positions of the vertices
                          (a vertex -> x,y position dictionary);
        :param vertex: a vertex of positions;
        :param other: another vertex of positions.
        :return the force vector produced by the spring between vertex and
                other, applied on vertex.
        """
        dx0, dy0, dx1, dy1 = self._distance_vector_from(positions,
                                                        vertex, other)

        # Use center to check when vertices overlap
        vcx, vcy = positions[vertex]
        ocx, ocy = positions[other]

        # Overlap: when overlapping, ignore the force
        if (ocx - vcx) * (dx1 - dx0) < 0 or (ocy - vcy) * (dy1 - dy0) < 0:
            return 0, 0

        dx, dy = dx1 - dx0, dy1 - dy0

        distance = math.sqrt(dx * dx + dy * dy)

        # Spring length is sum of radiuses of vertices
        dcx, dcy = ocx - vcx, ocy - vcy
        length = math.sqrt(dcx * dcx + dcy * dcy) - distance
        length = max(length, self.minSpringLength)

        if distance == 0:
            force = -self.maxForce
        else:
            force = -self.springStiffness * (length - distance) / distance
        force = max(min(force, self.maxForce), -self.maxForce)
        fx = force * dx
        fy = force * dy

        return fx, fy

    def _coulomb_repulsion(self, positions, vertex, other):
        """
        Return the electrical force produced by the other vertex on vertex.
        
        :param positions: the positions of the vertices
                          (a vertex -> x,y position dictionary);
        :param vertex: a vertex of positions;
        :param other: another vertex of positions.
        :return: the electrical force vector produced by other on vertex.
        """
        dx0, dy0, dx1, dy1 = self._distance_vector_from(positions,
                                                        vertex, other)

        # Use center to check when vertices overlap
        vcx, vcy = positions[vertex]
        ocx, ocy = positions[other]

        # Overlap: when overlapping inverse bounding box
        if (ocx - vcx) * (dx1 - dx0) < 0:
            dx0, dx1 = dx1, dx0
        if (ocy - vcy) * (dy1 - dy0) < 0:
            dy0, dy1 = dy1, dy0

        dx, dy = dx1 - dx0, dy1 - dy0

        distance = math.sqrt(dx * dx + dy * dy)

        if distance == 0:
            force = -self.maxForce
        else:
            force = -self.electricalRepulsion / (distance * distance)
        force = max(min(force, self.maxForce), -self.maxForce)
        fx = force * dx
        fy = force * dy

        return fx, fy

    def _apply_and_get_force(self, _, positions, edges, fixed=None):
        """
        Apply this layout on positions and edges, keeping fixed elements in
        place, and return the new positions as well as the average force on
        each element.

        :param canvas: the canvas on which operate;
        :param positions: a dictionary of elements -> x,y positions;
        :param edges: a list of couples representing the edges;
        :param fixed: a set of elements that must remain at given position.
        :return: a dictionary of new positions for elements of positions
                 and the average force applied on each element.
        """
        if fixed is None:
            fixed = set()

        forces = {}
        # Compute forces
        for vertex in positions:
            fx, fy = 0, 0

            # Repulsion forces
            for v in positions:
                if vertex != v:
                    cfx, cfy = self._coulomb_repulsion(positions,
                                                       vertex, v)
                    fx += cfx
                    fy += cfy

            # Spring forces
            for origin, end in edges:
                if origin == vertex or end == vertex:
                    if origin == vertex:
                        other = end
                    else:
                        other = origin

                    # Avoid computing the force for self-loop
                    if origin != end:
                        hfx, hfy = self._hooke_attraction(positions,
                                                          vertex, other)
                        fx += hfx
                        fy += hfy

            forces[vertex] = fx, fy

        # Compute new positions
        new_positions = {}
        sum_forces = 0
        for vertex in positions:
            fx, fy = forces[vertex]
            x, y = positions[vertex]
            nx = x + fx
            ny = y + fy
            sum_forces += math.sqrt(fx * fx + fy * fy)

            if vertex not in fixed:
                new_positions[vertex] = nx, ny
            else:
                new_positions[vertex] = x, y

        return (new_positions,
                sum_forces / len(new_positions)
                if len(new_positions) > 0 else 0)

    def apply(self, canvas, positions, edges, fixed=None):
        np, _ = self._apply_and_get_force(canvas,
                                          positions,
                                          edges,
                                          fixed=fixed)
        return np


class ForceBasedLayout(OneStepForceBasedLayout):
    """
    A force-based layout. One application gives the final positions.
    """

    def __init__(self):
        super().__init__()
        self.iterationNumber = 100
        self.forceThreshold = 0.001

    def apply(self, canvas, vertices, edges, fixed=None):
        np = vertices
        for i in range(self.iterationNumber):
            np, sf = super()._apply_and_get_force(canvas,
                                                  np,
                                                  edges,
                                                  fixed=fixed)
            if sf < self.forceThreshold:
                break
        return np


try:
    import pydot
except ImportError:
    pydot = None


class DotLayout:
    """
    A layout using fdp (part of graphviz library) to layout the graph.
    """

    def apply(self, _, vertices, edges, fixed=None):
        if pydot is None:
            raise ImportError("Cannot use dot layout, pydot is not installed.")

        # ----- CREATE DOT GRAPH -----
        # Mark all states
        ids = {}
        curid = 0
        for v in vertices:
            ids[v] = "s" + str(curid)
            curid += 1

        dot = "digraph {"

        # Add states to the dot representation
        for v in ids:
            dot += (ids[v] + " " + "[label=\"" + v.label + "\"]" + ";\n")

        # For each state, add each transition to the representation
        for origin, end in edges:
            dot += (ids[origin] + "->" + ids[end] + ";\n")

        dot += "}"

        # dot contains the dot representation of vertices and edges

        # ----- COMPUTE VERTICES POSITIONS -----
        graph = pydot.graph_from_dot_data(dot)
        graph = pydot.graph_from_dot_data(graph.create_dot(prog="fdp"))

        new_positions = {}
        for vertex in vertices:
            pos = graph.get_node(ids[vertex])[0].get("pos")
            pos = pos[1:-1]
            pos = pos.split(',')
            new_positions[vertex] = int(float(pos[0])), int(float(pos[1]))

        return new_positions
