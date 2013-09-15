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
import OpenGL.GLU as glu

class MeshView(QGLWidget):
    quadratic = glu.gluNewQuadric()
    def __init__(self, parent):
        super(MeshView, self).__init__(parent)
        self.rotCenter = [0.0, 0.0, 1.0]
        self.modelviewMatrix = [[1.0, 0.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0]]
        self.sceneCenter = [0.0, 0.0]
        self.sceneWidth = 5.0
        self.sceneHeight = 5.0
        self.aspect = 1.0
        self.rotFactor = 0.75
        self.iso = False
        self.lastPos = QPoint()
        self.setMouseTracking(True)
    def initializeGL(self):
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_NORMALIZE)
        gl.glShadeModel(gl.GL_SMOOTH)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glEnable(gl.GL_MULTISAMPLE)
        lightPosition = [0.5, 5.0, 7.0, 1.0]
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, lightPosition)
        self.frontView()
    def sizeHint(self):
        return QSize(500, 500)
    def pixelSize(self, projMatrix):
        """Find the size of a pixel in scene coordinates.

        Return [width, height]
        """
        return [2.0 / (projMatrix[0][0] * self.width()),
                2.0 / (projMatrix[1][1] * self.height())]
    # TODO: y is backwards O_o
    def screenToScene(self, x, y):
        """Find the scene coordinates of the pixel

        Return [x, y]
        """
        pw, ph = self.pixelSize(gl.glGetFloat(gl.GL_PROJECTION_MATRIX))
        return [self.sceneCenter[0] - (self.sceneWidth * 0.5) + pw * x,
                self.sceneCenter[1] - (self.sceneHeight * 0.5) + ph * y]
    def ortho(self):
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        self.sceneWidth = self.sceneHeight * self.aspect
        cx, cy = self.sceneCenter
        gl.glOrtho(cx - self.sceneWidth * 0.5,
                   cx + self.sceneWidth * 0.5,
                   cy - self.sceneHeight * 0.5,
                   cy + self.sceneHeight * 0.5,
                   -1000, 1000)
        gl.glMatrixMode(gl.GL_MODELVIEW)
    def resizeGL(self, w, h):
        if w == 0 or h == 0:
            return
        self.aspect = float(w) / h
        gl.glViewport(0, 0, w, h)
        self.ortho()
    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadMatrixf(self.modelviewMatrix)
        glu.gluSphere(MeshView.quadratic, 1, 32, 32)
        glu.gluCylinder(MeshView.quadratic, 0.5, 0.5, 2, 32, 32)
        gl.glPushMatrix()
        gl.glTranslatef(0, 0, 2)
        glu.gluDisk(MeshView.quadratic, 0, 0.5, 32, 2)
        gl.glPopMatrix()
    def topView(self):
        """Rotate to view the X/Y plane.
        """
        gl.glLoadIdentity()
        gl.glTranslatef(*[-1.0 * x for x in self.rotCenter])
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
    def bottomView(self):
        """Rotate to view the X/-Y plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(180.0, 1.0, 0.0, 0.0)
        gl.glTranslatef(*[-1.0 * x for x in self.rotCenter])
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
    def rightView(self):
        """Rotate to view the Y/Z plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(-90.0, 1.0, 0.0, 0.0)
        gl.glRotate(-90.0, 0.0, 0.0, 1.0)
        gl.glTranslatef(*[-1.0 * x for x in self.rotCenter])
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
    def leftView(self):
        """Rotate to view the -Y/Z plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(-90.0, 1.0, 0.0, 0.0)
        gl.glRotate(90.0, 0.0, 0.0, 1.0)
        gl.glTranslatef(*[-1.0 * x for x in self.rotCenter])
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
    def frontView(self):
        """Rotate to view the X/Z plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(-90.0, 1.0, 0.0, 0.0)
        gl.glTranslatef(*[-1.0 * x for x in self.rotCenter])
        self.modelviewMatrix = gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX)
    def backView(self):
        """Rotate to view the -X/Z plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(-90.0, 1.0, 0.0, 0.0)
        gl.glRotate(180.0, 0.0, 0.0, 1.0)
        gl.glTranslatef(*[-1.0 * x for x in self.rotCenter])
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
    def isoView(self):
        """Rotate to an isometric view.
        """
        gl.glLoadIdentity()
        gl.glRotate(-60.0, 1.0, 0.0, 0.0)
        gl.glRotate(-45.0, 0.0, 0.0, 1.0)
        gl.glTranslate(*[-1.0 * x for x in self.rotCenter])
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
    def rotate(self, dx, dy):
        axis = QVector3D(dy, dx, 0)   # dx/dy backwards!
        axisN = axis.normalized()
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glRotatef(self.rotFactor * axis.length(),
                     axisN.x(), axisN.y(), axisN.z())
        gl.glMultMatrixf(self.modelviewMatrix)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        gl.glTranslate(*self.rotCenter)
        gl.glPopMatrix()
    def pan(self, dx, dy):
        pw, ph = self.pixelSize(gl.glGetFloat(gl.GL_PROJECTION_MATRIX))
        self.sceneCenter[0] -= pw * dx
        self.sceneCenter[1] += ph * dy
        self.ortho()
    def mouseMoveEvent(self, e):
        if e.buttons() & qt.LeftButton:
            delta = e.pos() - self.lastPos
            self.rotate(delta.x(), delta.y())
            self.updateGL()
        if e.buttons() & qt.MiddleButton:
            delta = e.pos() - self.lastPos
            self.pan(delta.x(), delta.y())
            self.updateGL()
        self.lastPos = e.pos()
