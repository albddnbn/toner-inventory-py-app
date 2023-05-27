import sys
import yaml
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QListWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
    QLabel,
)
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QCursor
#  App-specific imports
from widgets.iconbuttons import IconButton
from utils.toner_utils import initialize_config


class ColumnEdit(QDialog):
    def __init__(self, current_columns: list, unused_columns: list, parent=None):
        """
        __init__ pop up window for editing the columns that are displayed in any table.

        Args:
            current_columns (list): current columns in table
            unused_columns (list): columns not currently being shown in table
            parent (_type_, optional): Defaults to None.
        """
        super().__init__(parent)
        initialize_config(self)
        self.initUI()
        # normalize the columns to lowercase
        current_columns = [x[0].lower() for x in current_columns]
        unused_columns = [x[0].lower() for x in unused_columns]

        self.lists["current"].addItems(current_columns)
        self.lists["unused"].addItems(unused_columns)
        self.columns = {
            "0": ["brand", "prt manufacturer"],
            "1": ["description", "item name"],
            "2": ["printers", "compatible printers"],
            "3": ["code"],
            "4": ["upc"],
            "5": ["stock"],
            "6": ["part_num", "part number"],
            "7": ["color"],
            "8": ["yield"],
            "9": ["type"],
            "10": ["comments"],
            "11": ["linked_codes", "linked items"],
            "12": ["needed"]
        }
        self.col_list = []
        for k, v in self.columns.items():
            self.col_list.append([v[0], int(k)])
        self.current_selected = None
        self.unused_selected = None
        for key, listview in self.lists.items():
            listview.clicked.connect(self.report_selection)
            listview.setProperty("list", key)
        self.setMaximumSize(800, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def initUI(self):
        self.setWindowTitle("Edit table columns")
        self.setWindowIcon(QIcon(self.icon))
        # Create two QListWidgets
        self.lists = {}
        self.lists["current"] = QListWidget(self)
        self.lists["unused"] = QListWidget(self)
        self.lists["current"].setProperty("class", "columnlist1")
        self.lists["unused"].setProperty("class", "columnlist2")
        self.lists["current"].setMaximumSize(QSize(300, 450))
        self.lists["unused"].setMaximumSize(QSize(300, 450))

        # Create a QHBoxLayout to hold the two QListWidgets
        layout = QHBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        vlayout = QVBoxLayout()

        # make vbox for each list so heading can go on top
        listlayout1 = QVBoxLayout()
        listlayout2 = QVBoxLayout()

        listtitle1 = QLabel("Current")
        listtitle2 = QLabel("Unused")
        listtitle1.setProperty("class", "listtitle1")
        listtitle2.setProperty("class", "listtitle2")

        listlayout1.addWidget(listtitle1)
        listlayout2.addWidget(listtitle2)
        listlayout1.addWidget(self.lists["current"])
        listlayout2.addWidget(self.lists["unused"])
        listlayout1.setAlignment(listtitle1, Qt.AlignCenter)
        listlayout2.setAlignment(listtitle2, Qt.AlignCenter)
        listlayout1.setAlignment(self.lists["current"], Qt.AlignTop)
        listlayout2.setAlignment(self.lists["unused"], Qt.AlignTop)
        # layout.addWidget(self.lists["current"])
        layout.addLayout(listlayout1)
        layout.addLayout(vlayout)
        layout.addLayout(listlayout2)

        # layout.addWidget(self.lists["unused"])

        # create self.submit for the bottom of the window:
        self.submit = QPushButton("SET COLUMNS")
        self.submit.setProperty("class", "submitbutton")
        self.submit.setMaximumSize(QSize(250, 100))
        self.submit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # make mouse cursor pointer
        self.submit.setCursor(QCursor(Qt.PointingHandCursor))
        self.submit.setCursor(QCursor(Qt.PointingHandCursor))
        self.submit.clicked.connect(self.accept)

        # Create two buttons
        self.add_button = IconButton(direction="left")
        self.add_button.setProperty("direction", "left")
        # self.add_button.setProperty("class", "col-dialog-btn")
        self.add_button.clicked.connect(self.move_column_names)
        self.remove_button = IconButton(direction="right")
        self.remove_button.setProperty("direction", "right")
        # self.remove_button.setProperty("class", "col-dialog-btn")
        self.remove_button.clicked.connect(self.move_column_names)

        vlayout.addWidget(self.add_button)
        vlayout.addWidget(self.remove_button)
        # Create a QVBoxLayout to hold the QHBoxLayout
        vbox = QVBoxLayout()
        vbox.addLayout(layout)
        vbox.addWidget(self.submit)
        vbox.setAlignment(self.submit, Qt.AlignCenter | Qt.AlignBottom)
        # Set the main layout of the QDialog
        self.setLayout(vbox)

        # Set the size of the QDialog and show it
        # self.setGeometry(100, 100, 400, 300)
        self.show()

    def report_selection(self):
        """
        report_selection only one column can be selected at a time. If you select one, any column you have previously selected will become unselected.
        """
        # only one list can be selected at a time
        if self.sender().property("list") == "current":
            self.current_selected = self.get_selected_value(self.lists["current"])
            self.lists["unused"].clearSelection()
            self.lists["unused"].setCurrentItem(None)
            self.current_selected = self.lists["current"].currentItem().text()
            # make sure current selection is highlighted
            self.lists["current"].setCurrentItem(self.lists["current"].currentItem())
            self.unused_selected = None
        # if the unused list reports that one of the column choices are selected - unselect any other selected column
        elif self.sender().property("list") == "unused":
            self.unused_selected = self.get_selected_value(self.lists["unused"])
            self.lists["unused"].clearSelection()
            self.lists["unused"].setCurrentItem(self.lists["unused"].currentItem())
            self.lists["current"].setCurrentItem(None)

            self.current_selected = None
            self.unused_selected = self.lists["unused"].currentItem().text()

    def get_selected_value(self, list_widget: QListWidget):
        """
        get_selected_value gets the text data from selected choice in listwidget box

        Args:
            list_widget (QListWidget): either the left or right QListWidget.

        Returns:
            _type_: _description_
        """
        if list_widget.currentItem():
            return list_widget.currentItem().text()

    def move_column_names(self):
        if self.sender().property("direction") == "left":
            # get selected value from list 2, to add it to list 1
            selected_value = self.get_selected_value(self.lists["unused"])
            self.lists["current"].addItem(selected_value)
            self.lists["unused"].takeItem(self.lists["unused"].currentRow())
            self.lists["unused"].setCurrentItem(None)
        elif self.sender().property("direction") == "right":
            # get selected value from list 1, to add it to list 2
            selected_value = self.get_selected_value(self.lists["current"])
            self.lists["unused"].addItem(selected_value)
            self.lists["current"].takeItem(self.lists["current"].currentRow())
            self.lists["current"].setCurrentItem(None)

    def get_values(self) -> tuple:
        # list1_values = [self.lists["current"].item(
        #     i).text() for i in range(self.lists["current"].count())]
        selected_names = []
        for x in range(self.lists["current"].count()):
            selected_names.append(self.lists["current"].item(x).text())
        unused_names = []
        for x in range(self.lists["unused"].count()):
            unused_names.append(self.lists["unused"].item(x).text())

        print(f"SELECTED NAMES: {selected_names}")
        selected_indices = [x[1] for x in self.col_list if x[0] in selected_names]
        unused_indices = [x[1] for x in self.col_list if x[0] in unused_names]
        # list2_values = [self.lists["unused"].item(
        #     i).text() for i in range(self.lists["unused"].count())]

        print("Setting state now and returning the tuple.")
        # all i need to do is reeqrite the config file
        self.set_state(",".join(selected_names), ",".join(selected_indices))
        return (selected_indices, unused_indices)

    def set_selected_columns(self, state: str):
        """
        set_selected_columns sets columns that will be displayed when table is shown.

        Column choices are written to & read from the config.yaml file in the config directory.

        Args:
            state (_type_): _description_
        """
        with open("config/config.yaml") as f:
            doc = yaml.safe_load(f)

        doc["preferences"]["selectedcolumns"] = state
        print(f"here's the doc {doc}")
        with open("config/config.yaml", "w") as newf:
            yaml.dump(doc, newf)

    def set_state(self, col_names: str, col_indices: str):
        """
        set_state sets the selectedcolumns variable in the config.yaml file.

        This function should probably be adapter so it can set any variable specified in the config.yaml file.

        Args:
            state (str): a comma-separated string with the selected column names.
        """
        with open("config/config.yaml") as f:
            doc = yaml.safe_load(f)

        doc["preferences"]["selectedcolumns"] = col_names
        doc["preferences"]["selectedindices"] = col_indices
        print(f"here's the doc {doc}")
        with open("config/config.yaml", "w") as newf:
            yaml.dump(doc, newf)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ColumnEdit()
    sys.exit(app.exec_())
