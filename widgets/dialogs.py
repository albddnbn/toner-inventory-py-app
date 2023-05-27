import os
from PyQt5.QtWidgets import (QListWidget,QFormLayout,QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget,QDialog,
                             QWidget, QComboBox,QVBoxLayout, QSizePolicy)
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QIcon, QFont, QCursor,QCloseEvent
import qtawesome
from widgets.clickablelineedit import ClickableLineEdit
from utils.toner_utils import initialize_config
# from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QFormLayout

class GetDatabaseCreds(QWidget):
    def __init__(self):
        super().__init__()
        title = QLabel('Enter database credentials:')
        self.user_lineedit = QLabel('Enter username:')
        self.username_input = QLineEdit()
        self.label = QLabel('Enter password:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        layout = QFormLayout()
        # layout.addWidget(self.label)
        # layout.addWidget(self.password_input)
        layout.addRow(title)
        layout.addRow(self.user_lineedit, self.username_input)
        layout.addRow(self.label, self.password_input)


        self.setLayout(layout)

class ColumnSelection(QWidget):
    # when the ok button is clicked - form will emit signal with two lists: selected and unselected columns that will be caught by main app
    data_ready = pyqtSignal(list, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        print("column setrtin")
        initialize_config(self)
        self.setWindowTitle("Select Columns")
        self.setWindowIcon(qtawesome.icon(
            "mdi6.format-list-checks", color="#ffffff"))
        outer_vbox = QVBoxLayout()

        # Create two QListWidgets
        self.left_list = QListWidget()
        self.left_list.setToolTip("Select columns to show on the table.")
        self.right_list = QListWidget()
        self.right_list.setToolTip(
            "Columns not selected will hidden from view.")
        selected_indices = self.chosen_indices
        unused_indices = []
        unused_names = []
        # read the column names from the config file, read selected columns from the config file, create two lists of unused col names/indices
        for index, col_name_list in self.columns.items():
            col_name = col_name_list[0]
            if col_name in self.selected_columns:
                self.left_list.addItem(col_name)
            else:
                self.right_list.addItem(col_name)
                unused_names.append(col_name)
                unused_indices.append(int(index))

        if self.theme in self.light_themes:
            icon_color = "#555555"
        elif self.theme in self.dark_themes:
            icon_color = "#dedede"
        else:
            icon_color = "#ffffff"

        # -- arrow pointing right -->
        # right_arrow_button = QPushButton("")
        # # check if its a light theme or dark theme before setting icon color
        # right_arrow_button.setIcon(qtawesome.icon(
        #     "mdi6.arrow-right-bold", color=self.default_icon_color, color_active="#dedede"))
        # right_arrow_button.setCursor(QCursor(Qt.PointingHandCursor))
        # right_arrow_button.setIconSize(QSize(35, 35))
        # right_arrow_button.setMinimumSize(QSize(60, 35))
        # # -- arrow pointing left -->
        # left_arrow_button = QPushButton("")
        # left_arrow_button.setIcon(qtawesome.icon(
        #     "mdi6.arrow-left-bold", color=self.default_icon_color, color_active="#dedede"))
        # left_arrow_button.setCursor(QCursor(Qt.PointingHandCursor))
        # left_arrow_button.setIconSize(QSize(35, 35))
        # left_arrow_button.setMinimumSize(QSize(60, 35))
        # dictionary to hold right/left arrow buttons
        buttons = {"right": None, "left": None}
        # use loop to create them since the only difference is the qtawesome icon
        for direction in ["right", "left"]:
            # form the icon string mdi6.arrow-{right/left}-bold
            icon_string = f"mdi6.arrow-{direction}-bold"
            # create the button
            buttons[direction] = QPushButton("")
            buttons[direction].setIcon(qtawesome.icon(
                icon_string, color=self.default_icon_color, color_active="#dedede"))
            buttons[direction].setCursor(QCursor(Qt.PointingHandCursor))
            buttons[direction].setIconSize(QSize(35, 35))
            buttons[direction].setMinimumSize(QSize(60, 35))

        # Connect the QPushButtons to the functions that move the items
        buttons["right"].clicked.connect(
            lambda: self.move_selected_item(self.left_list, self.right_list))
        buttons["left"].clicked.connect(
            lambda: self.move_selected_item(self.right_list, self.left_list))
        # Create a QHBoxLayout for the two QListWidgets
        list_layout = QHBoxLayout()
        list_layout.addWidget(self.left_list)
        # Create a QVBoxLayout for the two QPushButtons
        button_layout = QVBoxLayout()
        button_layout.addWidget(buttons["right"])
        button_layout.addWidget(buttons["left"])

        list_layout.addLayout(button_layout)
        list_layout.addWidget(self.right_list)

        # Create a QHBoxLayout for the QWidget and add the two layouts
        main_layout = QVBoxLayout()
        main_layout.addLayout(list_layout)
        # create OK button
        ok_button = QPushButton("OK")
        ok_button.setMaximumSize(QSize(300, 40))
        ok_button.setCursor(QCursor(Qt.PointingHandCursor))
        ok_button.setMinimumSize(QSize(250, 40))
        ok_button.clicked.connect(lambda: self.ok_button_clicked())
        main_layout.addWidget(ok_button)
        main_layout.setAlignment(ok_button, Qt.AlignHCenter)
        main_layout.setContentsMargins(10, 15, 10, 15)
        # main_layout.addLayout(button_layout)

        # Set the layout for the QWidget
        self.setLayout(main_layout)
        self.setProperty("class", "column-select")
        self.show()

    def ok_button_clicked(self):
        # emit signal with two lists: selected and unselected columns
        # Get the data from the two QListWidgets and emit the data_ready signal
        left_data = [self.left_list.item(i).text()
                     for i in range(self.left_list.count())]
        right_data = [self.right_list.item(i).text()
                      for i in range(self.right_list.count())]
        self.data_ready.emit(left_data, right_data)
        self.close()

    def move_selected_item(self, source: QListWidget, dest: QListWidget):
        """
        move_selected_item move the selected item from the source QListWidget to the destination QListWidget.

        _extended_summary_

        Args:
            source (QListWidget): _description_
            dest (_type_): _description_
        """
        try:
            # Get the selected row of the source list

            selected_column_name = source.selectedItems()[0].text()
            # Get the text of the item in the row
            if selected_column_name:
                source.takeItem(source.row(source.selectedItems()[0]))
                # add item to destination list
                dest.addItem(selected_column_name)

        except IndexError:
            # print("User likely clicked the wrong arrow, in other words, no item was selected in the correct column.")
            pass


class FindItemDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # create the form layout
        self.form_layout = QFormLayout()

        # qlabel instructing the user to enter the code or upc of an item
        self.label = QLabel(
            "Enter the code or UPC of the item you'd like to edit.")
        self.form_layout.addRow(self.label)

        # add labels and line edits to the form layout
        self.label1 = QLabel("Code")
        self.lineedit1 = QLineEdit()
        self.form_layout.addRow(self.label1, self.lineedit1)

        self.label2 = QLabel("UPC")
        self.lineedit2 = QLineEdit()
        self.form_layout.addRow(self.label2, self.lineedit2)

        # create the OK button and connect its clicked signal to the accept slot
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)

        # create the main layout and add the form layout and OK button
        self.layout = QVBoxLayout()
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.ok_button)

        # set the main layout for the dialog
        self.setLayout(self.layout)

    def accept(self):
        # get the data from the line edits
        self.code = self.lineedit1.text()
        self.upc = self.lineedit2.text()

        # call the accept method of the QDialog class
        super().accept()


class HelpPopup(QDialog):
    # dialog will emit a signal corresponding to which button was clicked
    docs_clicked = pyqtSignal()
    app_guide_clicked = pyqtSignal()

    def __init__(self, label_text="Please try the <b>app docs</b> or <b>guide</b> for help, or message Alex B. on Teams."):
        super().__init__()
        initialize_config(self)
        # Set the dialog title
        self.setWindowTitle(f"Help")
        self.setWindowIcon(QIcon(self.icon))
        # Create the label widget
        label = QLabel(label_text, self)

        # Create the two button widgets
        docs_button = QPushButton("Docs (pdoc)", self)
        app_guide_button = QPushButton("Guide.html", self)
        for button in [docs_button, app_guide_button]:
            # Set the size and font of the buttons
            button.setFixedSize(QSize(250, 40))
            button.setFont(QFont("Roboto", 14))
            button.setIconSize(QSize(24, 24))
            button.setCursor(QCursor(Qt.PointingHandCursor))
        # TODO: find way to dynamically set these qtawesome icon colors based on what theme is chosen
        # set the icon of the docs button to be a text file log looking icon from qtawesome
        docs_button.setIcon(qtawesome.icon('fa.file-text-o', color='#444444'))

        # set the guide html to be a web document looking file from qtawesome
        app_guide_button.setIcon(qtawesome.icon(
            'fa.file-code-o', color='#444444'))

        # Create the layout for the label and buttons
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        button_layout = QHBoxLayout()
        button_layout.addWidget(docs_button)
        button_layout.addWidget(app_guide_button)
        layout.addLayout(button_layout)

        # Connect the button signals to the custom signals
        docs_button.clicked.connect(self.docs_clicked.emit)
        app_guide_button.clicked.connect(self.app_guide_clicked.emit)
        # also make clicking either button close the dialog
        docs_button.clicked.connect(self.close)
        app_guide_button.clicked.connect(self.close)


class ItemPopup(QDialog):
    db_operation = pyqtSignal(dict, str)

    def __init__(self, parent=None, operation="edit", input_item=""):
        """
        ItemDialog QDialog class - dialog for adding/editing items.
        """
        super().__init__(parent)
        # initialize config for the self.columns variable
        initialize_config(self)
        self.setWindowIcon(qtawesome.icon('fa5s.table', color='#444444'))
        self.setWindowTitle("Edit Item")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # Create a QFormLayout for the dialog
        form_layout = QFormLayout()
        self.operation = operation
        self.qlabels = {}
        self.qlinedits = {}
        # use loop to generate qlabels and qlineedits
        for k, col_name_list in self.columns.items():
            col_name = col_name_list[0]
            self.qlabels[col_name] = QLabel(col_name)
            # make 'needed', and 'stock' columns clickable line edits, other qlineedits shouldn't erase themselves on user click
            if col_name in ["needed", "stock"]:
                self.qlinedits[col_name] = ClickableLineEdit(parent=self)
            else:
                self.qlinedits[col_name] = QLineEdit(parent=self)
            # if user is editing the item, then put current item details into qlineedits as placeholder text
            if (self.operation == "edit"):
                if (input_item != ""):
                    self.qlinedits[col_name].setText(str(input_item[col_name]))
                # if its the upc column and user is editing, disable textbox so they can't change upc
                if col_name == "upc":
                    self.qlinedits[col_name].setDisabled(True)

            # add them to form dialog
            form_layout.addRow(
                self.qlabels[col_name], self.qlinedits[col_name])
        self.input_item = input_item
        # build an hbox for the Ok button and the delete button
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(20, 20, 20, 20)

        # Create a button to accept the dialog
        accept_button = QPushButton("OK")
        accept_button.setCursor(QCursor(Qt.PointingHandCursor))
        # accept_button.clicked.connect(self.emitData)
        accept_button.clicked.connect(self.close)
        # add reutnr key press action to acceept button
        accept_button.setDefault(True)
        # add property to ok button so that styles can be applied in Aqua theme (possibly other themes, not Elegant Dark)
        accept_button.setProperty("class", "long-ok-button")

        # create delete button
        delete_button = QPushButton("")
        delete_button.setIcon(qtawesome.icon('mdi6.trash-can', color='#e7e7e7'))
        delete_button.setIconSize(QSize(35,35))
        delete_button.setCursor(QCursor(Qt.PointingHandCursor))
        # make the delete button emit the values from qlineedits when clicked
        # delete_button.clicked.connect(self.delete_item)

        form_layout.addRow(delete_button, accept_button)

        # Set the form_layout as the main layout for the dialog
        self.setLayout(form_layout)
        

        # make the accept button emit the values from qlineedits when clicked
        accept_button.clicked.connect(lambda: self.accept())
        accept_button.clicked.connect(self.signal_db_operation)
        delete_button.clicked.connect(lambda: self.signal_db_operation(delete_item=True))

    def signal_db_operation(self, delete_item=False):
        # gather item and emit it as dict
        item = self.get_item()
        if delete_item:
            self.db_operation.emit(item, "delete")
        else:
            self.db_operation.emit(item, self.operation)

        self.accept()

    def get_item(self):
        # loop through the qlineedits, return the text from them
        item_data = {}
        # loop through the qlinedits and add them to the data dictionary
        for k, col_name_list in self.columns.items():
            col_name = col_name_list[0]
            # if the user typed text into the qlineedit, then add it to the data dictionary
            if self.qlinedits[col_name].text():
                item_data[col_name] = self.qlinedits[col_name].text()
            elif self.qlinedits[col_name].placeholderText():
                item_data[col_name] = self.qlinedits[col_name].placeholderText()
            else:
                if col_name in ["stock", "needed"]:
                    item_data[col_name] = 0
                else:
                    item_data[col_name] = ""
        return item_data

    def sizeHint(self) -> QSize:
        return QSize(450, 350)


class ApiLookup(QDialog):
    def __init__(self, parent=None):
        super(ApiLookup, self).__init__(parent)

        self.setWindowTitle('Attempt Lookup')
        self.setMinimumSize(300, 75)
        self.setMaximumSize(300, 75)
        # set the window icon to something having to do with looking things up
        self.setWindowIcon(qtawesome.icon('fa.search', color='white'))

        # create the QLineEdit and OK button
        self.text_edit = QLineEdit()
        ok_button = QPushButton("LOOK UP")
        ok_button.setFont(QFont('Roboto', 11))
        ok_button.setMinimumSize(75, 30)
        ok_button.setMaximumSize(90, 35)

        # when clicked - return whatever is in the qlineedit
        ok_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.text_edit)
        hbox.addWidget(ok_button)
        layout.addLayout(hbox)

        self.setLayout(layout)

    def textValue(self):
        return self.text_edit.text()


class SearchColumnsPopup(QDialog):
    # emit the mode string (popup instead of table since search is being done from the popup not table)
    # and emit the actual query string to be used in the search_db_mode function of the app
    dataEntered = pyqtSignal(str, str)

    def __init__(self, parent=None):

        super().__init__(parent)
        # initiailize config for use of the self.columns dict
        initialize_config(self)

        self.setWindowTitle('Search Inventory')
        self.setWindowIcon(qtawesome.icon('mdi.table-large', color='white'))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # vlayout = QVBoxLayout(self)
        layout = QHBoxLayout(self)

        # label = QLabel('Search by any column:', self)
        # label.setFont(QFont('Roboto', 20))
        # vlayout.addWidget(label)
        # vlayout.addLayout(layout)

        self.combobox = QComboBox(self)
        for k, colname_list in self.columns.items():
            colname = colname_list[0]
            self.combobox.addItem(colname)
        layout.addWidget(self.combobox)

        # Add QlineEdit
        self.lineedit = QLineEdit(self)
        self.lineedit.setMinimumSize(QSize(200, 40))
        self.lineedit.setPlaceholderText(
            'Choose column, type, then click "Search"')
        layout.addWidget(self.lineedit)

        # Add search button
        search_button = SearchButton('Search', self)
        search_button.setMaximumSize(QSize(75, 35))
        layout.addWidget(search_button)
        # search button will emit the query string and close the popup window                search_button.clicked.connect(lambda: self.accept())
        search_button.clicked.connect(lambda: self.accept())
        search_button.clicked.connect(self.emitData)
        # Set the layout
        self.setLayout(layout)

    def emitData(self):
        # create a dictionary to hold the data from the qlineedits
        search_data = {}
        # get the selected column name from the combobox
        search_data['column'] = self.combobox.currentText()
        # get the search text from the lineedit
        search_data['text'] = self.lineedit.text()
        # form query string
        # form column string
        col_str = ""
        for k, colname_list in self.columns.items():
            colname = colname_list[0]
            col_str += colname + ", "
        col_str = col_str[:-2]

        # if it's the stock or needed column, make sure the value is changed to an int
        if search_data['column'] == 'stock' or search_data['column'] == 'needed':
            query_string = f"SELECT {col_str} FROM inventory WHERE {search_data['column']} = {int(search_data['text'])}"
        else:
            query_string = f"SELECT {col_str} FROM inventory WHERE {search_data['column']} LIKE \'%{search_data['text']}%\'"
        # emit the query string
        self.dataEntered.emit("popup", query_string)

    def sizeHint(self):
        return QSize(550, 100)


class SearchButton(QPushButton):
    # Additional constructor with a custom text label
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

        # set size policy for main buttons
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(125, 40)
        self.setMaximumSize(150, 50)
        # set DTCC Font
        self.setFont(QFont("Roboto", 12))
        self.setProperty("class", "search-button")
        # set button text
        self.setText(text.lower())
        self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self):
        return QSize(150, 40)


class ThemePopup(QDialog):
    themeSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Select QSS File")
        self.setWindowIcon(qtawesome.icon('fa5s.paint-brush', color='white'))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.layout = QVBoxLayout(self)
        # a qlabel explaining to user to choose a theme
        # self.layout.addWidget(QLabel("Select a theme:"))

        # hbox to hold combobox and button
        hbox = QHBoxLayout()
        self.layout.addLayout(hbox)

        # Get a list of all .qss files in the "qss-stuff" directory
        qss_dir = "themes"
        self.qss_files = [filename[:-4]
                          for filename in os.listdir(qss_dir) if filename.endswith(".qss")]

        # create one combobox to hold all the filenames
        self.combobox = QComboBox()
        self.combobox.addItem("Select a theme")
        self.combobox.addItems(self.qss_files)
        self.combobox.setMinimumSize(175, 35)
        hbox.addWidget(self.combobox)

        # Create an "OK" button at the bottom of the layout
        button_ok = QPushButton("SET THEME", self)
        button_ok.clicked.connect(self.accept)
        button_ok.clicked.connect(self.emitTheme)
        button_ok.setCursor(Qt.PointingHandCursor)
        button_ok.setMinimumSize(75, 35)
        hbox.addWidget(button_ok)

    def emitTheme(self):
        """
        emitTheme the theme dialog will emit a signal containing the QSS filename string when the Ok button is clicked.

        It will set the application theme to whatever the current setting is in the QComboBox.
        """
        self.themeSignal.emit(self.combobox.currentText())

    def accept(self):
        # Get the selected filename
        self.selected_theme = self.combobox.currentText()
        super().accept()

    def closeEvent(self, a0: QCloseEvent) -> None:
        """
        closeEvent if this window gets closed out - set off reject(), which will tell the main application not to look for the selected_theme attribute.

        Args:
            a0 (QCloseEvent): _description_
        """
        super().reject()
        return super().closeEvent(a0)

    def sizeHint(self):
        return QSize(300, 100)


class WarningPopup(QDialog):
    def __init__(self, title="Warning", message="This is a warning", parent=None):
        '''
        __init__ Popup class for displaying a warning message to the user, right now just being used for the popup that occurs on close event to give user chance to cancel the exiting of application.

        Args:
            title (str, optional): Title of the popup window. Defaults to "Warning".
            message (str, optional): Message displayed to user above the Yes/No buttons. Defaults to "This is a warning".
            parent (_type_, optional): parent Qt object. Defaults to None.
        '''
        super().__init__(parent)
        initialize_config(self)
        self.setWindowTitle(title)
        # create window icon
        warning = qtawesome.icon("fa.warning", color='#FFD700')
        self.setWindowIcon(warning)

        # create warning icon
        warning_icon = QLabel()
        warning_icon.setPixmap(warning.pixmap(64, 64))
        # QLabel with message
        message_label = QLabel(message)
        # yes/no buttons
        self.yes_button = QPushButton("Yes")
        self.no_button = QPushButton("No")
        # create hbox for everything
        hbox = QHBoxLayout()
        hbox.addWidget(warning_icon)

        vbox = QVBoxLayout()
        hbox.addLayout(vbox)

        vbox.addWidget(message_label)
        button_hbox = QHBoxLayout()

        vbox.addLayout(button_hbox)

        button_hbox.addWidget(self.yes_button)
        button_hbox.addWidget(self.no_button)

        self.setLayout(hbox)

        # connect signals to slots
        self.yes_button.clicked.connect(self.accept)
        self.yes_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.no_button.clicked.connect(self.reject)
        self.no_button.setCursor(QCursor(Qt.PointingHandCursor))
