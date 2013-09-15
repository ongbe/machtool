#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""mesh.py

Sunday, September 15 2013
"""

# from PyQt4.QtOpenGL import *
from OpenGL.GL import *

class Mesh():
    def __init__():
        self.faces = []
        self.indices = []
        self.normals = []
    def loadArrays(self):
        glVertexPointer(3, GL_FLOAT, 0, self.vertices)
        glNormalPointer(GL_FLOAT, 0, self.normals)

