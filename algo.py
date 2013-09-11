#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""algo.py

Saturday, March 30 2013
"""

from math import pi, fmod, degrees, atan2, sqrt

from PyQt4.QtCore import QPointF, QLineF
from PyQt4.QtGui import QVector2D

def clamp(x, low, high):
    """Return x clamped to the range given by low and high
    """
    return min(high, max(x, low))

def linesCollinear(l1, l2):
    """Find if two line segments are ON the same line.

    l1, l2 -- QLineF

    Return True or False
    """
    x1, y1 = l1.x1(), l1.y1()
    x2, y2 = l1.x2(), l1.y2()
    x3, y3 = l2.x1(), l2.y1()
    return (y1 - y2) * (x1 - x3) == (y1 - y3) * (x1 - x2)

def xsectLineRect1(l, r):
    """Find the first intersection point of a line segment and a rectangle.

    l -- QLineF
    r -- QRectF

    This algo assumes one line end point is INSIDE the rectangle.
    Return a QPointF()
    """
    rt = l.BoundedIntersection
    rp = QPointF()
    # left
    if l.intersect(QLineF(r.topLeft(), r.bottomLeft()), rp) == rt:
        return rp
    # top
    elif l.intersect(QLineF(r.topLeft(), r.topRight()), rp) == rt:
        return rp
    # right
    elif l.intersect(QLineF(r.topRight(), r.bottomRight()), rp) == rt:
        return rp
    # bottom
    elif l.intersect(QLineF(r.bottomRight(), r.bottomLeft()), rp) == rt:
        return rp

def pointOnLine(p, sp, ep):
    """Find a point on the line closest to the given reference point.

    p -- QPointF, reference point
    sp -- QPointF, line start point
    ep -- QPointF, line end point

    Return a QPointF
    """
    v = QVector2D(p - sp)
    u = QVector2D(ep - sp).normalized()
    return (QVector2D(sp) + v.dotProduct(v, u) * u).toPointF()

def pointOnArc(p, cp, r):
    """Find a point on the arc closest to the given reference point.
    
    p -- QPointF, reference point
    cp -- QPointF, arc center point
    r -- float, arc radius

    Return a QPointF
    """
    if p == cp:
        raise Exception("infinite points on arc found")
    v = QVector2D(p - cp).normalized()
    return (QVector2D(cp) + v * r).toPointF()

def midpoint(p1, p2):
    """Return the mid point of p1 and p2.

    p1, p2 -- QPointF

    Return a QPointF
    """
    return QPointF((p1.x() + p2.x()) * .5, (p1.y() + p2.y()) * .5)

def arcLength(span, r):
    """Find the length of an arc.

    span -- signed arc angle in degrees
    r -- arc radius

    Return the signed length.
    """
    return span / 360.0 * (2 * pi * r)

def isPointOnArc(p, cp, start, span, r=None, eps=1e-6):
    """Find if the given point is ON the arc.

    p -- ref point, QPointF
    cp -- arc center point, QPointF
    start -- signed start angle, in degrees
    span -- signed sweep angle, in degrees
    r -- arc radius, or None to check only the angles
    eps -- epsilon value for radius equality check

    Return True or False
    """
    v = QVector2D(p - cp)
    if r and abs(v.length() - r) > eps:
        return
    sa = start % 360.0
    ea = (start + span) % 360.0
    if span < 0.0:
        sa, ea = ea, sa
    ptx = v.toPointF()
    pa = degrees(atan2(ptx.y(), ptx.x())) % 360.0
    if ea < sa :
        return pa >= sa or pa <= ea
    else:
        return pa >= sa and pa <= ea

def isPointOnLineSeg(p, l, eps=1e-6):
    """Find if the point is ON the line segment.
    
    p -- QPointF
    l -- QLineF
    eps -- epsilon for checking vector parallelism
    """
    v1 = QVector2D(l.p2() - l.p1()) # line vector
    v2 = QVector2D(p - l.p1())
    dp = v1.dotProduct(v1.normalized(), v2.normalized())
    return 1.0 - dp < eps and v2.length() <= v1.length()

def vectorToAbsAngle(v):
    """Find the absolute angle of the vector.

    v -- QVector2D

    Return the angle in degrees where
      0.0 <= angle < 360.0.
    """
    vv = v.normalized()
    return degrees(atan2(v.y(), v.x())) % 360.0

def lineSegToParLine(l):
    """Find the parametric form of a 2d line segment.

    l -- QLineF

    return x1, y1, i, j
    """
    if l.isNull():
        raise Exception("line has zero length")
    x1 = l.p1().x()
    y1 = l.p1().y()
    x2 = l.p2().x()
    y2 = l.p2().y()
    norm = sqrt((x2 - x1)**2 + (y2 - y1)**2)
    i = (x2 - x1) / norm
    j = (y2 - y1) / norm
    return x1, y1, i, j

def xsectLineCir(l, cx, cy, r):
    """Find the intersection point(s) of a 2d line segment and a 2d circle.

    l -- QLineF
    cx, cy, r -- circle properties
    
    Return a list of [x,y] pairs or [] if no intersection.
    """
    x, y, f, g = lineSegToParLine(l)
    r = float(r)
    cp = [float(cx), float(cy)]
    x = float(x)
    y = float(y)
    f = float(f)
    g = float(g)
    p = []
    root = (r * r * (f * f + g * g)
            - (f * (cp[1] - y) - g * (cp[0] - x))
            * (f * (cp[1] - y) - g * (cp[0] - x)))
    if root == 0.0:
        t = (f * (cp[0] - x) + g * (cp[1] - y)) / (f * f + g * g)
        p.append([x + f * t, y + g * t])
    elif root > 0.0:
        a = f * (cp[0] - x) + g * (cp[1] - y)
        b = f * f + g * g
        t = (a - sqrt(root)) / b
        p.append([x + f * t, y + g * t])
        t = (a + sqrt(root)) / b
        p.append([x + f * t, y + g * t])
    return p

def xsectRectCir(rect, cx, cy, r):
    """Find the intersection points of a line and a rectangle.

    rect -- QRectF
    cx, cy, r -- circle properties

    Return a """

    points = []
    # left
    l = QLineF(rect.topLeft(), rect.bottomLeft())
    points.append(xsectLineCir(l, cx, cy, r))
    # top
    l = QLineF(rect.topLeft(), rect.topRight())
    points.append(xsectLineCir(l, cx, cy, r))
    # right
    l = QLineF(rect.topRight(), rect.bottomRight())
    points.append(xsectLineCir(l, cx, cy, r))
    # bottom
    l = QLineF(rect.bottomLeft(), rect.bottomRight())
    points.append(xsectLineCir(l, cx, cy, r))
    return points

# TODO: handle multiple intersection points if needed
def xsectArcRect1(arc, rect):
    """Find the single intersection point of the arc and the rectangle.

    arc -- Arc
    rect -- QRectF

    The arc start point is assumed to be at the center of the rect.

    Return a QPointF if the arc exits the rect exactly once and does not
    re-enter the rect. Else return None.
    """
    # points where the line SEGMENT and the arc SEGMENT intersect
    xsectPoints = []
    tl = rect.topLeft()
    tr = rect.topRight()
    bl = rect.bottomLeft()
    br = rect.bottomRight()
    cx = arc.centerX()
    cy = arc.centerY()
    r = arc.radius()
    for l in [QLineF(tl, tr),
              QLineF(tr, br),
              QLineF(br, bl),
              QLineF(bl, tl)]:
        for x, y in xsectLineCir(l, cx, cy, r):
            p = QPointF(x, y)
            if isPointOnArc(p, arc.center(), arc.start(), arc.span()):
                if isPointOnLineSeg(p, l):
                    xsectPoints.append(p)
    if len(xsectPoints) == 1:
        return xsectPoints[0]
    else:
        return None
        
