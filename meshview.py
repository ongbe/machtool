#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""meshview.py

Saturday, September 14 2013
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtCore import Qt as qt
from PyQt4.QtOpenGL import *
import OpenGL.GL as gl

from glview import GLView
from bbox import BBox

class MeshView(GLView):
    """A tool mesh viewer.
    """
    def __init__(self, parent):
        super(MeshView, self).__init__(parent)
        self.mesh = None
    def setMesh(self, mesh):
        self.mesh = mesh
        self.setRotCenter(mesh.bbox().center())
    def createContextMenu(self):
        super(MeshView, self).createContextMenu()
        a = QAction("Fit", self)
        self.connect(a, SIGNAL('triggered()'), self.fitMesh)
        self.addAction(a)
    # TODO: This works but QMatrix4x4 * v does not.
    def mxv(self, m, v):
        """Multiply matrix and vector.

        m -- 4x4 matrix
        v -- [x, y, z]

        Return the mapped [x, y, z].
        """
        vv = v + [1.0]
        out = [0.0, 0.0, 0.0, 0.0]
        for r in range(4):
            result = 0.0
            for c in range(4):
                result += vv[c] * m[c][r]
            out[r] = result
        return out[:3]
    def fitMesh(self):
        if self.mesh is None:
            return
        mappedVerts = []
        # TODO: get shared vertices here, not all of them
        for meshVert in self.mesh.sharedVertices():
            v = self.mxv(self.modelviewMatrix, meshVert)
            mappedVerts.append(v)
        bbox = BBox.fromVertices(mappedVerts)
        self.fit(QPointF(bbox.p1[0], bbox.p1[1]),
                 QPointF(bbox.p2[0], bbox.p2[1]))
        self.updateGL()
    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        if self.mesh:
            self.mesh.render()
    def topView(self):
        super(MeshView, self).topView(False)
        self.fitMesh()
    def bottomView(self):
        super(MeshView, self).bottomView(False)
        self.fitMesh()
    def rightView(self):
        super(MeshView, self).rightView(False)
        self.fitMesh()
    def leftView(self):
        super(MeshView, self).leftView(False)
        self.fitMesh()
    def frontView(self):
        super(MeshView, self).frontView(False)
        self.fitMesh()
    def backView(self):
        super(MeshView, self).backView(False)
        self.fitMesh()
    def isometricView(self):
        super(MeshView, self).isometricView(False)
        self.fitMesh()
