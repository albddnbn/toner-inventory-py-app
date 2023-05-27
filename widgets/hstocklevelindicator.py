import sys
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QLinearGradient


class HStockLevelIndicator(QWidget):
    def __init__(self, stocklevel, parent=None, size=80):
        """
        __init__ QWidget that looks like a battery meter on a cell phone/other device. Holds 8-10 red rectangles, then draws a number of green rectangles over top of the red ones corresponding to how many of the item is in stock.

        Something with rounded edges (rounded rectangle), and glowing red/green (or other color) rectangles might look good. Also some shading around the grey rectangle to give it some depth.


        Args:
            stocklevel (int): amount of the item currently in stock
            parent (_type_, optional): parent Qt object. Defaults to None.
            size (int, optional): Single integer relating to total area occupied by widget. Defaults to 150.
        """
        super().__init__(parent)
        self.thesize = min(150, size)
        self.stocklevel = stocklevel
        self.setProperty("class", "HStockLevelIndicator")
        # self.setMinimumSize(self.thesize * 2, self.thesize//2)
        # self.setMaximumSize(self.thesize * 2, self.thesize//2)
        self.show()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        # red rectangles
        bg_brush = QBrush(QColor("#9d9d9d"))
        qp.setBrush(bg_brush)
        # background/frame rectangle
        qp.setPen(QPen(QColor("#1e1e1e"), 2))
        # qp.drawRect(0, 0, self.width(), self.height())

        # Draw green rectangles
        rect_width = self.thesize // 12  # set a fixed width of 25 pixels
        qp.setPen(QPen(QColor("#1e1e1e"), 1))
        rect_gap = rect_width // 1.5  # set a fixed gap of 12 pixels
        num_rects = 12  # only draw up to 12 rectangles
        for i in range(num_rects):
            rect_x = 5  # set some left margin for the rectangles
            rect_height = self.thesize // 2
            rect_y = self.height() // 2 - rect_height // 2
            rect_x = i * (rect_width + rect_gap) + rect_gap

            if i < self.stocklevel:
                if i < 1:
                    start_color = QColor("#f71d1d")
                    end_color = QColor("#870606")
                elif i < 2:
                    start_color = QColor("#ffe11c")
                    end_color = QColor("#ffd300")
                else:
                    start_color = QColor("#00b600")
                    end_color = QColor("#007a00")
                gradient = QLinearGradient(rect_x, rect_y, rect_x, rect_y + rect_height)
                gradient.setColorAt(0, start_color)
                gradient.setColorAt(1, end_color)
                qp.setBrush(QBrush(gradient))
                qp.setPen(QPen(QColor("#1e1e1e"), 2))
            else:
                qp.setBrush(QBrush(QColor("#9d9d9d")))
                qp.setPen(QPen(QColor("#1e1e1e"), 1))
            qp.drawRoundedRect(rect_x, rect_y, rect_width, rect_height, rect_height // 8, rect_height // 8)

        qp.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = HStockLevelIndicator(stocklevel=6, parent=None)
    # win.rotate()
    win.show()
    sys.exit(app.exec_())