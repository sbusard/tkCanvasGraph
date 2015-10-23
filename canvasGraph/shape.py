"""
Shapes.

This module defines shapes for graph elements.
"""

import math


__all__ = ["Shape", "Oval", "Rectangle"]


class Shape:
    """
    The shape of a graph element.
    """

    def draw(self, canvas, bbox, style):
        """
        Draw this shape on canvas, around the given bounding box, with style,
        and return the handle on canvas.

        :param canvas: the canvas to draw on;
        :param bbox: the tkinter-style bounding box to draw around;
        :param style: the style of the shape.
        :return: the handle of the drawn shape.
        """
        raise NotImplementedError("Should be implemented by subclasses.")

    def intersection(self, bbox, end):
        """
        Return the point of intersection between this shape with given bounding
        box, and the line segment defined by the center of this bounding box
        and end.
        Return None is such an intersection does not exist.
        
        :param bbox: the tkinter-style bounding box of this shape;
        :param end: the (x, y) coordinates of the ending point.
        :return: the (x, y) coordinates of the intersection point of this
                 shape and the line between its center and end, if any,
                 None otherwise.
        """
        raise NotImplementedError("Should be implemented by subclasses.")

    def dimension(self, bbox):
        """
        Return the dimension of this shape around the given bounding box.

        :param bbox: the (x0, y0, x1, y1) bounding box.
        :return: the (x'0, y'0, x'1, y'1) bounding box of this shape around
                 bbox.
        """


class Oval(Shape):
    """
    The Oval shape is an ellipsis shape.
    """

    def __init__(self, diameter=20):
        """
        Create a new oval shape with default diameter. Default diameter is used
        to draw a circle when the bounding box to draw around is too small.

        :param diameter: the diameter of small shapes. (ignored if the shape
                         is large enough)
        """
        self._diameter = diameter

    def draw(self, canvas, bbox, style):
        return canvas.create_oval(self.dimension(bbox), **style)

    def intersection(self, bbox, end):
        xo0, yo0, xo1, yo1 = bbox
        xoc, yoc = (xo1 + xo0) / 2, (yo1 + yo0) / 2
        xec, yec = end

        ao = xo1 - xoc
        bo = yo1 - yoc

        if xec != xoc:
            m = (yec - yoc) / (xec - xoc)

            dox = (ao * bo) / math.sqrt(ao * ao * m * m + bo * bo)
            doy = (ao * bo * m) / math.sqrt(ao * ao * m * m + bo * bo)

        else:
            dox = 0
            doy = bo * (-1 if yec > yoc else 1)

        return (xoc + dox if xec >= xoc else xoc - dox,
                yoc + doy if xec > xoc else yoc - doy)

    def dimension(self, bbox):
        x0l, y0l, x1l, y1l = bbox
        xc, yc = (x1l + x0l) / 2, (y1l + y0l) / 2

        if x1l - x0l < self._diameter:
            x0e = xc - self._diameter / 2
            x1e = xc + self._diameter / 2
        else:
            x0e = xc - (x1l - x0l) / 2 * math.sqrt(2)
            x1e = xc + (x1l - x0l) / 2 * math.sqrt(2)

        if y1l - y0l < self._diameter:
            y0e = yc - self._diameter / 2
            y1e = yc + self._diameter / 2
        else:
            y0e = yc - (y1l - y0l) / 2 * math.sqrt(2)
            y1e = yc + (y1l - y0l) / 2 * math.sqrt(2)

        return x0e, y0e, x1e, y1e


class Rectangle(Shape):
    """
    A rectangle shape.
    """

    def __init__(self, size=5):
        """
        Create a new rectangle shape with default size. Default size is used
        to draw a square when the bounding box to draw around is too small.

        :param size: the size of the square if its content is too small.
                     (ignored if the content of the rectangle is large enough)
        """
        self._size = size

    def draw(self, canvas, bbox, style):
        return canvas.create_rectangle(self.dimension(bbox), **style)

    def intersection(self, bbox, end):
        xo0, yo0, xo1, yo1 = bbox
        xoc, yoc = (xo1 + xo0) / 2, (yo1 + yo0) / 2
        xec, yec = end

        if xec != xoc:
            m = abs((yec - yoc) / (xec - xoc))

            if m == 0:
                dox = xo1 - xoc
                doy = 0
            else:
                dox = min(xo1 - xoc, (yo1 - yoc) / m)
                doy = min(yo1 - yoc, (xo1 - xoc) * m)
        else:
            dox = 0
            doy = yo1 - yoc

        return (xoc + dox if xec > xoc else xoc - dox,
                yoc + doy if yec > yoc else yoc - doy)

    def dimension(self, bbox):
        x0l, y0l, x1l, y1l = bbox
        xc, yc = (x1l + x0l) / 2, (y1l + y0l) / 2

        if x1l - x0l < self._size:
            x0e = xc - self._size / 2
            x1e = xc + self._size / 2
        else:
            x0e, x1e = x0l, x1l

        if y1l - y0l < self._size:
            y0e = yc - self._size / 2
            y1e = yc + self._size / 2
        else:
            y0e, y1e = y0l, y1l

        return x0e, y0e, x1e, y1e
