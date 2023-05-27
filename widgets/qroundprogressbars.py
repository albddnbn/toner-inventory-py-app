#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#######################################################
#
# Copyright 2017 Pete Alexandrou
#
# Ported to Python from the original works in C++ by:
#
#     Sintegrial Technologies (c) 2015
#     https://sourceforge.net/projects/qroundprogressbar
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#######################################################
import operator
from enum import Enum
from PyQt5.QtCore import pyqtSlot, QPointF, Qt, QRectF
from PyQt5.QtGui import (QPalette, QConicalGradient, QGradient, QRadialGradient,
                         QFontMetricsF, QFont, QPainter, QPen, QImage,
                         QPaintEvent, QColor,QLinearGradient)
from PyQt5.QtWidgets import (QWidget)


class QRoundProgressBar(QWidget):

    # CONSTANTS

    PositionLeft = 180
    PositionTop = 90
    PositionRight = 0
    PositionBottom = -90

    # CONSTRUCTOR ---------------------------------------------------

    def __init__(self, parent=None, linecolor:str="", stockvalue:int=0):
        """
        __init__ Displays a grey circular line, partially covered by a colored circular line. In the center of the circle is a number, which corresponds to the item's stock.

        The radial is 'filled' corresponding to the item's stock value.

        Args:
            parent (_type_, optional): parent Qt object. Defaults to None.
            linecolor (str, optional): color of line - can be cyan, magenta, yellow, black, etc. Defaults to "".
            stockvalue (int, optional): item's stock value, pulled from 'inventory' table. Defaults to 0.
        """
        super(QRoundProgressBar, self).__init__(parent)
        self.colors_dict = {
            'cyan': '#00B7EB', 'yellow': '#ffff00', 'magenta': '#ff00ff',
            'black': '#0f0f0f', 'matte black': '#333333', 'photo black': '#444444',
            '': '#333333',
            'grey': '#808080',
            'gray': '#808080', }
        self.hsl_colors = {
            'cyan': (193, 100, 46),
            'yellow': (60, 100, 50),
            'magenta': (300, 100, 50),
            'black': (0, 0, 0),
            'matte black': (0, 0, 20), 'photo black': (0, 0, 27), '': (0, 0, 20), 'grey': (0, 0, 50), 'gray': (0, 0, 50)
        }
        
        # self.setProperty("class", "tonerradial")

        # self.linecolor = QColor(self.colors_dict[linecolor])
        self.linecolor = linecolor
        # self.description = description
        self.m_min = 0
        self.m_max = 10
        self.m_value = stockvalue
        self.m_nullPosition = QRoundProgressBar.PositionRight
        self.m_barStyle = self.BarStyle.DONUT
        self.m_outlinePenWidth = 1
        # set default width to 5 to make it thicker, 1 is way too thin
        self.m_dataPenWidth = 5
        self.m_rebuildBrush = False
        self.m_format = '%p%'
        self.m_decimals = 1
        self.m_updateFlags = self.UpdateFlags.PERCENT
        self.m_gradientData = None
        self.text_visability = True
        # set tooltip
        # parent.setToolTip(description)
        

    # ENUMS ---------------------------------------------------------

    class BarStyle(Enum):
        DONUT = 0,
        PIE = 1,
        LINE = 2,
        EXPAND = 3

    class UpdateFlags(Enum):
        VALUE = 0,
        PERCENT = 1,
        MAX = 2

    # GETTERS -------------------------------------------------------

    def minimum(self):
        return self.m_min

    def maximum(self):
        return self.m_max

    def isTextvisabile(self):
        return self.text_visability

    # SETTERS -------------------------------------------------------

    def setNullPosition(self, position: float):
        if position != self.m_nullPosition:
            self.m_nullPosition = position
            self.m_rebuildBrush = True
            self.update()

    def setBarStyle(self, style: BarStyle):
        if style != self.m_barStyle:
            self.m_barStyle = style
            self.m_rebuildBrush = True
            self.update()

    def setOutlinePenWidth(self, width: float):
        if width != self.m_outlinePenWidth:
            self.m_outlinePenWidth = width
            self.update()

    def setDataPenWidth(self, width: float):
        if width != self.m_dataPenWidth:
            self.m_dataPenWidth = width
            self.update()

    def setDataColors(self, stopPoints: list):
        if stopPoints != self.m_gradientData:
            self.m_gradientData = stopPoints
            self.m_rebuildBrush = True
            self.update()

    def setFormat(self, val: str):
        if val != self.m_format:
            self.m_format = val
            self.valueFormatChanged()

    def resetFormat(self):
        self.m_format = None
        self.valueFormatChanged()

    def setDecimals(self, count: int):
        if count >= 0 and count != self.m_decimals:
            self.m_decimals = count
            self.valueFormatChanged()

    def setTextVisability(self, show: bool):
        if show != self.text_visability:
            self.text_visability = show
            self.update()

    # SLOTS ---------------------------------------------------------

    @pyqtSlot(float, float)
    def setRange(self, minval: float, maxval: float):
        self.m_min = minval
        self.m_max = maxval
        if self.m_max < self.m_min:
            self.m_min = maxval
            self.m_max = minval
        if self.m_value < self.m_min:
            self.m_value = self.m_min
        elif self.m_value > self.m_max:
            self.m_value = self.m_max
        self.m_rebuildBrush = True
        self.update()

    @pyqtSlot(float)
    def setMinimum(self, val: float):
        self.setRange(val, self.m_max)

    @pyqtSlot(float)
    def setMaximum(self, val: float):
        self.setRange(self.m_min, val)

    @pyqtSlot(int)
    def setValue(self, val: int):
        if self.m_value != val:
            if val < self.m_min:
                self.m_value = self.m_min
            elif val > self.m_max:
                self.m_value = self.m_max
            else:
                self.m_value = val
            self.update()

    # PAINTING ------------------------------------------------------

    def paintEvent(self, event: QPaintEvent):
        outerRadius = min(self.width(), self.height())
        baseRect = QRectF(1, 1, outerRadius - 2, outerRadius - 2)
        buffer = QImage(outerRadius, outerRadius,
                        QImage.Format_ARGB32_Premultiplied)
        p = QPainter(buffer)
        p.setRenderHint(QPainter.Antialiasing)
        self.rebuildDataBrushIfNeeded()
        self.drawBackground(p, buffer.rect())
        if self.m_value > 0:
            # delta = (self.m_max - self.m_min) / (self.m_value - self.m_min)
            delta = ((self.m_value - self.m_min) /
                     (self.m_max - self.m_min)) * 10

            # print(f"m value is: {self.m_value} \ndelta is :{delta}")
        else:
            delta = 0
        self.drawValue(p, baseRect, self.m_value, delta)
        self.drawBase(p, baseRect)

        innerRect, innerRadius = self.calculateInnerRect(outerRadius)
        self.drawInnerBackground(p, innerRect)
        self.conditionalDrawText(self.text_visability,
                                 p, innerRect, innerRadius, self.m_value)
        p.end()
        painter = QPainter(self)
        painter.fillRect(baseRect, self.palette().window())
        painter.drawImage(0, 0, buffer)

    def drawBackground(self, p: QPainter, baseRect: QRectF):
        p.fillRect(baseRect, self.palette().window())

    def drawBase(self, p: QPainter, baseRect: QRectF):
        """
        Draws the colored line, that goes over the greyish background circular line
        """
        p.setPen(QPen(self.linecolor, self.m_outlinePenWidth))

        p.setBrush(Qt.NoBrush)

        # THIS LINE DRAWS THE COLORED CIRCULAR LINE (CYAN, MAGENTA, ETC)
        center = baseRect.center()
        # just self.m_outlinePenWidth puts the line on the inside edge of circle, leave it out and the colored line is on outside edge of circle
        radius = baseRect.width() / 2 - (self.m_outlinePenWidth/2)

        angle = self.m_value * 360 / 100
        p.drawArc(center.x()-radius, center.y() - radius, radius*2, radius*2, 0, (angle*16*10))
        # p.drawEllipse(baseRect.adjusted(self.m_outlinePenWidth / 2, self.m_outlinePenWidth / 2,
        #                                 -self.m_outlinePenWidth / 2, -self.m_outlinePenWidth / 2))

    def drawValue(self, p: QPainter, baseRect: QRectF, value: float, delta: float):
        """
        drawValue Actually draws the background circular line, NOT the colored line.

        Args:
            p (QPainter): _description_
            baseRect (QRectF): _description_
            value (float): _description_
            delta (float): _description_
        """
        if self.m_barStyle == self.BarStyle.LINE:
            gradient = QLinearGradient(
                baseRect.topLeft(), baseRect.bottomRight())
            gradient.setColorAt(0, QColor("#CCC8C8"))
            gradient.setColorAt(1, QColor("#CCC8C8"))
            p.setPen(QPen(gradient, self.m_dataPenWidth))
            p.setBrush(Qt.NoBrush)
            if self.m_value == 0:
                p.drawEllipse(baseRect.adjusted(self.m_outlinePenWidth / 2, self.m_outlinePenWidth / 2,
                                                -self.m_outlinePenWidth / 2, -self.m_outlinePenWidth / 2))
            else:

                # if value == self.m_max:
                #     p.drawEllipse(baseRect.adjusted(self.m_outlinePenWidth / 2, self.m_outlinePenWidth / 2,
                #                                     -self.m_outlinePenWidth / 2, -self.m_outlinePenWidth / 2))
                # else:

                #     arcLength = 360 / delta
                #     # p.drawArc(baseRect.adjusted(self.m_outlinePenWidth / 2, self.m_outlinePenWidth / 2,
                #     #                             -self.m_outlinePenWidth / 2, -self.m_outlinePenWidth / 2),
                #     #           int(self.m_nullPosition * 16),
                #     #           int(-arcLength * 16))
                #     p.drawArc(baseRect.adjusted(self.m_outlinePenWidth / 2, self.m_outlinePenWidth / 2,
                #                 -self.m_outlinePenWidth / 2, -self.m_outlinePenWidth / 2),
                # int(self.m_nullPosition * 16),
                # int(-arcLength * 16))
                p.drawEllipse(baseRect.adjusted(self.m_outlinePenWidth / 2, self.m_outlinePenWidth / 2,
                                                -self.m_outlinePenWidth / 2, -self.m_outlinePenWidth / 2))

            return

        # dataPath = QPainterPath()
        # dataPath.setFillRule(Qt.WindingFill)
        # if value == self.m_max:
        #     dataPath.addEllipse(baseRect)
        # else:
        #     arcLength = 360 / delta
        #     dataPath.moveTo(baseRect.center())
        #     dataPath.arcTo(baseRect, self.m_nullPosition, -arcLength)
        #     dataPath.lineTo(baseRect.center())
        # p.setBrush(self.palette().highlight())
        # p.setPen(QPen(self.palette().shadow().color(), self.m_dataPenWidth))
        # p.drawPath(dataPath)

    def calculateInnerRect(self, outerRadius: float):
        if self.m_barStyle in (self.BarStyle.LINE, self.BarStyle.EXPAND):
            innerRadius = outerRadius - self.m_outlinePenWidth
        else:
            innerRadius = outerRadius * 0.75
        delta = (outerRadius - innerRadius) / 2
        innerRect = QRectF(delta, delta, innerRadius, innerRadius)
        return innerRect, innerRadius

    def drawInnerBackground(self, p: QPainter, innerRect: QRectF):
        if self.m_barStyle == self.BarStyle.DONUT:
            p.setBrush(self.palette().alternateBase())
            p.drawEllipse(innerRect)

    def drawText(self, p: QPainter, innerRect: QRectF, innerRadius: float, value: float):
        if not self.m_format:
            return
        f = QFont(self.font())
        f.setPixelSize(10)
        fm = QFontMetricsF(f)
        maxWidth = fm.width(self.valueToText(self.m_max))
        delta = innerRadius / maxWidth
        fontSize = f.pixelSize() * delta * 0.75
        f.setPixelSize(int(fontSize))
        p.setFont(f)
        textRect = QRectF(innerRect)
        p.setPen(self.palette().text().color())
        p.drawText(textRect, Qt.AlignCenter, self.valueToText(value))

    def conditionalDrawText(self, visability, p: QPainter = None, innerRect: QRectF = None, innerRadius: float = None, value: float = None):
        if visability:
            self.drawText(p, innerRect, innerRadius, value)

    def valueToText(self, value: float):
        textToDraw = self.m_format
        if self.m_updateFlags == self.UpdateFlags.VALUE:
            textToDraw = textToDraw.replace(
                '%v', str(round(value, self.m_decimals)))
        if self.m_updateFlags == self.UpdateFlags.PERCENT:
            procent = (value - self.m_min) / (self.m_max - self.m_min) * 100
            textToDraw = textToDraw.replace(
                '%p', str(round(procent, self.m_decimals)))
        if self.m_updateFlags == self.UpdateFlags.MAX:
            textToDraw = textToDraw.replace(
                '%m', str(round(self.m_max - self.m_min + 1, self.m_decimals)))
        return textToDraw

    def valueFormatChanged(self):
        if operator.contains(self.m_format, '%v'):
            self.m_updateFlags = self.UpdateFlags.VALUE
        if operator.contains(self.m_format, '%p'):
            self.m_updateFlags = self.UpdateFlags.PERCENT
        if operator.contains(self.m_format, '%m'):
            self.m_updateFlags = self.UpdateFlags.MAX
        self.update()

    def rebuildDataBrushIfNeeded(self):
        # if not self.m_rebuildBrush or not self.m_gradientData or self.m_barStyle == self.BarStyle.LINE:
        if not self.m_rebuildBrush or not self.m_gradientData:

            return
        self.m_rebuildBrush = False
        p = self.palette()
        if self.m_barStyle == self.BarStyle.EXPAND:
            dataBrush = QRadialGradient(0.5, 0.5, 0.5, 0.5, 0.5)
            dataBrush.setCoordinateMode(QGradient.StretchToDeviceMode)
            for i in range(0, len(self.m_gradientData)):
                dataBrush.setColorAt(
                    self.m_gradientData[i][0], self.m_gradientData[i][1])
            p.setBrush(QPalette.Highlight, dataBrush)
        else:
            dataBrush = QConicalGradient(
                QPointF(0.5, 0.5), self.m_nullPosition)
            dataBrush.setCoordinateMode(QGradient.StretchToDeviceMode)
            for i in range(0, len(self.m_gradientData)):
                dataBrush.setColorAt(
                    1 - self.m_gradientData[i][0], self.m_gradientData[i][1])
            p.setBrush(QPalette.Highlight, dataBrush)
        self.setPalette(p)