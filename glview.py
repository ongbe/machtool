#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""glview.py

Saturday, September 14 2013
"""

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtCore import Qt as qt
from PyQt4.QtOpenGL import *
import OpenGL.GL as gl
import OpenGL.GLU as glu

class GLView(QGLWidget):
    """An OpenGL viewer with pan/rotate/zoom + fixed orientation views.
    """
    def __init__(self, parent):
        super(GLView, self).__init__(parent)
        self.rotCenter = [0.0, 0.0, 0.0]
        self.modelviewMatrix = [[1.0, 0.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0]]
        self.sceneCenter = [0.0, 0.0]
        self.sceneWidth = 5.0
        self.sceneHeight = 5.0
        self.aspect = 1.0
        self.rotFactor = 0.75
        self.lastMousePos = QPoint()
        self.minZoom = 0.1
        self.maxZoom = 30.0
        self.setMouseTracking(True)
        self.createContextMenu()
    def setRotCenter(self, p):
        self.rotCenter = p
    # TODO: too lazy
    def createContextMenu(self):
        self.setContextMenuPolicy(qt.ActionsContextMenu)
        for item in ['Top', 'Bottom', 'Left', 'Right', 'Front', 'Back',
                     'Isometric']:
            a = QAction(item, self)
            eval('self.connect(a, SIGNAL("triggered()"),'
                 'self.{}View)'.format(item.lower()))
            self.addAction(a)
    def initializeGL(self):
        gl.glClearColor(0.0, 0.25, 0.25, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, [50, 50, 170])
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, [0.5, 0.5, 1.0, 1.0])
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        # base class defaults to front view, +X/+Z plane
        self.frontView(False)
    def sizeHint(self):
        return QSize(500, 500)
    def minimumSizeHint(self):
        return QSize(100, 100)
    def pixelSize(self, projMatrix):
        """Find the size of a pixel in scene coordinates.

        Return [width, height]
        """
        return [2.0 / (projMatrix[0][0] * self.width()),
                2.0 / (projMatrix[1][1] * self.height())]
    # TODO: I got the y backwards and everything else depends on it
    def screenToScene(self, x, y):
        """Find the scene coordinates of the pixel

        Return [x, y]
        """
        pw, ph = self.pixelSize(gl.glGetFloat(gl.GL_PROJECTION_MATRIX))
        return [self.sceneCenter[0] - (self.sceneWidth * 0.5) + pw * x,
                self.sceneCenter[1] - (self.sceneHeight * 0.5) + ph * y]
    def ortho(self):
        """Set up the scene's bounds
        """
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
        self.updateGL()
    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        axisLen = 2.0
        gl.glDisable(gl.GL_LIGHTING)
        gl.glBegin(gl.GL_LINES)
        gl.glColor(1, 0, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(axisLen, 0, 0)
        gl.glColor(0, 1, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, axisLen, 0)
        gl.glColor(0, 0, 1)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, 0, axisLen)
        gl.glEnd()
        gl.glEnable(gl.GL_LIGHTING)
    def topView(self, update=True):
        """Rotate to view the X/Y plane.
        """
        gl.glLoadIdentity()
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def bottomView(self, update=True):
        """Rotate to view the X/-Y plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(180.0, 1.0, 0.0, 0.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def rightView(self, update=True):
        """Rotate to view the Y/Z plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(-90.0, 1.0, 0.0, 0.0)
        gl.glRotate(-90.0, 0.0, 0.0, 1.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def leftView(self, update=True):
        """Rotate to view the -Y/Z plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(-90.0, 1.0, 0.0, 0.0)
        gl.glRotate(90.0, 0.0, 0.0, 1.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def frontView(self, update=True):
        """Rotate to view the X/Z plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(-90.0, 1.0, 0.0, 0.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def backView(self, update=True):
        """Rotate to view the -X/Z plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(-90.0, 1.0, 0.0, 0.0)
        gl.glRotate(180.0, 0.0, 0.0, 1.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def isometricView(self, update=True):
        """Rotate to an isometric view.

        Not sure if this is 100% accurate, but it's close enough.
        """
        gl.glLoadIdentity()
        gl.glRotate(-60.0, 1.0, 0.0, 0.0)
        gl.glRotate(-45.0, 0.0, 0.0, 1.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def rotate(self, dx, dy):
        """Rotate about the current focal point (self.rotCenter).

        dx, dy -- mouse deltas
        """
        axis = QVector3D(dy, dx, 0)   # dx/dy backwards!
        axisN = axis.normalized()
        # find the rotation center point @ the current rotation
        gl.glPushMatrix()
        gl.glTranslatef(*[x for x in self.rotCenter])
        m = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        gl.glPopMatrix()
        gl.glLoadIdentity()
        # now shift/rotate/unshift and mulitiply
        gl.glTranslatef(m[3][0], m[3][1], m[3][2])
        gl.glRotate(self.rotFactor * axis.length(),
                     axisN.x(), axisN.y(), axisN.z())
        gl.glTranslatef(-m[3][0], -m[3][1], -m[3][2])
        gl.glMultMatrixf(self.modelviewMatrix)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
    def pan(self, dx, dy):
        """Shift the scene origin by dx/dy pixels
        """
        pw, ph = self.pixelSize(gl.glGetFloat(gl.GL_PROJECTION_MATRIX))
        self.sceneCenter[0] -= pw * dx
        self.sceneCenter[1] += ph * dy
        self.ortho()
    # TODO: buggy, the margin is not always consistent
    def fit(self, p1, p2, pad=10):
        """Fit the rectangle define by the two points into the scene.

        p1, p2 -- rectangle opposite sides
        pad -- margin in pixels
        """
        margin = self.pixelSize(gl.glGetFloat(gl.GL_PROJECTION_MATRIX))[0] \
                      * pad
        x1 = p1.x()
        y1 = p1.y()
        x2 = p2.x()
        y2 = p2.y()
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        if w == 0 or h == 0:
            return
        self.sceneCenter = [(x1 + x2) * 0.5, (y1 + y2) * 0.5]
        if float(w) / h >= self.aspect:
            self.sceneHeight = w / self.aspect + margin * 2.0
        else:
            self.sceneHeight = margin * 2.0 + h
        self.ortho()
    def mouseMoveEvent(self, e):
        """Left button rotate, middle button pan
        """
        if e.buttons() & qt.LeftButton:
            delta = e.pos() - self.lastMousePos
            self.rotate(delta.x(), delta.y())
            self.updateGL()
        if e.buttons() & qt.MiddleButton:
            delta = e.pos() - self.lastMousePos
            self.pan(delta.x(), delta.y())
            self.updateGL()
        self.lastMousePos = e.pos()
    def wheelEvent(self, e):
        """Zoom in/out.

        If zooming in, shift the coordinate under the mouse towards the center
        of the scene.
        """
        if e.delta() > 0:
            # zoom in and shift what's under the mouse towards the center of
            # the screen
            w = self.width()
            h = self.height()
            d = e.pos() - QPoint(w / 2, h / 2)
            dx = d.x() / float(w * 5)
            dy = -d.y() / float(h * 5)
            sw = self.sceneWidth * 0.9
            if sw < self.minZoom:
                return
            self.sceneWidth = sw
            self.sceneHeight *= 0.9
            cx, cy = self.sceneCenter
            self.sceneCenter = [cx + dx * self.sceneWidth,
                                cy + dy * self.sceneHeight]
        else:
            # zoom out with no shift
            sw = self.sceneHeight * 1.2
            if sw > self.maxZoom:
                return
            self.sceneWidth = sw
            self.sceneHeight *= 1.2
        self.ortho()
        self.updateGL()
