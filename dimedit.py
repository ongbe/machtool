#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""dimedit.py

QLineEdit specialized for editing dimension values.

Friday, August 30 2013
"""

# So the user can enter fractions and get a float back.
# 1/2 will evaluate to 0.5 instead of 0.
from __future__ import division

import re
from math import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt as qt

# shorter names for user
deg = degrees
rad = radians

sandboxFns = dict([(k, locals()[k]) for k in
                   'acos asin atan atan2 ceil cos deg degrees e exp fabs floor'
                   ' fmod hypot log log10 modf pi pow rad radians sin sqrt tan'
                   ' trunc'.split()])


class DimEditException(Exception):
    pass


class Validator(QValidator):
    def __init__(self, parent):
        super(Validator, self).__init__(parent)
        self.editBox = parent
        self.result = None      # invalid input
        

class DimValidator(Validator):
    def validate(self, text, pos):
        """Validate the user's input.

        text -- QString, input text
        pos -- cursor position

        This validator always returns success and does not modify the cursor
        position or input text.
        
        Its purpose is to modify the associated DimEdit's colors to inform the
        user of the validity of his/her input. It also stores the result of
        the expression (None if invalid) so DimEdit can check it when
        Return/Enter is pressed.
        """
        try:
            self.result = eval(str(text), {'__builtins__': None}, sandboxFns)
        except Exception:
            # the expression failed to evaluate, for what ever reason
            self.result = None
            self.editBox.setInvalidStyleSheet()
        else:
            # eval was ok, now check if it's a number > 0.0 and will not
            # result in invalid geometry.
            toolTip = str(self.editBox.item.toolTip()) # str, not QString
            toolDef = self.editBox.parent().parent().toolDef
            if (isinstance(self.result, (int, float))
                and self.result > 0.0
                and toolDef.checkGeometry({toolTip: self.result})):
                self.editBox.setValidStyleSheet()
            else:
                self.result = None
                self.editBox.setInvalidStyleSheet()
        return (2, pos)

class CommentValidator(Validator):
    def validate(self, text, pos):
        """Validate the user's input.

        text -- QString, input text
        pos -- cursor position

        This validator always returns success and does not modify the cursor
        position or input text.
        
        Its purpose is to modify the associated CommentEdit's colors to inform
        the user of the validity of his/her input. It also stores the result
        of the expression (None if invalid) so DimEdit can check it when
        Return/Enter is pressed.
        """
        if len(text) == 0:
            self.result = None
            self.editBox.setInvalidStyleSheet()
        else:
            self.result = str(text)
            self.editBox.setValidStyleSheet()
        return (2, pos)


class EditBox(QLineEdit):
    """A QLineEdit for modifying tool dimensions and comment text
    """
    validSS = 'QLineEdit { background-color: #aaffaa; color: #000000;' \
        ' selection-color: #000000; selection-background-color: #00ff00; }'
    invalidSS = 'QLineEdit { background-color: #ffaaaa; color: #000000;' \
        ' selection-color: #000000; selection-background-color: #ff0000; }'
    def setItem(self, item):
        """Set the associated DimText item
        """
        self.item = item
    def setValidStyleSheet(self):
        """Called from the validator
        """
        self.setStyleSheet(self.validSS)
    def setInvalidStyleSheet(self):
        """Called from the validator
        """
        self.setStyleSheet(self.invalidSS)
    def text(self):
        """Return a string not a QString
        """
        return unicode(super(EditBox, self).text())
    

# TODO:
#   * Dimension names other than the one being edited can be used in the
#     expression. oal, radius, shankDia etc.
class DimEdit(EditBox):
    """A single line edit box for modifying dimensions.

    The text may be a Python expression that evaluates to a number. Most of
    the more common functions in the math module are available.

    If the result of the expression is valid (a number > 0.0 that will not
    result in invalid tool geometry), the widget's background will be greenish
    and the Enter/Return key will work.

    If not, the background will be reddish and the Enter/Return key will do
    nothing.

    The Escape key will hide this widget and set focus to its parent.
    """
    def __init__(self, parent):
        super(DimEdit, self).__init__(parent)
        self.setValidator(DimValidator(self))
        self.setValidStyleSheet()
    def sizeHint(self):
        fm = QFontMetrics(self.font())
        # TODO: not really wide enough to enter an expression, but it looks
        #       goofy if it's really wide
        br = fm.boundingRect('__________')
        return br.adjusted(0, 0, 10, 5).size()
    def setText(self, text):
        """Strip Ø or R prefix, and mm, in, ", or ° suffix before setting.
        """
        mo = re.match(u'[ØR]?((\d+\.\d*)|(\d*\.\d+)|\d+)(mm|°|"|in)?', text)
        if not mo:
            raise DimEditException('invalid dimension text')
        super(DimEdit, self).setText(mo.group(1))
    def textValue(self):
        return float(self.text())
    def text(self):
        """Return a unicode string not a QString
        """
        return unicode(super(DimEdit, self).text())
    def keyPressEvent(self, e):
        """Handle some key presses.

        Enter/Return will not work if the user's input value is
        invalid. Escape will hide this widget and set focus to its parent.

        Everything else is handled by QLineEdit.
        """
        if e.key() in [qt.Key_Return, qt.Key_Enter]:
            if self.validator().result is None:
                return
            self.setText(str(self.validator().result))
        elif e.key() == qt.Key_Escape:
            self.hide()
            self.parent().setFocus()
        super(DimEdit, self).keyPressEvent(e)
        

class CommentEdit(EditBox):
    """A single line edit box for modifying the tool comment string.
    """
    def __init__(self, parent):
        super(CommentEdit, self).__init__(parent)
        self.setValidator(CommentValidator(self))
        self.setValidStyleSheet()
    def textValue(self):
        return self.text()
    def sizeHint(self):
        fm = QFontMetrics(self.font())
        br = fm.boundingRect(self.item.text())
        return br.adjusted(0, 0, 10, 5).size()
    def keyPressEvent(self, e):
        """Handle some key presses.

        Enter/Return will not work if the user's input value is
        invalid. Escape will hide this widget and set focus to its parent.

        Everything else is handled by QLineEdit.
        """
        if e.key() in [qt.Key_Return, qt.Key_Enter]:
            if self.validator().result is None:
                return
            self.setText(str(self.validator().result))
        elif e.key() == qt.Key_Escape:
            self.hide()
            self.parent().setFocus()
        super(CommentEdit, self).keyPressEvent(e)
