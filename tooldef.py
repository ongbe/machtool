#!/usr/bin/python -t
# -*- coding: utf-8 -*-

"""tooldef.py

P  -- profile defined
D  -- dimensions defined
S  -- surface defined

PD  BallMillDef
    BottomTapDef
PD  BullMillDef
P   CenterDrillDef   (fixed sizes, no dimensions)
    ChamferMillDef
    CounterBoreDef
    CounterSinkDef
PD  DrillDef
    DovetailMillDef
PD  EndMillDef
    FaceMillDef
    PlugTapDef
PD  RadiusMillDef
    ScribeDef        (engraving tool)
PD  SpotDrillDef
    TaperBallMillDef
    TaperBullMillDef
PD  TaperEndMillDef
    ThreadMillDef
    TSlotMillDef     (different from woodruff)
PD  WoodruffMillDef

Thursday, August  8 2013
"""

from math import degrees, radians, tan, sqrt, atan2, fabs, sin, cos
from copy import copy
from operator import lt, le, eq, ne, ge, gt

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt as qt

from dimension import TextLabel, DimText, LinearDim, RadiusDim, AngleDim
from arc import Arc, arcFromAngles


class CommentText(TextLabel):
    """Display the tool comment
    """
    def __init__(self, *args):
        super(CommentText, self).__init__(*args)
        self.setZValue(100)


class ToolDefException(Exception):
    pass


# TODO: inherit from QGraphicsPathItem
class ToolDef(QGraphicsPathItem):
    centerlinePen = QPen(QBrush(QColor(128, 128, 128)), 0, qt.DashDotLine)
    def __init__(self, specs):
        super(ToolDef, self).__init__()
        self.specs = copy(specs)
        self.checkSpecs()       # call subclasses method
        self.dirty = False
        self.ppath = QPainterPath()
        pen = QPen(QColor(0, 0, 255))
        pen.setWidth(2)         # 2 pixels wide
        pen.setCosmetic(True)   # don't scale line width
        self.setPen(pen)
        self.commentText = CommentText()
        self.commentText.font.setBold(True)
        self.commentText.setToolTip("name")
    def paint(self, painter, option, widget):
        """Draw a centerline.
        """
        tr = self.commentText.sceneBoundingRect()
        sbr = self.sceneBoundingRect()
        offset = tr.height()
        p1 = QPointF(0, -offset)
        p2 = QPointF(0, sbr.height() + offset)
        painter.setPen(self.centerlinePen)
        painter.drawLine(p1, p2)
        super(ToolDef, self).paint(painter, option, widget)
    def name(self):
        return self.commentText.text()
    @staticmethod
    def getSortKey():
        """Return the key used to sort this tool class

        Return a string. This base class returns 'dia'.
        """
        return 'dia'
    def setDirty(self, bDirty=True):
        self.dirty = bDirty
    def _checkSpec(self, specName, t1=None, t2=None, t3=None, enums=None,
                   noneOk=False):
        """Check a single tool spec.

        specName -- string key name
        t1, t2, t3 -- [cmpfn, value] or None
        enums -- list of values, the spec's value must occur in the list
        noneOk -- bool, the spec can be None (but not missing)

        cmpfn must be one found in the operator module:
          lt, le, eq, ne, ge, gt
        The spec's value will be placed on the LHS. tN's value will be palced
        on the RHS. All given must return True.

        Raise ToolDefException if the spec is invalid, else return None.

        Note: This fn is called indirectly from __init__(). It only makes sure
        the spec is present and has a valid value. Use checkGeometry() to
        ensure valid geometry will be created.
        """
        def raiseCmpFail(fn, x, val):
            raise ToolDefException('{} spec test failed: {}({}, {})' \
                                       .format(repr(specName), fn, x,
                                               val))
        if not self.specs.has_key(specName):
            raise ToolDefException('{} is missing from the tool definition'\
                                       .format(repr(specName)))
        x = self.specs[specName]
        if x is None:
            if noneOk:
                return
            else:
                raise ToolDefException("{} may not be None" \
                                           .format(repr(specName)))
        if t1:
            fn, val = t1
            if not fn(x, val):
                raiseCmpFail(fn, x, val)
        if t2:
            fn, val = t2
            if not fn(x, val):
                raiseCmpFail(fn, x, val)
        if t3:
            fn, val = t3
            if not fn(x, val):
                raiseCmpFail(fn, x, val)
        if enums:
            if x not in enums:
                raise ToolDefException('{} must be one of {}' \
                                           .format(repr(specName), enums))
    def checkSpecs(self):
        """Check if all key/val pairs are present and valid.

        Raise ToolDefException if not. This should be called only from
        __init__(). This base class only checks if the 'name' and 'metric'
        specs. Each subclass should call this base class method and validate
        its remaining specs.
        """
        self._checkSpec('name')
        self._checkSpec('metric', enums=[True, False])
    def checkGeometry(self, specs={}):
        """Find if the specs define valid geometry.

        specs -- the specs that were changed

        This is called by the DimEdit validator. Return True if ok, False if
        not. This base class returns True.
        """
        return True
    def _tipLength(self, includedAngle, dia):
        """Return the tip length.

        includedAngle -- tip angle in degrees
        dia -- dia of tip

        Note: This is a general function to find the adjacent side length of a
              right triangle if the opposite side is doubled (dia).
        """
        return dia * 0.5 / tan(radians(includedAngle * 0.5))
    def config(self, specs={}):
        for k,v in specs.iteritems():
            if self.specs[k] != v:
                self.setDirty(True)
                break
        self.specs.update(copy(specs))
    # TODO: The default sceneBoundingRect() will not work because the pen is
    #       cosmetic with a width of 2. Probably still not correct, but it
    #       works ok for now. 
    def sceneBoundingRect(self):
        return self.path().boundingRect()
    def isMetric(self):
        return self.specs.get('metric', False)
    def isDirty(self):
        return self.dirty
    def sceneChange(self, scene):
        """Add/Remove the name label

        Each subclass must call this from its sceneChange() if a label is to
        be show.
        """
        if scene:
            scene.addItem(self.commentText)
        else:
            self.scene().removeItem(self.commentText)
    def itemChange(self, change, value):
        if change == self.ItemSceneChange:
            self.sceneChange(value.toPyObject())
        return super(ToolDef, self).itemChange(change, value)
    def _updateDiaDim(self, dim, p1, p2, dia, ybase, yFactor, metric):
        """Update a tool's diameter dimension.

        dim -- Dimension to update
        p1 -- [x, y], 1st ref point
        p2 -- [x, y], 2nd ref point
        dia -- diameter
        ybase -- y coordinate to offset from, if None use p1's y (p1[1])
        yFactor -- the signed % of the dimension's bbox height to offset
                   from the ref points
        metric -- Is the tool metric? I could just call self.specs['metric']
                  but this way it's only called once in _updateDims() and
                  passed here.
        """
        y = p1[1] if ybase is None else ybase
        tr = dim.dimText.sceneBoundingRect()
        ar = dim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        if tr.width() * 1.1 < dia:
            labelP = QPointF(0.0, y + tr.height() * yFactor)
            if tr.width() * 1.1 + ar.width() * 2.1 < dia:
                outside = False
        # label left of witness lines
        else:
            labelP = QPointF(-p2[0] - tr.width(), y + tr.height() * yFactor)
            if ar.width() * 2.1 < dia:
                outside = False
        dim.config({'value': dia,
                    'ref1': QPointF(*p1),
                    'ref2': QPointF(*p2),
                    'outside': outside,
                    'format': '%.3fmm' if metric else '%.4f"',
                    'pos': labelP})
    def _updateCommentText(self, labelAbove, y, boxHeight):
        """Update the tool's comment label.

        labelAbove -- oal dimension position flag
        y -- largest geometry y coordinate
        boxHeight -- label box height in screen coords
        """
        labelYfactor = 2.0
        if labelAbove:
            labelYfactor = 3.0
        labelP = QPointF(0, y + boxHeight * labelYfactor)
        self.commentText.config({'pos': labelP, 'text': self.specs['name']})
    

class DrillDef(ToolDef):
    """Define a basic drill shape.
    specs:
      name
      shankDia
      dia
      fluteLength  (not including the tip)
      oal          (not including the tip)
      angle        (tip angle included)
      metric       True/False
    """
    def __init__(self, specs):
        super(DrillDef, self).__init__(specs)
        self.angleDim = AngleDim()
        self.angleDim.setToolTip("angle")
        self.shankDiaDim = LinearDim()
        self.shankDiaDim.setToolTip("shankDia")
        self.diaDim = LinearDim()
        self.diaDim.setToolTip("dia")
        self.fluteLenDim = LinearDim()
        self.fluteLenDim.setToolTip("fluteLength")
        self.oalDim = LinearDim()
        self.oalDim.setToolTip("oal")
    def sceneChange(self, scene):
        super(DrillDef, self).sceneChange(scene)
        if scene:
            scene.addItem(self.shankDiaDim)
            scene.addItem(self.diaDim)
            scene.addItem(self.fluteLenDim)      
            scene.addItem(self.oalDim)
            scene.addItem(self.angleDim)
        else:
            self.scene().removeItem(self.shankDiaDim)
            self.scene().removeItem(self.diaDim)
            self.scene().removeItem(self.fluteLenDim)
            self.scene().removeItem(self.oalDim)
            self.scene().removeItem(self.angleDim)
    def config(self, specs={}):
        """Update one or more of the tool's specs.
        """
        super(DrillDef, self).config(specs)
        self.prepareGeometryChange()
        self._update()
    def checkSpecs(self):
        super(DrillDef, self).checkSpecs()
        self._checkSpec('shankDia', [gt, 0.0])
        self._checkSpec('dia', [gt, 0.0])
        self._checkSpec('fluteLength', [gt, 0.0])
        self._checkSpec('oal', [gt, 0.0])
        self._checkSpec('angle', [gt, 30.0], [le, 180.0])
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        # angle [30, 180]
        if not 30.0 <= d['angle'] <= 180.0:
            return False
        # fluteLength < oal
        if d['fluteLength'] >= d['oal']:
            return False
        return True
    def _updateProfile(self):
        sdia = self.specs['shankDia']
        dia = self.specs['dia']
        flen = self.specs['fluteLength']
        angle = self.specs['angle']
        oal = self.specs['oal']
        srad = sdia / 2.0
        frad = dia / 2.0
        tiplen = self._tipLength(angle, dia)
        p1 = [0, 0]
        p2 = [frad, tiplen]
        p3 = [frad, tiplen + flen]
        p4 = [srad, tiplen + flen]
        p5 = [srad, tiplen + oal]
        p6 = [0, tiplen + oal]
        pp = QPainterPath()
        # right side
        pp.moveTo(*p1)
        pp.lineTo(*p2)
        pp.lineTo(*p3)
        pp.lineTo(*p4)
        pp.lineTo(*p5)
        pp.lineTo(*p6)
        # left
        pp.lineTo(-p5[0], p5[1])
        pp.lineTo(-p4[0], p4[1])
        pp.lineTo(-p3[0], p3[1])
        pp.lineTo(-p2[0], p2[1])
        pp.lineTo(*p1)
        # diagonal line to show flute
        pp.moveTo(-p2[0], p2[1])
        pp.lineTo(p3[0], p3[1])
        self.setPath(pp)
        return [p1, p2, p3, p4, p5, p6, angle, dia, oal, tiplen, sdia, flen]
    def _updateDims(self, p1, p2, p3, p4, p5, p6, angle, dia, oal, tiplen,
                    sdia, flen):
        # tip angle dimension
        tr = self.angleDim.dimText.sceneBoundingRect()
        angle = self.specs['angle']
        labelYfactor = 2.0
        if angle <= 135.0:
            labelYfactor = 1.0
        labelP = QPointF(0, -self._tipLength(angle, tr.width())
                         - tr.height() * labelYfactor)
        self.angleDim.config({'value': angle,
                              'pos': labelP,
                              'line1': QLineF(p1[0], p1[1], p2[0], p2[1]),
                              'line2': QLineF(p1[0], p1[1], -p2[0], p2[1]),
                              'outside': angle <= 135.0,
                              'quadV': QVector2D(0, -1),
                              'format': u'%.2f°'})
        # diameter dimension
        tr = self.diaDim.dimText.sceneBoundingRect()
        ar = self.diaDim.arrow1.sceneBoundingRect()
        outside = True
        # label always to left of tool
        labelP = QPointF(-p2[0] - tr.width(), p2[1] + tr.height() * .5)
        if ar.width() * 2.1 < dia:
            outside = False
        metric = self.specs['metric']
        self.diaDim.config({'value': dia,
                            'ref1': QPointF(-p2[0], p2[1]),
                            'ref2': QPointF(*p2),
                            'outside': outside,
                            'format': '%.3fmm' if metric else '%.4f"',
                            'pos': labelP})
        # shank diameter dimension
        self._updateDiaDim(self.shankDiaDim, [-p5[0], p5[1]], p5, sdia, None,
                           .75, metric)
        # flute len dimension
        fltr = self.fluteLenDim.dimText.sceneBoundingRect()
        ar = self.fluteLenDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        if fltr.height() * 1.1 < flen:
            labelY = p2[1] + flen * 0.5
            if fltr.height() * 1.1 + ar.height() * 2.1 < flen:
                outside = False
        # label below witness lines
        else:
            labelY = fltr.height() * -2.0
            if ar.height() * 2.1 < flen:
                outside = False
        if sdia > dia:
            ref2 = QPointF(*p4)
            labelX = p4[0] + fltr.width() * .6
        else:
            ref2 = QPointF(*p3)
            labelX = p2[0] + fltr.width() * .6
        fLabelP = QPointF(labelX, labelY)
        self.fluteLenDim.config({'value': flen,
                                 'ref1': QPointF(*p2),
                                 'ref2': ref2,
                                 'outside': outside,
                                 'format': '%.3fmm' if metric else '%.4f"',
                                 'pos': fLabelP,
                                 'force': 'vertical'})
        # OAL dimension
        tr = self.oalDim.dimText.sceneBoundingRect()
        ar = self.oalDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        labelAbove = False
        slen = oal - flen
        if tr.height() * 1.1 + ar.height() * 1.1 < slen:
            labelY = p3[1] + slen * .5
            outside = False
        # label above witness lines
        else:
            labelAbove = True
            labelY = p5[1] + tr.height() * 1.1
            if ar.height() * 2.1 < p2[1] + oal:
                outside = False
        labelX = fLabelP.x() + fltr.width() * .6
        labelP = QPointF(labelX, labelY)
        self.oalDim.config({'value': oal,
                            'ref1': QPointF(*p2),
                            'ref2': QPointF(*p5),
                            'outside': outside,
                            'format': '%.3fmm' if metric else '%.4f"',
                            'pos': labelP,
                            'force': 'vertical'})
        # comment label
        self._updateCommentText(labelAbove, p5[1], tr.height())
    def _update(self):
        self._updateDims(*self._updateProfile())

        
class SpotDrillDef(ToolDef):
    """Define a spot drill shape.
    specs:
      dia
      oal          (including the tip)
      angle        (included tip angle)
      metric       True/False
    """
    def __init__(self, specs):
        super(SpotDrillDef, self).__init__(specs)
        self.angleDim = AngleDim()
        self.angleDim.setToolTip("angle")
        self.diaDim = LinearDim()
        self.diaDim.setToolTip('dia')
        self.oalDim = LinearDim()
        self.oalDim.setToolTip('oal')
    def sceneChange(self, scene):
        super(SpotDrillDef, self).sceneChange(scene)
        if scene:
            scene.addItem(self.angleDim)
            scene.addItem(self.diaDim)
            scene.addItem(self.oalDim)
        else:
            self.scene().removeItem(self.angleDim)
            self.scene().removeItem(self.diaDim)
            self.scene().removeItem(self.oalDim)
    def config(self, specs={}):
        ""
        self.prepareGeometryChange()
        super(SpotDrillDef, self).config(specs)
        self._update()
    def checkSpecs(self):
        super(SpotDrillDef, self).checkSpecs()
        self._checkSpec('dia', [gt, 0.0])
        self._checkSpec('oal', [gt, 0.0])
        self._checkSpec('angle', [gt, 0.0], [le, 180.0])
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        # angle [30, 180]
        if not 30.0 <= d['angle'] <= 180.0:
            return False
        # tip length < oal
        if self._tipLength(d['angle'], d['dia']) >= d['oal']:
            return False
        return True
    def _updateProfile(self):
        dia = self.specs['dia']
        r = dia * 0.5
        oal = self.specs['oal']
        p1 = [0, 0]
        p2 = [r, self._tipLength(self.specs['angle'], dia)]
        p3 = [r, oal]
        p4 = [r, oal]
        pp = QPainterPath()
        # right side
        pp.moveTo(*p1)
        pp.lineTo(*p2)
        pp.lineTo(*p3)
        pp.lineTo(*p4)
        # left
        pp.lineTo(-p3[0], p3[1])
        pp.lineTo(-p2[0], p2[1])
        pp.lineTo(*p1)
        self.setPath(pp)
        return p1, p2, p3, p4, dia, oal
    def _updateDims(self, p1, p2, p3, p4, dia, oal):
        metric = self.specs['metric']
        # tip angle dimension
        tr = self.angleDim.dimText.sceneBoundingRect()
        self.angleDim.config({'value': self.specs['angle'],
                              'pos': QPointF(0, tr.height() * -2.2),
                              'line1': QLineF(p1[0], p1[1], p2[0], p2[1]),
                              'line2': QLineF(p1[0], p1[1], -p2[0], p2[1]),
                              'outside': True,
                              'quadV': QVector2D(0, -1),
                              'format': u'%.2f°'})
        # diameter dimension
        # A spot drill generally has the same shank dia as tip dia
        self._updateDiaDim(self.diaDim, [-p3[0], p3[1]], p3, dia, None, .75,
                           metric)
        # OAL dimension
        tr = self.oalDim.dimText.sceneBoundingRect()
        ar = self.oalDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        labelAbove = False
        if tr.height() * 1.1 < oal:
            labelY = oal * 0.5
            if tr.height() * 1.1 + ar.height() * 2.1 < oal:
                outside = False
        # label above witness lines
        else:
            labelAbove = True
            labelY = oal + tr.height() * 1.1
            if ar.height() * 2.1 < oal:
                outside = False
        labelX = p2[0] + tr.width() * 0.75
        labelP = QPointF(labelX, labelY)
        self.oalDim.config({'value': oal,
                            'ref1': QPointF(*p1),
                            'ref2': QPointF(*p3),
                            'outside': outside,
                            'format': '%.3fmm' if metric else '%.4f"',
                            'pos': labelP,
                            'force': 'vertical'})
        # comment label
        self._updateCommentText(labelAbove, oal, tr.height())
    def _update(self):
        self._updateDims(*self._updateProfile())


# TODO: bell center drill
class CenterDrillDef(ToolDef):
    """Define a plain center drill shape.
    specs:
      name
      shankDia
      dia
      oal          (including the tip)
      tipLength    (not including the tip)
      metric       True/False
    """
    def __init__(self, specs):
        super(CenterDrillDef, self).__init__(specs)
    @staticmethod
    def getSortKey():
        return 'tipDia'
    def sceneChange(self, scene):
        super(CenterDrillDef, self).sceneChange(scene)
        if scene:
            pass
        else:
            pass
    def config(self, specs={}):
        ""
        self.prepareGeometryChange()
        super(CenterDrillDef, self).config(specs)
        self._update()
    def _updateProfile(self):
        tipRadius = self.specs['tipDia'] / 2.0
        tipLength = self.specs['tipLength']
        bodyRadius = self.specs['bodyDia'] / 2.0
        oal = self.specs['oal']
        halfPointAngle = 118.0 / 2.0
        halfBellAngle = 30.0
        pointLength = tan(radians(90.0 - halfPointAngle)) * tipRadius
        bellLength = tan(radians(90.0 - 30)) * (bodyRadius - tipRadius)
        p1 = [0, 0]
        p2 = [tipRadius, pointLength]
        p3 = [tipRadius, pointLength + tipLength]
        p4 = [bodyRadius, pointLength + tipLength + bellLength]
        p5 = [bodyRadius, oal]
        p6 = [0, oal]
        pp = QPainterPath()
        # # right side
        pp.moveTo(*p1)
        pp.lineTo(*p2)
        pp.lineTo(*p3)
        pp.lineTo(*p4)
        pp.lineTo(*p5)
        pp.lineTo(*p6)
        # # left
        pp.lineTo(-p5[0], p5[1])
        pp.lineTo(-p4[0], p4[1])
        pp.lineTo(-p3[0], p3[1])
        pp.lineTo(-p2[0], p2[1])
        pp.lineTo(*p1)
        self.setPath(pp)
        return p1, p2, p3, p4, p5, p6, oal
    def _updateDims(self, p1, p2, p3, p4, p5, p6, oal):
        # There's only a fixed number of center drill sizes AFAIK so no need
        # for editable dimensions.
        tr = self.commentText.sceneBoundingRect()
        self.commentText.config({'pos': QPointF(0, oal + tr.height() * .75),
                               'text': self.specs['name']})
    def _update(self):
        self._updateDims(*self._updateProfile())
        
        
class EndMillDef(ToolDef):
    """Define a basic flat end mill shape.
    specs:
      shankDia
      dia
      fluteLength
      oal
      metric       True/False
    """
    def __init__(self, specs):
        super(EndMillDef, self).__init__(specs)
        self.diaDim = LinearDim()
        self.diaDim.setToolTip("dia")
        self.shankDiaDim = LinearDim()
        self.shankDiaDim.setToolTip("shankDia")
        self.fluteLenDim = LinearDim()
        self.fluteLenDim.setToolTip("fluteLength")
        self.oalDim = LinearDim()
        self.oalDim.setToolTip("oal")
    def sceneChange(self, scene):
        super(EndMillDef, self).sceneChange(scene)
        if scene:
            scene.addItem(self.diaDim)
            scene.addItem(self.shankDiaDim)
            scene.addItem(self.fluteLenDim)
            scene.addItem(self.oalDim)
        else:
            self.scene().removeItem(self.diaDim)
            self.scene().removeItem(self.shankDiaDim)
            self.scene().removeItem(self.fluteLenDim)
            self.scene().removeItem(self.oalDim)
    def config(self, specs={}):
        ""
        self.prepareGeometryChange()
        super(EndMillDef, self).config(specs)
        self._update()
    def checkSpecs(self):
        super(EndMillDef, self).checkSpecs()
        self._checkSpec('shankDia', [gt, 0.0])
        self._checkSpec('dia', [gt, 0.0])
        self._checkSpec('fluteLength', [gt, 0.0])
        self._checkSpec('oal', [gt, 0.0])
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        # flute length < oal
        if d['fluteLength'] >= d['oal']:
            return False
        return True
    def _updateProfile(self):
        """Create the tool's silhouette for display.

        Return a tuple of parameters used by _updateDims().
        """
        sdia = self.specs['shankDia']
        srad = sdia * 0.5
        dia = self.specs['dia']
        frad = dia * 0.5
        flen = self.specs['fluteLength']
        oal = self.specs['oal']
        p1 = [0.0, 0.0]
        p2 = [frad, 0.0]
        p3 = [frad, flen]
        p4 = [srad, flen]
        p5 = [srad, oal]
        p6 = [0.0, oal]
        step = sdia != dia
        pp = QPainterPath()
        # right side
        pp.moveTo(*p1)
        pp.lineTo(*p2)
        if step:
            pp.lineTo(*p3)
            pp.lineTo(*p4)
        pp.lineTo(*p5)
        # left side
        pp.lineTo(-p5[0], p5[1])
        if step:
            pp.lineTo(-p4[0], p4[1])
            pp.lineTo(-p3[0], p3[1])
        pp.lineTo(-p2[0], p2[1])
        pp.lineTo(*p1)
        # diagonal line to show flute
        pp.moveTo(-p2[0], p2[1])
        pp.lineTo(*p3)
        self.setPath(pp)
        return p1, p2, p3, p4, p5, p6, dia, sdia, oal, flen
    def _updateDims(self, p1, p2, p3, p4, p5, p6, dia, sdia, oal, flen):
        """Attempt to intelligently position the dimensions and name label.
        """
        metric = self.specs['metric']
        # flute diameter dimension
        self._updateDiaDim(self.diaDim, [-p2[0], p2[1]], p2, dia, None, -.75,
                           metric)
        # shank diameter dimension
        self._updateDiaDim(self.shankDiaDim, [-p5[0], p5[1]], p5, sdia, None,
                           .75, metric)
        # flute len dimension
        fltr = self.fluteLenDim.dimText.sceneBoundingRect()
        ar = self.fluteLenDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        if fltr.height() * 1.1 < flen:
            labelY = flen * 0.5
            if fltr.height() * 1.1 + ar.height() * 2.1 < flen:
                outside = False
        # label below witness lines
        else:
            labelY = fltr.height() * -2.0
            if ar.height() * 2.1 < flen:
                outside = False
        if sdia > dia:
            ref2 = QPointF(*p4)
            labelX = p4[0] + fltr.width() * .6
        else:
            ref2 = QPointF(*p3)
            labelX = p3[0] + fltr.width() * .6
        fLabelP = QPointF(labelX, labelY)
        self.fluteLenDim.config({'value': flen,
                                 'ref1': QPointF(*p2),
                                 'ref2': ref2,
                                 'outside': outside,
                                 'format': '%.3fmm' if metric else '%.4f"',
                                 'pos': fLabelP,
                                 'force': 'vertical'})
        # OAL dimension
        tr = self.oalDim.dimText.sceneBoundingRect()
        ar = self.oalDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        labelAbove = False
        slen = oal - flen
        if tr.height() * 1.1 < slen:
            labelY = oal - slen * 0.5
            if tr.height() * 1.1 + ar.height() * 2.1 < oal:
                outside = False
        # label above witness lines
        else:
            labelAbove = True
            labelY = oal + tr.height() * 1.1
            if ar.height() * 2.1 < oal:
                outside = False
        labelX = fLabelP.x() + fltr.width() * .6
        labelP = QPointF(labelX, labelY)
        self.oalDim.config({'value': oal,
                            'ref1': QPointF(*p2),
                            'ref2': QPointF(*p5),
                            'outside': outside,
                            'format': '%.3fmm' if metric else '%.4f"',
                            'pos': labelP,
                            'force': 'vertical'})
        # comment label
        self._updateCommentText(labelAbove, oal, tr.height())
    def _update(self):
        self._updateDims(*self._updateProfile())


# TODO: Possibly create a fillet to blend the flute with the body for cases
#       where the large end of the flute is smaller than the shank dia.
class TaperEndMillDef(ToolDef):
    """Define a basic tapered flat end mill shape.
    specs:
      shankDia
      dia          (tip dia)
      fluteLength
      oal
      angle        (half angle to vertical)
      metric       True/False
    """
    def __init__(self, specs):
        super(TaperEndMillDef, self).__init__(specs)
        self.diaDim = LinearDim()
        self.diaDim.setToolTip("dia")
        self.shankDiaDim = LinearDim()
        self.shankDiaDim.setToolTip("shankDia")
        self.fluteLenDim = LinearDim()
        self.fluteLenDim.setToolTip("fluteLength")
        self.oalDim = LinearDim()
        self.oalDim.setToolTip("oal")
        self.angleDim = AngleDim()
        self.angleDim.setToolTip("angle")
    def sceneChange(self, scene):
        super(TaperEndMillDef, self).sceneChange(scene)
        if scene:
            scene.addItem(self.diaDim)
            scene.addItem(self.shankDiaDim)
            scene.addItem(self.fluteLenDim)
            scene.addItem(self.oalDim)
            scene.addItem(self.angleDim)
        else:
            self.scene().removeItem(self.diaDim)
            self.scene().removeItem(self.shankDiaDim)
            self.scene().removeItem(self.fluteLenDim)
            self.scene().removeItem(self.oalDim)
            self.scene().removeItem(self.angleDim)
    def config(self, specs={}):
        ""
        self.prepareGeometryChange()
        super(TaperEndMillDef, self).config(specs)
        self._update()
    def checkSpecs(self):
        super(TaperEndMillDef, self).checkSpecs()
        self._checkSpec('shankDia', [gt, 0.0])
        self._checkSpec('dia', [gt, 0.0])
        self._checkSpec('fluteLength', [gt, 0.0])
        self._checkSpec('oal', [gt, 0.0])
        self._checkSpec('angle', [gt, 0.0], [lt, 90.0])
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        # flute length < oal
        if d['fluteLength'] >= d['oal']:
            return False
        # angle >= 90
        # TODO: what's a reasonable upper limit here?
        if d['angle'] >= 90.0:
            return False
        return True
    def _updateProfile(self):
        """Create the tool's silhouette for display.

        Return a tuple of parameters used by _updateDims().
        """
        sdia = self.specs['shankDia']
        srad = sdia * 0.5
        dia = self.specs['dia']
        frad = dia * 0.5
        flen = self.specs['fluteLength']
        oal = self.specs['oal']
        a = self.specs['angle']
        p1 = [0.0, 0.0]
        p2 = [frad, 0.0]
        p3 = [frad + tan(radians(a)) * flen, flen]
        p4 = [srad, flen]
        p5 = [srad, oal]
        p6 = [0.0, oal]
        step = sdia != dia
        pp = QPainterPath()
        # right side
        pp.moveTo(*p1)
        pp.lineTo(*p2)
        pp.lineTo(*p3)
        pp.lineTo(*p4)
        pp.lineTo(*p5)
        # left side
        pp.lineTo(-p5[0], p5[1])
        pp.lineTo(-p4[0], p4[1])
        pp.lineTo(-p3[0], p3[1])
        pp.lineTo(-p2[0], p2[1])
        pp.lineTo(*p1)
        # diagonal line to show flute
        pp.moveTo(-p2[0], p2[1])
        pp.lineTo(*p3)
        self.setPath(pp)
        return p1, p2, p3, p4, p5, p6, dia, sdia, srad, oal, flen, a
    def _updateDims(self, p1, p2, p3, p4, p5, p6, dia, sdia, srad, oal, flen,
                    a):
        """Attempt to intelligently position the dimensions and name label.
        """
        metric = self.specs['metric']
        # flute diameter dimension
        self._updateDiaDim(self.diaDim, [-p2[0], p2[1]], p2, dia, None, -.75,
                           metric)
        # shank diameter dimension
        self._updateDiaDim(self.shankDiaDim, [-p5[0], p5[1]], p5, sdia, None,
                           .75, metric)
        # flute len dimension
        fltr = self.fluteLenDim.dimText.sceneBoundingRect()
        ar = self.fluteLenDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        if fltr.height() * 1.1 < flen:
            labelY = flen * 0.5
            if fltr.height() * 1.1 + ar.height() * 2.1 < flen:
                outside = False
        # label below witness lines
        else:
            labelY = fltr.height() * -2.0
            if ar.height() * 2.1 < flen:
                outside = False
        if srad > p3[0]:
            ref2 = QPointF(*p4)
            labelX = p4[0] + fltr.width() * .6
        else:
            ref2 = QPointF(*p3)
            labelX = p3[0] + fltr.width() * .6
        fLabelP = QPointF(labelX, labelY)
        self.fluteLenDim.config({'value': flen,
                                 'ref1': QPointF(*p2),
                                 'ref2': ref2,
                                 'outside': outside,
                                 'format': '%.3fmm' if metric else '%.4f"',
                                 'pos': fLabelP,
                                 'force': 'vertical'})
        # OAL dimension
        tr = self.oalDim.dimText.sceneBoundingRect()
        ar = self.oalDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        labelAbove = False
        slen = oal - flen
        if tr.height() * 1.1 < slen:
            labelY = oal - slen * 0.5
            if tr.height() * 1.1 + ar.height() * 2.1 < oal:
                outside = False
        # label above witness lines
        else:
            labelAbove = True
            labelY = oal + tr.height() * 1.1
            if ar.height() * 2.1 < oal:
                outside = False
        labelX = fLabelP.x() + fltr.width() * .6
        labelP = QPointF(labelX, labelY)
        self.oalDim.config({'value': oal,
                            'ref1': QPointF(*p2),
                            'ref2': QPointF(*p5),
                            'outside': outside,
                            'format': '%.3fmm' if metric else '%.4f"',
                            'pos': labelP,
                            'force': 'vertical'})
        # flute angle dimension
        tr = self.angleDim.dimText.sceneBoundingRect()
        # left flute edge end points
        qp1 = QPointF(-p2[0], p2[1])
        qp2 = QPointF(-p3[0], p3[1])
        # centerline end points
        qp3 = QPointF(*p1)
        qp4 = QPointF(*p6)
        # flute edge vector
        v1 = QVector2D(qp2 - qp3)
        # centerline vector
        v2 = QVector2D(qp4 - qp3)
        labelP = QPointF(-p2[0] - tr.width() * 2, tr.height() * 0.75)
        self.angleDim.config({'value': self.specs['angle'],
                              'pos': labelP,
                              'line1': QLineF(qp1, qp2),
                              'line2': QLineF(qp3, qp4),
                              'outside': True,
                              'quadV': v1 + v2,
                              'format': u'%.2f°'})
        # comment label
        self._updateCommentText(labelAbove, oal, tr.height())
    def _update(self):
        self._updateDims(*self._updateProfile())
        

class TaperBallMillDef(ToolDef):
    """Define a basic tapered ball end mill shape.
    specs:
      shankDia
      dia          (tip dia)
      fluteLength
      oal
      angle        (half angle to vertical)
      metric       True/False
    """
    def __init__(self, specs):
        super(TaperBallMillDef, self).__init__(specs)
        self.diaDim = RadiusDim()
        self.diaDim.setToolTip("dia")
        self.shankDiaDim = LinearDim()
        self.shankDiaDim.setToolTip("shankDia")
        self.fluteLenDim = LinearDim()
        self.fluteLenDim.setToolTip("fluteLength")
        self.oalDim = LinearDim()
        self.oalDim.setToolTip("oal")
        self.angleDim = AngleDim()
        self.angleDim.setToolTip("angle")
    def sceneChange(self, scene):
        super(TaperBallMillDef, self).sceneChange(scene)
        if scene:
            scene.addItem(self.diaDim)
            scene.addItem(self.shankDiaDim)
            scene.addItem(self.fluteLenDim)
            scene.addItem(self.oalDim)
            scene.addItem(self.angleDim)
        else:
            self.scene().removeItem(self.diaDim)
            self.scene().removeItem(self.shankDiaDim)
            self.scene().removeItem(self.fluteLenDim)
            self.scene().removeItem(self.oalDim)
            self.scene().removeItem(self.angleDim)
    def config(self, specs={}):
        ""
        self.prepareGeometryChange()
        super(TaperBallMillDef, self).config(specs)
        self._update()
    def checkSpecs(self):
        super(TaperBallMillDef, self).checkSpecs()
        self._checkSpec('shankDia', [gt, 0.0])
        self._checkSpec('dia', [gt, 0.0])
        self._checkSpec('fluteLength', [gt, 0.0])
        self._checkSpec('oal', [gt, 0.0])
        self._checkSpec('angle', [gt, 0.0], [lt, 90.0])
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        # flute length < oal
        if d['fluteLength'] >= d['oal']:
            return False
        # angle >= 90
        # TODO: what's a reasonable upper limit here?
        if d['angle'] >= 90.0:
            return False
        return True
    def _updateProfile(self):
        """Create the tool's silhouette for display.

        Return a tuple of parameters used by _updateDims().
        """
        sdia = self.specs['shankDia']
        srad = sdia * 0.5
        dia = self.specs['dia']
        frad = dia * 0.5
        flen = self.specs['fluteLength']
        oal = self.specs['oal']
        a = self.specs['angle']
        ra = radians(a)
        p2X = cos(-ra) * frad
        p2Y = frad + sin(-ra) * frad
        p3Y = flen
        p3X = p2X + tan(ra) * (flen - p2Y)
        p1 = [0.0, 0.0]
        p2 = [p2X, p2Y]
        p3 = [p3X, p3Y]
        p4 = [srad, flen]
        p5 = [srad, oal]
        p6 = [0.0, oal]
        pp = QPainterPath()
        rect = QRectF(-frad, dia, dia, -dia)
        # right side
        # pp.moveTo(*p1)
        pp.arcMoveTo(rect, 180 + a)
        pp.arcTo(rect, 180 + a, 180 - 2 * a)
        pp.lineTo(*p3)
        pp.lineTo(*p4)
        pp.lineTo(*p5)
        # left side
        pp.lineTo(-p5[0], p5[1])
        pp.lineTo(-p4[0], p4[1])
        pp.lineTo(-p3[0], p3[1])
        pp.lineTo(-p2[0], p2[1])
        # diagonal line to show flute
        pp.moveTo(*p1)
        pp.lineTo(*p3)
        self.setPath(pp)
        return p1, p2, p3, p4, p5, p6, dia, frad, sdia, srad, oal, flen, a
    def _updateDims(self, p1, p2, p3, p4, p5, p6, dia, frad, sdia, srad, oal,
                    flen, a):
        """Attempt to intelligently position the dimensions and name label.
        """
        metric = self.specs['metric']
        # flute diameter dimension (actaully a RadiusDim)
        tr = self.diaDim.dimText.sceneBoundingRect()
        labelP = QPointF(-p2[0] - tr.width(), tr.height() * -1.0)
        arc = arcFromAngles(180 + a, -a, frad)
        arc.center(QPointF(p1[0], frad))
        self.diaDim.config({'value': dia,
                            'pos': labelP,
                            'arc': arc,
                            'outside': True,
                            'format':
                                u'Ø%.3fmm' if metric else u'Ø%.4f"'})
        # shank diameter dimension
        self._updateDiaDim(self.shankDiaDim, [-p5[0], p5[1]], p5, sdia, None,
                           .75, metric)
        # flute len dimension
        fltr = self.fluteLenDim.dimText.sceneBoundingRect()
        ar = self.fluteLenDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        if fltr.height() * 1.1 < flen:
            labelY = flen * 0.5
            if fltr.height() * 1.1 + ar.height() * 2.1 < flen:
                outside = False
        # label below witness lines
        else:
            labelY = fltr.height() * -2.0
            if ar.height() * 2.1 < flen:
                outside = False
        if srad > p3[0]:
            ref2 = QPointF(*p4)
            labelX = p4[0] + fltr.width() * .6
        else:
            ref2 = QPointF(*p3)
            labelX = p3[0] + fltr.width() * .6
        fLabelP = QPointF(labelX, labelY)
        self.fluteLenDim.config({'value': flen,
                                 'ref1': QPointF(*p1),
                                 'ref2': ref2,
                                 'outside': outside,
                                 'format': '%.3fmm' if metric else '%.4f"',
                                 'pos': fLabelP,
                                 'force': 'vertical'})
        # OAL dimension
        tr = self.oalDim.dimText.sceneBoundingRect()
        ar = self.oalDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        labelAbove = False
        slen = oal - flen
        if tr.height() * 1.1 < slen:
            labelY = oal - slen * 0.5
            if tr.height() * 1.1 + ar.height() * 2.1 < oal:
                outside = False
        # label above witness lines
        else:
            labelAbove = True
            labelY = oal + tr.height() * 1.1
            if ar.height() * 2.1 < oal:
                outside = False
        labelX = fLabelP.x() + fltr.width() * .6
        labelP = QPointF(labelX, labelY)
        self.oalDim.config({'value': oal,
                            'ref1': QPointF(*p1),
                            'ref2': QPointF(*p5),
                            'outside': outside,
                            'format': '%.3fmm' if metric else '%.4f"',
                            'pos': labelP,
                            'force': 'vertical'})
        # flute angle dimension
        tr = self.angleDim.dimText.sceneBoundingRect()
        # left flute edge end points
        qp1 = QPointF(-p2[0], p2[1])
        qp2 = QPointF(-p3[0], p3[1])
        # centerline end points
        qp3 = QPointF(*p1)
        qp4 = QPointF(*p6)
        # flute edge vector
        v1 = QVector2D(qp2 - qp3)
        # centerline vector
        v2 = QVector2D(qp4 - qp3)
        labelP = QPointF(-p2[0] - tr.width() * 2, tr.height() * 0.75)
        self.angleDim.config({'value': self.specs['angle'],
                              'pos': labelP,
                              'line1': QLineF(qp1, qp2),
                              'line2': QLineF(qp3, qp4),
                              'outside': True,
                              'quadV': v1 + v2,
                              'format': u'%.2f°'})
        # comment label
        self._updateCommentText(labelAbove, oal, tr.height())
    def _update(self):
        self._updateDims(*self._updateProfile())
        

class BallMillDef(EndMillDef):
    """Define a basic ball end mill shape.
    specs:
      name
      shankDia
      dia
      fluteLength
      oal
      metric       True/False
    """
    def _updateProfile(self):
        sdia = self.specs['shankDia']
        srad = sdia * 0.5
        dia = self.specs['dia']
        frad = dia * 0.5
        flen = self.specs['fluteLength']
        oal = self.specs['oal']
        p1 = [0.0, 0.0]
        p2 = [frad, frad]
        p3 = [frad, flen]
        p4 = [srad, flen]
        p5 = [srad, oal]
        p6 = [0.0, oal]
        pp = QPainterPath()
        step = sdia != dia
        rect = QRectF(-frad, dia, dia, -dia)
        pp.arcMoveTo(rect, 180.0)
        pp.arcTo(rect, 180.0, 180.0)
        if step:
            pp.lineTo(*p3)
            pp.lineTo(*p4)
        pp.lineTo(*p5)
        pp.lineTo(-p5[0], p5[1])
        if step:
            pp.lineTo(-p4[0], p4[1])
            pp.lineTo(-p3[0], p3[1])
        pp.lineTo(-p2[0], p2[1])
        # flute
        pp.moveTo(0.0, 0.0)
        pp.lineTo(*p3)
        self.setPath(pp)
        return p1, p2, p3, p4, p5, p6, dia, sdia, oal, flen
    def _updateDims(self, p1, p2, p3, p4, p5, p6, dia, sdia, oal, flen):
        """Attempt to intelligently position the dimensions and name label.
        """
        metric = self.specs['metric']
        # flute diameter dimension
        self._updateDiaDim(self.diaDim, [-p2[0], p2[1]], p2, dia, 0.0, -.75,
                           metric)
        # shank diameter dimension
        self._updateDiaDim(self.shankDiaDim, [-p5[0], p5[1]], p5, sdia, None,
                           .75, metric)
        # flute len dimension
        fltr = self.fluteLenDim.dimText.sceneBoundingRect()
        ar = self.fluteLenDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        if fltr.height() * 1.1 < flen:
            labelY = flen * 0.5
            if fltr.height() * 1.1 + ar.height() * 2.1 < flen:
                outside = False
        # label below witness lines
        else:
            labelY = fltr.height() * -2.0
            if ar.height() * 2.1 < flen:
                outside = False
        if sdia > dia:
            ref2 = QPointF(*p4)
            labelX = p4[0] + fltr.width() * .6
        else:
            ref2 = QPointF(*p3)
            labelX = p3[0] + fltr.width() * .6
        fLabelP = QPointF(labelX, labelY)
        self.fluteLenDim.config({'value': flen,
                                 'ref1': QPointF(*p1),
                                 'ref2': ref2,
                                 'outside': outside,
                                 'format': '%.3fmm' if metric else '%.4f"',
                                 'pos': fLabelP,
                                 'force': 'vertical'})
        # OAL dimension
        tr = self.oalDim.dimText.sceneBoundingRect()
        ar = self.oalDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        labelAbove = False
        slen = oal - flen
        if tr.height() * 1.1 < slen:
            labelY = oal - slen * 0.5
            if tr.height() * 1.1 + ar.height() * 2.1 < oal:
                outside = False
        # label above witness lines
        else:
            labelAbove = True
            labelY = oal + tr.height() * 1.1
            if ar.height() * 2.1 < oal:
                outside = False
        labelX = fLabelP.x() + fltr.width() * .6
        labelP = QPointF(labelX, labelY)
        self.oalDim.config({'value': oal,
                            'ref1': QPointF(*p1),
                            'ref2': QPointF(*p5),
                            'outside': outside,
                            'format': '%.3fmm' if metric else '%.4f"',
                            'pos': labelP,
                            'force': 'vertical'})
        # comment label
        self._updateCommentText(labelAbove, oal, tr.height())
    def _update(self):
        self._updateDims(*self._updateProfile())
        
        
class BullMillDef(EndMillDef):
    """Define a basic bull end mill shape.
    specs:
      name
      shankDia
      dia
      fluteLength  from tip
      oal          from tip
      radius       corner
      metric       True/False
    """
    def __init__(self, specs):
        super(BullMillDef, self).__init__(specs)
        self.radiusDim = RadiusDim()
        self.radiusDim.setToolTip("radius")
    def sceneChange(self, scene):
        super(BullMillDef, self).sceneChange(scene)
        if scene:
            scene.addItem(self.radiusDim)
        else:
            self.scene().removeItem(self.radiusDim)
    def checkSpecs(self):
        super(BullMillDef, self).checkSpecs()
        self._checkSpec('radius', [gt, 0.0])
    def checkGeometry(self, specs={}):
        if not super(BullMillDef, self).checkGeometry(specs):
            return False
        d = copy(self.specs)
        d.update(specs)
        # radius * 2 < dia
        if not d['radius'] * 2.0 < d['dia']:
            return False
        # radius < flute length
        if not d['radius'] < d['fluteLength']:
            return False
        return True
    def _updateProfile(self):
        sdia = self.specs['shankDia']
        srad = sdia * 0.5
        dia = self.specs['dia']
        frad = dia * 0.5
        flen = self.specs['fluteLength']
        oal = self.specs['oal']
        r = self.specs['radius']
        p1 = [0.0, 0.0]
        p2 = [frad - r, 0.0]
        p3 = [frad, r]
        p4 = [frad, flen]
        p5 = [srad, flen]
        p6 = [srad, oal]
        p7 = [0, oal]
        rect = QRectF(frad - r*2, r*2, r*2, -r*2)
        pp = QPainterPath()
        # right side
        pp.moveTo(*p1)
        pp.lineTo(*p2)
        pp.arcMoveTo(rect, 270.0)
        pp.arcTo(rect, 270.0, 90.0)
        pp.lineTo(*p4)
        pp.lineTo(*p5)
        pp.lineTo(*p6)
        pp.lineTo(*p7)
        # left side
        pp.lineTo(-p6[0], p6[1])
        pp.lineTo(-p5[0], p5[1])
        pp.lineTo(-p4[0], p4[1])
        pp.lineTo(-p3[0], p3[1])
        rect.moveLeft(-frad)
        pp.arcMoveTo(rect, 180.0)
        pp.arcTo(rect, 180.0, 90.0)
        pp.lineTo(*p1)
        # flute
        pp.moveTo(-frad + r, 0.0)
        pp.lineTo(*p4)
        self.setPath(pp)
        return p1, p2, p3, p4, p5, p6, p7, dia, sdia, oal, flen, r
    def _updateDims(self, p1, p2, p3, p4, p5, p6, p7, dia, sdia, oal, flen,
                    r):
        """Attempt to intelligently position the dimensions and name label.
        """
        metric = self.specs['metric']
        # dia dimensions
        self._updateDiaDim(self.diaDim, [-p3[0], p3[1]], p3, dia, 0.0, -.75,
                           metric)
        # shank diameter dimension
        self._updateDiaDim(self.shankDiaDim, [-p6[0], p6[1]], p6, sdia, None,
                           .75, metric)
        # flute len dimension
        fltr = self.fluteLenDim.dimText.sceneBoundingRect()
        ar = self.fluteLenDim.arrow1.sceneBoundingRect()
        outside = True
        fluteY = p4[1]
        # label inside witness lines
        if fltr.height() * 1.1 < fluteY:
            labelY = fluteY * .5
            if fltr.height() * 1.1 + ar.height() * 2.1 < fluteY:
                outside = False
        # label below witness lines
        else:
            labelY = fltr.height() * -2.0
            if ar.height() * 2.1 < fluteY:
                outside = False
        if sdia > dia:
            ref2 = QPointF(p5[0], p5[1])
            labelX = p5[0] + fltr.width() * .6
        else:
            ref2 = QPointF(p4[0], p4[1])
            labelX = p4[0] + fltr.width() * .6
        fLabelP = QPointF(labelX, labelY)
        self.fluteLenDim.config({'value': flen,
                                 'ref1': QPointF(p2[0], 0.0),
                                 'ref2': ref2,
                                 'outside': outside,
                                 'format': '%.3fmm' if metric else '%.4f"',
                                 'pos': fLabelP,
                                 'force': 'vertical'})
        # OAL dimension
        tr = self.oalDim.dimText.sceneBoundingRect()
        ar = self.oalDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        labelAbove = False
        if tr.height() * 1.1 < oal:
            labelY = oal * 0.75
            if tr.height() * 1.1 + ar.height() * 2.1 < oal:
                outside = False
        # label above witness lines
        else:
            labelAbove = True
            labelY = oal + tr.height() * 1.1
            if ar.height() * 2.1 < oal:
                outside = False
        labelX = fLabelP.x() + fltr.width() * .6
        labelP = QPointF(labelX, labelY)
        self.oalDim.config({'value': oal,
                            'ref1': QPointF(*p2),
                            'ref2': QPointF(*p6),
                            'outside': outside,
                            'format': '%.3fmm' if metric else '%.4f"',
                            'pos': labelP,
                            'force': 'vertical'})
        # corner radius dimension
        tr = self.radiusDim.dimText.sceneBoundingRect()
        arc = Arc({'center': QPointF(p2[0], p3[1]),
                   'radius': r,
                   'start': 270.0,
                   'span': 90.0})
        labelP = QPointF(-p3[0] - tr.width() * .6, (p3[1] + p4[1]) * .5)
        self.radiusDim.config({'value': r,
                               'pos': labelP,
                               'arc': arc,
                               'outside': True,
                               'format':
                                   'R%.3fmm' if metric else 'R%.4f"'})
        # comment label
        self._updateCommentText(labelAbove, oal, tr.height())
    def _update(self):
        self._updateDims(*self._updateProfile())


# TODO:
#   * Neck relief radius is computed, and not very well.
class WoodruffMillDef(ToolDef):
    """Define a Woodruff keyseat cutter.
    specs:
      name
      shankDia
      neckDia
      dia
      fluteLength
      oal
      metric       True/False
    """
    def __init__(self, specs):
        super(WoodruffMillDef, self).__init__(specs)
        self.shankDiaDim = LinearDim()
        self.shankDiaDim.setToolTip("shankDia")
        self.neckDiaDim = LinearDim()
        self.neckDiaDim.setToolTip("neckDia")
        self.diaDim = LinearDim()
        self.diaDim.setToolTip("dia")
        self.fluteLenDim = LinearDim()
        self.fluteLenDim.setToolTip("fluteLength")
        self.oalDim = LinearDim()
        self.oalDim.setToolTip("oal")
    def sceneChange(self, scene):
        super(WoodruffMillDef, self).sceneChange(scene)
        if scene:
            scene.addItem(self.shankDiaDim)
            scene.addItem(self.neckDiaDim)
            scene.addItem(self.diaDim)
            scene.addItem(self.fluteLenDim)
            scene.addItem(self.oalDim)
        else:
            self.scene().removeItem(self.shankDiaDim)
            self.scene().removeItem(self.neckDiaDim)
            self.scene().removeItem(self.diaDim)
            self.scene().removeItem(self.fluteLenDim)
            self.scene().removeItem(self.oalDim)
    def config(self, specs={}):
        ""
        self.prepareGeometryChange()
        super(WoodruffMillDef, self).config(specs)
        self._update()
    def checkSpecs(self):
        super(WoodruffMillDef, self).checkSpecs()
        self._checkSpec('shankDia', [gt, 0.0])
        self._checkSpec('neckDia', [gt, 0.0])
        self._checkSpec('dia', [gt, 0.0])
        self._checkSpec('fluteLength', [gt, 0.0])
        self._checkSpec('oal', [gt, 0.0])
    # TODO: need to include the relief radius when checking oal > flute len
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        # flute length < oal
        if not d['fluteLength'] < d['oal']:
            return False
        # neck dia < shank dia
        if not d['neckDia'] < d['shankDia']:
            return False
        # neck dia < dia
        if not d['neckDia'] < d['dia']:
            return False
        return True
    def _updateProfile(self):
        sdia = self.specs['shankDia']
        srad = sdia * 0.5
        ndia = self.specs['neckDia']
        nrad = ndia * 0.5
        dia = self.specs['dia']
        frad = dia * 0.5
        flen = self.specs['fluteLength']
        oal = self.specs['oal']
        # TODO: better way to find this
        reliefRadius = fabs(srad - nrad) + flen * 2
        arcOrigin = QPointF(nrad + reliefRadius, flen)
        rect = QRectF(arcOrigin - QPointF(reliefRadius, reliefRadius),
                      arcOrigin + QPointF(reliefRadius, reliefRadius))
        arcX = (reliefRadius - (srad - nrad))
        arcY = sqrt(reliefRadius * reliefRadius - arcX * arcX)
        sweepAngle = degrees(atan2(arcY, arcX))
        p1 = [0, 0]
        p2 = [frad, 0]
        p3 = [frad, flen]
        p4 = [nrad, flen]
        p5 = [rect.center().x() - arcX, rect.center().y() + arcY]
        p6 = [srad, oal]
        p7 = [0, oal]
        pp = QPainterPath()
        # right side
        pp.moveTo(p1[0], p1[1])
        pp.lineTo(p2[0], p2[1])
        pp.lineTo(p3[0], p3[1])
        pp.lineTo(p4[0], p4[1])
        pp.arcMoveTo(rect, -180.0)
        pp.arcTo(rect, -180.0, sweepAngle)
        pp.lineTo(p6[0], p6[1])
        pp.lineTo(p7[0], p7[1])
        # left
        rect.moveCenter(QPointF(-rect.center().x(), rect.center().y()))
        pp.lineTo(-p6[0], p6[1])
        pp.lineTo(-p5[0], p5[1])
        pp.arcMoveTo(rect, -sweepAngle)
        pp.arcTo(rect, -sweepAngle, sweepAngle)
        pp.lineTo(-p3[0], p3[1])
        pp.lineTo(-p2[0], p2[1])
        pp.lineTo(p1[0], p1[1])
        # diagonal line to show flute
        pp.moveTo(-p2[0], p2[1])
        pp.lineTo(p3[0], p3[1])
        self.setPath(pp)
        return p1, p2, p3, p4, p5, p6, p7, dia, sdia, oal, ndia, flen
    def _updateDims(self, p1, p2, p3, p4, p5, p6, p7, dia, sdia, oal, ndia,
                    flen):
        metric = self.specs['metric']
        # dia dimension
        self._updateDiaDim(self.diaDim, [-p2[0], p2[1]], p2, dia, None, -.75,
                           metric)
        # shank diameter dimension
        self._updateDiaDim(self.shankDiaDim, [-p6[0], p6[1]], p6, sdia, None,
                           .75, metric)
        # neck diameter dimension
        self._updateDiaDim(self.neckDiaDim, [-p4[0], p4[1]], p4, ndia, None,
                           2.0, metric)
        # flute len dimension
        fltr = self.fluteLenDim.dimText.sceneBoundingRect()
        ar = self.fluteLenDim.arrow1.sceneBoundingRect()
        outside = True
        fLabelX = p2[0] + fltr.width() * .6
        # label inside witness lines
        if fltr.height() * 1.1 < p3[1]:
            fLabelP = QPointF(fLabelX, p3[1] * 0.5)
            if fltr.height() * 1.1 + ar.height() * 2.1 < p3[1]:
                outside = False
        # label below witness lines
        else:
            fLabelP = QPointF(fLabelX, fltr.height() * -2.0)
            if ar.height() * 2.1 < p3[1]:
                outside = False
        self.fluteLenDim.config({'value': flen,
                                 'ref1': QPointF(*p2),
                                 'ref2': QPointF(*p3),
                                 'outside': outside,
                                 'format': '%.3fmm' if metric else '%.4f"',
                                 'pos': fLabelP,
                                 'force': 'vertical'})
        # oal len dimension
        tr = self.oalDim.dimText.sceneBoundingRect()
        ar = self.oalDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        labelAbove = False
        slen = p6[1] - p3[1]
        if tr.height() * 1.1 + ar.height() * 1.1 < slen:
            labelY = oal - slen * 0.5
            if tr.height() * 1.1 + ar.height() * 2.1 < oal:
                outside = False
        # label above witness lines
        else:
            labelAbove = True
            labelY = oal + tr.height() * 1.1
            if ar.height() * 2.1 < oal:
                outside = False
        labelX = fLabelX + fltr.width() * .6
        labelP = QPointF(labelX, labelY)
        self.oalDim.config({'value': oal,
                            'ref1': QPointF(*p2),
                            'ref2': QPointF(*p6),
                            'outside': outside,
                            'format': '%.3fmm' if metric else '%.4f"',
                            'pos': labelP,
                            'force': 'vertical'})
        # comment label
        self._updateCommentText(labelAbove, oal, tr.height())
    def _update(self):
        self._updateDims(*self._updateProfile())
        

# TODO: The bodyLength parameters are guesses in tools.json
class RadiusMillDef(ToolDef):
    """Define a corner rounding end mill.
    specs:
      name
      shankDia
      bodyDia
      tipDia
      bodyLength
      radius
      oal
      metric

      Note: CornerRoundingMillDef is just too long :/
    """
    def __init__(self, specs):
        super(RadiusMillDef, self).__init__(specs)
        self.shankDiaDim = LinearDim()
        self.shankDiaDim.setToolTip("shankDia")
        self.bodyDiaDim = LinearDim()
        self.bodyDiaDim.setToolTip("bodyDia")
        self.tipDiaDim = LinearDim()
        self.tipDiaDim.setToolTip("tipDia")
        self.bodyLengthDim = LinearDim()
        self.bodyLengthDim.setToolTip("bodyLength")
        self.radiusDim = RadiusDim()
        self.radiusDim.setToolTip("radius")
        self.oalDim = LinearDim()
        self.oalDim.setToolTip("oal")
    @staticmethod
    def getSortKey():
        return 'radius'
    def sceneChange(self, scene):
        super(RadiusMillDef, self).sceneChange(scene)
        if scene:
            scene.addItem(self.bodyDiaDim)
            scene.addItem(self.tipDiaDim)
            scene.addItem(self.shankDiaDim)
            scene.addItem(self.bodyLengthDim)
            scene.addItem(self.radiusDim)
            scene.addItem(self.oalDim)
        else:
            self.scene().removeItem(self.bodyDiaDim)
            self.scene().removeItem(self.tipDiaDim)
            self.scene().removeItem(self.shankDiaDim)
            self.scene().removeItem(self.bodyLengthDim)
            self.scene().removeItem(self.radiusDim)
            self.scene().removeItem(self.oalDim)
    def config(self, specs={}):
        ""
        self.prepareGeometryChange()
        super(RadiusMillDef, self).config(specs)
        self._update()
    def checkSpecs(self):
        super(RadiusMillDef, self).checkSpecs()
        self._checkSpec('shankDia', [gt, 0.0])
        self._checkSpec('bodyDia', [gt, 0.0])
        self._checkSpec('tipDia', [gt, 0.0])
        self._checkSpec('bodyLength', [gt, 0.0])
        self._checkSpec('radius', [gt, 0.0])
        self._checkSpec('oal', [gt, 0.0])
    def checkGeometry(self, specs={}):
        d = copy(self.specs)
        d.update(specs)
        # will check body dia, tip dia, and radius
        flat = d['bodyDia'] - d['tipDia'] - d['radius'] * 2.0
        if flat < 0.0:
            return False
        # body length > radius + flat
        if not d['bodyLength'] > d['radius'] + flat:
            return False
        # body length < oal
        if not d['bodyLength'] < d['oal']:
            return False
        return True
    def _updateProfile(self):
        sdia = self.specs['shankDia']
        srad = sdia * 0.5
        bdia = self.specs['bodyDia']
        brad = bdia * 0.5
        tdia = self.specs['tipDia']
        trad = tdia * 0.5
        blen = self.specs['bodyLength']
        r = self.specs['radius']
        oal = self.specs['oal']
        flat = brad - trad - r
        p1 = [0, 0]
        p2 = [trad, 0.0]
        p3 = [trad, flat]
        p4 = [brad - flat, r + flat]
        p5 = [brad, r + flat]
        p6 = [brad, blen]
        p7 = [srad, blen]
        p8 = [srad, oal]
        p9 = [0, oal]
        pp = QPainterPath()
        rect = QRectF(QPointF(trad, r + flat),
                      QPointF(trad + r * 2.0, flat - r))
        # right side
        pp.moveTo(*p1)
        pp.lineTo(*p2)
        pp.lineTo(*p3)
        pp.arcMoveTo(rect, -180.0)
        pp.arcTo(rect, -180.0, -90.0)
        pp.lineTo(*p5)
        pp.lineTo(*p6)
        pp.lineTo(*p7)
        pp.lineTo(*p8)
        pp.lineTo(*p9)
        # left
        rect.moveTopRight(QPointF(-trad, flat + r))
        pp.lineTo(-p8[0], p8[1])
        pp.lineTo(-p7[0], p7[1])
        pp.lineTo(-p6[0], p6[1])
        pp.lineTo(-p5[0], p5[1])
        pp.lineTo(-p4[0], p4[1])
        pp.arcMoveTo(rect, 90)
        pp.arcTo(rect, 90, -90)
        pp.lineTo(-p2[0], p2[1])
        pp.lineTo(*p1)
        self.setPath(pp)
        return p1, p2, p3, p4, p5, p6, p7, p8, p9, tdia, sdia, oal, bdia, blen
    def _updateDims(self, p1, p2, p3, p4, p5, p6, p7, p8, p9, tdia, sdia, oal,
                    bdia, blen):
        metric = self.specs['metric']
        # tip dia dimension
        self._updateDiaDim(self.tipDiaDim, [-p2[0], p2[1]], p2, tdia, None,
                           -.75, metric)
        # shank diameter dimension
        self._updateDiaDim(self.shankDiaDim, [-p8[0], p8[1]], p8, sdia, None,
                           .75, metric)
        # body diameter dimension
        self._updateDiaDim(self.bodyDiaDim, [-p6[0], p6[1]], p6, bdia, None,
                           .75, metric)
        # body len dimension
        bltr = self.bodyLengthDim.dimText.sceneBoundingRect()
        ar = self.bodyLengthDim.arrow1.sceneBoundingRect()
        outside = True
        bLabelX = p6[0] + bltr.width() * .6
        # label inside witness lines
        if bltr.height() * 1.1 < p6[1]:
            fLabelP = QPointF(bLabelX, p6[1] * 0.5)
            if bltr.height() * 1.1 + ar.height() * 2.1 < p6[1]:
                outside = False
        # label below witness lines
        else:
            fLabelP = QPointF(bLabelX, bltr.height() * -2.0)
            if ar.height() * 2.1 < p6[1]:
                outside = False
        self.bodyLengthDim.config({'value': blen,
                                   'ref1': QPointF(*p2),
                                   'ref2': QPointF(*p6),
                                   'outside': outside,
                                   'format': '%.3fmm' if metric else '%.4f"',
                                   'pos': fLabelP,
                                   'force': 'vertical'})
        # oal len dimension
        tr = self.oalDim.dimText.sceneBoundingRect()
        ar = self.oalDim.arrow1.sceneBoundingRect()
        outside = True
        # label inside witness lines
        labelAbove = False
        slen = p8[1] - p6[1]
        if tr.height() * 1.1 + ar.height() * 1.1 < slen:
            labelY = oal - slen * 0.5
            if tr.height() * 1.1 + ar.height() * 2.1 < oal:
                outside = False
        # label above witness lines
        else:
            labelAbove = True
            labelY = oal + tr.height() * 1.1
            if ar.height() * 2.1 < oal:
                outside = False
        labelX = bLabelX + bltr.width() * .6
        labelP = QPointF(labelX, labelY)
        self.oalDim.config({'value': oal,
                            'ref1': QPointF(*p2),
                            'ref2': QPointF(*p8),
                            'outside': outside,
                            'format': '%.3fmm' if metric else '%.4f"',
                            'pos': labelP,
                            'force': 'vertical'})
        # corner radius dimension
        tr = self.radiusDim.dimText.sceneBoundingRect()
        r = self.specs['radius']
        arc = Arc({'center': QPointF(p4[0], p3[1]),
                   'radius': r,
                   'start': 90.0,
                   'span': 90.0})
        labelP = QPointF(-p6[0] - tr.width() * .6, (p6[1] + p5[1]) * .5)
        self.radiusDim.config({'value': r,
                               'pos': labelP,
                               'arc': arc,
                               'outside': True,
                               'format':
                                   'R%.3fmm' if metric else 'R%.4f"'})
        # comment label
        self._updateCommentText(labelAbove, oal, tr.height())
    def _update(self):
        self._updateDims(*self._updateProfile())
        
