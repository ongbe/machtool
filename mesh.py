#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""mesh.py

Sunday, September 15 2013
"""

# NumPy
# * linspace -- evenly spaced numbers over interval

from math import pi, radians, degrees, sin, cos, sqrt

# from PyQt4.QtOpenGL import *
from PyQt4.QtGui import QVector2D, QVector3D
from PyQt4.QtCore import QPointF
import OpenGL.GL as gl
import numpy as np

from arc import Arc
from bbox import BBox

pi2 = pi*2

def windowItr(seq, sz, step):
    n = ((len(seq) - sz) / step) + 1
    for i in range(0, n * step, step):
        yield seq[i:i+sz]

class Patch(object):
    """A section of a Mesh.

    Smooth normals are computed per patch. This results in sharp edges between
    non-tangent patches. Each patch contains a start index into its parent
    mesh's vertices.
    """
    def __init__(self, mesh):
        """Initialize a Patch

        mesh -- Mesh, parent
        """
        self._mesh = mesh
        # number of triangles in this patch
        self._nTris = 0
        # offset into mesh._indices where this patch starts
        self._startIndex = mesh.vertexCount()
        # indices into the parent mesh's vertex list
        self._indices = []
        # r, g, b, a
        self._color = [0.1, 0.1, 0.7, 1.0]
        # 'wire', 'flat', or 'smooth'
        self._surfaceMode = 'smooth'
    def setColor(self, color):
        self._color = color
    def setWireFrame(self):
        self._surfaceMode = 'wire'
    def setSmoothShaded(self):
        self._surfaceMode = 'smooth'
    def setFlatShaded(self):
        self._surfaceMode = 'flat'
    def startIndex(self):
        """Return this patch's offset into its parent mesh's vertices.
        """
        return self._startIndex
    def addTri(self, a, b, c, apexVertex=None):
        """Add a triangle.

        a, b, c -- [x, y, z]
                   The three vertices, given in CCLW winding order.
        apexVertex -- [x, y, z]
                      The apex vertice, for a cone tip. Must be the same as a,
                      b, or c, or None.

        Return None.
        """
        # triangle normal
        n = QVector3D.normal(QVector3D(*a),
                             QVector3D(*b),
                             QVector3D(*c))
        n = [n.x(), n.y(), n.z()]
        self._indices.append(self._mesh.addVertex(a, n, self._startIndex,
                                                  apexVertex == a))
        self._indices.append(self._mesh.addVertex(b, n, self._startIndex,
                                                  apexVertex == b))
        self._indices.append(self._mesh.addVertex(c, n, self._startIndex,
                                                  apexVertex == c))
        self._nTris += 1
    def addQuad(self, a, b, c, d):
        """Add a quad.

        a, b, c, d -- [x, y, z]

        The quad is split into two triangles and added. The points must be
        given in cclw winding order.

        c o---o b
          |  /|
          | / |
        d o---o a
        """
        self.addTri(a, b, c)
        self.addTri(a, c, d)
    def addRevLineSeg(self, x1, z1, x2, z2):
        """Add a 360 degree revolved line to this Patch.

        x1, z1 -- start point
        x2, z2 -- end point

        It is assumed the points are in the XZ plane and the axis of
        revolution is parallel to the vector (0, 0, 1), and passes through the
        point (0, 0, 0).
        """
        # tip triangles
        if x1 == 0.0:
            a = [float(x1), 0.0, float(z1)]
            for (sa1, ca1), (sa2, ca2) in self._mesh.sincos:
                r = x2
                b = [r * ca2, r * sa2, z2]
                c = [r * ca1, r * sa1, z2]
                self.addTri(a, b, c, None if z1 == z2 else a)
        # shank end triangle fan, p1 = top center
        elif x2 == 0.0:
            a = [float(x2), 0.0, float(z2)]
            for (sa1, ca1), (sa2, ca2) in self._mesh.sincos:
                b = [x1 * ca1, x1 * sa1, z1]
                c = [x1 * ca2, x1 * sa2, z1]
                self.addTri(a, b, c, None if z1 == z2 else a)
        # triangle strip
        # d o--o c
        #   | /|
        #   |/ |
        # a o--o b
        else:
            for (sa1, ca1), (sa2, ca2) in self._mesh.sincos:
                self.addQuad([x1 * ca1, x1 * sa1, z1],
                             [x1 * ca2, x1 * sa2, z1],
                             [x2 * ca2, x2 * sa2, z2],
                             [x2 * ca1, x2 * sa1, z2])
    def addRevArcSeg(self, x1, z1, x2, z2, cx, cz, arcDir):
        """Add a 360 degree revolved arc to this Patch.

        x1, z1 -- start vertex
        x2, z2 -- end vertex
        cx, cz -- center point
        arcDir -- 'cclw' or 'clw'

        It is assumes the points are in the XZ plane and the axis of
        revolution is parallel to the vector (0, 0, 1), and passes through the
        point (0, 0, 0).
        """
        a = x1 - cx
        b = z1 - cz
        r = sqrt(a*a + b*b)
        arc = Arc.fromVectors(QVector2D(a, b),
                              QVector2D(x2 - cx, z2 - cz),
                              r,
                              arcDir == 'cclw')
        # TODO: By halving the mesh segs ( * 0.5), fewer triangles are
        #       created. Shading is ok but arc edges look blocky.
        angstep = 360.0 / (self._mesh.segs * 0.5)
        angstep = 360.0 / self._mesh.segs
        # minimum 2 segments in the arc
        segs = max(int(abs(arc.span()) / angstep), 3)
        step = arc.span() / segs
        sa = arc.startAngle()
        a1 = radians(sa)
        sa1 = sin(a1)
        ca1 = cos(a1)
        for i in range(1, segs):
            a2 = radians(sa + step * i)
            sa2 = sin(a2)
            ca2 = cos(a2)
            x1 = cx + r * ca1
            z1 = cz + r * sa1
            x2 = cx + r * ca2
            z2 = cz + r * sa2
            self.addRevLineSeg(x1, z1, x2, z2)
            a1 = a2
            sa1 = sa2
            ca1 = ca2
            if i == 1:
                # only blend the first strip
                self._mesh.blendTangent(False)
        else:
            a2 = radians(arc.endAngle())
            x1 = cx + r * ca1
            z1 = cz + r * sa1
            x2 = cx + r * cos(a2)
            z2 = cz + r * sin(a2)
            self.addRevLineSeg(x1, z1, x2, z2)
    def render(self):
        """Render this Patch.
        """
        if self._surfaceMode == 'smooth':
            gl.glEnable(gl.GL_LIGHTING)
            gl.glPolygonMode(gl.GL_FRONT, gl.GL_FILL)
            gl.glShadeModel(gl.GL_SMOOTH)
            gl.glEnable(gl.GL_LINE_SMOOTH)
            gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE,
                            self._color)
            gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR,
                            [0.3, 0.3, 1.0, 1.0])
            gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, 64)
        elif self._surfaceMode == 'wire':
            gl.glDisable(gl.GL_LIGHTING)
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            gl.glColor(*self._color)
        elif self._surfaceMode == 'flat':
            gl.glEnable(gl.GL_LIGHTING)
            gl.glPolygonMode(gl.GL_FRONT, gl.GL_FILL)
            gl.glShadeModel(gl.GL_FLAT)
            gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE,
                            self._color)
            gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR,
                            [0.0, 0.0, 1.0, 1.0])
            gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, 128)
        gl.glDrawElements(gl.GL_TRIANGLES, self._nTris * 3,
                          gl.GL_UNSIGNED_INT, self._indices)
    @staticmethod
    def fromRevLineSeg(x1, z1, x2, z2, mesh):
        """Create a revolved Patch from a line segment.

        x1, z1, x2, z2 -- line start and end coords
        mesh -- Mesh, parent

        Return a new Patch instance
        """
        patch = Patch(mesh)
        patch.addRevLineSeg(x1, z1, x2, z2)
        return patch
    @staticmethod
    def fromRevArcSeg(x1, z1, x2, z2, cx, cz, arcDir, mesh):
        """Create a revolved Patch from an arc segment.

        x1, z1 -- arc start point
        x2, z2 -- arc end point
        cx, cy -- arc center point
        arcDir -- 'cclw' or 'clw'
        mesh -- Mesh, parent

        Return a new Patch instance
        """
        patch = Patch(mesh)
        patch.addRevArcSeg(x1, z1, x2, z2, cx, cz, arcDir)
        return patch
        

class Mesh(object):
    """A Collection of Patch instances.
    """
    def __init__(self):
        # Patch instances
        self._patches = []
        # [x, y, z], all vertices of every triangle in the mesh
        self._vertices = []
        # [i, j, k], associated normals
        self._normals = []
        # [x, y, z], the unique set of all vertices, for bbox calc
        self._sharedVertices = []
        # integer, self.vertices count
        self._nVertices = 0
        # if true, include the previous patches vertices when summing normals
        self._prevStartIndex = 1e10
        # vertice bounding box
        self._bbox = None
    def setColor(self, color):
        """Set the color for all child patches.

        color -- (r, g, b, a)
        """
        for patch in self._patches:
            patch.setColor(color)
    def setWireFrame(self):
        """Set all patches to render as triangles.
        """
        for patch in self._patches:
            patch.setWireFrame()
    def setSmoothShaded(self):
        """Set all patches to render smooth shaded.
        """
        for patch in self._patches:
            patch.setSmoothShaded()
    def setFlatShaded(self):
        """Set all patches to render flat shaded.
        """
        for patch in self._patches:
            patch.setFlatShaded()
    def blendTangent(self, blend):
        """Search the previous Patch's vertices when adding a vertex.
        
        blend -- bool

        This will create the correct normals between tangent patches.
        """
        if blend and self._patches:
            self._prevStartIndex = self._patches[-1].startIndex()
        else:
            self._prevStartIndex = 1e10
    def verticesEqual(self, v1, v2, eps=1e-8):
        """Return True if the vertices are equal.

        v1, v2 -- [x, y, z]
        eps -- allowed difference
        """
        if abs(v1[0] - v2[0]) > eps:
            return False
        if abs(v1[1] - v2[1]) > eps:
            return False
        if abs(v1[2] - v2[2]) > eps:
            return False
        return True
    def addVertex(self, v, n, startIndex, apex=False):
        """Add the vertex and associated normal.

        v -- [x, y, z]
        n -- [i, j, k], normal of vertex's parent triangle or an apex normal
                        as described below
        startIndex -- index where vertex's Patch starts
        apex -- If True, the vertex is the apex of a cone. Its associated
                normal (n) will have been pre-calculated. v and n will be
                appended without any further checks or normal sums.
        """
        for vv in self._sharedVertices[-1::-1]:
            #TODO: 
            # if np.allclose(v, vv):
            if self.verticesEqual(v, vv):
                break
        else:
            self._sharedVertices.append(v)
        if not apex:
            startIndex = min(startIndex, self._prevStartIndex)
            i = self._nVertices - 1
            while i >= startIndex:
                # if self._vertices[i] == v:
                if self.verticesEqual(self._vertices[i], v): 
                    # vertex found
                    # sum its normal with the duplicate vertex's normal
                    nn = QVector3D(*self._normals[i])
                    nn += QVector3D(*n)
                    nn.normalize()
                    # if v[0] == 0.0 and v[1] == 0.0:
                    #     print nn
                    self._normals[i] = [nn.x(), nn.y(), nn.z()]
                    return i
                i -= 1
        # vertex not found or it's an apex vertex
        self._vertices.append(v)
        self._normals.append(n)
        self._nVertices += 1
        return self._nVertices - 1
    def vertexCount(self):
        """Return the length of self.vertices (cached)
        """
        return self._nVertices
    def sharedVertices(self):
        """Return the list of unique vertices in this mesh.
        """
        return self._sharedVertices
    def bbox(self):
        """Find the coordinate-aligned bounding box of this meshes vertices.

        Return a BBox instance.
        """
        return self._bbox
    def render(self):
        """Render all the patches.
        """
        gl.glVertexPointer(3, gl.GL_DOUBLE, 0, self._vertices);
        gl.glNormalPointer(gl.GL_FLOAT, 0, self._normals);
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY);
        gl.glEnableClientState(gl.GL_NORMAL_ARRAY);
        for patch in self._patches:
            patch.render()
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY);
        gl.glDisableClientState(gl.GL_NORMAL_ARRAY);

        
def getSinCosCache(nSegs):
    """Find the sin and cos of every angle of a circle divided by nSegs.

    This build the sin/cos cache for RevolvedMesh.

    Return the list:
      [((sin0, cos0), (sinAng1, cosAng1)),
       ...
       ((sinAngN, cosAngN), (sin0, cos0))]
      where N is pi*2 / nSegs
      
    """
    step = pi2 / nSegs
    rangs = [0.0]
    for i in range(1, nSegs):
        rangs.append(step * i)
    rangs.append(0.0)
    return map(lambda x: ((sin(x[0]), cos(x[0])),
                          (sin(x[1]), cos(x[1]))),
               windowItr(rangs, 2, 1))
        

class RevolvedMesh(Mesh):
    """A 360 degree surface of revolution.
    """
    segs = 32
    sincos = getSinCosCache(segs)
    def __init__(self, profile=None, color=[0.1, 0.1, 0.7, 1.0], close=False):
        super(RevolvedMesh, self).__init__()
        if profile:
            self.addProfile(profile, color, close)
    def _isLineTanToArc(self, x1, y1, x2, y2, cx, cy, d):
        """Find if the line is tangent to the arc.

        x1, y1 -- [x, y], line start point
        x2, y2 -- [x, y], line end, arc start
        cx, cy -- [x, y], arc center point
        d -- 'clw' or 'cclw'

        It is assumed that the line end point and the arc start point are the
        same.

        Return True or False.
        """
        p = QPointF(x2, y2)
        # line start -> end
        v1 = QVector2D(p - QPointF(x1, y1)).normalized()
        # arc center -> arc start
        v2 = QVector2D(p - QPointF(cx, cy)).normalized()
        if abs(v1.dotProduct(v1, v2)) <= 1e-6:
            # TODO: handle case where arc turns back into the line
            return True
        else:
            return False
    # TODO: untested
    def _isArcTangentToArc(self, px, py, cx1, cy1, cx2, cy2):
        """Find if two arcs are tangent

        px, p1 -- [x, y], common point of arcs
        cxN, cyN -- [x, y], arc center points

        It is assumed that the arcs share a common point.

        Return True or Fasle
        """
        p = QPointF(px, py)
        v1 = QVector2D(p - QPointF(cx1, cy1)).normalized()
        v2 = QVector2D(p - QPointF(cx1, cy1)).normalized()
        if abs(v1.dotProduct(v1, v2)) <= 1e-6:
            # TODO: handle case where arc turns back into the other arc
            return True
        else:
            return False
    def addProfile(self, profile, color=None, close=False):
        """Create each Patch defined by the profile.

        profile -- a list of tuples as defined in tooldef.py
        color -- [r, g, b, a]
        close -- if True and the profile start or end points are not on
                 the axis of revolution, insert one with X=0.0 and Z
                 equal to the start or end point Z.
        """
        if close:
            e1 = profile[0]     # will always be a point
            if e1[0] != 0.0:
                profile = [(0.0, e1[1])] + profile
            e2 = profile[-1]
            if e2[0] != 0.0:
                if len(e2) == 2:
                    profile.append((0.0, e2[1]))
                else:
                    # profile ends in an arc
                    profile.append((0.0, e2[0][1]))
        # previous line start x/y, for line -> arc
        px1 = py1 = None
        for e1, e2 in windowItr(profile, 2, 1):
            if e2 is None:
                break
            le1 = len(e1)
            le2 = len(e2)
            # line or start -> line
            if le1 == 2 and le2 == 2:
                x1, y1 = e1
                x2, y2 = e2
                self.blendTangent(False)
                patch = Patch.fromRevLineSeg(x1, y1, x2, y2, self)
                if color:
                    patch.setColor(color)
                self._patches.append(patch)
                px1 = x1
                py1 = y1
            # line or start -> arc
            elif le1 == 2 and le2 == 3:
                x1, y1 = e1
                (x2, y2), (cx, cy), d = e2
                if px1 is not None:
                    self.blendTangent(self._isLineTanToArc(px1, py1, x1, y1,
                                                           cx, cy, d))
                patch = Patch.fromRevArcSeg(x1, y1, x2, y2, cx, cy, d, self)
                if color:
                    patch.setColor(color)
                self._patches.append(patch)
            # arc -> line
            elif le1 == 3 and le2 == 2:
                (aex, aey), (cx, cy), d = e1
                lex, ley = e2
                self.blendTangent(self._isLineTanToArc(lex, ley, aex, aey, cx,
                                                       cy, d))
                patch = Patch.fromRevLineSeg(aex, aey, lex, ley, self)
                if color:
                    patch.setColor(color)
                self._patches.append(patch)
                px1 = aex
                py1 = aey
            # arc -> arc
            # TODO: untested, no tool defined with this geometry
            else:
                (x1, y1), (cx1, cy1), d1 = e1
                (x2, y2), (cx2, cy2), d2 = e2
                self.blendTangent(self._isArcTangentToArc(x1, y1, cx1, cy1,
                                                          cx2, cy2))
                patch = Patch.fromRevArcSeg(x1, y1, x2, y2, cx2, cy2, d2,
                                            self)
                if color:
                    patch.setColor(color)
                self._patches.append(patch)
        self._bbox = BBox.fromVertices(self._sharedVertices)
