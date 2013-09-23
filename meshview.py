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
import numpy as np

from glview import GLView
from bbox import BBox

class MeshView(GLView):
    """A tool mesh viewer.
    """
    def __init__(self, parent):
        super(MeshView, self).__init__(parent)
        self._mesh = None
        # copy of GLView.rotFactor
        self.baseRotFactor = self.rotFactor
        self._shadeMode = 'smooth'
    def wheelEvent(self, e):
        """Zoom in/out and adjust the mouse rotation factor.
        """
        super(MeshView, self).wheelEvent(e)
        self._setRotFactor()
    # TODO:
    #  * Works well but is probably going to need some tweaking.
    #    * added rotFactor lower bound of 0.05
    def _setRotFactor(self):
        """Adjust the mouse rotation factor.

        The factor is computed based on how much of the mesh is visible and
        how deep into the scene it extends.
        """
        if self._mesh:
            bbox = self.getMeshSceneBBox()
            w, h, d = bbox.size()
            # mesh is fully in view
            if self.sceneHeight >= h and self.sceneWidth > w:
                if d > w+h:
                    self.rotFactor = max(self.baseRotFactor * ((w+h) / d),
                                         0.05)
                else:
                    self.rotFactor = self.baseRotFactor
            # partially in view
            else:
                self.rotFactor = max(self.baseRotFactor
                                     * self.sceneHeight / max(w, h) * 0.5,
                                     0.05)
    def setMesh(self, mesh):
        self._mesh = mesh
        self.setRotCenter(mesh.bbox().center())
        if self._shadeMode == 'smooth':
            self._mesh.setSmoothShaded()
        elif self._shadeMode == 'flat':
            self._mesh.setFlatShaded()
        else:
            self._mesh.setWireFrame()
    def createContextMenu(self):
        a = QAction("Fit", self)
        self.connect(a, SIGNAL('triggered()'), self.fitMesh)
        self.addAction(a)
        sep = QAction(self)
        sep.setSeparator(True)
        self.addAction(sep)
        super(MeshView, self).createContextMenu()
        # remove redundant fixed views
        for a in [x for x in self.actions()
                  if x.text() in ['Left', 'Right', 'Back']]:
            self.removeAction(a)
    def mxv(self, m, v):
        """Multiply matrix and vector.

        m -- 4x4 matrix
        v -- [x, y, z, 1.0]

        Return the mapped [x, y, z, 1.0].
        """
        out = np.zeros(4)
        for r in (0, 1, 2, 3):
            result = 0.0
            for c in (0, 1, 2, 3):
                result += v[c] * m[c, r]
            out[r] = result
        return out
    # TODO: The mesh's bounding box vertices are transformed by the current
    #       model view matrix. The bounding box of those points is used to fit
    #       the tool. This isn't as accurate as using the meshes vertices but
    #       it is faster.
    # def fitMesh(self):
    #     if self._mesh is None:
    #         return
    #     mappedVerts = []
    #     for boxVert in self._mesh.bbox().vertices():
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
        for meshVert in self._mesh.sharedVertices():
            # mv = np.array(meshVert + [1.0])
            # nm = self.modelviewMatrix * mv
            # diag = nm.diagonal()
            # v = diag[:3]
            mappedVerts.append(self.mxv(self.modelviewMatrix,
                                        meshVert + [1.0])[:3])
            # mappedVerts.append(self.mxv(self.modelviewMatrix, meshVert))
        bbox = BBox.fromVertices(mappedVerts)
        return bbox
    def fitMesh(self):
        if self._mesh is None:
            return
        bbox = self.getMeshSceneBBox()
        # fit calls updateGL()
        self.fit(bbox.leftTop(), bbox.rightBottom())
        self._setRotFactor()
    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        if self._mesh:
            self._mesh.render()
    def topView(self, update=False):
        super(MeshView, self).topView(update)
        self.fitMesh()
    def bottomView(self, update=False):
        super(MeshView, self).bottomView(update)
        self.fitMesh()
    def frontView(self, update=False):
        super(MeshView, self).frontView(update)
        self.fitMesh()
    def isometricView(self, update=False):
        super(MeshView, self).isometricView(update)
        self.fitMesh()
    def keyPressEvent(self, e):
        if self._mesh is None:
            super(MeshView, self).keyPressEvent(e)
            return
        if e.key() == qt.Key_F:
            self.fitMesh()
        if e.key() == qt.Key_W:
            self._shadeMode = 'wire'
            self._mesh.setWireFrame()
            self.updateGL()
        if e.key() == qt.Key_S:
            self._shadeMode = 'smooth'
            self._mesh.setSmoothShaded()
            self.updateGL()
        if e.key() == qt.Key_T:
            self._shadeMode = 'flat'
            self._mesh.setFlatShaded()
            self.updateGL()
    # def mouseMoveEvent(self, e):
    #     super(MeshView, self).mouseMoveEvent(e)
    #     print 'pos', self.screenToScene(e.x(), e.y())
