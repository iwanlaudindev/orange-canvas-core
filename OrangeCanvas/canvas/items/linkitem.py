"""
Link Item

"""

from PyQt4.QtGui import (
    QGraphicsItem, QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsObject,
    QGraphicsDropShadowEffect,
    QPen, QBrush, QColor, QPainterPath
)

from PyQt4.QtCore import (
    Qt, QPointF, QRectF
)

from .nodeitem import SHADOW_COLOR


class LinkCurveItem(QGraphicsPathItem):
    """Link curve item. The main component of `LinkItem`.
    """
    def __init__(self, parent):
        QGraphicsPathItem.__init__(self, parent)
        assert(isinstance(parent, LinkItem))
        self.__canvasLink = parent
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.RightButton)
        self.setAcceptedMouseButtons(Qt.LeftButton)

        self.shadow = QGraphicsDropShadowEffect(
            blurRadius=5, color=QColor(SHADOW_COLOR),
            offset=QPointF(0, 0)
        )

        self.normalPen = QPen(QBrush(QColor("#9CACB4")), 2.0)
        self.hoverPen = QPen(QBrush(QColor("#7D7D7D")), 2.1)
        self.setPen(self.normalPen)
        self.setGraphicsEffect(self.shadow)
        self.shadow.setEnabled(False)

        self.__hover = False

    def hoverEnterEvent(self, event):
        self.setHoverState(True)
        return QGraphicsPathItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        self.setHoverState(False)
        return QGraphicsPathItem.hoverLeaveEvent(self, event)

    def setHoverState(self, state):
        self.__hover = state
        self._update()
        self.__canvasLink.setHoverState(state)

    def _update(self):
        shadow_enabled = self.__hover
        if self.shadow.isEnabled() != shadow_enabled:
            self.shadow.setEnabled(shadow_enabled)

        link_enabled = self.isEnabled()
        if link_enabled:
            pen_style = Qt.SolidLine
        else:
            pen_style = Qt.DashLine

        if self.__hover:
            pen = self.hoverPen
        else:
            pen = self.normalPen

        pen.setStyle(pen_style)
        self.setPen(pen)


class LinkAnchorIndicator(QGraphicsEllipseItem):
    """A visual indicator of the link anchor point at both ends
    of the `LinkItem`.

    """
    def __init__(self, *args):
        QGraphicsEllipseItem.__init__(self, *args)
        self.setRect(-3, -3, 6, 6)
        self.setPen(QPen(Qt.NoPen))
        self.normalBrush = QBrush(QColor("#9CACB4"))
        self.hoverBrush = QBrush(QColor("#7D7D7D"))
        self.setBrush(self.normalBrush)
        self.__hover = False

    def setHoverState(self, state):
        """The hover state is set by the LinkItem.
        """
        self.__hover = state
        if state:
            self.setBrush(self.hoverBrush)
        else:
            self.setBrush(self.normalBrush)


class LinkItem(QGraphicsObject):
    """A Link in the canvas.
    """

    Z_VALUE = 0
    """Z value of the item"""

    def __init__(self, *args):
        QGraphicsObject.__init__(self, *args)
        self.setFlag(QGraphicsItem.ItemHasNoContents, True)
        self.setAcceptedMouseButtons(Qt.RightButton)

        self.setZValue(self.Z_VALUE)

        self.sourceItem = None
        self.sourceAnchor = None
        self.sinkItem = None
        self.sinkAnchor = None
        self.curveItem = LinkCurveItem(self)
        self.sourceIndicator = LinkAnchorIndicator(self)
        self.sinkIndicator = LinkAnchorIndicator(self)
        self.sourceIndicator.hide()
        self.sinkIndicator.hide()

        self.hover = False

    def setSourceItem(self, item, anchor=None):
        """Set the source `item` (:class:`CanvasNodeItem`). Use `anchor`
        (:class:`AnchorPoint) as the curve start point (if `None` a new
        output anchor will be created).

        Setting item to `None` and a valid anchor is a valid operation
        (for instance while mouse dragging one and of the link).

        """
        if item is not None and anchor is not None:
            if anchor not in item.outputAnchors:
                raise ValueError("Anchor must be belong to the item")

        if self.sourceItem != item:
            if self.sourceAnchor:
                # Remove a previous source item and the corresponding anchor
                self.sourceAnchor.scenePositionChanged.disconnect(
                    self._sourcePosChanged
                )

                if self.sourceItem is not None:
                    self.sourceItem.removeOutputAnchor(self.sourceAnchor)

                self.sourceItem = self.sourceAnchor = None

            self.sourceItem = item

            if item is not None and anchor is None:
                # Create a new output anchor for the item if none is provided.
                anchor = item.newOutputAnchor()

            # Update the visibility of the start point indicator.
            self.sourceIndicator.setVisible(bool(item))

        if anchor != self.sourceAnchor:
            if self.sourceAnchor is not None:
                self.sourceAnchor.scenePositionChanged.disconnect(
                    self._sourcePosChanged
                )

            self.sourceAnchor = anchor

            if self.sourceAnchor is not None:
                self.sourceAnchor.scenePositionChanged.connect(
                    self._sourcePosChanged
                )

        self.__updateCurve()

    def setSinkItem(self, item, anchor=None):
        """Set the sink `item` (:class:`CanvasNodeItem`). Use `anchor`
        (:class:`AnchorPoint) as the curve end point (if `None` a new
        input anchor will be created).

        Setting item to `None` and a valid anchor is a valid operation
        (for instance while mouse dragging one and of the link).
        """
        if item is not None and anchor is not None:
            if anchor not in item.inputAnchors:
                raise ValueError("Anchor must be belong to the item")

        if self.sinkItem != item:
            if self.sinkAnchor:
                # Remove a previous source item and the corresponding anchor
                self.sinkAnchor.scenePositionChanged.disconnect(
                    self._sinkPosChanged
                )

                if self.sinkItem is not None:
                    self.sinkItem.removeInputAnchor(self.sinkAnchor)

                self.sinkItem = self.sinkAnchor = None

            self.sinkItem = item

            if item is not None and anchor is None:
                # Create a new input anchor for the item if none is provided.
                anchor = item.newInputAnchor()

            # Update the visibility of the end point indicator.
            self.sinkIndicator.setVisible(bool(item))

        if self.sinkAnchor != anchor:
            if self.sinkAnchor is not None:
                self.sinkAnchor.scenePositionChanged.disconnect(
                    self._sinkPosChanged
                )

            self.sinkAnchor = anchor

            if self.sinkAnchor is not None:
                self.sinkAnchor.scenePositionChanged.connect(
                    self._sinkPosChanged
                )

        self.__updateCurve()

    def _sinkPosChanged(self, *arg):
        self.__updateCurve()

    def _sourcePosChanged(self, *arg):
        self.__updateCurve()

    def __updateCurve(self):
        if self.sourceAnchor and self.sinkAnchor:
            source_pos = self.sourceAnchor.anchorScenePos()
            sink_pos = self.sinkAnchor.anchorScenePos()
            source_pos = self.curveItem.mapFromScene(source_pos)
            sink_pos = self.curveItem.mapFromScene(sink_pos)
            # TODO: get the orthogonal angle to the anchors path.
            path = QPainterPath()
            path.moveTo(source_pos)
            path.cubicTo(source_pos + QPointF(60, 0),
                         sink_pos - QPointF(60, 0),
                         sink_pos)

            self.curveItem.setPath(path)
            self.sourceIndicator.setPos(source_pos)
            self.sinkIndicator.setPos(sink_pos)
        else:
            self.setHoverState(False)
            self.curveItem.setPath(QPainterPath())

    def removeLink(self):
        self.setSinkItem(None)
        self.setSourceItem(None)
        self.__updateCurve()

    # TODO: This item should control the hover state not its child.
    #       (use sceneEventFilter on curveItem??).
    def setHoverState(self, state):
        if self.hover != state:
            self.hover = state
            self.sinkIndicator.setHoverState(state)
            self.sourceIndicator.setHoverState(state)

    def boundingRect(self):
        return QRectF()

    def setEnabled(self, enabled):
        QGraphicsObject.setEnabled(self, enabled)
        self.curveItem._update()
