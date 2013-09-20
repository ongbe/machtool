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
from mesh import RevolvedMesh


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
        mesh = RevolvedMesh()
        mesh.addProfile(cprof)
        mesh.addProfile(sprof, (0.5, 0.5, 0.5, 1.0))
        self.meshview.setMesh(mesh)
        self.meshview.fitMesh()
    def toolLoaded(self):
        """The user loaded a tool.
        """
        tdef = self.tdefWidget.toolDef
        sprof = tdef.shankProfile()
        cprof = tdef.cutterProfile()
        mesh = RevolvedMesh()
        mesh.addProfile(cprof)
        mesh.addProfile(sprof, (0.5, 0.5, 0.5, 1.0))
        self.meshview.setMesh(mesh)
        self.meshview.frontView()
    def closeEvent(self, e):
        toolBrowser = self.tdefWidget.toolBrowser
        if toolBrowser.isDirty():
            toolBrowser.saveToolMap()
        e.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    fontDb = QFontDatabase()
    fontDb.addApplicationFont(":/fonts/Simplex.ttf")
    mainwin = MainWindow()
    mainwin.show()
    # tdw = ToolDefWidget()
    # tdw.show()
    app.exec_()
