#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""machtool.py

Tuesday, September 10 2013
"""

import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtCore import Qt as qt
from tooldefwidget import ToolDefWidget
from meshview import MeshView

# DEBUG:
from mesh import RevolvedMesh
from path2d import Path2d


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.meshview = MeshView(self)
        self.setCentralWidget(self.meshview)
        self.toolDefDock = QDockWidget("Tools", self)
        self.toolDefDock.setAllowedAreas(qt.RightDockWidgetArea |
                                         qt.LeftDockWidgetArea)
        self.tdefWidget = ToolDefWidget()
        self.toolDefDock.setWidget(self.tdefWidget)
        self.addDockWidget(qt.RightDockWidgetArea, self.toolDefDock)
        # TODO: A little better but noticeable lag. Also need to figure out
        #       how to pass the ToolDef as a param.
        self.connect(self.tdefWidget, SIGNAL('toolModified()'),
                     self.toolModified)
        self.connect(self.tdefWidget, SIGNAL('toolLoaded()'),
                     self.toolLoaded)
    def toolModified(self):
        """The user changed a dimension on the current tool.
        """
        tdef = self.tdefWidget.toolDef
        sprof = tdef.shankProfile()
        cprof = tdef.cutterProfile()
        mesh = RevolvedMesh(cprof)
        mesh.addProfile(sprof, (0.5, 0.5, 0.5, 1.0))
        self.meshview.setMesh(mesh)
        self.meshview.fitMesh()
    def toolLoaded(self):
        """The user loaded a tool.
        """
        tdef = self.tdefWidget.toolDef
        sprof = tdef.shankProfile()
        cprof = tdef.cutterProfile()
        mesh = RevolvedMesh(cprof)
        mesh.addProfile(sprof, (0.5, 0.5, 0.5, 1.0))
        self.meshview.setMesh(mesh)
        self.meshview.frontView()
    def closeEvent(self, e):
        toolBrowser = self.tdefWidget.toolBrowser
        if toolBrowser.isDirty():
            toolBrowser.saveToolMap()
        e.accept()
    def keyPressEvent(self, e):
        # DEBUG:
        from math import sin, cos, radians
        if e.key() == qt.Key_Space:
            mesh = RevolvedMesh()
            p = Path2d([0, 0])
            p.arcTo(1, 1, 0, 1, 'cclw')
            p.arcTo(2, 2, 2, 1, 'clw')
            p.arcTo(3, 3, 2, 3, 'cclw')
            p.lineTo(2, 3.5)
            p.lineTo(1.5, 3.5)
            p.arcTo(1.0, 3., 1.5, 3, 'cclw')
            mesh.addProfile(p.elements(), close=True)
            self.meshview.setMesh(mesh)
            self.meshview.fitMesh()
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    fontDb = QFontDatabase()
    fontDb.addApplicationFont(":/fonts/Simplex.ttf")
    mainwin = MainWindow()
    mainwin.show()
    # tdw = ToolDefWidget()
    # tdw.show()
    app.exec_()
