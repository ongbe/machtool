#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""bbox.py

Monday, September 16 2013
"""

class BBoxException(Exception):
    pass


class BBox(object):
    """Coordinate aligned 3d bounding box.

    """
    def __init__(self, p1, p2):
        """Initialize the box.

        p1, p2 -- [x, y, z]

        Where p2 > p1.
        """
        if p1 == p2:
            raise BBoxException('box has zero size')
        if p1[0] >= p2[0]:
            raise BBoxException('invalid x len {}'.format(p2[0] - p1[0]))
        if p1[1] >= p2[1]:
            raise BBoxException('invalid y len {}'.format(p2[1] - p1[1]))
        if p1[2] >= p2[2]:
            raise BBoxException('invalid z len {}'.format(p2[2] - p1[2]))
        self.p1 = p1
        self.p2 = p2
        self._center = [(p1[0] + p2[0]) * 0.5,
                        (p1[1] + p2[1]) * 0.5,
                        (p1[2] + p2[2]) * 0.5]
    def center(self):
        """Return the center coordinate of this bounding box.

        [x, y, z]
        """
        return self._center
    def __str__(self):
        return "[({}, {}, {}), ({}, {}, {})]" \
            .format(self.p1[0], self.p1[1], self.p1[2],
                    self.p2[0], self.p2[1], self.p2[2])
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
    def xLen(self):
        return self.p2[0] - self.p1[0]
    def yLen(self):
        return self.p2[1] - self.p1[2]
    def zLen(self):
        return self.p2[2] - self.p1[2]
    def left(self):
        return self.p1[0]
    def right(self):
        return self.p2[0]
    def top(self):
        return self.p2[2]
    def bottom(self):
        return self.p1[2]
    def front(self):
        return self.p1[1]
    def back(self):
        return self.p2[1]
    def vertices(self):
        """Return a list of of the boxes corner points
        
                   7 o--------o 6
                    /|       /|
                   / |      / |                     
                3 o--------o 2|
                  |4 o-----|--o 5
                  | /      | /
                  |/       |/
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
                
