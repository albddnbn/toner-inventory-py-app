from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import qtawesome as qta

class Example(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Example')
        self.setGeometry(100, 100, 400, 300)

        # Create a button with a QtAwesome icon
        icon = qta.icon('fa5s.heart', color='red')
        self.btn = QPushButton(icon, 'test', self)
        self.btn.setGeometry(100, 100, 50, 50)
        self.btn.clicked.connect(self.change_icon_color)

    def change_icon_color(self):
        # Change the color of the icon when the button is clicked
        color = QColor("#ffffff")
        icon = qta.icon('fa5s.heart', color=color)
        self.btn.setIcon(icon)

if __name__ == '__main__':
    app = QApplication([])
    ex = Example()
    ex.show()
    app.exec_()
