#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""arc.py

Thursday, August 22 2013
"""

import os
import sys
import re
from math import degrees, radians, sin, cos, atan2
from copy import copy

from PyQt4.QtCore import QPointF
from PyQt4.QtGui import QVector2D

class ArcException(Exception): pass

class Arc(object):
    """Define a 2D arc in the right-handed cartesian plane.

    The internal map is defined as follows:
    'center' -- QPointF, arc center point
    'radius' -- arc radius
    'start' -- start angle in degrees
    'span' -- Signed sweep angle from start. A positive span will create a
              counter-clockwise arc.
    """
    def __init__(self, m={'center': QPointF(0.0, 0.0),
                          'radius': 0.5,
                          'start': 0.0,
                          'span': 90.0}):
        r = m.get('radius', None)
        if r is not None and r <= 0.0:
            raise ArcException("radius must be > 0.0")
        self.m = copy(m)
    def config(self, m={}):
        self.m.update(m)
        r = self.m.get('radius', None)
        if r is not None and r <= 0.0:
            raise ArcException("radius must be > 0.0")
    def center(self, value=None):
        if value:
            self.m['center'] = value
        else:
            return self.m['center']
    def centerX(self, value=None):
        if value:
            self.m['center'] = QPointF(value, self.m['center'].y())
        else:
            return self.m['center'].x()
    def centerY(self, value=None):
        if value:
            self.m['center'] = QPointF(self.m['center'].x(), value)
        else:
            return self.m['center'].y()
    def radius(self, value=None):
        if value:
            self.m['radius'] = value
        else:
            return self.m['radius']
    def start(self, value=None):
        if value:
            self.m['start'] = value
        else:
            return self.m['start']
    def span(self, value=None):
        if value:
            self.m['span'] = value
        else:
            return self.m['span']
    def startAngle(self):
        return self.m['start']
    def endAngle(self):
        return self.m['start'] + self.m['span']
    def startPoint(self):
        r = self.m['radius']
        s = radians(self.m['start'])
        return self.m['center'] + QPointF(cos(s) * r, sin(s) * r)
    def endPoint(self):
        r = self.m['radius']
        e = radians(self.endAngle())
        return self.m['center'] + QPointF(cos(e) * r, sin(e) * r)
    def startAngleVector(self):
        return QVector2D(self.startPoint() - self.m['center']).normalized()
    def endAngleVector(self):
        return QVector2D(self.endPoint() - self.m['center']).normalized()
    def bisector(self):
        """Find the arc bisector.

        Raise ArcException if this arc is a circle.
        
        Return a normalized QVector2D.
        """
        span = self.m['span']
        if abs(span) == 360.0:
            raise ArcException('Arc of 360 degrees has no bisector')
        a = radians(self.m['start'] + self.m['span'] / 2.0)
        return QVector2D(cos(a), sin(a))

def arcFromAngles(a1, a2, radius, cclw=True):
    """Construct an arc centered @ (0, 0) from a1 to a2.
    
    a1, a2 -- signed angles in degrees
    radius -- arc radius
    cclw -- If True, return a counter-clockwise arc (positive span angle) from
            a1 to a2, else a clockwise arc (negative span angle).

    If a1 and a2 are equal, the arc will span +/-360.0 degrees.

    Return an Arc.
    """
    a = Arc()
    if a1 == a2:
        a.config({'radius': radius,
                  'start': 0.0,
                  'span': 360.0 if cclw else -360.0})
    else:
        a1 %= 360.0
        a2 %= 360.0
        if cclw:
            a.config({'radius': radius,
                      'start': a1,
                      'span': (a2 + 360.0 if a2 < a1 else a2) - a1})
        else:
            a.config({'radius': radius,
                      'start': a1,
                      'span': -((a1 + 360.0 if a1 < a2 else a1) - a2)})
    return a


def arcFromVectors(v1, v2, radius, cclw=True):
    """Construct an arc centered @ (0, 0) from v1 to v2.

    v1, v2 -- QVector2D (do not have to be normalized)
    radius -- arc radius
    cclw -- if True, the arc will span counter-clockwise from v1 to v2

    Return an Arc
    """
    a1 = degrees(atan2(v1.y(), v1.x()))
    a2 = degrees(atan2(v2.y(), v2.x()))
    return arcFromAngles(a1, a2, radius, cclw)
        

if __name__ == '__main__':
    # a1 = Arc()
    # a1.config({'span': -100})
    # print 'start angle', a1.startAngle()
    # print '  end angle', a1.endAngle()
    # print ' angle diff', a1.angleDiff()
    # p1 = QPointF(-1, 1)
    # p2 = QPointF(1, -1)
    # print arcFromPoints(p1, p2, cclw=True).m
    a1 = -120
    a2 = 90
    print arcFromAngles(a1, a2, 1, cclw=False).m

    
