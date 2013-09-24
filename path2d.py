#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""path2d.py

Sunday, September 22 2013
"""

from math import atan2, degrees, hypot

from PyQt4.QtGui import QPainterPath
from PyQt4.QtCore import QRectF


class Path2dException(Exception):
    pass


class Path2d(object):
    """A list of connected line and arc segments in the x/y cartesian plane.
    
    Three methods are used to construct path segments:
     * moveTo
     * lineTo
     * arcTo
     
    The path must start with a point but may end with a point or arc. A valid
    path requires at least two elements, a point followed by an arc, or a
    point followed by a point.
    """
    def __init__(self, startPoint=None):
        """Initialize the path.

        startPoint -- [x, y] If not supplied, moveTo must be called before
                             adding lines or arcs.
        """
        self._elements = []
        if startPoint:
            self._elements.append(startPoint)
    def __str__(self):
        elmstr = '\n       '.join([str(x) for x in self._elements])
        if elmstr:
            return 'Path2D[' + elmstr + ']'
        else:
            return 'Path2D[]'
    def isValid(self):
        """Return True if the path has at least two elements.

        The first must be a point.
        """
        return len(self._elements) >= 2 and len(self._elements[0]) == 2
    def elements(self):
        """Return a list of path elements.

        The list may contain two element types:
        1. [x, y]   a start or end point
        2. [[x, y], arc end point
            [x, y], arc center point
            d]      either 'cclw' or 'clw'
        """
        return self._elements
    def isEmpty(self):
        """Return True if there are no elements in the path.
        """
        return not self._elements
    def moveTo(self, x, y):
        """Clear the path and set the start point.
        """
        self._elements = [[x, y]]
    def lineTo(self, x, y):
        """Add the end point to the path.

        If the path is empty raise Path2dException.
        """
        if self.isEmpty():
            raise Path2dException("path needs a line start point")
        self._elements.append([x, y])
    def arcTo(self, endX, endY, centerX, centerY, arcDir):
        """Add an arc to the path.

        arcDir -- 'cclw' or 'clw'

        If the path is empty raise Path2dException.
        """
        if self.isEmpty():
            raise Path2dException("path needs an arc start point")
        self._elements.append([[endX, endY],
                               [centerX, centerY],
                               arcDir])
    def endPoints(self):
        """Return a list of all line and arc end points, in order.
        """
        return [e if len(e) == 2 else e[0] for e in self._elements]
    def toQPainterPath(self):
        """Return a QPainterPath containing all segments of this path.
        """
        if not self.isValid():
            raise Path2dException('invalid path')
        p = QPainterPath()
        sx, sy = self._elements[0]
        if len(self._elements[1]) == 2:
            # Only add a start point if the QPainterPath will start with a
            # line, not an arc.
            p.moveTo(sx, sy)
        for e in self._elements[1:]:
            if len(e) == 2:
                p.lineTo(*e)
                sx, sy = e
            else:
                (ex, ey), (cx, cy), arcDir = e
                r = hypot(ex-cx, ey-cy)
                d = r*2
                sa = degrees(atan2(sy-cy, sx-cx)) % 360.0
                ea = degrees(atan2(ey-cy, ex-cx)) % 360.0
                # NOTE: machtool uses a right-handed cartesian coordinate
                #       system with the Y+ up. Because of this, the QRectF
                #       used to define the arc has a negative height. This
                #       makes a positive arc angle sweep cclw as it should.
                rect = QRectF(cx - r, cy + r, d, -d)
                if arcDir == 'cclw':
                    span = (ea + 360.0 if ea < sa else ea) - sa
                else:
                    span = -((sa + 360.0 if sa < ea else sa) - ea)
                p.arcMoveTo(rect, sa)
                p.arcTo(rect, sa, span)
                sx, sy = ex, ey
        return p

if __name__ == '__main__':
    p = Path2d([0, 0])
    p.arcTo(1, 1, 0, 1, 'cclw')
    p.toQPainterPath()
    print p
