#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""machtool.py

Tuesday, September 10 2013
"""

import sys
from PyQt4.QtGui import QApplication, QFontDatabase
from tooldefwidget import ToolDefWidget

if __name__ == '__main__':
    app = QApplication(sys.argv)
    fontDb = QFontDatabase()
    fontDb.addApplicationFont(":/fonts/Simplex.ttf")
    tdw = ToolDefWidget()
    tdw.show()
    app.exec_()
    
    
    
    
