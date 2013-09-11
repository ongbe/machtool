#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""tooldefscene.py

Thursday, August  8 2013
"""

from PyQt4.QtCore import QRectF, QRect
from PyQt4.QtGui import QGraphicsScene


class ToolDefScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(ToolDefScene, self).__init__(QRectF(-5000, -5000, 10000, 10000),
                                           parent)
        self.pixelSize = 0.0
    def pixelsToScene(self, n):
        """Return the length of n pixels in scene coordinates.
        """
        view = self.views()[0]
        return view.mapToScene(QRect(0, 0, n, n)).boundingRect().width()
