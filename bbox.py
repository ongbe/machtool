#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""bbox.py

Monday, September 16 2013
"""

import numpy as np


class BBoxException(Exception):
    pass


class BBox(object):
    """Coordinate aligned 3d bounding box.

    p1's coordinates must always be < p2's.

            o--------o                   Y+
           /.       /|                   |
          / .      / |                   |   
         o--------o<---p2                |
      p1-|->o. . .|. o                   o------X+
         | .      | /                   /
         |.       |/                   /
         o--------o p2                Z+ (out of the screen)
    """
    def __init__(self, p1, p2):
        """Initialize the box.

        p1 -- [x, y, z], left, bottom, back
        p2 -- [x, y, z], right, top, front

        Where p2 > p1.
        """
        if np.allclose(p1, p2): # NUMPY: vector equality w/epsilon
            raise BBoxException('box has zero size')
        if not np.all(p1 < p2): # NUMPY:
            raise BBoxException('p1 must be < p2')
        # [left bottom back,
        #  right top front]
        self._coords = np.array((p1, p2))
        self._center = np.sum(self._coords, axis=0) * 0.5
    def p1(self):
        return self._coords[0]
    def p2(self):
        return self._coords[1]
    def center(self):
        """Return the center coordinate of this bounding box.
        """
        return self._center
    # def __str__(self):
    #     return "[({}, {}, {}), ({}, {}, {})]" \
    #         .format(self._p1[0], self._p1[1], self._p1[2],
    #                 self._p2[0], self._p2[1], self._p2[2])
    @staticmethod
    def fromVertices(vertices, m=None):
        """Create a coordinate-aligned BBox from the given list of vertices.

        vertices -- [(x, y, z), (x, y, z), ...]
        m -- 4x4 numpy array

        If m is supplied, find the bbox of the transformed vertices.

        Return a new BBox instance.
        """
        p1 = np.min(vertices, axis=0)
        p2 = np.max(vertices, axis=0)
        return BBox(p1, p2)
    def size(self):
        """Return [x width , y height, z depth]
        """
        return [self._coords[1][0] - self._coords[0][0],
                self._coords[1][1] - self._coords[0][1],
                self._coords[1][2] - self._coords[0][2]]
        # return np.apply_along_axis(np.diff, 0, self._coords)[0]
    def width(self):
        """Return the X length of the box.
        """
        return self.xLen()
    def height(self):
        """Return the Y length of the box.
        """
        return self.yLen()
    def depth(self):
        """Return the Z length of the box.
        """
        return self.zLen()
    def xLen(self):
        return self.size()[0]
    def yLen(self):
        return self.size()[1]
    def zLen(self):
        return self.size()[2]
    def left(self):
        return self._coords[0, 0]
    def right(self):
        return self._coords[1, 0]
    def bottom(self):
        return self._coords[0, 1]
    def top(self):
        return self._coords[1, 1]
    def back(self):
        return self._coords[0, 2]
    def front(self):
        return self._coords[1, 2]
    def leftTop(self):
        return np.array([self.left(), self.top()])
    def leftBottom(self):
        return np.array([self.left(), self.bottom()])
    def rightBottom(self):
        return np.array([self.right(), self.bottom()])
    def rightTop(self):
        return np.array([self.right(), self.top()])
    def vertices(self):
        """Return a list of of the boxes corner points.
        
                   7 o--------o 6
                    /.       /|
                   / .      / |                     
                3 o--------o<--------2
           4 -----|->o . . |. o 5
                  | .      | /
                  |.       |/
                0 o--------o 1
        """
        left = self.left()
        right = self.right()
        top = self.top()
        bottom = self.bottom()
        front = self.front()
        back = self.back()
        return [[left, front, bottom],
                [right, front, bottom],
                [right, front, top],
                [left, front, top],
                [left, back, bottom],
                [right, back, bottom],
                [right, back, top],
                [left, back, top]]
