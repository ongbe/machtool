#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""tooldefwidget.py

Thursday, August  8 2013
"""

import os
import re
import json

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt as qt

from tooldefscene import ToolDefScene
from tooldefview import ToolDefView
from tooldef import *
from mesh import RevolvedMesh

# ToolDef class to tool category
TDEF2CAT = {DrillDef: 'Twist Drill',
            EndMillDef: 'Flat End Mill',
            WoodruffMillDef: 'Woodruff Keyseat Cutter',
            RadiusMillDef: 'Corner Rounding Mill',
            SpotDrillDef: 'Spot Drill',
            BallMillDef: 'Ball End Mill',
            CenterDrillDef: 'Center Drill',
            BullMillDef: 'Bull End Mill',
            TaperEndMillDef: 'Taper End Mill',
            TaperBallMillDef: 'Taper Ball End Mill',
            DovetailMillDef: 'Dovetail End Mill'}
# Tool category to ToolDef class
CAT2TDEF = dict([(v, k) for k,v in TDEF2CAT.iteritems()])


# http://stackoverflow.com/questions/11335602/
class TreeToolItem(QTreeWidgetItem):
    """Tree item sortable by settable column data
    """
    def __init__(self, *args):
        super(TreeToolItem, self).__init__(*args)
        self._sortData = {}
    def __lt__(self, other):
        if (not isinstance(other, TreeToolItem)):
            return super(TreeToolItem, self).__lt__(other)
        tree = self.treeWidget()
        if (not tree):
            column = 0
        else:
            column = tree.sortColumn()
        return self.sortData(column) < other.sortData(column)
    def sortData(self, column):
        return self._sortData.get(column, self.text(column))
    def setSortData(self, column, data):
        self._sortData[column] = data
        

class ToolBrowserView(QTreeWidget):
    """Select a library and tool to load.
    """
    def __init__(self, parent=None):
        super(ToolBrowserView, self).__init__(parent)
        self.setColumnCount(1)
        self.header().close()
        self.hide()
        self.setStyleSheet("QTreeView { background-color: #ddffdd; }")
        self.setSortingEnabled(True)
        self.sortItems(0, qt.AscendingOrder)
        # current lib has changed but not been saved
        self.dirty = False
        # Directory of last loaded tool lib. The open file dialog will always
        # open in this dir.
        self.lastDir = "."
        # name of the currently loaded tool lib
        self.libFileName = None
        # data read from JSON tool lib
        self.toolMap = {}
        self.readToolLib("./tools.json")
    def isDirty(self):
        return self.dirty
    def getToolData(self, item):
        """Find the category and spec map for the given item.

        item -- QTreeWidget, a tool in the tree

        Return [category as string, tool specs as map]
        """
        toolName = item.text(0)
        for category, tools in self.toolMap.iteritems():
            for toolSpecs in tools:
                if toolSpecs['name'] == toolName:
                    return [category, toolSpecs]
    def sizeHint(self):
        return QSize(300, 900)
    def openToolLib(self):
        """Show an open file dialog. Load the library selected.
        """
        fname = str(QFileDialog.getOpenFileName(self, 'Open machtool Library',
                                                self.lastDir,
                                                'JSON files (*.json)'))
        if fname:
            self.libFileName = fname
            self.lastDir = os.path.abspath(fname)
            self.readToolLib(fname)
    def saveToolLib(self):
        """Show a save file dialog. Write to the file selected.
        """
        fname = QFileDialog.getSaveFileName(self, "Save machtool Library",
                                            self.libFileName,
                                            'JSON file (*.json)')
        if fname:
            self.writeToolLib(fname)
    def readToolLib(self, fileName):
        """Read and load the tool library.

        fileName -- string, file name to read
        """
        self.libFileName = fileName
        f = open(fileName, 'r')
        self.toolMap = json.load(f)
        f.close()
        self.clear()
        for k, v in self.toolMap.iteritems():
            catItem = TreeToolItem([k], 2000)
            for m in v:
                item = TreeToolItem(catItem, [m['name']], 3000)
                sortVal = m[CAT2TDEF[k].getSortKey()]
                # convert metric to inch for tree sorting
                item.setSortData(0, sortVal / 25.4
                                 if m['metric'] else sortVal)
            self.addTopLevelItem(catItem)
        self.dirty = False
    def writeToolLib(self, fileName=None):
        """Write the current library to a file.

        fileName -- string, if None, use the name of the currently loaded lib
        """
        f = open(fileName or self.libFileName, 'w')
        json.dump(self.toolMap, f, indent=1)
        f.close()
        self.dirty = False
    def keyPressEvent(self, e):
        if e.key() == qt.Key_Escape:
            self.parent().showToolDefView()
        super(ToolBrowserView, self).keyPressEvent(e)
    def addTool(self, toolDef):
        # first see if we're going to modify an existing tool
        curItem = self.currentItem()
        newToolName = toolDef.name()
        catItem = curItem.parent()
        if self.currentItem().text(0) == newToolName:
            result = QMessageBox.question(self,
                                          'machtool',
                                          '"{}" already exists, overwrite?' \
                                              .format(newToolName),
                                          QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.No:
                return False
            # Update the existing tool. Just need to update toolMap since the
            # tree just holds the comment string (which hasn't changed).
            for tool in self.toolMap[unicode(catItem.text(0))]:
                if tool['name'] == newToolName:
                    tool.update(toolDef.specs)
                    break
            self.dirty = True
            return True
        # add a new tool
        # add to the tree view
        newItem = QTreeWidgetItem(catItem, [newToolName], 3000)
        catItem.addChild(newItem)
        # add to the tool map
        self.toolMap[unicode(catItem.text(0))].append(toolDef.specs)
        self.dirty = True
        return True


class ToolDefWidget(QWidget):
    """Define and edit tools

    Load Button
      Show a QTreeView from which the user can select a tool
    Save Button
      Show the same QTreeView, but allow saving the current tool
    Metric CheckBox
      Toggle the current tool's units.
    Tool Definition View
      Display the profile of the current tool along with editable dimensions.
    Tool Browser View
      A QTreeView to display all available tools. When a tool is clicked, the
      tool def view is shown with that tool loaded. If Escape is pressed, the
      tool def view is shown with no change.
    """
    def __init__(self, parent=None):
        super(ToolDefWidget, self).__init__(parent)
        # the active tool def
        self.toolDef = None
        # library load/save layout
        libSaveLayout = QHBoxLayout()
        self.openLibButton = QPushButton("Open Lib", self)
        self.connect(self.openLibButton, SIGNAL("clicked()"),
                     self.openToolLib)
        libSaveLayout.addWidget(self.openLibButton)
        self.saveLibButton = QPushButton("Save Lib", self)
        self.connect(self.saveLibButton, SIGNAL("clicked()"),
                     self.saveToolLib)
        libSaveLayout.addWidget(self.saveLibButton)
        libSaveLayout.insertStretch(2, 1)
        # tool load/save metric layout
        toolSaveLayout = QHBoxLayout()
        self.loadToolButton = QPushButton("Load Tool", self)
        self.connect(self.loadToolButton, SIGNAL("clicked()"),
                     self.showToolBrowserView)
        toolSaveLayout.addWidget(self.loadToolButton)
        # Button will be disable if current tool has not been modified
        self.saveToolButton = QPushButton("Save Tool", self)
        self.connect(self.saveToolButton, SIGNAL("clicked()"),
                     self.saveCurrentTool)
        toolSaveLayout.addWidget(self.saveToolButton)
        toolSaveLayout.insertStretch(2, 1)
        self.metricCheckBox = QCheckBox("Metric", self)
        self.metricCheckBox.setChecked(False)
        self.connect(self.metricCheckBox, SIGNAL("toggled(bool)"),
                     self.onMetricToggle)
        toolSaveLayout.addWidget(self.metricCheckBox)
        # vlayout
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setContentsMargins(3, 3, 3, 3)
        self.vLayout.addLayout(toolSaveLayout)
        self.vLayout.addLayout(libSaveLayout)
        self.tdefScene = ToolDefScene()
        self.tdefView = ToolDefView(self.tdefScene, self)
        self.connect(self.tdefView.dimBox, SIGNAL("returnPressed()"),
                     lambda box=self.tdefView.dimBox:
                         self.onEditBoxReturn(box))
        self.connect(self.tdefView.commentBox, SIGNAL("returnPressed()"),
                     lambda box=self.tdefView.commentBox:
                         self.onEditBoxReturn(box))
        self.vLayout.addWidget(self.tdefView)
        # tool browser
        self.toolBrowser = ToolBrowserView()
        self.connect(self.toolBrowser,
                     SIGNAL('itemClicked(QTreeWidgetItem*, int)'),
                     self.loadTool)
        self.showToolBrowserView()
    def loadTool(self, item):
        """Load a tool into the ToolDefView.

        item -- a QTreeWidgetItem
        
        Called when the user clicks a tool in the ToolBrowserView.
        """
        if not item.parent():
            return              # category clicked
        category, specs = self.toolBrowser.getToolData(item)
        if self.toolDef:
            self.tdefScene.removeItem(self.toolDef)
        self.toolDef = CAT2TDEF[category](specs)
        self.tdefScene.addItem(self.toolDef)
        self.toolDef.config(specs)
        self.showToolDefView()
        mesh = RevolvedMesh(self.toolDef.profile())
        # TODO: signals/slots
        self.parent().parent().meshview.setMesh(mesh)
        self.parent().parent().meshview.frontView()
    def showToolBrowserView(self):
        """Replace the ToolDefView with the ToolBrowserView
        
        loading -- True if loading a tool, False if saving a tool
        """
        if self.toolBrowser.isVisible():
            return
        if self.toolDef and self.toolDef.isDirty():
            result = QMessageBox.question(self,
                                          "machtool",
                                          "The tool was modified. Save it?",
                                          QMessageBox.Yes | QMessageBox.No
                                          | QMessageBox.Cancel)
            if result == QMessageBox.Yes:
                self.saveCurrentTool()
            elif result == QMessageBox.Cancel:
                return
        self.openLibButton.show()
        self.saveLibButton.show()
        self.saveLibButton.setEnabled(self.toolBrowser.isDirty())
        self.metricCheckBox.hide()
        self.loadToolButton.hide()
        self.saveToolButton.hide()
        self.tdefView.hide()
        self.tdefView.dimBox.hide()
        self.tdefView.commentBox.hide()
        self.vLayout.removeWidget(self.tdefView)
        self.vLayout.addWidget(self.toolBrowser)
        self.toolBrowser.show()
        self.toolBrowser.setFocus()
    def showToolDefView(self):
        """Replace the ToolBrowserView with the ToolDefView
        """
        if self.tdefView.isVisible():
            return
        self.loadToolButton.setEnabled(True)
        self.saveToolButton.setEnabled(False)
        self.metricCheckBox.setEnabled(True)
        self.openLibButton.hide()
        self.saveLibButton.hide()
        self.metricCheckBox.show()
        self.loadToolButton.show()
        self.saveToolButton.show()
        self.toolBrowser.hide()
        self.vLayout.removeWidget(self.toolBrowser)
        # this will trigger a resize event which will trigger a fitAll
        self.vLayout.addWidget(self.tdefView)
        self.tdefView.show()
        self.tdefView.setFocus()
        self.metricCheckBox.setChecked(self.toolDef.isMetric())
    def onMetricToggle(self, state):
        self.toolDef.config({'metric': state})
        self.tdefView.fitAll()
        self.saveToolButton.setEnabled(self.toolDef.isDirty())
    def onEditBoxReturn(self, box):
        """Update the tool's dimension or comment and fit it.

        box -- the EditBox the user just updated
        """
        box.hide()
        self.toolDef.config({str(box.item.toolTip()): box.textValue()})
        self.tdefView.setFocus()
        self.tdefView.fitAll()
        self.saveToolButton.setEnabled(self.toolDef.isDirty())
        mesh = RevolvedMesh(self.toolDef.profile())
        # TODO: signals/slots
        self.parent().parent().meshview.setMesh(mesh)
        self.parent().parent().meshview.updateGL()
    def saveCurrentTool(self):
        result = self.toolBrowser.addTool(self.toolDef)
        if result:
            self.toolDef.setDirty(False)
            self.saveToolButton.setEnabled(False)
    def openToolLib(self):
        if self.toolBrowser.isDirty():
            result = QMessageBox.question(self,
                                          "machtool",
                                          'The current tool library has been'
                                          ' modified. Save it?',
                                          QMessageBox.Yes | QMessageBox.No
                                          | QMessageBox.Cancel)
            if result == QMessageBox.Yes:
                self.saveToolLib()
                self.saveToolButton.setEnabled(False)
            elif result == QMessageBox.Cancel:
                return
        self.toolBrowser.openToolLib()
    def saveToolLib(self):
        self.toolBrowser.writeToolLib()
        self.saveToolButton.setEnabled(False)
    def minimumSizeHint(self):
        return QSize(300, 300)
