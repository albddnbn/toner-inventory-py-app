import sys
import os
import yaml
import webbrowser
from functools import partial
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QStackedWidget,
    QCompleter,
    QAction,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSystemTrayIcon,
    QMenu, QFileDialog, QPushButton, QVBoxLayout, QComboBox,
    QDialog, QPushButton, QVBoxLayout, QSystemTrayIcon, QMessageBox, QFormLayout, QLabel, QLineEdit)
from PyQt5.QtCore import QSize, Qt, QModelIndex
from PyQt5.QtGui import QColor, QColor, QIcon
import qtawesome
# Application-specific imports
from widgets.radialframe import RadialFrame
from widgets.dialogs import ColumnSelection, FindItemDialog, HelpPopup, ItemPopup, ApiLookup, SearchColumnsPopup, ThemePopup, WarningPopup
from widgets.barcodescan import ScanInputWindow
from widgets.columnchoices import ColumnEdit
from widgets.layouts import HomeLayout, TableLayout, DashboardLayout
from widgets.itemframe import ItemFrame
from widgets.settingsdialog import SettingsPopup
from widgets.tonertoolbar import TonerToolbar
from utils.toner_utils import connect_to_db, initialize_config, write_log
from utils.createreport import ReportDialog
from utils.backup_to_csv import DataBackup
from utils.upclookup import ItemLookup
from utils.fillout_columns import DBHousekeeping


class StackedApp(QWidget):
    def __init__(self, parent:QMainWindow=None):
        """
        __init__ This is the main QWidget used by the app GUI. The QMainWindow is just a shell that holds this widget, because QMainWindows come with the main menubars built-in and made building the GUI easier.

        The main widget inside of this class, is saved in the 'stack' property, which is a QStackedWidget. This widget is used to switch between the three main pages of the app: home, table, and dashboard using the statement: self.stack.setCurrentIndex(index).

        Args:
            parent (QMainWindow, optional): _description_. Defaults to None.
        """
        super(StackedApp, self).__init__(parent)
        initialize_config(self)
        # this dictionary is to change the menubar icon colors, based on whether the user has a light or dark theme set:
        # TODO: write steps for adding new icons to the menubar
        self.icon_strings = {
            "search": ["fa5s.search"],
            "reset": ["mdi6.database-refresh"],
            "import": ["mdi.import"],
            "home": ["mdi.home"],
            "insert": ["mdi.plus-box-outline"],
            "edit": ["mdi6.database-edit-outline"],
            "theme": ["mdi6.monitor-eye"],
            "columns": ["ri.insert-column-left"],
            "settings": ["mdi6.cog"],
            "about": ["mdi.information-outline"]
        }
        layout = QVBoxLayout(self)
        # create the three QWidgets
        self.home_page = QWidget(parent=self)
        self.table_page = QWidget(parent=self)
        self.dashboard_page = QWidget(parent=self)

        self.tray_icon, tray_menu = self.build_tray()

        self.stack = QStackedWidget(self)

        # set each qwidgets layout to be the corresponding page
        self.home_layout = HomeLayout()
        self.home_page.setLayout(self.home_layout)
        self.table_layout = TableLayout()
        self.table_layout.rowclicked.connect(self.edit_app_item)
        self.table_page.setLayout(self.table_layout)
        self.dashboard_layout = DashboardLayout()
        self.dashboard_page.setLayout(self.dashboard_layout)

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.table_page)
        self.stack.addWidget(self.dashboard_page)

        layout.addWidget(self.stack)

        self.stack.setCurrentIndex(0)

        self.setLayout(layout)

        # set up qcompleters for the textbox on home window
        self.printer_models_qcompleter, self.codes_qcompleter = self.build_qcompleters()
        # TODO: attach either the printer models or item codes q completer based on user selection (will have to add buttons next to the QlineEdit on the home page or something similar)
        self.home_layout.search_bar.setCompleter(
            self.printer_models_qcompleter)
        self.dashboard_layout.search_bar.setCompleter(
            self.printer_models_qcompleter)
        # connections
        self.home_layout.search_bar.completer().activated.connect(
            partial(self.show_dashboard_page, window="home"))
        self.home_layout.search_button.clicked.connect(
            partial(self.show_dashboard_page, window="home"))

        self.dashboard_layout.search_button.clicked.connect(
            partial(self.show_dashboard_page, window="dashboard"))

        # connect the search bar button to search function
        # if enter is pressed
        # self.table_layout.search_bar.completer().activated.connect(
        #     lambda: self.show_dashboard_page(window="home"))
        self.table_layout.search_button.clicked.connect(
            lambda: self.search_db_mode(mode="table"))

        # connect main buttons on home layout
        for k, button in self.home_layout.buttons.items():
            if isinstance(k, str):
                button.clicked.connect(
                    partial(self.show_table_page, manufacturer=k))
        # -- SET the THEME --
        self.set_theme(theme=self.theme)
        self.table_layout_assigned = False
        write_log(logfile=self.logfile, action="APP START",
                  comment="Application started", prt=True)
        self.gen_notification(title="Application started",
                              message="Printer Supply App started")
        self.show()

    def fill_columns(self):
        """
        fill_columns run the fillout_columns.py utility in the utils folder. This file (the DBHousekeeping class) will try to fill in any empty or invalid values held by items for columns including brand, type, color, and possibly more.

        fillout_columns.py can also be used independent of the application.
        """
        DBHousekeeping()
        # messagebox popup saying columns have been filled in as much as possible
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Columns have been filled in as much as possible.")
        msg.setWindowTitle("Columns Filled")
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(100, 35)
        msg.addButton(ok_button, QMessageBox.AcceptRole)
        msg.exec_()

    def show_home_page(self):
        """
        show_home_page shows the main window of the application.

        Displays the campus (set in config) above a QLineEdit (textbox) where the user can search by printer model. Four buttons are stacked beneath the textbox which lead to the app's spreadsheet view.

        """
        self.stack.setCurrentIndex(0)

    def show_table_page(self, manufacturer: str = None, table_query: str = None):
        """
        show_table_page displays the spreadsheet view of the stacked widget, index 1. The home page/view is index 0, and the dashboard view is index 2.

        Using a QStackedWidget allows to easily change between the app's 3 different windows, and change the actual data that the windows use to display information as well.

        Args:
            manufacturer (str, optional): manufacturer of items being shown. <b>If this argument is supplied, it means one of the home page's buttons is being clicked, or one of the View options in menubar</b>. Defaults to None.
            table_query (str, optional): query that the app will use to populate the table with items. Defaults to None.
        """
        column_str = ",".join([x[0] for x in self.columns.values()])

        # if the manufacturer argument is supplied, it means either the main page buttons or the View > Spreadsheet buttons are being clicked
        # --------------------------------------------------------------------------------------------------------------------------------------
        if manufacturer and (manufacturer.lower() != "others"):
            self.table_layout.set_table_model(
                query=f"SELECT {column_str} FROM inventory WHERE brand='{manufacturer}';")
            if manufacturer.lower() == "hp":
                self.table_layout.title.setText(
                    f"{manufacturer.upper()} Inventory")
            else:
                self.table_layout.title.setText(
                    f"{manufacturer.capitalize()} Inventory")
        elif manufacturer and (manufacturer.lower() == "others"):
            self.table_layout.set_table_model(
                query=f"SELECT {column_str} FROM inventory WHERE LOWER(brand) NOT IN ('hp', 'lexmark', 'dell')")
            self.table_layout.title.setText(
                f"{manufacturer[:-1].capitalize()} Inventory")

        # if the manufacturer argument is not supplied, but query is, use that to grab the table data
        elif table_query:
            self.table_layout.set_table_model(query=table_query)
            # TODO: come up with better looking title than whats below
            self.table_layout.title.setText(f"Results: {table_query}")
        # --------------------------------------------------------------------------------------------------------------------------------------

        # set stacked widget to show the table view
        self.stack.setCurrentIndex(1)

        # THE IF STATEMENT BELOW IS NECESSARY BECAUSE - without it, the table will make the doubleclicked connection to edit_app_item multiple times (every time the table page is reloaded)
        # edit item dialog will popup more and more times
        if not self.table_layout_assigned:
            self.table_layout.table.doubleClicked.connect(self.edit_app_item)
            self.table_layout_assigned = True

    def show_dashboard_page(self, window="home"):
        """
        show_dashboard_page displays the second index of the QStackedWidget that the application uses - the dashboard view.

        A printer model's "dashboard" will show all of the items held in inventory that are compatible with that printer model. It's a quick way to see if you have enough resources for a particular model, providing the compatible printers column of the inventory table has been filled out correctly.

        Args:
            window (str, optional): the window that the app is leaving to come into the dashboard view. Defaults to "home".
        """
        # get the current text from the home layout search bar
        if window == "home":
            home_model = self.home_layout.search_bar.text()
            printer_model = home_model
        else:
            dash_model = self.dashboard_layout.search_bar.text()
            printer_model = dash_model
        # check if printer model is in the qcompleter list - if it's not, it won't be a valid printer model from printers column in database
        if printer_model in self.printer_models_qcompleter.model().stringList():
            if printer_model.lower().startswith("hp"):
                model_name = printer_model[3:]
            elif printer_model.lower().startswith("dell"):
                model_name = printer_model[5:]
            elif printer_model.lower().startswith("lexmark"):
                model_name = printer_model[8:]
            elif printer_model.lower().startswith("brother"):
                model_name = printer_model[8:]
            else:
                model_name = printer_model
            # set title of dashboard padge
            self.dashboard_layout.set_model_title(printer_model.upper())

            # construct the query
            query = f"SELECT * FROM inventory WHERE FIND_IN_SET(\'{model_name.lower()}\', LOWER(printers))"
            # query the database
            results = self.query_database(query)
            self.stack.setCurrentIndex(1)
            self.populate_dashboard(results)
            self.stack.setCurrentIndex(2)

    def populate_dashboard(self, results):
        """
        populate_dashboard function to populate the app's dashboard view with widgets. Toner and ink items have the colored radials as their widgets.

        As of 5/6/23, other items like fusers, drums, waste containers, all use the same stock dashboard widget. <b>It'd be great to get some help coming up with ideas for widgets for these item types!</b>

        Args:
            results (list): a list of item dictionaries that the app will use to populate the dashboard with item widgets.
        """
        for i in reversed(range(self.dashboard_layout.grid.count())):
            self.dashboard_layout.grid.itemAt(i).widget().setParent(None)
        toner_radials = {}
        if hasattr(self, "radial_widgets"):
            for item in self.radial_widgets:
                self.radial_widgets[item].setParent(None)
        self.radial_widgets = {}
        x = 0
        x2=0
        y = 0
        y2 = 1
        for item in results:
            # if its toner or ink, create a circular progress bar (radial)
            if (item["type"] == "toner") or (item["type"] == "ink"):
                # this creates the frame that holds the radial / labels for a toner object
                toner_radials[item["code"]] = RadialFrame(
                    item, parent=self.parent())
                # connect the radials signal to edit function
                toner_radials[item["code"]].userClicked.connect(
                    self.edit_app_item)
                self.dashboard_layout.grid.addWidget(
                    toner_radials[item["code"]], y, x)
                x += 1
                # this (along with lines in elif statement) will try to separate the toner/ink radials from the other item widgets on the dashboard
                if x % 5 == 0:
                    y += 2
                    x = 0
            elif item["type"] in [
                "drum",
                "fuser",
                "transfer",
                "waste",
                "developer",
                "cleaner",
                "roller",
                "toner",
                "paper",
            ]:
                print("aframe")
                aframe = ItemFrame(item, parent=self.parent())
                # aframe.userClicked.connect(self.edit_item)
                aframe.userClicked.connect(self.edit_app_item)
                self.dashboard_layout.grid.addWidget(aframe, y2, x2)
                x2 += 1
                if x2 % 5 == 0:
                    y2 += 2
                    x2 = 0



    # Opening dialogs/popups: help dialog, search, add item, edit item, etc.
    # ----------------------------------------------------------------------------------------------------------

    def open_help_dialog(self):
        """open_help_dialog Function opens the help dialog window"""
        help_dialog = HelpPopup()
        help_dialog.docs_clicked.connect(
            lambda: self.open_in_browser(filepath=self.docs_file))
        help_dialog.app_guide_clicked.connect(
            lambda: self.open_in_browser(filepath=self.guide_file))
        help_dialog.exec_()

    def open_search_dialog(self):
        """
        open_search_dialog opens the popup dialog that has a QComboBox, QLineEdit, and QPushButton, so the user can choose a column and enter a search term to display items that fit those criteria.

        The search dialog is displayed by clicking the search option on either the main menubar or the app's secondary toolbar.
        """
        # show the search dialog
        search_dialog = SearchColumnsPopup(parent=self)
        search_dialog.dataEntered.connect(self.search_db_mode)

        search_dialog.exec_()

    def open_settings_dialog(self):
        """open_settings_dialog Function opens the settings dialog window"""
        settings_dialog = SettingsPopup()
        # if the settings dialog returns accepted() signal
        if settings_dialog.exec_():
            # the setting that you really notice right away when it doesn't take effect, is the theme
            # so we just run set_theme after initializing the config
            initialize_config(self)
            initialize_config(self.parent())
            self.set_theme(self.theme)
            self.set_home_title(self.campus)

    def set_home_title(self, campus: str):
        """set_home_title Function sets the title of the home page"""
        self.home_layout.title.setText(
            f"{campus.capitalize()} Printer Inventory")

    def open_in_browser(self, filepath):
        """open_in_browser Function opens the filepath in the default browser"""
        # Convert the file path to a QUrl object
        url = os.path.abspath(filepath)
        webbrowser.open_new_tab(url)

    # App theme functions
    # --------------------------------------------------------------------------------------

    def open_theme_dialog(self):
        """open_theme_dialog Function opens the theme dialog window"""
        theme_dialog = ThemePopup()
        theme_dialog.themeSignal.connect(self.set_theme)
        theme_dialog.exec_()
        """set_theme Function sets the theme of the application based on the config file"""

    def set_theme(self, theme):
        """
        set_theme sets the QSS stylesheet and theme of the app based on the configuration file, or the user's choices in one of the settings popups.

        _extended_summary_

        Args:
            theme (str): a filename of a QSS stylesheet, without the .qss file extension.
        """
        # make sure the user chose a theme:
        if theme == "Select a theme":
            return
        # set current app config theme to be the new theme
        self.theme = theme
        # load the new theme stylesheet and apply to app
        # try this - unless file isn't found, then load elegantdark
        try:
            with open(f"themes/{theme}.qss", "r") as f:
                app.setStyleSheet(f.read())

        # if somethings wrong and the specified theme file isn't found, load elegantdark (hopefully no one deletes this one?)
        # TODO: fallback to blank style / no file?
        except FileNotFoundError:
            theme = "ElegantDark"
            self.theme = theme
            with open(f"themes/{theme}.qss", "r") as f:
                app.setStyleSheet(f.read())

        # either way,
        # rewrite the ./config/config.yaml to show the new [app][theme]
        with open("./config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
            config["app"]["theme"] = theme
        with open("./config/config.yaml", "w") as f:
            yaml.dump(config, f)
        write_log(logfile=self.logfile, action="THEME CHANGE",
                  comment=f"Theme set to {theme}", prt=True)

        self.change_icon_colors()

    def open_scan_dialog(self):
        """
        open_scan_dialog open the popup that the user can use to scan printer-related item codes into the database.

        it has a red and greed 'LED' widget that will light up green when its ok to keep scanning, and red when you need to stop. The app will also play a sound when the red LED lights up, and play a relatively pleasant chime sound on a successful scan event.
        """
        self.input_window = ScanInputWindow(
            parent=self, systemtray=self.tray_icon)
        self.input_window.show()  # display the input window
        # set focus on the textEdit widget, hopefully place users cursor inside textbox
        self.input_window.textEdit.setFocus()

    # ----------------------------------------------------------------------------------------

    # Application Column-Selection related Functions:
    # ----------------------------------------------------------------------------------------
    def open_column_dialog(self):
        """open_column_dialog Function opens the column dialog window"""
        # check to make sure a table is currently being displayed
        if self.stack.currentIndex() != 1:
            self.gen_notification(
                title="Table not showing", message="Table must be visible to change columns in view.", notif_type=QSystemTrayIcon.Information)
            return
        column_dialog = ColumnSelection()
        column_dialog.data_ready.connect(self.set_columns)
        column_dialog.setStyleSheet(self.styleSheet())

    def set_columns(self, selected: list, unselected: list):
        """
        set_columns sets the columns of the table based on the config file

        _extended_summary_

        Args:
            selected (list): list of selected columns (in text / header form, not index)
            unselected (list): list of unselected columns in text
        """
        # loop through self.columns.items() and get the selected indices and unused indices
        selected_indices = []
        unused_indices = []
        for i, (k, col_name_list) in enumerate(self.columns.items()):

            if col_name_list[0] in selected:
                selected_indices.append(i)
            else:
                unused_indices.append(i)

        # open config/config.yaml and set all 4 config variables after converting the lists to comma separated strings
        with open("./config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
            config["preferences"]["selectedcolumns"] = ",".join(selected)
            config["preferences"]["selectedindices"] = ",".join(
                [str(i) for i in selected_indices])
            config["preferences"]["unusedcolumns"] = ",".join(unselected)
            config["preferences"]["unusedindices"] = ",".join(
                [str(i) for i in unused_indices])
        with open("./config/config.yaml", "w") as f:
            yaml.dump(config, f)
        # hide/show the correct columns with selected/unused indices
        for i in selected_indices:
            self.table_layout.table.setColumnHidden(i, False)
        for i in unused_indices:
            self.table_layout.table.setColumnHidden(i, True)
        # reset the table model
        self.table_layout.set_table_model()

    def handle_item_dialog(self, item, operation):
        """
        handle_item_dialog handles the signals emitted from the item dialog

        _extended_summary_

        Args:
            item (dict): dictionary containing details about an item.
            operation (str): string containing the operation to perform on the item. (edit, delete, insert)
        """
        if operation == "edit":
            self.edit_db_item(item=item)
        elif operation == "delete":
            self.delete_from_db(input_arg=item)
        elif operation == "insert":
            self.insert_into_db(item_dict=item)
        else:
            return
    # ----------------------------------------------------------------------------------------

    # Import UPC text file & Export Excel report:
    # ----------------------------------------------------------------------------------------
    def export_to_excel(self):

        # TODO: Get report type and some other details into the log
        ReportDialog(parent=self).exec_()
        write_log(logfile=self.logfile, action="REPORT CREATED",
                  comment=f"Report created", prt=True)
        self.gen_notification(
            title="Report Created", message="Report created successfully", notif_type=QSystemTrayIcon.Information)

    def import_item_list(self):

        upcfile, _ = QFileDialog.getOpenFileName(
            parent=self, caption="Choose file to import", directory="", filter="Text Files (*.txt)"
        )
        lookup_fails = []
        if upcfile:
            with open(upcfile, "r") as f:
                lines = f.readlines()
                # for each code
                for code in lines:
                    lookup_result = ItemLookup(
                        input_code=code, systemtray=self.tray_icon
                    )
                    if not lookup_result.look_up_code():
                        lookup_fails.append(code)

            # write failed lookups to file
            with open("failed-lookups.txt", "w") as f:
                f.writelines(lookup_fails)
            write_log(logfile=self.logfile, action="FILE IMPORT",
                      comment=f"Imported {len(lines)} items from {upcfile}", prt=True)
            # TODO: write system tray notification function that can do informational, alert, warning, etc. with a title and a message argument
            self.gen_notification(
                title="Import Complete", message=f"Imported {len(lines)} items from {upcfile}", notif_type=QSystemTrayIcon.Information)
        else:
            pass
    # ----------------------------------------------------------------------------------------

    # DATABASE Procedure functions:
    # Query for results
    def query_database(self, query: str, fetch_num="all"):
        """
        query_database takes arguments of: 1. an SQL query as a string, and 2. the number of results to fetch (all or one) and returns the results of the query

        The results of the query are returned as a list of dictionaries. Each dictionary represents a row in the database table and the keys are the column names.

        Args:
            query (str): SQL query to execute
            fetch_num (str, optional): how many rows or items to get (fetchall, fetchone...). Defaults to "all".

        Returns:
            _type_: _description_
        """
        db, cursor = connect_to_db(
            db_host=self.dbhost,
            db_user=self.dbuser,
            db_name=self.dbname,
            db_pass=self.dbpass,
            dicttrue=True,
        )
        cursor.execute(query)
        if fetch_num == "all":
            results = cursor.fetchall()
        elif fetch_num == "one":
            results = cursor.fetchone()
        cursor.close()
        db.close()
        return results
    # insert item into database

    def insert_into_db(self, item_dict: dict):
        # connect to the database
        db, cursor = connect_to_db(
            db_host=self.dbhost,
            db_user=self.dbuser,
            db_name=self.dbname,
            db_pass=self.dbpass,
            dicttrue=True,
        )
        # construct the query
        insert_statement = f"INSERT INTO inventory (brand,description,code,upc,stock,part_num,color,yield,type,comments,linked_codes,needed) VALUES (\'{item_dict['brand']}\', \'{item_dict['description']}\', \'{item_dict['code']}\', \'{item_dict['upc']}\', {int(item_dict['stock'])}, \'{item_dict['part_num']}\', \'{item_dict['color']}\', \'{item_dict['yield']}\', \'{item_dict['type']}\', \'{item_dict['comments']}\', \'{item_dict['linked_codes']}\', {int(item_dict['needed'])})"
        # TODO: check to make sure user has entered the 3 -5 required fields
        cursor.execute(insert_statement)
        db.commit()
        cursor.close()
        db.close()
        write_log(logfile=self.logfile, action="INSERT",
                  comment=f"Inserted {item_dict['description']} into database", prt=True)
        self.gen_notification(
            title="Item Inserted", message=f"Inserted {item_dict['description']} into database", notif_type=QSystemTrayIcon.Information)
        # TODO: add write_log statement for inserting item
        # TODO: make a sheet of all the log statements - insert, update, etc. - for the app guide
    # Edit

    def edit_db_item(self, item: dict):
        """
        edit_db_item basic function that takes a dictionary of item details as an argument, and edits the specified item in the database.

        Since the user is not allowed to change the UPC through the GUI, the UPC will stay the same, and therefore can be used to identify the item the user is trying to edit.

        Args:
            item (dict): dictionary of item details, each key is a column name from the 'inventory' table in the database, value is the data value of that item from that column.
        """
        try:
            # connect to the database
            db, cursor = connect_to_db(
                db_host=self.dbhost,
                db_user=self.dbuser,
                db_name=self.dbname,
                db_pass=self.dbpass,
                dicttrue=True,
            )
            # construct the query
            update_statement = f"UPDATE inventory SET brand=\'{item['brand']}\', description=\'{item['description']}\',printers=\'{item['printers']}\', code=\'{item['code']}\', stock=\'{item['stock']}\', part_num=\'{item['part_num']}\', color=\'{item['color']}\', yield=\'{item['yield']}\', type=\'{item['type']}\', comments=\'{item['comments']}\', linked_codes=\'{item['linked_codes']}\', needed=\'{item['needed']}\' WHERE upc=\'{item['upc']}\'"
            cursor.execute(update_statement)
            db.commit()
            cursor.close()
            db.close()
            write_log(logfile=self.logfile, action="UPDATE",
                      comment=f"Updated {item['description']} in database", prt=True)
            self.gen_notification(
                title="Item Updated", message=f"Updated {item['description']} in database", notif_type=QSystemTrayIcon.Information)
        except Exception as e:
            write_log(logfile=self.logfile, action="UPDATE FAIL",
                      comment=f"{item['description']} Failed: {e}", prt=True)
            self.gen_notification(
                title="Item Update Failed", message=f"Failed to update {item['description']} in database", notif_type=QSystemTrayIcon.Warning)
        if self.stack.currentIndex() == 1:
            self.table_layout.set_table_model()
        # TODO: refresh table
        # TODO: write log - db update
    # Delete

    def insert_item(self):
        """
        insert_item allows user to insert items into the database after checking to make sure theyre not already in there.

        The app will also try to grab as many details about the item as possible and insert them into the database using whatever code is typed in by the user.
        """
        # first ask user to type code into a ApiLookup - app will try to look it up and grab details\
        user_notes = ApiLookup(parent=self)
        if user_notes.exec_() == QDialog.Accepted:
            # get code and try look it up, this will actually check the database first, but then it will go out and check api
            notes = user_notes.textValue()
            if (notes) and (notes != ""):
                result = ItemLookup(input_code=notes).look_up_code()
                if result:
                    # TODO: open an edit item dialog, with the item's existing details (one's that api pulled) inserted in the qlineedits
                    # if the lookup was successful, then item has been inserted into the database, so open an edit item dialog with the item details
                    # -- for now, just display popup saying item was added
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText(f"Item {notes} added to database.")
                    msg.setWindowTitle("Item Added")
                    ok_button = QPushButton("OK")
                    ok_button.setFixedSize(100, 35)
                    msg.addButton(ok_button, QMessageBox.AcceptRole)
                    msg.exec_()

                else:
                    item_dialog = ItemPopup(
                        operation="insert", parent=self)
                    # item_dialog.dataEntered.connect(self.edit_db_item)
                    if item_dialog.exec_() == QDialog.Accepted:
                        # get the item from the item dialog
                        item = item_dialog.get_item()
                        # open the edit item dialog
                        self.insert_into_db(item_dict=item)

                write_log(logfile=self.logfile, action="INSERT",
                          comment=f"Inserted {notes} into database", prt=True)
                self.gen_notification(
                    title="Item Inserted", message=f"Inserted {notes} into database", notif_type=QSystemTrayIcon.Information)
                return
        # if user closes the notes dialog or something else goes wrong:
        else:
            # just open the item dialog with a blank item
            item_dialog = ItemPopup(
                operation="insert", parent=self)
            # item_dialog.dataEntered.connect(self.edit_db_item)
            if item_dialog.exec_() == QDialog.Accepted:
                # get the item from the item dialog
                item = item_dialog.get_item()
                # open the edit item dialog
                self.insert_into_db(item_dict=item)
                write_log(logfile=self.logfile, action="INSERT",
                          comment=f"Inserted {item['description']} into the database", prt=True)
                self.gen_notification(
                    title="Item Inserted", message=f"Inserted {item} into database", notif_type=QSystemTrayIcon.Information)

    def edit_app_item(self, input_arg):
        """
        edit_app_item called when the user double-clicks either a an item via a table row, or a widget on a dashboard. When the user double-clicks a table row, input_arg will be a QModelIndex. When the user clicks dashboard widget, input_arge will be a dictionary of the widget's details.

        This function is meant to combine the multiple edit functions present in previous versions.

        Args:
            input_arg (_type_): _description_
        """
        if isinstance(input_arg, QModelIndex):
            row = input_arg.row()
            data = {}
            for column in range(self.table_layout.table.model().columnCount()):
                header = self.table_layout.table.model().headerData(column, Qt.Horizontal)
                item = self.table_layout.table.model().index(row, column).data(Qt.DisplayRole)
                data[header.lower()] = item
            # open item dialog with the item dictionary
            item_dialog = ItemPopup(
                operation="edit", parent=self, input_item=data)
            item_dialog.db_operation.connect(self.handle_item_dialog)

            # item_dialog.dataEntered.connect(self.edit_db_item)
            item_dialog.exec_()
            # return
        elif isinstance(input_arg, dict):
            item_dialog = ItemPopup(
                operation="edit", parent=self, input_item=input_arg)
            # item_dialog.dataEntered.connect(self.edit_db_item)
            item_dialog.db_operation.connect(self.handle_item_dialog)
            item_dialog.exec_()

            # return
        elif input_arg == None:
            popup = FindItemDialog(parent=self)
            popup.exec_()
            if popup.result() == 1:
                # get the code and upc from the popup
                code = popup.code
                upc = popup.upc

                # construct query using the parameters entered (either code, upc, or both)
                if code == "" and upc == "":
                    return
                elif code == "":
                    query = f"SELECT * FROM inventory WHERE upc=\'{upc}\'"
                elif upc == "":
                    query = f"SELECT * FROM inventory WHERE code=\'{code}\'"
                else:
                    query = f"SELECT * FROM inventory WHERE code=\'{code}\' AND upc=\'{upc}\'"
                results = self.query_database(query, fetch_num="one")
                # if there are no results, show a popup saying that no item was found
                if len(results) == 0:
                    return
                else:
                    # if there are results, populate the item dialog with the data
                    # open item dialog with data pre-populated
                    item_dialog = ItemPopup(
                        operation="edit", parent=self, input_item=results)
                    item_dialog.db_operation.connect(self.handle_item_dialog)
                    item_dialog.exec_()

        # if there are results, populate the item dialog with the data
        else:
            # open item dialog with data pre-populated
            item_dialog = ItemPopup(
                operation="edit", parent=self, input_item=item)
            item_dialog.db_operation.connect(self.handle_item_dialog)
            item_dialog.exec_()

    def delete_from_db(self, input_arg=None):
        """
        delete_from_db deletes item from the database, and from the table on display (if applicable).

        Function is called when the user clicks on the trash can icon, after double-clicking a row on a table or widget on a dashboard.

        Args:
            input_arg (_type_, optional): _description_. Defaults to None.
        """
        description = input_arg["description"]
        upc = input_arg["upc"]

        db, cursor = connect_to_db(
            db_host=self.dbhost,
            db_user=self.dbuser,
            db_name=self.dbname,
            db_pass=self.dbpass,
            dicttrue=True,
        )
        delete_query = f"DELETE FROM {self.tablename} WHERE upc = \'{upc}\' AND description=\'{description}\'"
        cursor.execute(delete_query)
        db.commit()
        cursor.close()
        db.close()
        write_log(logfile=self.logfile, action="DELETE",
                  comment=f"Deleted {description} from database", prt=True)
        self.gen_notification(
            title="Item Deleted", message=f"Deleted {description} from database", notif_type=QSystemTrayIcon.Information)
        # if a table is being displayed, then get currently selected row and delete it from the table
        if self.stack.currentIndex() == 1:
            self.table_layout.set_table_model()

    def search_db_mode(self, mode: str, input_query: str = None):
        """
        search_db_mode the user can search any of the columns in the inventory table by typing in the search bar. This function will display the results in a table.

        _extended_summary_

        Args:
            mode (str): where the search is initiated from. Can be either 'table' or 'popup', this tells the app in which QLineEdit (textbox) to look for the search term that the user has typed.
            input_query (str, optional): an SQL query passed in as an argument when the search is initiated from the popup. A user can view this popup by choosing search on one of the menubars. Defaults to None.
        """
        # search the database for the search term
        # column stirng
        column_str = ""
        for col_name in self.columns.values():
            column_str += f"{col_name[0]}, "
        column_str = column_str[:-2]
        # set the table model to the results of the search
        # if mode is table, get text from table qlineedit
        if mode == "table":
            search_term = self.table_layout.search_bar.text()
            # get column name from combobox
            column_name = self.table_layout.combobox.currentText()
            if search_term and column_name != "Choose column:":
                # construct query
                # CANNOT just use * in query, because the table model will not be able to match the correct column's data to the correct column header
                # TODO: Try to fix the above issue.
                search_query = f"SELECT {column_str} FROM inventory WHERE {column_name} LIKE '%{search_term}%'"
                new_title = f"Search Results: {column_name} - {search_term}"
                self.table_layout.set_table_model(query=search_query)
                self.table_layout.set_title_text(new_title)
        # if search is done from the popup dialog
        if mode == "popup":
            # don't need to get search text because query passed in input_query
            search_query = input_query
            new_title = "Search Results:"
            self.table_layout.set_table_model(query=search_query)
            self.table_layout.set_title_text(new_title)

        self.show_table_page()

    def backup_to_csv(self, notification=True):
        """
        backup_to_csv first prompts the user with a yes/no popup asking if they'd like to backup the inventory table to a csv file. If yes, then the table is backed up to a csv file in the <b>output folder.</b>

        If the user hasn't muted the app's notifications, then a notification is sent to the system tray with the filename. CSV filenames are auto-generated with the date and time appended to the end.

        Args:
            notification (bool, optional): _description_. Defaults to True.
        """
        # output filename is auto-created
        # TODO: make config setting for this, or prompt user?
        # first do yes no messagebox asking user if they want to backup to csv
        # make QMessageBox w/ok button
        popup = QMessageBox()
        popup.setWindowTitle("Backup to CSV?")
        popup.setWindowIcon(QIcon(self.icon))
        popup.setText(
            "Would you like to backup the inventory table to a CSV file?")
        popup.setIcon(QMessageBox.Question)
        popup.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        for button in popup.buttons():
            button.setCursor(Qt.PointingHandCursor)
        if popup.exec_() == QMessageBox.Yes:
            # filepath is returned from databackup - put it on Okpopup for user
            backup = DataBackup()
            relative_path = os.path.join("output", backup.csvname)
            # show popup QMessageBox with filepath
            message = f"Backup file saved to: {relative_path}"
            # if user needs popup notification, do that
            if (notification == True) and (not self.mute):

                # make QMessageBox w/ok button
                popup = QMessageBox()
                popup.setWindowTitle("Backup Complete")
                popup.setWindowIcon(QIcon(self.icon))
                popup.setText(message)
                popup.setIcon(QMessageBox.Information)
                popup.setStandardButtons(QMessageBox.Ok)
                popup.button(QMessageBox.Ok).setCursor(Qt.PointingHandCursor)
                popup.exec_()
                # log it
                write_log(logfile=self.logfile, action="BACKUP TO CSV",
                          comment=message, prt=True)

    # Build QCompleters for search QLineEdits (Search bars)

    def build_qcompleters(self) -> tuple:
        """
        build_qcompleters builds the two QCompleters used by the app. As of 5/6/23, this version of the app only uses the models completer. The codes completer is not used.

        The codes completer could be used to add an extra way of searching to the home page. There could be a couple of buttons to the left of the textbox where the user can choose to search by model or by code. The code completer would be used if the user chooses to search by code.

        Returns:
            tuple: returns a tuple containing the two QCompleters
        """
        # built the printer model qcompleter to be used in the search bar on home window (possibly other locations)
        db, cursor = connect_to_db(
            db_host=self.dbhost,
            db_user=self.dbuser,
            db_name=self.dbname,
            db_pass=self.dbpass,
            dicttrue=False,
        )
        # -- LIST OF ALL PRINTER MODELS FROM THE 'PRINTERS' COLUMN IN THE DATABASE --
        models_list = []
        # -- LIST OF ALL TONER/ITEM CODES FROM THE 'CODE' COLUMN IN THE DATABASE --
        codes_list = []

        # dictionary to hold lists of each manufacturer's printer models (to be used in the suggestion listbox part of the autocomplete Entry)
        printer_models = {
            "dell": [],
            "hp": [],
            "lexmark": [],
            # brother, canon, epson don't have enough printers to need a table to themselves so they're combined, might change the text on the actual button to say brother,canon,epson though
            "others": [],
        }
        prevlist = ""
        # cycle thru each of the keys in the above dictionary
        for brand in printer_models.keys():
            if brand in ["dell", "hp", "lexmark"]:
                # set query to select the 'printers' column from each brand's table (there are three brand tables in the database - dell, hp, lexmark)
                query = f"SELECT printers, code, brand FROM inventory WHERE brand=\'{brand}\'"
            else:
                # set query to select the 'printers' column from each brand's table (there are three brand tables in the database - dell, hp, lexmark)
                query = f"SELECT printers, code, brand FROM inventory WHERE brand NOT IN ('dell', 'lexmark', 'hp')"

            cursor.execute(query)
            # temp_list will be all resulting rows from the query
            temp_list = cursor.fetchall()

            # keys will be the  upc, with lists containing code and stock as values

            # start cycling through each of the rows in the result, each row is a row of the 'printers' column from the database tables
            for row in temp_list:
                manufacturer = row[2]
                if row[0] != None:
                    sublist = row[0].split(",")
                    if sublist == prevlist:
                        pass
                    else:
                        # for each printer model in this list that we just created (sublist)
                        for model in sublist:
                            # strip any whitespace
                            model = model.strip()
                            # check if the model is already in the list and append it if it isn't
                            if model.lower() not in printer_models[brand]:
                                printer_models[brand].append(
                                    model.lower())

                        # for key in self.manufacturer_btns.keys():
                        for model in printer_models[brand]:
                            # key is the manufacturer name, model is the printer model
                            models_list.append(f"{manufacturer} {model}")
                # code gets here if the query returns no results / rows
                else:
                    pass
                codes_list += [row[1] for row in temp_list if row[1] != None]
        codes_list = set(codes_list)
        # if the above loops are fixed - wont have to use this way to get unique values in list
        models_list = set(models_list)
        models_list = list(models_list)
        # close connection to database
        db.close()
        # make a QCompleter for the auto-suggestion textbox so it will suggest printer model names as you type
        models_completer = QCompleter(models_list)
        codes_completer = QCompleter(codes_list)
        # make it case insensitive
        models_completer.setCaseSensitivity(Qt.CaseInsensitive)
        codes_completer.setCaseSensitivity(Qt.CaseInsensitive)

        return models_completer, codes_completer

    def build_tray(self) -> tuple:
        """
        build_tray build_tray_menu builds the tray menu and adds the context menu and actions to it. It uses the icon from config.yaml, like alot of the popups and other things in the app.

        Clicking on the tray icon doesn't seem to work in Windows 11, and the tray icon exhibits other wierd behaviors. Note --> try it out in Windows 10 to get confirmation that it works there.

        Returns:
            tuple: returns a tuple containg the QSystemTrayIcon and the QMenu that's attached to it.
        """
        tray_icon = QSystemTrayIcon(parent=self)
        tray_icon.setIcon(QIcon(self.icon))
        tray_icon.setToolTip(self.app_name)

        # create the tray menu
        tray_menu = QMenu(parent=self)
        tray_menu.addAction("About", self.open_help_dialog)
        tray_menu.addAction("Exit", self.close)
        tray_icon.setContextMenu(tray_menu)
        return tray_icon, tray_menu

    def gen_notification(self, title: str, message: str, notif_type: QSystemTrayIcon = QSystemTrayIcon.Information):
        """
        gen_notification generates a notification using the title and message provided. Notif_type is set to Information by default, but can be changed to Warning or Critical to change the icon that is displayed with the notification.

        Args:
            title (str): the title of the system tray notification.
            message (str): the message body of the system tray notification.
            notif_type (QSystemTrayIcon, optional): the type of icon to be displayed with the system tray icon. Defaults to QSystemTrayIcon.Information.
        """
        # if user has muted notifications, don't notify them
        if self.mute == 0:
            return
        # create a notification
        notification = QSystemTrayIcon(parent=self)
        notification.setIcon(QIcon(self.icon))
        notification.show()
        notification.showMessage(title, message, notif_type, 4000)

    def change_table_columns(self):
        """
        change_table_columns user can add or remove columns from the table that is currently being shown, using a popup that appears.

        If a table isn't currently being shown, nothing will happen.
        """
        # the model attribute is created when a spreadsheet is shown
        initialize_config(
            self
        )  # reread the config to get the selected column names, they might be new since start of app
        if self.stack.currentIndex() == 1:
            # get used columns from the config
            selected_columns = []
            # self.selected_columns is set in initialize_config
            used_column_names = [
                column_name for column_name in self.selected_columns]
            unused_columms = []
            # get indices of columns
            for index, value in self.columns.items():
                if value[0] in used_column_names:
                    # selected_columns[selected_columns.index(value)] = index
                    selected_columns.append([value[0], int(index)])
                    # selected_columns.replace(value[0], index)
                else:
                    unused_columms.append([value[0], int(index)])

            header_list = selected_columns
            unused_header_list = unused_columms
            try:
                dialog = ColumnEdit(
                    header_list, unused_header_list, parent=self)

                if dialog.exec_() == QDialog.Accepted:
                    self.table_columns = dialog.get_values()
                    self.table_layout.set_table_model()
                    dialog.close()
            except AttributeError:
                self.gen_notification(
                    title="Error", message="Wasn't able to open the column choices dialog.", notif_type=QSystemTrayIcon.Critical)

        else:
            self.gen_notification(
                title="Cannot open dialog:", message="No table is currently visible.", notif_type=QSystemTrayIcon.Information)

    def change_icon_colors(self):
        """
        change_icon_colors cycles through the qtawesome icons used in the app (like the ones used in the main menubar) and changes their color to white or black, depending on the theme that is currently being used.

        <b>Themes are divided into dark and light theme groups in the utils.toner_utils initialize_config module</b>.
        """
        # check the main application window's background color and see if  its dark or light
        # then  so set icon colors to near white
        # cycle through the main menubar actions and reset their icons
        for action in self.parent().menuBar().actions():
            # for each menu, iterate through its actions
            for subaction in action.menu().actions():
                # get the text from the action
                text = subaction.text()
                # check if any of the icon string keys are in the text from the action (for example, the key "import" will be in the action text "Import UPC File")
                for key in self.icon_strings.keys():
                    if key in text.lower():
                        # check if its a dark or light theme
                        if self.theme in self.dark_themes:
                            # create qtawesome icon
                            icon = qtawesome.icon(
                                self.icon_strings[key][0], color="white")
                        else:
                            icon = qtawesome.icon(
                                self.icon_strings[key][0], color="black")
                        # set the icon
                        subaction.setIcon(icon)

    def reset_database(self):
        """
        reset_database resets all stock values in the inventory table to 0 after double-checking with the user.

        The app will also perform a silent backup to csv before resetting the database.
        """
        # check if the user is sure they want to reset the database
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Are you sure you want to reset the database?")
        msg.setWindowTitle("Reset Database")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        # if the user clicks yes, reset the database
        if msg.exec_() == QMessageBox.Yes:

            # update all stock in database to 0 after running backup.
            self.backup_to_csv(notification=False)
            # connect to database
            db, cursor = connect_to_db(
                db_host=self.dbhost,
                db_user=self.dbuser,
                db_name=self.dbname,
                db_pass=self.dbpass,
                dicttrue=True,
            )
            # had to disable SAFE UPDATES in MySQL database to be able to do this query
            update_query = f"UPDATE {self.tablename} SET stock = 0 WHERE 1=1"
            cursor.execute(update_query)
            db.commit()
            db.close()
            self.gen_notification(
                title="Database Reset", message="Database has been reset."
            )
            # log the reset
            write_log(logfile=self.logfile, action="RESET DB",
                      comment="Database was reset, all stock values set to 0.", prt=True)

    def check_for_duplicates_popup(self):
        """
        check_for_duplicates generate popup window that shows a combo box with all table columns in it and an ok button

        Oftentimes, items that have duplicate values will be ones that can be linked. For example, two separate toner items that amount to the same part number (same yield value, same color, etc.) but they have different UPCs. By default, the app will separate these items into two different ones, but through the use of this function and 'linking the items', the user can choose to have the two items show up as one.
        """
        # get the column names from the config
        column_names = [value[0] for value in self.columns.values()]
        # create a dialog
        dialog = QDialog(parent=self)
        dialog.setWindowTitle("Check for Duplicates")
        dialog.setWindowIcon(QIcon(self.icon))
        # create a layout
        layout = QVBoxLayout(dialog)
        # create a combo box
        combo_box = QComboBox(dialog)
        combo_box.addItems(column_names)
        # create a button
        button = QPushButton("OK", dialog)
        # add the combo box and button to the layout
        layout.addWidget(combo_box)
        layout.addWidget(button)
        # set the layout
        dialog.setLayout(layout)
        # connect the button to a function
        button.clicked.connect(
            lambda: self.check_for_duplicates_action(combo_box, dialog))
        # show the dialog
        dialog.exec_()

    def check_for_duplicates_action(self, combo_box, dialog):
        """
        check_for_duplicates_action the action of checking for duplicates.

        <b>Read description of check_for_duplicates_popup for more information.</b>

        Args:
            combo_box (QComboBox): necessary so that the function can get the text from the combo box (the column that will be searched for duplicates)
            dialog (QDialog): so the app can close the QDialog.
        """
        # get text from combobox
        column_name = combo_box.currentText()
        # close the dialog
        dialog.close()
        # get query ready for table
        column_str = ",".join([x[0] for x in self.columns.values()])

        query = f"SELECT {column_str} FROM {self.tablename} WHERE {column_name} IN (SELECT {column_name} FROM {self.tablename} GROUP BY {column_name} HAVING COUNT(*) > 1)"
        # display table with the data
        self.show_table_page(table_query=query)


class MainWindowShell(QMainWindow):
    def __init__(self):
        """
        __init__ This QMainWindow holds the QStackedWidget which makes up the core of the application. The QStackedWidget stacks widgets on top of each other, and can switch between them.
        """
        super().__init__()
        initialize_config(self)

        # set basic window details
        self.setWindowTitle(f"{self.app_name} - {self.version}")
        self.setWindowIcon(QIcon(self.icon))

        self.stackedwidget = StackedApp(self)
        self.build_menu()
        self.setCentralWidget(self.stackedwidget)

    def build_menu(self):
        """
        build_menu Creates the main MenuBar for the app, as well as the secondary toolbar which is directly underneath the main menubar. Adds icons and actions to the menubar and toolbar buttons.
        """
        # TODO: Look for more efficient way to build main menubar and secondary toolbar.
        # ------------------------------------
        # MAIN MENUBAR:
        menubar = self.menuBar()
        # TOP/MAIN MENU OPTIONS:
        menubar_option_names = ["File", "Edit", "View", "Settings", "Help"]
        # create the top/main menu options
        menubar_options = {}
        for option in menubar_option_names:
            menubar_options[option] = menubar.addMenu(option)

        # -- File menu
        #  Search function : File > Search
        search_icon = qtawesome.icon("fa5s.search", color=QColor("#e7e7e7"))
        search_action = QAction(search_icon, "Search", self)

        search_action.setShortcut("Ctrl+F")
        search_action.triggered.connect(self.stackedwidget.open_search_dialog)
        menubar_options["File"].addAction(search_action)

        # Import upcs option : File > Import UPCs
        qtimporticon = qtawesome.icon(
            "mdi.import", color=QColor("#e7e7e7"), scale_factor=1.75
        )
        import_item_list_action = QAction(
            qtimporticon, "Import UPC File", self)
        menubar_options["File"].addAction(import_item_list_action)
        import_item_list_action.triggered.connect(
            self.stackedwidget.import_item_list)

        # File > Reset Database
        reset_icon = qtawesome.icon(
            "mdi6.database-refresh", color=QColor("#e7e7e7"))
        reset_database_action = QAction(reset_icon, "Reset Database", self)
        reset_database_action.triggered.connect(
            self.stackedwidget.reset_database)
        menubar_options["File"].addAction(reset_database_action)

        # File > Normalize database
        normalize_icon = qtawesome.icon(
            "fa.bar-chart-o", color=QColor("#e7e7e7"))
        normalize_database_action = QAction(
            normalize_icon, "Fill in columns", self)
        normalize_database_action.triggered.connect(
            self.stackedwidget.fill_columns)
        menubar_options["File"].addAction(normalize_database_action)
        menubar_options["File"].addSeparator()

        # Return Home option : File > Return Home
        home_icon = qtawesome.icon(
            "mdi.home", color=QColor("#e7e7e7"), scale_factor=1.75)
        return_home_action = QAction(home_icon, "Return Home", self)

        return_home_action.triggered.connect(self.stackedwidget.show_home_page)
        return_home_action.setShortcut("Ctrl+H")
        menubar_options["File"].addAction(return_home_action)
        menubar_options["File"].addSeparator()

        # Exit option : File > Exit
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        menubar_options["File"].addAction(exit_action)

        # -- Edit menu
        duplicates_icon = qtawesome.icon(
            "mdi6.content-duplicate", color=QColor("#e7e7e7"), scale_factor=1.75
        )
        # Remove Duplicates option : Edit > Check for duplicates
        check_for_duplicates_action = QAction(
            duplicates_icon, "Check for duplicates", self)
        check_for_duplicates_action.setShortcut("Ctrl+D")
        menubar_options["Edit"].addAction(check_for_duplicates_action)
        check_for_duplicates_action.triggered.connect(
            self.stackedwidget.check_for_duplicates_popup)
        menubar_options["Edit"].addSeparator()
        # Insert Item option : Edit > Insert Item
        insert_icon = qtawesome.icon(
            "mdi.plus-box-outline", color=QColor("#e7e7e7"), scale_factor=1.75
        )
        insert_item_action = QAction(insert_icon, "Insert Item", self)
        insert_item_action.setShortcut("Ctrl+I")
        menubar_options["Edit"].addAction(insert_item_action)
        insert_item_action.triggered.connect(self.stackedwidget.insert_item)
        # Edit Item option : Edit > Edit Item
        edit_icon = qtawesome.icon(
            "mdi6.database-edit-outline", color=QColor("#e7e7e7"), scale_factor=1.75)
        edit_item_action = QAction(edit_icon, "Edit Item", self)
        # edit_item_action.triggered.connect(
        #     partial(self.stackedwidget.edit_item, item=None))
        edit_item_action.triggered.connect(
            partial(self.stackedwidget.edit_app_item, input_arg=None))
        edit_item_action.setShortcut("Ctrl+E")
        menubar_options["Edit"].addAction(edit_item_action)

        # -- View menu
        # Options to view each manufacturer spreadsheet
        actions = {}
        for mfr in ["dell", "hp", "lexmark", "others"]:
            actions[mfr] = QAction(f"{mfr.capitalize()} spreadsheet", self)
            menubar_options["View"].addAction(actions[mfr])
            menubar_options["View"].addSeparator()
            # connect to show table
            actions[mfr].triggered.connect(
                partial(self.stackedwidget.show_table_page, manufacturer=mfr))

        # -- Settings menu
        # Display theme toggle : Settings > Dark/Light mode
        theme_icon = qtawesome.icon(
            "mdi6.monitor-eye", color=QColor("#e7e7e7"), scale_factor=1.75
        )
        change_display_mode = QAction(theme_icon, "Change theme", self)
        change_display_mode.setToolTip(
            "Change the QSS stylesheet (theme) for the application.")
        change_display_mode.triggered.connect(
            self.stackedwidget.open_theme_dialog)

        menubar_options["Settings"].addAction(change_display_mode)
        # change table columns
        change_table_icon = qtawesome.icon(
            "ri.insert-column-left", color=QColor("#e7e7e7"), scale_factor=1.75
        )
        change_table_columns = QAction(
            change_table_icon, "Choose columns", self
        )
        change_table_columns.setToolTip(
            "Add or substract from current columns being shown on a table."
        )
        change_table_columns.triggered.connect(
            self.stackedwidget.open_column_dialog)
        menubar_options["Settings"].addAction(change_table_columns)

        # View ALL SETTINGS option : Settings > View all settings
        view_settings_icon = qtawesome.icon(
            'mdi6.cog', color=QColor("#e7e7e7"), scale_factor=1.75)
        view_settings_action = QAction(
            view_settings_icon, "View all settings", self)
        view_settings_action.setToolTip("View all settings in the app.")
        view_settings_action.triggered.connect(
            self.stackedwidget.open_settings_dialog)
        menubar_options["Settings"].addAction(view_settings_action)

        # -- Help menu
        # About option : Help > About
        about_icon = qtawesome.icon(
            "mdi.information-outline", color=QColor("#e7e7e7"), scale_factor=1.75
        )
        about_action = QAction(about_icon, "About", self)
        menubar_options["Help"].addAction(about_action)
        about_action.triggered.connect(self.stackedwidget.open_help_dialog)

        # ------------------------------------
        # TOOLBAR UNDERNEATH MAIN MENU (self.secondary_toolbar)
        secondary_toolbar = TonerToolbar(parent=self)
        self.addToolBar(secondary_toolbar)
        toolbaricons = {}
        toolbaractions = {}
        # return home button
        toolbaricons["home"] = qtawesome.icon(
            "mdi6.home", color="white", scale_factor=0.75
        )
        toolbaractions["home"] = QAction(self)
        toolbaractions["home"].setToolTip("Return to home page.")
        toolbaractions["home"].triggered.connect(
            self.stackedwidget.show_home_page)
        # settings button
        toolbaricons["settings"] = qtawesome.icon(
            'ei.cogs', color='white', scale_factor=0.75)
        toolbaractions["settings"] = QAction(self)
        toolbaractions["settings"].setToolTip("Open settings dialog.")
        toolbaractions["settings"].triggered.connect(
            self.stackedwidget.open_settings_dialog)
        # database backup
        toolbaricons["backup"] = qtawesome.icon('mdi.database-arrow-down',
                                                color='white', scale_factor=0.75)
        toolbaractions["backup"] = QAction(self)
        toolbaractions["backup"].setToolTip(
            "Backup the database to a file on your computer.")
        toolbaractions["backup"].triggered.connect(
            self.stackedwidget.backup_to_csv)
        # search button
        toolbaricons["search"] = qtawesome.icon(
            "mdi6.printer-search", color="white", scale_factor=0.75
        )
        toolbaractions["search"] = QAction(self)
        toolbaractions["search"].setToolTip(
            "Search the database by any of it's existing columns."
        )
        toolbaractions["search"].triggered.connect(
            self.stackedwidget.open_search_dialog)

        # open scan input window
        toolbaricons["barcode"] = qtawesome.icon(
            "mdi6.barcode-scan", color="white", scale_factor=0.75
        )
        toolbaractions["barcode"] = QAction(self)
        secondary_toolbar.setIconSize(QSize(30, 30))
        # toolbaractions["barcode"].setIcon(toolbaricons["barcode"])
        toolbaractions["barcode"].setToolTip(
            "Place cursor inside the textbox that opens and begin scanning items, turn up volume please."
        )
        toolbaractions["barcode"].setShortcut("Ctrl+B")
        toolbaractions["barcode"].triggered.connect(
            self.stackedwidget.open_scan_dialog)

        # -- Import UPC FILE option : on the secondary toolbar
        toolbaricons["import"] = qtawesome.icon(
            "fa5s.file-import", color="white", scale_factor=0.60
        )
        toolbaractions["import"] = QAction(self)
        # toolbaractions["import"].setIcon(toolbaricons["import"])
        toolbaractions["import"].setToolTip(
            "Import .txt File containing 1 UPC code per line"
        )
        toolbaractions["import"].setShortcut("Ctrl+I")
        toolbaractions["import"].triggered.connect(
            self.stackedwidget.import_item_list)

        # -- Export to Excel button
        toolbaricons["export"] = qtawesome.icon(
            "mdi6.microsoft-excel", color="white", scale_factor=0.75
        )

        toolbaractions["export"] = QAction(self)
        toolbaractions["export"].setToolTip(
            "Export the current inventory to .xlsx spreadsheet"
        )
        secondary_toolbar.setIconSize(QSize(50, 50))
        toolbaractions["export"].setShortcut("Ctrl+E")
        toolbaractions["export"].triggered.connect(
            self.stackedwidget.export_to_excel)

        for key, qaction in toolbaractions.items():
            qaction.setIcon(toolbaricons[key])
            secondary_toolbar.addAction(qaction)
            # self.stackedwidget.secondary_toolbar.addSeparator()

    def closeEvent(self, event):
        """closeEvent Overrides the default closeEvent to prompt user to confirm they want to close the application."""
        if self.safety_net == 1:
            close_warning = WarningPopup(
                parent=self, title="Exit", message="Are you sure you want to exit?"
            )
            # close_warning.setStyleSheet(self.current_style)
            if close_warning.exec() == QDialog.Accepted:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

class CredsPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Credentials")
        self.setWindowIcon(qtawesome.icon("mdi6.database-settings"))
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(400, 200)

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        # create 2 sets of a qlabel and qlineedit - one for username, one for password
        self.username_label = QLabel("Username: ")
        self.username_lineedit = QLineEdit()
        self.username_lineedit.setPlaceholderText("Enter username here")
        self.username_lineedit.setFixedWidth(200)
        self.username_lineedit.setFixedHeight(30)
        self.username_lineedit.setClearButtonEnabled(True)
        self.layout.addRow(self.username_label, self.username_lineedit)

        self.password_label = QLabel("Password: ")
        self.password_lineedit = QLineEdit()
        self.password_lineedit.setPlaceholderText("Enter password here")
        self.password_lineedit.setFixedWidth(200)
        self.password_lineedit.setFixedHeight(30)
        self.password_lineedit.setClearButtonEnabled(True)
        self.layout.addRow(self.password_label, self.password_lineedit)

        # create a submit button
        self.submit_button = QPushButton("Submit")
        self.submit_button.setFixedWidth(200)
        self.submit_button.setFixedHeight(30)
        self.submit_button.clicked.connect(self.submit_creds)
        self.layout.addRow(self.submit_button)
    
    def submit_creds(self):
        pass

if __name__ == '__main__':
    # Create the application instance
    app = QApplication(sys.argv)
    # create a QMessageBox for database creds
    # creds_popup = CredsPopup()
    # creds_popup.show()

    # Create the main window shell (which creates stacked widget and sets it as central widget with home page on display)
    window = MainWindowShell()
    window.show()
    # Run the event loop
    sys.exit(app.exec_())
