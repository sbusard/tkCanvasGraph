import math

springLength = 60
springStiffness = 0.25
electricalRepulsion = 500

iterationNumber = 1000
forceThreshold = 0.001

maxForce = 10

def _distance_vector_from(canvas, vertex, other):
    """
    Return the distance vector from vertex to the other vertex.
    If vertex is at greater position than other,
    the distance vector is negative.
    
    Warning: if vertices overlap, the vector is directed towards vertex.
    
            |               ____
            |      dv      /
      v     /____________>/
           /             /      o
    ______/             |
                        |
    """
    
    xv0, yv0, xv1, yv1 = vertex.bbox(canvas)
    xvc, yvc = (xv1 + xv0) / 2, (yv1 + yv0) / 2
    xo0, yo0, xo1, yo1 = other.bbox(canvas)
    xoc, yoc = (xo1 + xo0) / 2, (yo1 + yo0) / 2
    
    av = xv1 - xvc      #    +---a-----|
    bv = yv1 - yvc      #    |         |
    ao = xo1 - xoc      #    b        /
    bo = yo1 - yoc      #    |      /
                        #   _|____/
    
    if xoc != xvc:
        m = abs((yoc - yvc) / (xoc - xvc))
        
        dvx = (av * bv) / math.sqrt(av*av * m*m + bv*bv)
        dvx *= -1 if xoc < xvc else 1
        
        dox = (ao * bo) / math.sqrt(ao*ao * m*m + bo*bo)
        dox *= -1 if xoc > xvc else 1
        
        dvy = (av * bv * m) / math.sqrt(av*av * m*m + bv*bv)
        dvy *= -1 if yoc < yvc else 1
        
        doy = (ao * bo * m) / math.sqrt(ao*ao * m*m + bo*bo)
        doy *= -1 if yoc > yvc else 1
    
    else:
        dvx = dox = 0
        dvy = bv
        dvy *= -1 if yoc < yvc else 1
        doy = bo
        doy *= -1 if yoc > yvc else 1
    
    return (xvc + dvx, yvc + dvy, xoc + dox, yoc + doy)

def _hooke_attraction(canvas, vertex, other):
    """
    Return the force produced by the spring between vertex and other, applied
    on vertex.
    
    canvas -- the canvas of interest;
    vertex -- a vertex;
    other -- another vertex.
    """
    dx0, dy0, dx1, dy1 = _distance_vector_from(canvas, vertex, other)
    
    # Use center to check when vertices overlap
    vcx, vcy = vertex.center(canvas)
    ocx, ocy = other.center(canvas)
    
    # Overlap: when overlapping, ignore the force
    if (ocx - vcx) * (dx1 - dx0) < 0 or (ocy - vcy) * (dy1 - dy0) < 0:
        return 0, 0
    #if (ocx - vcx) * (dx1 - dx0) < 0:
    #    dx0, dx1 = dx1, dx0
    #if (ocy - vcy) * (dy1 - dy0) < 0:
    #    dy0, dy1 = dy1, dy0
    
    dx, dy = dx1 - dx0, dy1 - dy0
    
    distance = math.sqrt(dx*dx + dy*dy)
    
    force = -springStiffness * (springLength - distance) / distance
    force = max(min(force, maxForce), -maxForce)
    fx = force * dx
    fy = force * dy
    
    return fx, fy

def _coulomb_repulsion(canvas, vertex, other):
    """
    Return the electrical force produced by the other vertex on vertex.
    
    canvas -- the canvas of interest;
    vertex -- a vertex;
    other -- another vertex.
    """
    dx0, dy0, dx1, dy1 = _distance_vector_from(canvas, vertex, other)
    
    # Use center to check when vertices overlap
    vcx, vcy = vertex.center(canvas)
    ocx, ocy = other.center(canvas)
    
    # Overlap: when overlapping inverse bounding box
    if (ocx - vcx) * (dx1 - dx0) < 0:
        dx0, dx1 = dx1, dx0
    if (ocy - vcy) * (dy1 - dy0) < 0:
        dy0, dy1 = dy1, dy0
    
    dx, dy = dx1 - dx0, dy1 - dy0
    
    distance = math.sqrt(dx*dx + dy*dy)
    
    force = -electricalRepulsion / (distance*distance)
    force = max(min(force, maxForce), -maxForce)
    fx = force * dx
    fy = force * dy
    
    return fx, fy

def force_based_layout_step(canvas, positions, edges, fixed=None):
    """
    Return the new positions of vertices in positions on canvas,
    given edges between them.
    If fixed is not None, only vertices out of fixed are moved.
    
    canvas -- the canvas on which operate;
    positions -- a dictionary of vertex -> x,y coordinates values;
    edges -- a set of edges between vertices of positions;
    fixed -- a set of vertices.
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
                cfx, cfy = _coulomb_repulsion(canvas, vertex, v)
                fx += cfx
                fy += cfy
        
        # Spring forces
        for edge in edges:
            if edge.origin == vertex or edge.end == vertex:
                if edge.origin == vertex:
                    other = edge.end
                else:
                    other = edge.origin
                
                hfx, hfy = _hooke_attraction(canvas, vertex, other)
                #fx += hfx
                #fy += hfy
        
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
        
        if vertex not in fixed:
            newPositions[vertex] = nx, ny
        else:
            newPositions[vertex] = x, y
    
    return newPositions, sumForces/len(newPositions)

def force_based_layout(canvas, vertices, edges, fixed=None):
    """
    Return the new positions of vertices on canvas,
    given their initial positions and their connected edges.
    Return a dictionary of vertices -> positions pairs, with new positions of
    the vertices.
    If fixed is not None, only vertices out of fixed are moved.
    
    canvas   -- the canvas on which operate;
    vertices -- a dictionary of vertices -> position pairs, where positions
                are couples of x,y coordinates
    edges    -- a set of couples (v1, v2) where v1 and v2 belong to vertices;
    fixed    -- a set of vertices.
    """
    np = vertices
    for i in range(iterationNumber):
        np, sf = force_based_layout_step(canvas, np, edges, fixed=fixed)
        if sf < forceThreshold:
            break
    return np