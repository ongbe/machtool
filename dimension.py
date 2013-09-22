#!/usr/bin/python -t
# -*- coding: utf-8 -*-

from math import degrees, atan2, fmod, sin, cos, radians, acos
from copy import copy

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt as qt

from arc import Arc
from algo import (xsectLineRect1, linesCollinear, pointOnLine, pointOnArc,
                  isPointOnArc, xsectArcRect1, vectorToAbsAngle,
                  clamp, isPointOnLineSeg)

from strutil import dimFormat, FMTMM, FMTRIN, FMTANG


class DimArrowException(Exception): pass
class LinearDimException(Exception): pass
class RadiusDimException(Exception): pass
class AngleDimException(Exception): pass


class TextLabel(QGraphicsItem):
    """Graphical representation of a single-line text label.

    The item consists of:
      * An empty rectangle the size of the text's bounding rect.
      * The text which is centered on this item's local origin.
    
    Use the config method to update with the following specMap:
    
    String Key   Value Type   Value Description
    ----------   ----------   -----------------------------------------
    pos          QPointF      This item's position in screen coordinates
    text         string       The text to display

    Will render the bounding rect when hovered.
    """
    def __init__(self, parent=None, specMap={'pos': QPointF(),
                                             'text': '1.0'}):
        super(TextLabel, self).__init__(parent)
        self.setFlag(self.ItemIgnoresTransformations, True)
        self.specMap = copy(specMap)
        self.font = QFont("Simplex")
        self.setAcceptHoverEvents(True)
        self.config(specMap)
    def text(self):
        return self.specMap['text']
    def config(self, specMap={}):
        self.prepareGeometryChange()
        self.specMap.update(specMap)
        self.setPos(self.specMap['pos'])
        text = self.specMap['text']
        fm = QFontMetrics(self.font)
        r = QRectF(fm.boundingRect(text))
        # XXX: The next two lines are crap. They're based on a 12 point
        #      Simplex font. The default QFontMetrics bounding box will
        #      leave space on the right side.
        r.setWidth(r.width() - 0.75 * len(text))
        r.adjust(-3, 0, 3, 0)
        c = r.center()
        self.textOrigin = -c
        r.translate(-c)
        self.textBoundingRect = r
        self.hovered = False
    def boundingRect(self):
        return self.textBoundingRect
    def sceneBoundingRect(self):
        scene = self.scene()
        if scene:
            view = scene.views()[0]
            brect = self.boundingRect().toRect()
            br = view.mapToScene(brect).boundingRect()
            br.moveCenter(self.pos())
            return br
        else:
            return QRectF()
    def paint(self, painter, option, widget):
        painter.setFont(self.font)
        painter.drawText(self.textOrigin, self.specMap['text'])
        if self.hovered:
            painter.setBrush(qt.NoBrush)
            painter.drawRect(self.textBoundingRect)
    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()
    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()


# This exists so I can differentiate dimension text
# from other subclasses of TextLabel. 
class DimLabel(TextLabel):
    """A graphical representation of a dimension's text label.

    The label is dumb. It only displays text in a given format. It has no
    knowledge of the item it's referencing.
    """
    pass


class DimArrow(QGraphicsPathItem):
    """Graphical representation of a dimension arrow head.

    Use the config method to update with the following specMap:

    String Key   Value Type   Value Description
    ----------   ----------   -------------------------------------------
    pos          QPointF      Position of arrow tip in screen coordinates
    dir          QVector2D    Direction the arrow points

    The arrow tip is at this item's local origin.
    """
    length = 14                 # pixels
    width = 5                   # pixels
    def __init__(self, parent,
                 specMap={'pos': QPointF(), 'dir': QVector2D(1, 0)}):
        if specMap['dir'].isNull():
            raise DimArrowException('zero magnitude arrow vector')
        super(DimArrow, self).__init__(parent)
        self.setPen(QColor(0, 0, 0))
        self.setBrush(QBrush(QColor(0, 0, 0)))
        self.setFlag(self.ItemIgnoresTransformations, True)
        self.specMap = copy(specMap)
        self.config()
    def config(self, specMap={}):
        """Set geometry
        """
        self.prepareGeometryChange()
        self.specMap.update(specMap)
        if self.specMap['dir'].isNull():
            raise DimArrowException('zero magnitude arrow vector')
        self.setPos(self.specMap['pos'])
        v = self.specMap['dir']
        self.specMap['rotAngle'] = degrees(atan2(v.y(), v.x()))
        self._updatePainterPath()
    def setRotation():
        """Noop
        
        Rotations are done manually in _updatePainterPath()
        """
        pass
    def sceneBoundingRect(self):
        scene = self.scene()
        if scene:
            # what a hack O_o
            view = scene.views()[0]
            brect = self.boundingRect().toRect()
            zero = view.mapToScene(QPoint())
            br = view.mapToScene(brect).boundingRect()
            br.moveTopLeft(self.pos() + (br.topLeft() - zero))
            return br
        else:
            return QRectF()
    def _updatePainterPath(self):
        t = QTransform().rotate(-self.specMap['rotAngle'])
        p1 = t.map(QPointF(-self.length, self.width / 2.0))
        p2 = t.map(QPointF(-self.length, -self.width / 2.0))
        pp = QPainterPath()
        pp.moveTo(0, 0)
        pp.lineTo(p1.x(), p1.y())
        pp.lineTo(p2.x(), p2.y())
        pp.lineTo(0, 0)
        self.setPath(pp)
        

class Dimension(QGraphicsPathItem):
    """Pseudo-Abstract base class for all dimensions.
    """
    leaderLen = 30        # outside leader length (pixels)
    extensionLineExt = 5  # passed arrow tip (pixels)
    extensionLineGap = 5  # from ref point (pixels)
    jogLineLen = 30       # line attaching to radius dim label (pixels)
    gapAngle = 1.5        # from ref point to start of extension arc (degrees)
    extAngle = .5         # from arrow tip to end of extension arc (degrees)
    def __init__(self, parent=None):
        super(Dimension, self).__init__(parent)
        # TODO: A proper z value. This is just a temporary value so the
        #       dimension can be selected.
        self.setZValue(100)
        self.dimText = DimLabel(self) # all dimensions have a label
    def config(self, specMap={}):
        """Update the specs.
        """
        self.specMap.update(specMap)
        self.dimText.config({'pos': self.specMap['pos'],
                             'text': dimFormat(self.specMap['format'],
                                               self.specMap['value'])})
        if self.scene() is None:
            return False
        self.prepareGeometryChange()
        return True
    def boundingRect(self):
        r = super(Dimension, self).boundingRect()
        r = r.united(self.dimText.sceneBoundingRect())
        return r
    def setToolTip(self, toolTip):
        """Set the dimension's label tool tip text.
        """
        self.dimText.setToolTip(toolTip)
    def _addExtensionLines(self, p1, p2, ap1, ap2, pp):
        """Add extension lines to pp

        p1, p2 -- ref point locations, None to not draw that line
        ap1, ap2 -- arrow point locations
        pp -- QPainterPath
        """
        ext = self.scene().pixelsToScene(self.extensionLineExt)
        gap = self.scene().pixelsToScene(self.extensionLineGap)
        if p1 is not None:      # deja fucking vu QPointF() == None
            # From p1 to arrow1
            l1v = QVector2D(ap1 - p1)
            l1nv = l1v.normalized()
            if l1v.length() > gap:
                pp.moveTo(p1 + (l1nv * gap).toPointF())
                pp.lineTo(ap1 + (l1nv * ext).toPointF())
        if p2 is not None:
            # From p2 to arrow2
            l2v = QVector2D(ap2 - p2)
            l2nv = l2v.normalized()
            # render only if arrow tip is not too close to ref point
            if l2v.length() > gap:
                pp.moveTo(p2 + (l2nv * gap).toPointF())
                pp.lineTo(ap2 + (l2nv * ext).toPointF())
            

# TODO:
#   * Not optimized at all
class LinearDim(Dimension):
    """Graphical representation of a linear dimension.
    
    The dim consists of a DimLabel, DimArrow (x2), leader and extension lines.
    All lines are added to this item's QPainterPath.

    Use the config() method to update with the following specMap. All keys
    must be defined in __init__() or the initial call to config(). Thereafter,
    config may be called with zero or more key/value pairs to update.
    
    String Key   Value Type(s)   Value Description
    ----------   -------------   ----------------------------------------------
    value        number          Value of dim. The format key will determine
                                 how the value is displayed.
    pos          QPointF         The dim text position in scene coords.
    ref1         QPointF         First dim reference in scene coords
                 QLineF
    ref2         QPointF         Second dim reference in scene coords, If ref1
                 QLineF          is a QLineF, ref2 may be None. In this case,
                 None            the line will be dimensioned.
    outside      bool            if True, arrows point towards each other
    format       string          "%.3f", for instance
    force        string          May be:
                 None              1. 'horizontal'
                                   2. 'vertical'
                                   3. None, don't care
                                 This exists for the case where the two ref
                                 points are diagonal to one another but a
                                 vertical or horizontal dim is preferred.

    If two points are given as references, and they are not vertically or
    horizontally aligned, the orientation of the dimension depends on the
    placement of the dim label as follows.

        The O's are the two points

         1 | 2 | 3
        ---O---+---
         4 | 5 | 6
        ---+---O---
         7 | 8 | 9

         If the position is within:
         4,6 - vertical
         2,8 - horizontal
         1,3,5,7,9 - parallel to a line passing through the points (diagonal)
    
    An exception will be raised on the following conditions:
    1. refs are not a QPointF or QLineF or None
    2. If two line segments are supplied for ref1 and ref2 and
       a. they are not parallel
       b. they are on the same parent line (co-linear)
    3. If a line segment has zero length
    """
    def __init__(self, parent=None, specMap={'value': 30,
                                             'pos': QPointF(),
                                             'ref1': QPointF(-15, 0),
                                             'ref2': QPointF(15, 0),
                                             'outside': False,
                                             'format': FMTMM,
                                             'force': None}):
        super(LinearDim, self).__init__(parent)
        self.specMap = copy(specMap)
        self.arrow1 = DimArrow(self)
        self.arrow2 = DimArrow(self)
        self.config(specMap)
    def config(self, specMap={}):
        if not super(LinearDim, self).config(specMap):
            return
        ref1 = self.specMap['ref1']
        ref2 = self.specMap['ref2']
        if isinstance(ref1, QPointF) and isinstance(ref2, QPointF):
            self._configTwoPoints(ref1, ref2)
        elif isinstance(ref1, QLineF) and isinstance(ref2, QLineF):
            self._configTwoLineSegs(ref1, ref2)
        elif isinstance(ref1, QLineF) and ref2 is None:
            self._configOneLineSeg(ref1)
        elif isinstance(ref1, QPointF) and isinstance(ref2, QLineF):
            self._configPointLine(ref1, ref2)
        elif isinstance(ref1, QLineF) and isinstance(ref2, QPointF):
            self._configPointLine(ref2, ref1)
        else:
            raise LinearDimException("Illegal ref type(s): %r, %r" %
                                     (ref1, ref2))
    def _configTwoPoints(self, p1, p2):
        pos = self.specMap['pos']
        outside = self.specMap['outside']
        px, py = pos.x(), pos.y()
        p1x, p1y = p1.x(), p1.y()
        p2x, p2y = p2.x(), p2.y()
        force = self.specMap['force']
        if p1 == p2:
            raise LinearDimException("ref points are the same")
        # vertical
        if p1x == p2x:
            if force == 'horizontal':
                raise LinearDimException("LinearDim cannot be forced"
                                         " horizontal")
            self._configVertical(p1, p2, px, py, outside)
        # horizontal
        elif p1.y() == p2.y():
            if force == 'vertical':
                raise LinearDimException("LinearDim cannot be forced"
                                         " vertical")
            self._configHorizontal(p1, p2, px, py, outside)
        # points are diagonal
        else:
            rect = QRectF(p1, p2).normalized()
            posInRect = rect.contains(pos)
            if force == 'vertical':
                self._configVertical(p1, p2, px, py, outside)
            elif force == 'horizontal':
                self._configHorizontal(p1, p2, px, py, outside)
            # section 4 or 7, vertical
            elif py < rect.bottom() and py > rect.top() and not posInRect:
                self._configVertical(p1, p2, px, py, outside)
            # section 2 or 8, horizontal
            elif px > rect.left() and px < rect.right() and not posInRect:
                self._configHorizontal(p1, p2, px, py, outside)
            # section 1, 3, 5, 7, 9
            else:
                self._configParallel(p1, p2, px, py, outside)
    def _configTwoLineSegs(self, line1, line2):
        """Dimension between two parallel lines.

        line1, line2 -- QLineF

        If the lines are not parallel, raise LinearDimException.
        """
        # some checks first
        lv1 = QVector2D(line1.p1() - line1.p2())
        lv2 = QVector2D(line2.p1() - line2.p2())
        dp = lv1.dotProduct(lv1.normalized(), lv2.normalized())
        # XXX: constant 0.001
        if 1.0 - abs(dp) > 0.001:
            raise LinearDimException("Cannot dimension intersecting lines")
        if linesCollinear(line1, line2):
            raise LinearDimException("Cannot dimension collinear lines")
        pp = QPainterPath()
        pos = self.specMap['pos']
        # arrow tip positions
        ap1 = pointOnLine(pos, line1.p1(), line1.p2())
        ap2 = pointOnLine(pos, line2.p1(), line2.p2())
        # vector from label center to arrow tips
        v1 = QVector2D(ap1 - pos)
        v2 = QVector2D(ap2 - pos)
        # find nearest line, arrow and vector to label
        l1, l2 = line1, line2
        if v1.length() > v2.length():
            v1, v2 = v2, v1
            ap1, ap2 = ap2, ap1
            l1, l2 = l2, l1     # for extension lines
        # label center is outside lines
        dimOutside = v1.dotProduct(v1.normalized(), v2.normalized()) >= 0.0
        br = self.dimText.sceneBoundingRect().normalized()
        # arrows pointing in
        if self.specMap['outside']:
            leaderLen = self.scene().pixelsToScene(self.leaderLen)
            if dimOutside:
                self.arrow1.config({'pos': ap1, 'dir': v1})
                self.arrow2.config({'pos': ap2, 'dir': v2 * -1})
                xp = xsectLineRect1(QLineF(pos, ap1), br)
                if xp:
                    pp.moveTo(xp)
                    pp.lineTo(ap1)
                v = v2.normalized()
                ep = ap2 + (v2.normalized() * leaderLen).toPointF()
                pp.moveTo(ap2)
                pp.lineTo(ep)
            else:
                self.arrow1.config({'pos': ap1, 'dir': v1 * -1})
                self.arrow2.config({'pos': ap2, 'dir': v2 * -1})
                v = v2.normalized()
                ep = ap2 + (v2.normalized() * leaderLen).toPointF()
                pp.moveTo(ap2)
                pp.lineTo(ep)
                v = v1.normalized()
                ep = ap1 + (v1.normalized() * leaderLen).toPointF()
                pp.moveTo(ap1)
                pp.lineTo(ep)
        # arrows pointing out
        else:
            if dimOutside:
                self.arrow1.config({'pos': ap1, 'dir': v1 * -1})
                self.arrow2.config({'pos': ap2, 'dir': v2})
                xp = xsectLineRect1(QLineF(pos, ap2), br)
                if xp:
                    pp.moveTo(xp)
                    pp.lineTo(ap2)
            else:
                self.arrow1.config({'pos': ap1, 'dir': v1})
                self.arrow2.config({'pos': ap2, 'dir': v2})
                xp1 = xsectLineRect1(QLineF(pos, ap1), br)
                if xp1:
                    pp.moveTo(xp1)
                    pp.lineTo(ap1)
                xp2 = xsectLineRect1(QLineF(pos, ap2), br)
                if xp2:
                    pp.moveTo(xp2)
                    pp.lineTo(ap2)
        # extension lines
        # TODO: rethink this, it renders okay, but...
        p1 = ap1                # should I
        p2 = ap2                # copy apN here?
        # first            
        v1 = QVector2D(l1.p1() - ap1)
        v2 = QVector2D(l1.p2() - ap1)
        offLine = v1.dotProduct(v1.normalized(), v2.normalized()) >= 0.0
        # set v1 to closest end point
        if v1.length() > v2.length():
            v1, v2 = v2, v1
        if offLine:
            p1 = ap1 + v1.toPointF()
        # second
        v1 = QVector2D(l2.p1() - ap2)
        v2 = QVector2D(l2.p2() - ap2)
        offLine = v1.dotProduct(v1.normalized(), v2.normalized()) >= 0.0
        # set v1 to closest end point
        if v1.length() > v2.length():
            v1, v2 = v2, v1
        if offLine:
            p2 = ap2 + v1.toPointF()
        self._addExtensionLines(p1, p2, ap1, ap2, pp)
        self.setPath(pp)
    def _configOneLineSeg(self, line):
        """Dimension the given QLineF
        """
        if line.isNull():
            raise LinearDimException("Cannot dimension zero length line")
        self._configTwoPoints(line.p1(), line.p2())
    def _configPointLine(self, point, line):
        # cheat by creating a 0.0001 length line parallel to line
        # that passes through point
        v = QVector2D(line.p2() - line.p1()).normalized()
        l2 = QLineF(point, point + (v * 0.0001).toPointF())
        self._configTwoLineSegs(line, l2)
    def _configVertical(self, p1, p2, px, py, outside):
        """Define a vertical (same x coordiante) dimension.

        y1, y2 -- first and second ref point y coordinates
        px, py -- dim label center coordinates
        outside -- True if arrows should point towards each other
        """
        pp = QPainterPath()
        br = self.dimText.sceneBoundingRect().normalized()
        # ensure p1 refers to the bottom point
        if p1.y() > p2.y():
            p1, p2 = p2, p1
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        # arrows pointing in
        if outside:
            leaderLen = self.scene().pixelsToScene(self.leaderLen)
            # configure arrow heads, arrow1 is the bottom
            self.arrow1.config({'pos': QPointF(px, y1),
                                'dir': QVector2D(0, 1)})
            self.arrow2.config({'pos': QPointF(px, y2),
                                'dir': QVector2D(0, -1)})
            # dim text outside top (br top and bottom reversed)
            if br.top() > y2:
                pp.moveTo(px, br.top())
                pp.lineTo(px, y2)
                pp.moveTo(px, y1)
                pp.lineTo(px, y1 - leaderLen)
            # dim text outside bottom
            elif br.bottom() < y1:
                pp.moveTo(px, br.bottom())
                pp.lineTo(px, y1)
                pp.moveTo(px, y2)
                pp.lineTo(px, y2 + leaderLen)
            # dim text between arrows
            else:
                pp.moveTo(px, y2)
                pp.lineTo(px, y2 + leaderLen)
                pp.moveTo(px, y1)
                pp.lineTo(px, y1 - leaderLen)
        # arrows pointing out
        else:
            # configure arrow heads
            self.arrow1.config({'pos': QPointF(px, y1),
                                'dir': QVector2D(0, -1)})
            self.arrow2.config({'pos': QPointF(px, y2),
                                'dir': QVector2D(0, 1)})
            # dim text center above top
            if py > y2:
                if br.top() > y1:
                    pp.moveTo(px, br.top())
                    pp.lineTo(px, y1)
            # dim text center below bottom
            elif py < y1:
                if br.bottom() < y2:
                    pp.moveTo(px, br.bottom())
                    pp.lineTo(px, y2)
            # dim center between arrows
            else:
                if br.top() > y1:
                    pp.moveTo(px, br.top())
                    pp.lineTo(px, y1)
                if br.bottom() < y2:
                    pp.moveTo(px, br.bottom())
                    pp.lineTo(px, y2)
        # extension lines
        self._addExtensionLines(p1, p2, self.arrow1.pos(), self.arrow2.pos(),
                              pp)
        self.setPath(pp)
    def _configHorizontal(self, p1, p2, px, py, outside):
        """Define a horizontal (same y coordiante) dimension.

        x1, x2 -- first and second ref point x coordinates
        px, py -- dim label center coordinates
        outside -- True if arrows should point towards each other
        """
        pp = QPainterPath()
        br = self.dimText.sceneBoundingRect().normalized()
        # ensure x1 refers to the left point
        if p1.x() > p2.x():
            p1, p2 = p2, p1
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        # arrows pointing in
        if outside:
            leaderLen = self.scene().pixelsToScene(self.leaderLen)
            # configure arrow heads
            self.arrow1.config({'pos': QPointF(x1, py),
                                'dir': QVector2D(1, 0)})
            self.arrow2.config({'pos': QPointF(x2, py),
                                'dir': QVector2D(-1, 0)})
            # dim text center outside right
            if px > x2:
                if br.left() > x2:
                    pp.moveTo(x2, py)
                    pp.lineTo(br.left(), py)
                pp.moveTo(x1, py)
                pp.lineTo(x1 - leaderLen, py)
            # dim text center outside left
            elif px < x1:
                if br.right() < x1:
                    pp.moveTo(x1, py)
                    pp.lineTo(br.right(), py)
                pp.moveTo(x2, py)
                pp.lineTo(x2 + leaderLen, py)
            # dim text between arrows
            else:
                pp.moveTo(x1, py)
                pp.lineTo(x1 - leaderLen, py)
                pp.moveTo(x2, py)
                pp.lineTo(x2 + leaderLen, py)
        # arrows pointing out
        else:
            # configure arrow heads
            self.arrow1.config({'pos': QPointF(x1, py),
                                'dir': QVector2D(-1, 0)})
            self.arrow2.config({'pos': QPointF(x2, py),
                                'dir': QVector2D(1, 0)})
            # dim text center outside right
            if px > x2:
                if br.left() > x1:
                    pp.moveTo(br.left(), py)
                    pp.lineTo(x1, py)
            # dim text center outside left
            elif px < x1:
                if br.right() < x2:
                    pp.moveTo(br.right(), py)
                    pp.lineTo(x2, py)
            # dim center between arrows
            else:
                if br.right() < x2:
                    pp.moveTo(br.right(), py)
                    pp.lineTo(x2, py)
                if br.left() > x1:
                    pp.moveTo(br.left(), py)
                    pp.lineTo(x1, py)
        # extension lines
        self._addExtensionLines(p1, p2, self.arrow1.pos(), self.arrow2.pos(),
                              pp)
        self.setPath(pp)
    def _configParallel(self, p1, p2, px, py, outside):
        """Define a parallel (diagonal) dimension.

        p1 -- first ref point
        p2 -- second ref point
        px, py -- dimension label center point
        outside -- True if arrows should point towards each other

        p1 and p2 have different x and y coordinates
        """
        pp = QPainterPath()
        pos = QPointF(px, py)
        v = QVector2D(pos - p1)
        # from p1 to p2
        u = QVector2D(p2 - p1).normalized()
        # point on line through p1 and p2 where pos is projected
        mp = (QVector2D(p1) + v.dotProduct(v, u) * u).toPointF()
        # perpendicular vector pointing towards pos
        sv = pos - mp
        # new arrow positions
        ap1 = p1 + sv
        ap2 = p2 + sv
        # vectors from label center point to arrow tips
        lv1 = QVector2D(ap1 - pos)
        lv2 = QVector2D(ap2 - pos)
        # dim label is outside extension lines if lv1 & 2 point in the same dir
        dimOutside = lv1.dotProduct(lv1.normalized(), lv2.normalized()) >= 0.0
        br = self.dimText.sceneBoundingRect().normalized()
        # arrows pointing towards each other
        if outside:
            leaderLen = self.scene().pixelsToScene(self.leaderLen)
            self.arrow1.config({'pos': ap1, 'dir': u})
            self.arrow2.config({'pos': ap2, 'dir': u * -1})
            if dimOutside:
                if lv1.length() > lv2.length():
                    np = ap2        # ap2 is near point
                    fp = ap1
                    npv = u
                else:
                    np = ap1
                    fp = ap2
                    npv = u * -1
                pp.moveTo(np)
                xp = xsectLineRect1(QLineF(pos, np), br)
                if not xp:
                    ep = np + (npv * leaderLen).toPointF()
                    pp.lineTo(ep)
                else:
                    pp.lineTo(xp)
                ep = fp + (npv * -leaderLen).toPointF()
                pp.moveTo(fp)
                pp.lineTo(ep)
            else:
                ep = ap1 + (u * -leaderLen).toPointF()
                pp.moveTo(ap1)
                pp.lineTo(ep)
                ep = ap2 + (u * leaderLen).toPointF()
                pp.moveTo(ap2)
                pp.lineTo(ep)
        # arrows pointing away from each other
        else:
            self.arrow1.config({'pos': ap1, 'dir': u * -1})
            self.arrow2.config({'pos': ap2, 'dir': u})
            if dimOutside:
                if lv1.length() > lv2.length():
                    ep = ap1
                else:
                    ep = ap2
                xp = xsectLineRect1(QLineF(pos, ep), br)
                pp.moveTo(xp)
                pp.lineTo(ep)
            else:
                xp1 = xsectLineRect1(QLineF(pos, ap1), br)
                if not xp1:
                    pp.moveTo(ap2)
                else:
                    pp.moveTo(xp1)
                pp.lineTo(ap1)
                xp2 = xsectLineRect1(QLineF(pos, ap2), br)
                if not xp2:
                    pp.moveTo(ap1)
                else:
                    pp.moveTo(xp2)
                pp.lineTo(ap2)
        # extension lines
        self._addExtensionLines(p1, p2, self.arrow1.pos(), self.arrow2.pos(),
                              pp)
        self.setPath(pp)
    

# TODO:
#   * Not optimized at all
#   * Dimension to inside of the arc. The leader will pass THROUGH the arc
#     center. This is mutually exclusive with the next TODO.
#   * Show as a diameter dimension.
#   * Extension arc gap and distance passed arrow tip are hard-coded. Their
#     relative size will change with scene scale. But, this seems to be the
#     way at least one professional CAD apps handle it.
class RadiusDim(Dimension):
    """A graphical representation of a radius dimension.
    
    The dim consists of a DimLabel, a DimArrow, and a leader line.
    All lines are added to this item's QPainterPath.

    Use the config method to update with the following specMap. All keys must
    be defined in __init__() or the initial call to config(). Thereafter,
    config may be called with zero or more key/value pairs to update.
    
    String Key   Value Type(s)   Value Description
    ----------   -------------   ----------------------------------------------
    value        number          Value of dim. The format key will determine
                                 how the value is displayed.
    pos          QPointF         The dim text position in scene coords.
    arc          Arc             The reference arc being dimensioned.
    outside      bool            If True, arrow points towards arc center.
    
    TODO: inside is not yet implemented
    inside       bool            If True, dimension to the inside of the arc.
                                 The bent leader will pass through the center
                                 of the arc. The end of the label extension
                                 line and the arrow will always be on opposite
                                 sided of the arc center.
                                 
    format       string          "%.3f", for instance
    """
    def __init__(self, parent=None, specMap={'value': 0.5,
                                             'pos': QPointF(3.5, 3.5),
                                             'arc': Arc({'center': QPointF(),
                                                         'radius': 0.5,
                                                         'start': 0.0,
                                                         'span': 90.0}),
                                             'outside': True,
                                             'format': FMTRIN}):
        if specMap['arc'].radius() <= 0:
            raise RadiusDimException("refrenced arc radius must be > 0.0")
        super(RadiusDim, self).__init__(parent)
        self.specMap = copy(specMap)
        self.arrow = DimArrow(self)
        self.config(specMap)
    def config(self, specMap={}):
        if not super(RadiusDim, self).config(specMap):
            return
        arcRadius = self.specMap['arc'].radius()
        pos = self.specMap['pos']
        pp = QPainterPath()
        arcCenter = self.specMap['arc'].center()
        # is the label outside the arc
        labelOutside = QVector2D(pos - arcCenter).length() > arcRadius
        # is the label to the right of the arc's y axis?
        labelRight = pos.x() > arcCenter.x()
        br = self.dimText.sceneBoundingRect().normalized()
        # arrow pointing toward arc center point
        if self.specMap['outside']:
            if labelOutside:
                jogLen = self.scene().pixelsToScene(self.jogLineLen)
                if labelRight:
                    jogV = QVector2D(-1, 0).normalized()
                    jogSp = QPointF(br.left(), br.center().y())
                else:
                    jogV = QVector2D(1, 0).normalized()
                    jogSp = QPointF(br.right(), br.center().y())
                jogEp = jogSp + (jogV * jogLen).toPointF()
                ap = pointOnArc(jogEp, arcCenter, arcRadius)
                av = QVector2D(arcCenter - jogEp)
                self.arrow.config({'pos': ap, 'dir': av})
                pp.moveTo(jogSp)
                pp.lineTo(jogEp)
                pp.lineTo(ap)
            # label inside arc
            else:
                leaderLen = self.scene().pixelsToScene(self.leaderLen)
                ap = pointOnArc(pos, arcCenter, arcRadius)
                av = QVector2D(arcCenter - ap).normalized()
                self.arrow.config({'pos': ap, 'dir': av})
                # fixed len arrow leader
                ep = ap + (av * -1 * leaderLen).toPointF()
                pp.moveTo(ap)
                pp.lineTo(ep)
        # arrow pointing away from arc center
        else:
            if labelOutside:
                jogLen = self.scene().pixelsToScene(self.jogLineLen)
                if labelRight:
                    jogV = QVector2D(-1, 0).normalized()
                    jogSp = QPointF(br.left(), br.center().y())
                else:
                    jogV = QVector2D(1, 0).normalized()
                    jogSp = QPointF(br.right(), br.center().y())
                jogEp = jogSp + (jogV * jogLen).toPointF()
                ap = pointOnArc(jogEp, arcCenter, arcRadius)
                av = QVector2D(ap - arcCenter)
                self.arrow.config({'pos': ap, 'dir': av})
                pp.moveTo(arcCenter)
                pp.lineTo(ap)
                pp.lineTo(jogEp)
                pp.lineTo(jogSp)
            # label inside the arc
            else:
                ap = pointOnArc(pos, arcCenter, arcRadius)
                av = QVector2D(ap - arcCenter)
                self.arrow.config({'pos': ap, 'dir': av})
                # label to arc center leader
                xp1 = xsectLineRect1(QLineF(pos, arcCenter), br)
                if xp1:
                    pp.moveTo(xp1)
                    pp.lineTo(arcCenter)
                # label to arrow leader
                xp2 = xsectLineRect1(QLineF(pos, ap), br)
                if xp2:
                    pp.moveTo(xp2)
                    pp.lineTo(ap)
        # extension arc
        arc = self.specMap['arc']
        arcStart = arc.start()
        arcSpan = arc.span()
        if not isPointOnArc(ap, arcCenter, arcStart, arcSpan):
            # arc rect
            p = QPointF(arcRadius, arcRadius)
            r = QRectF(arcCenter - p, arcCenter + p)
            bisV = arc.bisector()
            # arc center to arrow tip vector
            apV = QVector2D(ap - arcCenter).normalized()
            # bisector rotated 90
            bis90V = QVector2D(-bisV.y(), bisV.x())
            spV = arc.startAngleVector()
            spLeftOfBisector = spV.dotProduct(spV, bis90V) >= 0.0
            epV = arc.endAngleVector()
            # is the arrow tip to the left of the bisector?
            if bis90V.dotProduct(apV, bis90V) >= 0.0:
                # is the start point left of the bisector?
                if spLeftOfBisector:
                    extensionArc = Arc.fromVectors(spV, apV, arcRadius, True)
                else:
                    extensionArc = Arc.fromVectors(epV, apV, arcRadius, True)
                pp.arcMoveTo(r, -extensionArc.start() - self.gapAngle)
                pp.arcTo(r, -extensionArc.start() - self.gapAngle,
                         -extensionArc.span() - self.extAngle)
            # arrow tip to right of bisector
            else:
                # is the start point left of the bisector?
                if spLeftOfBisector:
                    extensionArc = Arc.fromVectors(epV, apV, arcRadius, False)
                else:
                    extensionArc = Arc.fromVectors(spV, apV, arcRadius, False)
                pp.arcMoveTo(r, -extensionArc.start() + self.gapAngle)
                pp.arcTo(r, -extensionArc.start() + self.gapAngle,
                         -extensionArc.span() + self.extAngle)
        self.setPath(pp)


# TODO:
#   * Not optimized at all
#   * Horribly sloppy, redundant code, but it works!
class AngleDim(Dimension):
    """A graphical representation of an angle dimension.
    
    The dim consists of a DimLabel, a DimArrow (x2), and a leader arcs.
    All lines are added to this item's QPainterPath.

    Use the config method to update with the following specMap. All keys must
    be defined in __init__() or the initial call to config(). Thereafter,
    config may be called with zero or more key/value pairs to update.
    
    String Key   Value Type(s)   Value Description
    ----------   -------------   ----------------------------------------------
    value        number          Value of dim. The format key will determine
                                 how the value is displayed.
    pos          QPointF         The dim text position in scene coords.
    line1        QLineF          First ref line
    line2        QLineF          Second ref line
    outside      bool            If True, arrow points towards arc center.
    quadV        QVector         This vector points to the quadrant to be
                                 dimensioned. If a horizontal and vertical
                                 line are to be dimensioned, (0.707, 0.707)
                                 will point to quadrant 1. (0.707, -0.707)
                                 would point to quadrant 4. This will
                                 generally be a vector parallel to the angle
                                 bisector pointing away from the ref line's
                                 intersection point. The vector does not have
                                 to be normalized.
    format       string          "%.2f°", for instance
    """
    def __init__(self, parent=None, specMap={'value': 90.0,
                                             'pos': QPointF(0.5, 0.5),
                                             'line1': QLineF(-1, 0, 1, 0),
                                             'line2': QLineF(0, -1, 0, 1),
                                             'outside': False,
                                             'quadV': QVector2D(0.7071,
                                                                0.7071),
                                             'format': FMTANG}):
        if specMap['line1'].isNull() or specMap['line2'].isNull():
            raise AngleDimException("refrenced line has zero length")
        super(AngleDim, self).__init__(parent)
        self.specMap = copy(specMap)
        self.arrow1 = DimArrow(self)
        self.arrow2 = DimArrow(self)
        self.config(specMap)
    def config(self, specMap={}):
        if not super(AngleDim, self).config(specMap):
            return
        pp = QPainterPath()
        labelP = self.specMap['pos']
        tb = self.dimText.sceneBoundingRect()
        l1 = self.specMap['line1']
        l2 = self.specMap['line2']
        outside = self.specMap['outside']
        if l1.isNull() or l2.isNull():
            raise AngleDimException("refrenced line has zero length")
        # line intersection point
        xsectP = QPointF()
        xsectType = l1.intersect(l2, xsectP)
        if xsectType == QLineF.NoIntersection:
            raise AngleDimException("reference lines are parallel")
        # radius of arc leaders that pass through the label's center point
        labelV = QVector2D(labelP - xsectP)
        dp = labelV.dotProduct
        radius = labelV.length()
        # find fixed leader span angle
        chordLen = self.scene().pixelsToScene(self.leaderLen)
        rsq = radius * radius
        res = (rsq + rsq - chordLen * chordLen) / (2 * rsq)
        fixedLeaderSpan = degrees(acos(clamp(res, 0.0, 1.0)))
        # guess the line vectors
        v1 = QVector2D(l1.p2() - l1.p1()).normalized()
        v2 = QVector2D(l2.p2() - l2.p1()).normalized()
        # maybe reverse the line vectors so they point towards the quadrant
        # specified
        quadV = self.specMap['quadV'].normalized()
        if dp(v1, quadV) <= 0:
            v1 = -v1
        if dp(v2, quadV) <= 0:
            v2 = -v2
        # angle bisector
        bisectV = (v1 + v2).normalized()
        # angle bisector rotated 90 degrees cclw
        bisectV90 = QVector2D(-bisectV.y(), bisectV.x())
        # determine which side of the bisector the arrow tips lay
        lL = l1
        rL = l2
        lV = v1
        rV = v2
        lAp = xsectP + (lV * radius).toPointF()
        rAp = xsectP + (rV * radius).toPointF()
        if dp(bisectV90, v1) <= 0.0:
            lL, rL, lV, rV, lAp, rAp = rL, lL, rV, lV, rAp, lAp
        # find where the label lays
        lableV = labelV.normalized()
        lVperp = QVector2D(-lV.y(), lV.x())
        rVperp = QVector2D(rV.y(), -rV.x())
        # leader arc rectangle
        rect = QRectF(xsectP.x() - radius,
                      xsectP.y() + radius,
                      radius * 2, -radius * 2)

        # When left and right are mentioned, they are relative to the
        # intersection point of the two reference lines, looking in the
        # direction of the angle bisector.
        
        # label left of quad
        if dp(labelV, lVperp) > 0.0:
            if outside:
                # leader from lable to left arrow
                arc = Arc.fromVectors(labelV, lV, radius, False)
                arc.center(xsectP)
                clipP = xsectArcRect1(arc, tb)
                if clipP:
                    arc = Arc.fromVectors(QVector2D(clipP - xsectP), lV,
                                         radius, False)
                    arc.center(xsectP)
                    pp.arcMoveTo(rect, arc.start())
                    pp.arcTo(rect, arc.start(), arc.span())
                # fixed leader from right arrow
                sa = vectorToAbsAngle(rV)
                pp.arcMoveTo(rect, sa)
                pp.arcTo(rect, sa, -fixedLeaderSpan)
            else:
                # leader from label, through left arrow, to right arrow
                arc = Arc.fromVectors(labelV, rV, radius, False)
                arc.center(xsectP)
                clipP = xsectArcRect1(arc, tb)
                if clipP:
                    arc = Arc.fromVectors(QVector2D(clipP - xsectP), rV,
                                         radius, False)
                    arc.center(xsectP)
                    pp.arcMoveTo(rect, arc.start())
                    pp.arcTo(rect, arc.start(), arc.span())
        # label right of quad
        elif dp(labelV, rVperp) > 0.0:
            if outside:
                # leader from label to right arrow
                arc = Arc.fromVectors(labelV, rV, radius)
                arc.center(xsectP)
                clipP = xsectArcRect1(arc, tb)
                if clipP:
                    arc = Arc.fromVectors(QVector2D(clipP - xsectP), rV,
                                         radius)
                    arc.center(xsectP)
                    pp.arcMoveTo(rect, arc.start())
                    pp.arcTo(rect, arc.start(), arc.span())
                # fixed length leader from left arrow
                sa = vectorToAbsAngle(lV)
                pp.arcMoveTo(rect, sa)
                pp.arcTo(rect, sa, fixedLeaderSpan)
            else:
                # leader from label, through right arrow, to left arrow
                arc = Arc.fromVectors(labelV, lV, radius)
                arc.center(xsectP)
                clipP = xsectArcRect1(arc, tb)
                if clipP:
                    arc = Arc.fromVectors(QVector2D(clipP - xsectP), lV,
                                         radius)
                    arc.center(xsectP)
                    pp.arcMoveTo(rect, arc.start())
                    pp.arcTo(rect, arc.start(), arc.span())
        # label inside quad
        else:
            if outside:
                # fixed length leader from right arrow
                sa = vectorToAbsAngle(rV)
                pp.arcMoveTo(rect, sa)
                pp.arcTo(rect, sa, -fixedLeaderSpan)
                # from left arrow
                sa = vectorToAbsAngle(lV)
                pp.arcMoveTo(rect, sa)
                pp.arcTo(rect, sa, fixedLeaderSpan)
            else:
                # leader from label to left arrow
                clipP = xsectArcRect1(Arc.fromVectors(labelV, lV, radius), tb)
                if clipP:
                    arc = Arc.fromVectors(QVector2D(clipP - xsectP), lV,
                                          radius)
                    pp.arcMoveTo(rect, arc.start())
                    pp.arcTo(rect, arc.start(), arc.span())
                # to right arrow
                clipP = xsectArcRect1(Arc.fromVectors(labelV, rV, radius,
                                                      False), tb)
                if clipP:
                    arc = Arc.fromVectors(QVector2D(clipP - xsectP), rV,
                                          radius, False)
                    pp.arcMoveTo(rect, arc.start())
                    pp.arcTo(rect, arc.start(), arc.span())
        # arrow tips
        if outside:
            self.arrow1.config({'pos': lAp,
                                'dir': -QVector2D(-lV.y(), lV.x())})
            self.arrow2.config({'pos': rAp,
                                'dir': -QVector2D(rV.y(), -rV.x())})
        else:
            self.arrow1.config({'pos': lAp,
                                'dir': QVector2D(-lV.y(), lV.x())})
            self.arrow2.config({'pos': rAp,
                                'dir': QVector2D(rV.y(), -rV.x())})
        # Find the end points closest to their arrow tips for extension lines
        # Don't render the extension if the arrow tip is on its line.
        p1 = None
        if not isPointOnLineSeg(lAp, lL):
            p1 = lL.p1()
            if QVector2D(lAp - lL.p2()).length() \
                    < QVector2D(lAp - p1).length():
                p1 = lL.p2()
        p2 = None
        if not isPointOnLineSeg(rAp, rL):
            p2 = rL.p1()
            if QVector2D(rAp - rL.p2()).length() \
                    < QVector2D(rAp - p2).length():
                p2 = rL.p2()
        self._addExtensionLines(p1, p2, lAp, rAp, pp)
        self.setPath(pp)
