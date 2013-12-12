class CanvasGraphError(Exception):
    """A generic CanvasGraph error."""
    pass

class UnknownCanvasError(CanvasGraphError):
    """The given canvas is unknown."""
    pass