from PyQt5.QtWidgets import (
    QSizePolicy,
    QTableView,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QFrame,
    QLabel,QComboBox, QAbstractItemView)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import QSize, Qt, QSortFilterProxyModel, QVariant, QAbstractTableModel, QModelIndex, pyqtSignal
import qtawesome
from widgets.clickablelineedit import ClickableLineEdit
from widgets.buttons import SearchButton, HomepageButton
from utils.toner_utils import connect_to_db, initialize_config


class HomeLayout(QVBoxLayout):
    def __init__(self, parent=None):
        """
        __init__ QVBoxLayout for the home page of the QStackedWidget that the app is built on.

        This layout holds the title of the app (X Campus Inventory), a search bar, and 4 buttons (Dell, HP, Lexmark, Others).

        Args:
            parent (_type_, optional): Parent Qt widget. Defaults to None.
        """
        super().__init__(parent)
        initialize_config(self)
        self.top_layout = QVBoxLayout()
        title_text = f"{self.campus} Printer Inventory"
        self.title = QLabel(text=title_text)
        self.title.setFont(QFont("Roboto", 24, QFont.Bold))
        # self.title.setProperty("class", "main-self.title")
        self.top_layout.addWidget(self.title)
        self.top_layout.setAlignment(Qt.AlignCenter)

        self.addLayout(self.top_layout)
        self.setAlignment(self.top_layout, Qt.AlignCenter)

        search_layout = QHBoxLayout()
        self.search_bar = self.build_search_bar()
        self.search_button = SearchButton("Search")
        self.search_button.setFont(QFont("Roboto", 12))
        # self.search_button.setMaximumSize(150, 50)

        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(self.search_button)
        # search_layout.setAlignment(self.search_bar, Qt.AlignCenter)

        self.addLayout(search_layout)
        self.setAlignment(search_layout, Qt.AlignCenter)

        button_box = self.build_button_box()
        self.addWidget(button_box)
        self.setAlignment(button_box, Qt.AlignTop)

    def build_search_bar(self):
        # build the qlineedit for the search bar
        return ClickableLineEdit(parent=self.parent(), placeholder_text="Search by any printer model, e. g. 'Dell S5840cdn'")

    def build_button_box(self):
        layout = QVBoxLayout()
        button_frame = QFrame()
        layout.setAlignment(Qt.AlignCenter)
        button_frame.setProperty("class", "button-frame")
        button_frame.setLayout(layout)
        # build the 4 buttons
        button_titles = ["Dell", "HP", "Lexmark", "Others"]
        self.buttons = {}     
        for title in button_titles:
            title = title.lower()
            self.buttons[title] = HomepageButton(text=title)
            # set button class to 'wide-button' class
            self.buttons[title].setProperty("class", "wide-button")
            # set cursor to pointer
            self.buttons[title].setCursor(Qt.PointingHandCursor)
            layout.addWidget(self.buttons[title])
            # layout.setAlignment(self.buttons[title], Qt.AlignCenter)
            
            # TODO: connect the buttons to the table view function
        return button_frame
    
class TableLayout(QVBoxLayout):
    rowclicked = pyqtSignal(QModelIndex)
    def __init__(self, parent=None):
        """
        __init__ QVBoxLayout for the table view page of the QStackedWidget that the app is built on.

        This layout holds a search bar that allows user to search by any column, a table view under the search bar, and the title of the table on top of everything.

        Args:
            parent (_type_, optional): _description_. Defaults to None.
        """
        super().__init__(parent)
        initialize_config(self)
        self.top_layout = QVBoxLayout()
        self.title = QLabel(parent=self.parent(), text=f"Inventory Spreadsheet")
        self.title.setProperty("class", "table-title")

        self.top_layout.addWidget(self.title)
        self.top_layout.setAlignment(Qt.AlignCenter)

        # hbox layout for the search bar/buttons
        self.search_layout = QHBoxLayout()
        # vertically center everything inside the search alyout
        self.search_layout.setAlignment(Qt.AlignVCenter)
        # Add ComboBox, self is a layout, so we need to specify the parent - a qwidget
        self.combobox = QComboBox(parent=self.parent())
        self.combobox.setFont(QFont("Roboto", 12))
        # add choose column instruction for user:
        # TODO: make this option go away once the user clicks on the combobox
        self.combobox.addItem("Choose column")
        for k, colname_list in self.columns.items():
            colname = colname_list[0]
            self.combobox.addItem(colname)
        self.search_layout.addWidget(self.combobox)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by any column...")
        self.search_bar.setFont(QFont("Roboto", 12))
        self.search_button = SearchButton("Search")
        # self.search_button.setMaximumSize(150, 50)
        self.search_button.setFont(QFont("Roboto", 12))
        
        self.search_layout.addWidget(self.search_bar)
        self.search_layout.addWidget(self.search_button)
        self.search_layout.setAlignment(Qt.AlignCenter)

        # add the layouts to the main layout
        self.addLayout(self.top_layout)
        self.addLayout(self.search_layout)
        # self.addLayout(self.table_buttons_layout)

        # create the table
        self.table = ModTableView()
        self.addWidget(self.table)
        self.mouseDoubleClickEvent = self.emit_item

    def emit_item(self, index):
        
        # get index of currently selected row on table
        index = self.table.currentIndex()
        self.rowclicked.emit(index)
    def update_table_filter(self, text):
        """ Update the table filter to show only items that match the search string. """
        column_index = self.table.horizontalHeader().sortIndicatorSection()
        header_model = (
            self.table.horizontalHeader().model()
        )  #: get header model from table
        column_name = header_model.headerData(
            column_index, Qt.Horizontal
        )  #: get the name of the column that was clicked on (name, code, stock)
        sort_order = (
            self.table.horizontalHeader().sortIndicatorOrder()
        )  #: get the sort order of the column that was clicked on
    def initialize_model(self):
        """ initialize_model Initialize the model for the tableview: creates QSortFilterProxyModel. """
        self.sortermodel = QSortFilterProxyModel()
        self.sortermodel.setSourceModel(self.model)
        # self.sortermodel.setFilterKeyColumn(-1)  #: -1 means all columns
        # self.sortermodel.setDynamicSortFilter(True)

        # self.table.sortByColumn(1, Qt.AscendingOrder)
        self.table.setModel(self.sortermodel)
        self.table.setSortingEnabled(True)

        self.sortermodel.layoutChanged.connect(self.table.updateGeometries)
        # row height is set here
        # TODO: make this an option in config / settings
        for row in range(len(self.model.modeldata)):
            self.table.setRowHeight(row, 35)

        # set column widths - description
        self.table.setColumnWidth(1, 400)
        # upc
        self.table.setColumnWidth(4, 125)
        # stock
        self.table.setColumnWidth(5, 90)
        # set width of type to 30 since the type column consists of one icon per row
        self.table.setColumnWidth(9, 30)

        self.table.horizontalHeader().setStretchLastSection(True)
        # user can only select rows
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setVisible(False)

    def set_table_model(self, query:str=None):
        initialize_config(self)
        if query != None:
            self.previous_query = query
        # if query is NOT supplied then use the previous query, to refresh the table
        else:
            query = self.previous_query
        table_rows = self.get_table_data(query)
        # -- SELF.MODEL DEFINED IN THE TABLEVIEW CLASS
        self.model = SortingTableModel(
                headers=[col_header[0].upper() for col_header in list(self.columns.values())], model_data=table_rows)
        # self.table.setModel(self.model)
        self.initialize_model()
        self.hidden_indices = []
        # read the config file and hide hidden columns
        # get hidden and shown columns
        self.all_indices = [int(i) for i in range(len(self.columns))]
        for col_index in self.all_indices:
            if col_index not in self.chosen_indices:
                self.hidden_indices.append(col_index)
        for col in self.hidden_indices:
            self.table.hideColumn(int(col))
        # show shown columns
        for col in self.chosen_indices:
            self.table.showColumn(int(col))

    def get_table_data(self, query:str):

        db, cursor = connect_to_db(
            db_host=self.dbhost,
            db_user=self.dbuser,
            db_name=self.dbname,
            db_pass=self.dbpass,
            dicttrue=False,
        )
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        db.close()
        # convert results to be used as model
        table_rows = []
        for inner_tuple in results:
            item_details = []
            for detail in inner_tuple:
                item_details.append(detail)
            table_rows.append(item_details)
        
        table_rows = sorted(table_rows, key=lambda x: x[1])
        return table_rows

    def set_title_text(self, text:str):
        self.title.setText(text)


class SortingTableModel(QAbstractTableModel):
    def __init__(self, parent=None, headers:list=None, model_data:dict=None):
        """
        __init__ Slightly modified subclass of QAbstractTableModel which allows for sorting of the table data, applies some formatting to the table cells, and a couple of other things.

        Args:
            parent (_type_, optional): parent Qt object. Defaults to None.
            headers (list, optional): list containing the table headers, ex: ["name", "stock", "upc"]. Defaults to None.
            model_data (dict, optional): dictionary containing the data within the model. Defaults to None.
        """
        super().__init__(parent)
        # self.colorset = ['#800000', '#cc2900', '#cc9900', '#86b300', '#00b33c', '#00b33c', '#00b33c', '#00b33c', '#00b33c', '#00b33c', '#00b33c']
        self.colorset = ['#800000', '#cc2900', '#cc9900', '#86b300', '#00b33c']

        self.headers = headers
        self.modeldata = model_data

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.headers[section]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        column_name = self.headerData(
            col, Qt.Horizontal, Qt.DisplayRole)
        value = self.modeldata[row][col]
        if role == Qt.DisplayRole:
            if column_name.lower() in ["stock"]:
                return QVariant(value)
            if column_name.lower() == "t":
                return ""
            return QVariant(value)
        elif role == Qt.TextAlignmentRole:
            if (col in [3, 4, 5, 6, 9]) or column_name.lower() in ["stock", "upc", "type", "needed"]:
                return QVariant(Qt.AlignCenter)
        elif role == Qt.DecorationRole and column_name.lower() == "t":
            if self.modeldata[row][col] in ["ink", "toner"]:
                toner_icon = qtawesome.icon(
                    "ri.paint-fill", color="#0252c2", size=56)
                return QVariant(toner_icon)
            elif self.modeldata[row][col] in ["paper"]:
                paper_icon = qtawesome.icon(
                    "ri.file-paper-2-fill", color="#0252c2")
                return QVariant(paper_icon)
            elif self.modeldata[row][col] in ["drum", "fuser"]:
                drum_icon = qtawesome.icon(
                    "ri.printer-line", color="#0252c2", size=56)
                return QVariant(drum_icon)
            else:
                other_icon = qtawesome.icon(
                    "ri.printer-line", color="#0252c2", size=56)
                return QVariant(other_icon)
        elif role == Qt.FontRole and value == 0:
            font = QFont('Roboto', 12, QFont.Bold)
            font.setBold(True)
            font.setWeight(75)
            return QVariant(font)
        elif role == Qt.FontRole:
            font = QFont('Roboto', 12)
            font.setBold(False)
            font.setWeight(50)
            return QVariant(font)

        elif role == Qt.BackgroundRole:
            if column_name.lower() == "stock":
                try:
                    value = int(value)  # Convert to integer for indexing.
                    value = min(4, value)

                    return QVariant(QColor(self.colorset[value]))
                except ValueError:
                    pass
        return QVariant()

    def columnCount(self, parent):
        return len(self.headers)

    def rowCount(self, parent):
        return len(self.modeldata)

    def insertRows(self, position, rows, parent=QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)
        self.endInsertRows()
        return True
    

class ModTableView(QTableView):
    def __init__(self, parent=None, *args, **kwargs):
        """
        __init__ Subclass of QTableView that sets some default values including size policy, disabling horizontal scroll bar, and setting default size of 30 for veritcal header sections.

        Args:
            parent (_type_, optional): parent Qt object. Defaults to None.
        """
        super().__init__(parent, *args, **kwargs)

        self.setSizePolicy(QSizePolicy.Expanding,
                           QSizePolicy.Expanding)

    def sizeHint(self):
        return QSize(2000, 1200)
    

class DashboardLayout(QVBoxLayout):
    def __init__(self, parent=None):
        """
        __init__ Subclass of QVBoxLayout that contains the dashboard page's layout. This is index 2 of the QStackedWidget that the app is built on.

        The dashboard shows how many items are currently in stock for any given printer model. Also allows user to double-click a dashboard widget to edit or delete any of the item's values except the upc column values.

        Args:
            parent (_type_, optional): _description_. Defaults to None.
        """
        super().__init__(parent)
        self.setAlignment(Qt.AlignTop)

        self.top_layout = QVBoxLayout()
        self.title = QLabel(parent=self.parent(), text=f"Printer Item Dashboard")
        self.title.setFont(QFont('Roboto', 24, QFont.Bold))
        self.title.setProperty("class", "dash-title")

        self.top_layout.addWidget(self.title)
        self.top_layout.setAlignment(Qt.AlignCenter)

        # hbox layout for the search bar/buttons
        self.search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for any printer model...")
        self.search_button = SearchButton("Search")
        self.search_button.setFont(QFont('Roboto', 12))
        self.search_layout.addWidget(self.search_bar)
        self.search_layout.addWidget(self.search_button)

        self.model_title = QLabel(parent=self.parent(), text="")

        # create grid layout for the dashboard
        self.grid = QGridLayout()
        self.grid.setVerticalSpacing(75)
        self.addLayout(self.search_layout)
        self.addLayout(self.top_layout)
        self.addLayout(self.grid)

    def set_model_title(self, model_name):
        self.title.setText(model_name.upper())