#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""mesh.py

Sunday, September 15 2013
"""

from math import pi, radians, degrees, sin, cos, sqrt

# from PyQt4.QtOpenGL import *
from PyQt4.QtGui import QVector2D
import OpenGL.GL as gl

from arc import arcFromVectors

pi2 = pi*2

def windowItr(seq, sz, step):
    n = ((len(seq) - sz) / step) + 1
    for i in range(0, n * step, step):
        yield seq[i:i+sz]

class Mesh(object):
    def __init__(self):
        self.indices = []
        self.vertices = []
        self.normals = []
        self.nTris = 0
        self.nVertices = 0
    def loadArrays(self):
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, self.vertices)
        # glNormalPointer(GL_FLOAT, 0, self.normals)
    def render(self):
        gl.glColor(1, 1, 1)
        gl.glDisable(gl.GL_LIGHTING)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        self.loadArrays()
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY);
        gl.glDrawElements(gl.GL_TRIANGLES, self.nTris * 3, gl.GL_UNSIGNED_INT,
                          self.indices)
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY);


class RevolvedMesh(Mesh):
    segs = 24
    def __init__(self, profile):
        super(RevolvedMesh, self).__init__()
        segs = 32
        step = pi2 / self.segs
        rangs = [0.0]
        for i in range(1, self.segs):
            rangs.append(step * i)
        rangs.append(0.0)
        self.angpairs = list(windowItr(rangs, 2, 1))
        print
        print profile
        for e1, e2 in windowItr(profile, 2, 1):
            d = None
            if e2 is None:
                break
            if len(e1) == 2:
                x1, y1 = e1
            else:
                (x1, y1), _, _ = e1
            if len(e2) == 2:
                x2, y2 = e2
            else:
                (x2, y2), (cx, cy), d = e2
            if d:
                self.addArcSeg(x1, y1, x2, y2, cx, cy, d)
            else:
                self.addLineSeg(x1, y1, x2, y2)
        print 'nTris', self.nTris
        print 'nVertices', self.nVertices
    def _addVertex(self, v):
        self.vertices.append(v)
        self.nVertices += 1
        return self.nVertices - 1
    # shared vertex version
    # def _addVertex(self, v):
    #     if v in self.vertices:
    #         return self.vertices.index(v)
    #     else:
    #         self.vertices.append(v)
    #         self.nVertices += 1
    #         return self.nVertices - 1
    def addLineSeg(self, x1, z1, x2, z2):
        # tip triangle fan, p1 == tip
        if x1 == 0.0:
            i = self._addVertex([float(x1), 0.0, float(z1)])
            for a1, a2 in self.angpairs:
                r = x2
                p2 = [r * cos(a2), r * sin(a2), z2]
                p3 = [r * cos(a1), r * sin(a1), z2]
                self.indices.append(i)
                self.indices.append(self._addVertex(p2))
                self.indices.append(self._addVertex(p3))
                self.nTris += 1
        # shank end triangle fan, p1 = top center
        elif x2 == 0.0:
            i = self._addVertex([float(x2), 0.0, float(z2)])
            for a1, a2 in self.angpairs:
                p2 = [x1 * cos(a1), x1 * sin(a1), z1]
                p3 = [x1 * cos(a2), x1 * sin(a2), z1]
                self.indices.append(i)
                self.indices.append(self._addVertex(p2))
                self.indices.append(self._addVertex(p3))
                self.nTris += 1
        # triangle strip
        # i3 o--o i4
        #    | /|
        #    |/ |
        # i1 o--o i2
        else:
            for a1, a2 in self.angpairs:
                sa1 = sin(a1)
                ca1 = cos(a1)
                sa2 = sin(a2)
                ca2 = cos(a2)
                i1 = self._addVertex([x1 * ca1, x1 * sa1, z1])
                i2 = self._addVertex([x1 * ca2, x1 * sa2, z1])
                i3 = self._addVertex([x2 * ca1, x2 * sa1, z2])
                i4 = self._addVertex([x2 * ca2, x2 * sa2, z2])
                self.indices.extend([i1, i2, i4, i1, i4, i3])
                self.nTris += 2
    def addArcSeg(self, x1, z1, x2, z2, cx, cz, arcDir):
        a = x1 - cx
        b = z1 - cz
        r = sqrt(a*a + b*b)
        arc = arcFromVectors(QVector2D(a, b),
                             QVector2D(x2 - cx, z2 - cz),
                             r,
                             arcDir == 'cclw')
        angstep = 360.0 / self.segs
        # minimum 4 segments in the arc
        segs = max(int(abs(arc.span()) / angstep), 3) + 1
        step = arc.span() / segs
        sa = arc.startAngle()
        rangs = [radians(sa)]
        for i in range(1, segs):
            rangs.append(radians(sa + step * i))
        rangs.append(radians(arc.endAngle()))
        print list(windowItr(rangs, 2, 1))
        for a1, a2 in list(windowItr(rangs, 2, 1)):
            sa1 = sin(a1)
            ca1 = cos(a1)
            sa2 = sin(a2)
            ca2 = cos(a2)
            x1 = cx + r * ca1
            z1 = cz + r * sa1
            x2 = cx + r * ca2
            z2 = cz + r * sa2
            self.addLineSeg(x1, z1, x2, z2)
        
        
