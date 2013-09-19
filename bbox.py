#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""bbox.py

Monday, September 16 2013
"""

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
        if p1 == p2:
            raise BBoxException('box has zero size')
        if p1[0] >= p2[0]:
            raise BBoxException('invalid x len {}'.format(_p2[0] - _p1[0]))
        if p1[1] >= p2[1]:
            raise BBoxException('invalid y len {}'.format(_p2[1] - _p1[1]))
        if p1[2] >= p2[2]:
            raise BBoxException('invalid z len {}'.format(_p2[2] - _p1[2]))
        self._p1 = p1
        self._p2 = p2
        self._center = [(p1[0] + p2[0]) * 0.5,
                        (p1[1] + p2[1]) * 0.5,
                        (p1[2] + p2[2]) * 0.5]
    def p1(self):
        return self._p1
    def p2(self):
        return self._p2
    def center(self):
        """Return the center coordinate of this bounding box.

        [x, y, z]
        """
        return self._center
    def __str__(self):
        return "[({}, {}, {}), ({}, {}, {})]" \
            .format(self._p1[0], self._p1[1], self._p1[2],
                    self._p2[0], self._p2[1], self._p2[2])
    @staticmethod
    def fromVertices(vertices):
        """Create a coordinate-aligned BBox from the given list of vertices.

        vertices -- [(x, y, z), (x, y, z), ...]

        Return a new BBox instance.
        """
        p1 = [1e10, 1e10, 1e10]
        p2 = [-1e10, -1e10, -1e10]
        for x, y, z in vertices:
            p1 = [min(x, p1[0]), min(y, p1[1]), min(z, p1[2])]
            p2 = [max(x, p2[0]), max(y, p2[1]), max(z, p2[2])]
        return BBox(p1, p2)
    def size(self):
        """Return (x width , y height, z depth)
        """
        return (self.width(), self.height(), self.depth())
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
        return self._p2[0] - self._p1[0]
    def yLen(self):
        return self._p2[1] - self._p1[1]
    def zLen(self):
        return self._p2[2] - self._p1[2]
    def left(self):
        return self._p1[0]
    def right(self):
        return self._p2[0]
    def top(self):
        return self._p2[1]
    def bottom(self):
        return self._p1[1]
    def front(self):
        return self._p2[2]
    def back(self):
        return self._p1[2]
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
                
