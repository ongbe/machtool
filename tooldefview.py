#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""tooldefview.py

Thursday, August  8 2013
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt as qt

from dimedit import DimEdit, CommentEdit
from dimension import DimText
from tooldef import ToolDef, CommentText


class ToolDefView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super(ToolDefView, self).__init__(parent)
        self.setStyleSheet("QGraphicsView { background-color: #ddddff; }")
        self.setRenderHints(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setScene(scene)
        src = self.sceneRect().center()
        # Cartesian coord sys w/origin at the center of the scene rect
        self.setTransform(QTransform().scale(1, -1) \
                              .translate(src.x(), src.y()))
        # for dimension
        self.dimBox = DimEdit(self)
        self.dimBox.hide()
        # for comment
        self.commentBox = CommentEdit(self)
        self.commentBox.hide()
        self.fitInView(QRectF(-.5, -.5, 1.0, 1.0), qt.KeepAspectRatio)
    def sizeHint(self):
        return QSize(300, 900)
    def updatePixelSize(self):
        sz = self.mapToScene(QRect(0, 0, 1, 1)).boundingRect().width()
        self.scene().pixelSize = sz
        return sz
    def fitAll(self):
        """Fit tool profile and dimensions into the view.

        Because the dimension labels do not scale, a half-assed iterative
        approach is used to position and fit them.
        """
        items = self.scene().items()
        ps = self.updatePixelSize()
        iters = 1
        while True:
            r = QRectF()
            for item in items:
                if not item.parentItem():
                    r = r.united(item.sceneBoundingRect())
            self.fitInView(r, qt.KeepAspectRatio)
            pps = self.updatePixelSize()
            for item in items:
                if isinstance(item, ToolDef):
                    item.config()
            if iters == 10 or abs(ps - pps) < 0.0001:
                break
            ps = pps
            iters += 1
    def resizeEvent(self, e):
        super(ToolDefView, self).resizeEvent(e)
        self.fitAll()
        if self.dimBox.isVisible():
            self.posEditBox(self.dimBox)
        elif self.commentBox.isVisible():
            self.posEditBox(self.commentBox)
    def posEditBox(self, box):
        """Ensure the dimension edit text box is not clipped if possible.

        If both the left and right sides are clipped, it's just centered over
        the dim as if it were not clipped.
        """
        item = box.item
        viewpos = self.mapFromScene(item.pos())
        sz = box.size()
        lclip = min(0, viewpos.x() - sz.width() / 2.0)
        rclip = max(0, viewpos.x() + sz.width() / 2.0 - self.width())
        if lclip and rclip or not lclip and not rclip:
            box.move(viewpos.x() - sz.width() / 2,
                     viewpos.y() - sz.height() / 2)
        elif lclip:
            box.move(viewpos.x() - sz.width() / 2 - lclip,
                     viewpos.y() - sz.height() / 2)
        elif rclip:
            box.move(viewpos.x() - sz.width() / 2 - rclip,
                     viewpos.y() - sz.height() / 2)
    def mousePressEvent(self, e):
        """Handle Dimension selection.
        
        When a dimension is clicked, an associated line edit box is shown and
        given focus. If one is already visible and the mouse is clicked on
        anything except another dimension text, the line edit is hidden.
        """
        item = self.itemAt(e.pos())
        self.commentBox.hide()
        self.dimBox.hide()
        if item and isinstance(item, (DimText, CommentText)):
            if isinstance(item, DimText):
                box = self.dimBox
            elif isinstance(item, CommentText):
                box = self.commentBox
            box.setItem(item)
            box.setText(item.text())
            box.selectAll()
            box.show()
            self.posEditBox(box)
            box.setFocus()
    # def mouseMoveEvent(self, e):
    #     print self.mapToScene(e.pos())
    def wheelEvent(self, e):
        e.accept()              # eat it so the scene does not scroll
    
