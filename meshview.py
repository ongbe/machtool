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
        # copy of GLView.rotFactor
        self.baseRotFactor = self.rotFactor
    def wheelEvent(self, e):
        """Zoom in/out and adjust the mouse rotation factor.
        """
        super(MeshView, self).wheelEvent(e)
        self._setRotFactor()
    # TODO: Works well but is probably going to need some tweaking
    def _setRotFactor(self):
        """Adjust the mouse rotation factor.

        The factor is computed based on how much of the mesh is visible and
        how deep into the scene it extends.
        """
        if self.mesh:
            bbox = self.getMeshSceneBBox()
            w, h, d = bbox.size()
            # mesh is fully in view
            if self.sceneHeight >= h and self.sceneWidth > w:
                if d > w+h:
                    self.rotFactor = self.baseRotFactor * ((w+h) / d)
                else:
                    self.rotFactor = self.baseRotFactor
            # partially in view
            else:
                self.rotFactor = \
                    self.baseRotFactor * self.sceneHeight / max(w, h) * 0.5
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
    # TODO: The mesh's bounding box vertices are transformed by the current
    #       model view matrix. The bounding box of those points is used to fit
    #       the tool. This isn't as accurate as using the meshes vertices but
    #       it is faster.
    # def fitMesh(self):
    #     if self.mesh is None:
    #         return
    #     mappedVerts = []
    #     for boxVert in self.mesh.bbox().vertices():
    #         v = self.mxv(self.modelviewMatrix, boxVert)
    #         mappedVerts.append(v)
    #     bbox = BBox.fromVertices(mappedVerts)
    #     self.fit(QPointF(bbox.p1[0], bbox.p1[1]),
    #              QPointF(bbox.p2[0], bbox.p2[1]))
    #     self.updateGL()
    # fit mesh vertices version
    def getMeshSceneBBox(self):
        """Get the view-aligned bbox of the mesh at its current orientation.

        Return a BBox.
        """
        mappedVerts = []
        for meshVert in self.mesh.sharedVertices():
            v = self.mxv(self.modelviewMatrix, meshVert)
            mappedVerts.append(v)
        return BBox.fromVertices(mappedVerts)
    def fitMesh(self):
        if self.mesh is None:
            return
        bbox = self.getMeshSceneBBox()
        self.fit(QPointF(bbox.left(), bbox.top()),
                 QPointF(bbox.right(), bbox.bottom()))
        self.updateGL()
        self._setRotFactor()
    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        if self.mesh:
            self.mesh.render()
    def topView(self, update=False):
        super(MeshView, self).topView(update)
        self.fitMesh()
    def bottomView(self, update=False):
        super(MeshView, self).bottomView(update)
        self.fitMesh()
    def rightView(self, update=False):
        super(MeshView, self).rightView(update)
        self.fitMesh()
    def leftView(self, update=False):
        super(MeshView, self).leftView(update)
        self.fitMesh()
    def frontView(self, update=False):
        super(MeshView, self).frontView(update)
        self.fitMesh()
    def backView(self, update=False):
        super(MeshView, self).backView(update)
        self.fitMesh()
    def isometricView(self, update=False):
        super(MeshView, self).isometricView(update)
        self.fitMesh()
    def keyPressEvent(self, e):
        if e.key() == qt.Key_F:
            self.fitMesh()
        super(MeshView, self).keyPressEvent(e)
