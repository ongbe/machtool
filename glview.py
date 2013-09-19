#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""glview.py

Saturday, September 14 2013
"""

from math import sqrt

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtCore import Qt as qt
from PyQt4.QtOpenGL import *
import OpenGL.GL as gl
import OpenGL.GLU as glu

class GLView(QGLWidget):
    """An OpenGL viewer with pan/rotate/zoom + fixed orientation views.

    A single light is provided at the fixed point (50, 50, 170).

    A basic xyz axis is rendered at the origin. red=X+, green=Y+, blue=Z+.

    A fit method is supplied. The two [x, y] points define the corners of
    the rectangle to fit. The coordinates should be relative to the default
    X/Y plane.

    Default Behavior
    ================
    * Initial view orientation is the default OpenGL X/Y plane. This is the
      'top' view.
    * Mouse wheel zooms in (with shift) and out (with no shift).
    * Left button rotates the scene about rotCenter.
    * Middle button pans the scene.
    * Arrows rotate the scene about the vertical and horizontal axes.
      GLView.arrowRotationStep defaults to 15 degrees.
    * Visible scene is 10x10 units with the origin at the center.

    Default Context Menu
    ====================
    * Top, Bottom, Left, Right, Front, Back, and Isometric views can be
      selected.
    """
    # up, down, left, right arrow key rotation amount
    arrowRotationStep = 15.0
    def __init__(self, parent):
        super(GLView, self).__init__(parent)
        self.rotCenter = [0.0, 0.0, 0.0]
        self.modelviewMatrix = [[1.0, 0.0, 0.0, 0.0],
                                [0.0, 1.0, 0.0, 0.0],
                                [0.0, 0.0, 1.0, 0.0],
                                [0.0, 0.0, 0.0, 1.0]]
        self.sceneCenter = [0.0, 0.0]
        self.sceneWidth = 10.0
        self.sceneHeight = 10.0
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
        # gl.glShadeModel(gl.GL_FLAT)
        # gl.glEnable(gl.GL_BLEND)
        # gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        # gl.glEnable(gl.GL_MULTISAMPLE)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, [50, 50, 170])
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, [0.5, 0.5, 1.0, 1.0])
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, [0.3, 0.3, 1.0, 0.5])
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        # base class defaults to front view, +X/+Z plane
        self.topView(False)
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
    # TODO: Not sure if this is 100% accurate, but it's close enough.
    def isometricView(self, update=True):
        """Rotate to an isometric view.

        """
        gl.glLoadIdentity()
        gl.glRotate(-60.0, 1.0, 0.0, 0.0)
        gl.glRotate(-45.0, 0.0, 0.0, 1.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def mouseRotate(self, dx, dy):
        """Rotate the scene about the current focal point (self.rotCenter).

        dx, dy -- mouse deltas
        """
        self.rotateScene([dy, dx, 0],
                         self.rotFactor * sqrt(dx*dx + dy*dy))
    def rotateScene(self, axis, angle):
        """Apply the scene-relative rotation to the model view matrix.

        axis -- [i, j, k], doesn't have to be normalized
        angle -- signed degrees

        Y+ is up, X+ is right
        """
        axis = QVector3D(*axis)
        axisN = axis.normalized()
        # find the rotation center point @ the current rotation
        gl.glPushMatrix()
        gl.glTranslatef(*self.rotCenter)
        m = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        gl.glPopMatrix()
        gl.glLoadIdentity()
        # now shift/rotate/unshift and mulitiply
        gl.glTranslatef(m[3][0], m[3][1], m[3][2])
        gl.glRotate(angle, axisN.x(), axisN.y(), axisN.z())
        gl.glTranslatef(-m[3][0], -m[3][1], -m[3][2])
        gl.glMultMatrixf(self.modelviewMatrix)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        self.updateGL()
    def pan(self, dx, dy):
        """Shift the scene origin by dx/dy pixels
        """
        pw, ph = self.pixelSize(gl.glGetFloat(gl.GL_PROJECTION_MATRIX))
        self.sceneCenter[0] -= pw * dx
        self.sceneCenter[1] += ph * dy
        self.ortho()
    def fit(self, p1, p2, pad=True):
        """Fit the rectangle define by the two points into the scene.

        p1, p2 -- rectangle opposite sides
        pad -- if True, include a small outside margin
        """
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
            self.sceneHeight = w / self.aspect
        else:
            self.sceneHeight = h
        if pad:
            self.sceneHeight *= 1.02 # just a little padding
        self.ortho()
    def mouseMoveEvent(self, e):
        """Left button rotate, middle button pan
        """
        if e.buttons() & qt.LeftButton:
            delta = e.pos() - self.lastMousePos
            self.mouseRotate(delta.x(), delta.y())
            self.updateGL()
        if e.buttons() & qt.MiddleButton:
            delta = e.pos() - self.lastMousePos
            self.pan(delta.x(), delta.y())
            self.updateGL()
        self.lastMousePos = e.pos()
    def mousePressEvent(self, e):
        super(QGLWidget, self).mousePressEvent(e)
        self.setFocus()
    def wheelEvent(self, e):
        """Zoom in/out.

        If zooming in, shift the coordinate under the mouse towards the center
        of the scene.
        """
        if e.delta() > 0:
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
            sw = self.sceneHeight * 1.2
            if sw > self.maxZoom:
                return
            self.sceneWidth = sw
            self.sceneHeight *= 1.2
        self.ortho()
        self.updateGL()
    def keyPressEvent(self, e):
        """Handle key press events

        GLView handles the arrow keys and nothing else. They rotate the scene
        about the vertical or horizontal axes.
        """
        # OpenGL defaults to Y+ up, so (0, 1, 0) is the vertical axis
        if e.key() == qt.Key_Left:
            self.rotateScene([0, 1, 0], -self.arrowRotationStep)
        elif e.key() == qt.Key_Right:
            self.rotateScene([0, 1, 0], self.arrowRotationStep)
        elif e.key() == qt.Key_Up:
            self.rotateScene([1, 0, 0], -self.arrowRotationStep)
        elif e.key() == qt.Key_Down:
            self.rotateScene([1, 0, 0], self.arrowRotationStep)
        super(GLView, self).keyPressEvent(e)
