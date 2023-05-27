# LED Indicator widget modified from: https://github.com/nlamprian/pyqt5-led-indicator-widget
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QRadialGradient, QMouseEvent
from PyQt5.QtWidgets import QAbstractButton
from PyQt5.QtCore import *
# from PyQt5.QtGui import *
# from PyQt5.QtWidgets import *


class LedIndicator(QAbstractButton):
    scaledSize = 1125.0
    # TODO: make it so when you click the LEDs - nothing happens. right now, they turn on / off i think.
    def __init__(self, parent=None, color: str = "green"):
        """
        __init__  LED Indicator class adapted from **nlamprian** <link>https://github.com/nlamprian/pyqt5-led-indicator-widget</link>

        _extended_summary_

        Args:
            parent (_type_, optional): parent Qt object. Defaults to None.
            color (str, optional): Color of LED, ex: "red" or "green" are the only available choices right now. Defaults to "green".
        """
        QAbstractButton.__init__(self, parent)

        self.setMinimumSize(100, 100)
        self.setCheckable(True)
        # each red or green LED is composed of a few different shades, to make it look more like a light
        self.colors_dict = {
            "green": {
                "on1": QColor("#00FF00"),
                "on2": QColor("#00C000"),
                "off1": QColor("#001C00"),
                "off2": QColor("#008000"),
                "glow": QColor("#2aff2a70")
            },
            "red": {
                "on1": QColor("#FF0000"),
                "on2": QColor("#C00000"),
                "off1": QColor("#1C0000"),
                "off2": QColor("#800000"),
                "glow": QColor("#ff2a2a70")
            }
        }
        self.on_color_1 = self.colors_dict[color]["on1"]
        self.on_color_2 = self.colors_dict[color]["on2"]
        self.off_color_1 = self.colors_dict[color]["off1"]
        self.off_color_2 = self.colors_dict[color]["off2"]
        self.glow = self.colors_dict[color]["glow"]
    def mousePressEvent(self, e: QMouseEvent) -> None:
        pass
        # return super().mousePressEvent(e)
    def resizeEvent(self, QResizeEvent):
        self.update()

    def paintEvent(self, QPaintEvent):
        realSize = min(self.width(), self.height())

        painter = QPainter(self)
        pen = QPen(Qt.black)
        pen.setWidth(1)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(realSize / self.scaledSize, realSize / self.scaledSize)

        # add darker gradient around outside
        gradient = QRadialGradient(QPointF(0, 0), 1500, QPointF(500, 500))
        gradient.setColorAt(0, QColor("#1c1c1c"))
        gradient.setColorAt(1, QColor("#dedede"))
        painter.setPen(pen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), 520, 520)

        # outer grey radial gradient border
        gradient = QRadialGradient(
            QPointF(-500, -500), 1500, QPointF(-500, -500))
        gradient.setColorAt(0, QColor("#e0e0e0"))
        gradient.setColorAt(1, QColor("#1c1c1c"))
        painter.setPen(pen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), 500, 500)
        # inner grey radial gradient border
        gradient = QRadialGradient(QPointF(500, 500), 1500, QPointF(500, 500))
        gradient.setColorAt(0, QColor("#e0e0e0"))
        gradient.setColorAt(1, QColor("#1c1c1c"))
        painter.setPen(pen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), 450, 450)
        # the red or green part
        painter.setPen(pen)
        if self.isChecked():
            gradient = QRadialGradient(
                QPointF(-500, -500), 1500, QPointF(-500, -500))
            gradient.setColorAt(0, self.on_color_1)
            gradient.setColorAt(1, self.on_color_2)
        else:
            gradient = QRadialGradient(
                QPointF(500, 500), 1500, QPointF(500, 500))
            gradient.setColorAt(0, self.off_color_1)
            gradient.setColorAt(1, self.off_color_2)

        painter.setBrush(gradient)
        painter.drawEllipse(QPointF(0, 0), 400, 400)

        # draw greyish gradient for inside the LED / on top of green/red color to give it some depth
        gradient = QRadialGradient(QPointF(0, 0), 1500, QPointF(500, 500))
        gradient.setColorAt(0, QColor("#323232"))
        gradient.setColorAt(1, QColor("#ffffff"))
        painter.setPen(pen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), 300, 300)

    def turn_on(self):
        self.setChecked(True)

    def turn_off(self):
        self.setChecked(False)

    @pyqtProperty(QColor)
    def onColor1(self) -> str:
        return self.on_color_1

    @onColor1.setter
    def onColor1(self, color):
        self.on_color_1 = color

    @pyqtProperty(QColor)
    def onColor2(self) -> str:
        return self.on_color_2

    @onColor2.setter
    def onColor2(self, color):
        self.on_color_2 = color

    @pyqtProperty(QColor)
    def offColor1(self) -> str:
        return self.off_color_1

    @offColor1.setter
    def offColor1(self, color):
        self.off_color_1 = color

    @pyqtProperty(QColor)
    def offColor2(self) -> str:
        return self.off_color_2

    @offColor2.setter
    def offColor2(self, color):
        self.off_color_2 = color

