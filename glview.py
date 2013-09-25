#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""glview.py

Saturday, September 14 2013
"""

from copy import copy
from math import sqrt

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtCore import Qt as qt
from PyQt4.QtOpenGL import *
import OpenGL.GL as gl
import OpenGL.GLU as glu
import numpy as np

class GLView(QGLWidget):
    """An OpenGL viewer with pan/rotate/zoom + fixed orientation views.

                                top
                                 |
                                 V     back
                                       /
                                      /
                                 Y+ |/
                                 |  
                                 | 
                                 |
                left ->          o------- X+        <- right
                                /
                               /
                              Z+ (out of screen)

                           /|
                          /     ^
                         /      |
                       front  bottom
                           
    A single light is provided at the fixed point (50, 50, 170).

    A basic xyz axis indicator is rendered in a seperate viewport in the lower
    left corner. red=X+, green=Y+, blue=Z+.

    A fit method is supplied. The two [x, y] points define the corners of
    the rectangle to fit. The coordinates should be relative to the default
    X/Y plane.

    Default Behavior
    ================
    * Initial view orientation is the default OpenGL X/Y plane. This is the
      'front' view.
    * Mouse wheel zooms in (with shift) and out (with no shift).
    * Left button rotates the scene about rotCenter.
    * Middle button pans the scene.
    * Arrows rotate the scene about the vertical and horizontal axes.
      GLView.arrowRotationStep defaults to 15 degrees.
      Alt+Left/Right arrow to rotate about the screen Z axis.
    * Visible scene is 10x10 units with the origin at the center.

    Default Context Menu
    ====================
    * Top, Bottom, Left, Right, Front, Back, and Isometric views can be
      selected.
    """
    # up, down, left, right arrow key rotation amount
    arrowRotationStep = 15.0
    # Length of one leg of the axis indicator. The subwindow's scene size
    # will be twice this.
    axisLen = 5.0
    def __init__(self, parent):
        super(GLView, self).__init__(parent)
        self.rotCenter = [0.0, 0.0, 0.0]
        self.modelviewMatrix = np.identity(4)
        self.sceneCenter = [0.0, 0.0]
        self.sceneWidth = 10.0
        self.sceneHeight = 10.0
        self.aspect = 1.0
        self.rotFactor = 0.75
        self.lastMousePos = QPoint()
        self.minZoom = 0.01
        self.maxZoom = 100.0
        self.setMouseTracking(True)
        self.createContextMenu()
    def setRotCenter(self, p):
        self.rotCenter = p
    # TODO: too lazy
    def createContextMenu(self):
        self.setContextMenuPolicy(qt.ActionsContextMenu)
        for item in ['Front', 'Top', 'Right', 'Back', 'Bottom', 'Left', 
                     'Isometric']:
            a = QAction(item, self)
            eval('self.connect(a, SIGNAL("triggered()"),'
                 'self.{}View)'.format(item.lower()))
            self.addAction(a)
    def initializeGL(self):
        gl.glClearColor(0.0, 0.25, 0.25, 1.0)
        gl.glFrontFace(gl.GL_CCW) # default
        gl.glCullFace(gl.GL_BACK)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, [50, 50, 170])
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, [0.5, 0.5, 1.0, 1.0])
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, [0.3, 0.3, 1.0, 0.5])
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        self.buildAxisIndicator()
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
    def screenToScene(self, x, y):
        """Find the scene coordinates of the pixel.

        x, y -- pixel coordinates

        Return (x, y)
        """
        pw, ph = self.pixelSize(gl.glGetFloat(gl.GL_PROJECTION_MATRIX))
        return (self.sceneCenter[0] - self.sceneWidth * 0.5 + pw * x,
                self.sceneCenter[1] + self.sceneHeight * 0.5 + ph * -y)
    def ortho(self):
        """Set up the scene's visible bounds.
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
    def buildAxisIndicator(self):
        """Assemble the axis indicator into a display list.
        """
        # single axis specs
        bodyLen = GLView.axisLen * 0.75
        tipLen = GLView.axisLen * 0.25
        majDia = GLView.axisLen * 0.125
        slices = 8
        stacks = 2
        # build one axis
        axisId = gl.glGenLists(1)
        quadric = glu.gluNewQuadric()
        gl.glNewList(axisId, gl.GL_COMPILE)
        glu.gluCylinder(quadric, 0.0, majDia, bodyLen, slices, stacks)
        gl.glPushMatrix()
        gl.glTranslate(0, 0, bodyLen)
        glu.gluCylinder(quadric, majDia, 0, tipLen, slices, stacks)
        gl.glPopMatrix()
        gl.glEndList()
        # now assemble all three
        self.axisIndicatorId = gl.glGenLists(1)
        gl.glNewList(self.axisIndicatorId, gl.GL_COMPILE)
        # always lit and smooth shaded with a bit a spec
        gl.glEnable(gl.GL_LIGHTING)
        gl.glPolygonMode(gl.GL_FRONT, gl.GL_FILL)
        gl.glShadeModel(gl.GL_SMOOTH)
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR,
                        [1.0, 1.0, 1.0, 1.0])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, 64)
        # X axis, red
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE,
                        [0.7, 0.0, 0.0, 1.0])
        gl.glPushMatrix()
        gl.glRotate(90, 0, 1, 0)
        gl.glCallList(axisId)
        gl.glPopMatrix()
        # Y axis, green
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE,
                        [0.0, 0.7, 0.0, 1.0])
        gl.glPushMatrix()
        gl.glRotate(-90, 1, 0, 0)
        gl.glCallList(axisId)
        gl.glPopMatrix()
        # Z axis, blue
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE,
                        [0.0, 0.0, 0.7, 1.0])
        gl.glCallList(axisId)
        gl.glEndList()
    def renderAxisIndicator(self):
        """Render an axis orientation aid.

        A small square viewport is created in the lower left corner of the
        view to render into.
        """
        # 1/8 the view width with a minimum of 100 pixels.
        viewportSize = max(self.width() / 8, 100)
        gl.glViewport(0, 0, viewportSize, viewportSize)
        # Set up an orthographic projection whoes size depends on the size of
        # the axis indicator.
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        # TODO: understand the near/far clip plane vs the depth buffer
        gl.glOrtho(-GLView.axisLen, GLView.axisLen,
                    -GLView.axisLen, GLView.axisLen,
                    -10000.0 - GLView.axisLen, .0)
        # now render into that viewport
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        # Move the indicators origin far away from the origin. This is the
        # only way I know to keep the mesh from clipping it. Probably need
        # some sort of overlay buffer.
        gl.glTranslatef(0.0, 0.0, 10000.0)
        # only need the rotation of the global matrix, no translation
        m = copy(self.modelviewMatrix)
        m[3] = [0.0, 0.0, 0.0, 1.0]
        gl.glMultMatrixf(m)
        # render the indicator
        gl.glCallList(self.axisIndicatorId)
        # pop the global modelview
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        # pop the main viewports projection matrix
        gl.glPopMatrix()
        # after these two, we should be back where we started, maybe!
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glViewport(0, 0, self.width(), self.height())
    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self.renderAxisIndicator()
    def frontView(self, update=True):
        """Rotate to view the X/Y plane.
        """
        gl.glLoadIdentity()
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def backView(self, update=True):
        """Rotate to view the -X/Y plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(180.0, 0.0, 1.0, 0.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def rightView(self, update=True):
        """Rotate to view the -Z/Y plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(-90.0, 0.0, 1.0, 0.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def leftView(self, update=True):
        """Rotate to view the Z/Y plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(90.0, 0.0, 1.0, 0.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def topView(self, update=True):
        """Rotate to view the X/Z- plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(90.0, 1.0, 0.0, 0.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def bottomView(self, update=True):
        """Rotate to view the -X/Z plane.
        """
        gl.glLoadIdentity()
        gl.glRotate(-90.0, 1.0, 0.0, 0.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    # TODO: Not sure if this is 100% accurate, but it's close enough.
    def isometricView(self, update=True):
        """Rotate to an isometric view.

        +Y up, +X right, +Z forward

        """
        gl.glLoadIdentity()
        gl.glRotate(30.0, 1.0, 0.0, 0.0)
        gl.glRotate(-45.0, 0.0, 1.0, 0.0)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        if update:
            self.updateGL()
    def mouseRotate(self, dx, dy):
        """Rotate the scene about the current focal point (self.rotCenter).

        dx, dy -- mouse deltas
        """
        # NUMPY: delta magnitude
        self.rotateScene([dy, dx, 0],
                         self.rotFactor * np.linalg.norm([dx, dy]))
    def rotateScene(self, axis, angle):
        """Apply the scene-relative rotation to the model view matrix.

        axis -- [i, j, k], doesn't have to be normalized
        angle -- signed degrees

        Y+ is up, X+ is right
        """
        # find the rotation center point @ the current rotation
        gl.glPushMatrix()
        gl.glTranslatef(*self.rotCenter)
        m = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        gl.glPopMatrix()
        gl.glLoadIdentity()
        # now shift/rotate/unshift and mulitiply
        gl.glTranslatef(*m[3,:3]) # NUMPY: indexing
        gl.glRotate(angle, *axis)
        gl.glTranslatef(*(m[3,:3] * -1.0))
        # gl.glTranslatef(-m[3, 0], -m[3, 1], -m[3, 2]) # NUMPY: indexing
        gl.glMultMatrixf(self.modelviewMatrix)
        self.modelviewMatrix = gl.glGetFloat(gl.GL_MODELVIEW_MATRIX)
        # self.updateGL()
    def pan(self, dx, dy):
        """Shift the scene origin by dx/dy pixels.

        dx, dy -- mouse deltas in pixels
        """
        pw, ph = self.pixelSize(gl.glGetFloat(gl.GL_PROJECTION_MATRIX))
        self.sceneCenter[0] -= pw * dx
        self.sceneCenter[1] -= ph * -dy
        self.ortho()
        self.updateGL()
    def fit(self, p1, p2, pad=True):
        """Fit the rectangle define by the two points into the scene.

        p1, p2 -- [x, y], rectangle opposite sides
        pad -- if True, include a 2% outside margin
        """
        x1 = p1[0]
        y1 = p1[1]
        x2 = p2[0]
        y2 = p2[1]
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
        self.updateGL()
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
        about the vertical or horizontal axes and, if the Alt key is pressed,
        rotate about the axis perpendicular to the screen.
        """
        # OpenGL defaults to Y+ up, so (0, 1, 0) is the vertical axis
        if e.modifiers() == qt.AltModifier:
            if e.key() == qt.Key_Left:
                self.rotateScene((0, 0, 1), self.arrowRotationStep)
                self.updateGL()
            elif e.key() == qt.Key_Right:
                self.rotateScene([0, 0, 1], -self.arrowRotationStep)
                self.updateGL()
            else:
                super(GLView, self).keyPressEvent(e)
        elif e.key() == qt.Key_Left:
            self.rotateScene([0, 1, 0], -self.arrowRotationStep)
            self.updateGL()
        elif e.key() == qt.Key_Right:
            self.rotateScene([0, 1, 0], self.arrowRotationStep)
            self.updateGL()
        elif e.key() == qt.Key_Up:
            self.rotateScene([1, 0, 0], -self.arrowRotationStep)
            self.updateGL()
        elif e.key() == qt.Key_Down:
            self.rotateScene([1, 0, 0], self.arrowRotationStep)
            self.updateGL()
        else:
            super(GLView, self).keyPressEvent(e)
