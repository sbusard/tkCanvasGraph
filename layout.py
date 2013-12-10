import math

springLength = 80
springStiffness = 0.1
electricalRepulsion = 100

iterationNumber = 10000
forceThreshold = 0.1

def _hooke_attraction(positions, vertex, end):
    """
    Return the force produced by the spring between vertex and end, applied
    on vertex.
    """
    xv, yv = positions[vertex]
    xe, ye = positions[end]
    dx = xv - xe
    dy = yv - ye
    distance = math.sqrt(dx*dx + dy*dy)
    
    fx = springStiffness * (springLength - distance) * dx / distance
    fy = springStiffness * (springLength - distance) * dy / distance
    
    return fx, fy

def _coulomb_repulsion(positions, vertex, other):
    """
    Return the electrical force produced by the other vertex on vertex.
    """
    xv, yv = positions[vertex]
    xo, yo = positions[other]
    dx = xv - xo
    dy = yv - yo
    distance = math.sqrt(dx*dx + dy*dy)
    
    fx = electricalRepulsion * dx / (distance*distance)
    fy = electricalRepulsion * dy / (distance*distance)
    
    return fx, fy

def _force_based_layout_step(positions, edges):
    """
    Return the new positions of vertices in positions, given edges between them.
    """
    forces = {}
    # Compute forces
    for vertex in positions:
        fx, fy = 0, 0
        for v in positions:
            if vertex != v:
                cfx, cfy = _coulomb_repulsion(positions, vertex, v)
                fx += cfx
                fy += cfy
        for (o, e) in edges:
            if o == vertex or e == vertex:
                other = o if e == vertex else e
                hfx, hfy = _hooke_attraction(positions, vertex, other)
                fx += hfx
                fy += hfy
        forces[vertex] = fx, fy
                
    # Compute new positions
    newPositions = {}
    sumForces = 0
    for vertex in positions:
        fx, fy = forces[vertex]
        x, y = positions[vertex]
        nx = x + fx
        ny = y + fy
        sumForces += math.sqrt(fx*fx + fy*fy)
        newPositions[vertex] = nx, ny
    
    return newPositions, sumForces

def force_based_layout(vertices, edges):
    """
    Return the new positions of vertices, given their initial positions and
    their connected edges.
    Return a dictionary of vertices -> positions pairs, with new positions of
    the vertices.
    
    vertices -- a dictionary of vertices -> position pairs, where positions
                are couples of x,y coordinates
    edges    -- a set of couples (v1, v2) where v1 and v2 belong to vertices.
    """
    np = vertices
    for i in range(iterationNumber):
        np, sf = _force_based_layout_step(np, edges)
        yield np
        if sf < forceThreshold:
            break