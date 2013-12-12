import math

springLength = 60
springStiffness = 0.25
electricalRepulsion = 250

iterationNumber = 1000
forceThreshold = 0.001

def _hooke_attraction(canvas, origin, end):
    """
    Return the force produced by the spring between origin and end, applied
    on origin.
    
    canvas -- the canvas of interest;
    origin -- an x,y couple;
    end -- an x,y couple.
    """
    xv, yv = origin
    xe, ye = end
    dx = xv - xe
    dy = yv - ye
    distance = math.sqrt(dx*dx + dy*dy)
    
    fx = springStiffness * (springLength - distance) * dx / distance
    fy = springStiffness * (springLength - distance) * dy / distance
    
    return fx, fy

def _distance_vector_from(canvas, vertex, other):
    """
    Return the distance vector (x,y) from vertex to the other vertex.
    """
    xo0, yo0, xo1, yo1 = vertex.bbox(canvas)
    xoc, yoc = (xo1 + xo0) / 2, (yo1 + yo0) / 2
    xe0, ye0, xe1, ye1 = other.bbox(canvas)
    xec, yec = (xe1 + xe0) / 2, (ye1 + ye0) / 2
    
    ao = xo1 - xoc
    bo = yo1 - yoc
    ae = xe1 - xec
    be = ye1 - yec
    
    if xec != xoc:
        m = (yec - yoc) / (xec - xoc)
    
        dox = (ao * bo) / math.sqrt(ao * ao * m * m + bo * bo)
        dex = (ae * be) / math.sqrt(ae * ae * m * m + be * be)
        doy = (ao * bo * m) / math.sqrt(ao * ao * m * m + bo * bo)
        dey = (ae * be * m) / math.sqrt(ae * ae * m * m + be * be)
    
    else:
        dox = dex = 0
        doy = bo * (-1 if yec > yoc else 1)
        dey = be * (-1 if yec > yoc else 1)
    
    dbbox = (xoc + dox if xec >= xoc else xoc - dox,
             yoc + doy if xec > xoc else yoc - doy,
             xec - dex if xec >= xoc else xec + dex,
             yec - dey if xec > xoc else yec + dey)
    
    if xoc < xec:
        dx = dbbox[2] - dbbox[0]
    else:
        dx = dbbox[0] - dbbox[2]
    if yoc < yec:
        dy = dbbox[3] - dbbox[1]
    else:
        dy = dbbox[1] - dbbox[3]
    dx = dbbox[2] - dbbox[0]
    dy = dbbox[3] - dbbox[1]
    return dx, dy

def _coulomb_repulsion(canvas, vertex, other):
    """
    Return the electrical force produced by the other vertex on vertex.
    
    canvas -- the canvas of interest;
    vertexbbox -- a vertex;
    otherbbox -- another vertex.
    """
    dx, dy = _distance_vector_from(canvas, vertex, other)
    distance = math.sqrt(dx*dx + dy*dy)
    
    fx = -electricalRepulsion * dx / (distance*distance)
    fy = -electricalRepulsion * dy / (distance*distance)
    
    return fx, fy

def _coords_from_ends(canvas, positions, origin, end):
    wo, ho = origin.dimensions(canvas)
    xoc, yoc = positions[origin]
    we, he = end.dimensions(canvas)
    xec, yec = positions[end]

    ao = wo/2
    bo = ho/2
    ae = we/2
    be = he/2

    if xec != xoc:
        m = (yec - yoc) / (xec - xoc)

        dox = (ao * bo) / math.sqrt(ao * ao * m * m + bo * bo)
        dex = (ae * be) / math.sqrt(ae * ae * m * m + be * be)
        doy = (ao * bo * m) / math.sqrt(ao * ao * m * m + bo * bo)
        dey = (ae * be * m) / math.sqrt(ae * ae * m * m + be * be)

    else:
        dox = dex = 0
        doy = bo * (-1 if yec > yoc else 1)
        dey = be * (-1 if yec > yoc else 1)

    return ((xoc + dox if xec >= xoc else xoc - dox,
             yoc + doy if xec > xoc else yoc - doy),
            (xec - dex if xec >= xoc else xec + dex,
             yec - dey if xec > xoc else yec + dey))

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
                # Compute coordinates of edge
                opos, epos = _coords_from_ends(canvas, positions, edge.origin,
                                               edge.end)
                
                if edge.origin == vertex:
                    vertexpos = opos
                    otherpos = epos
                else:
                    vertexpos = epos
                    otherpos = opos
                
                hfx, hfy = _hooke_attraction(canvas, vertexpos, otherpos)
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