import os
import yaml
from datetime import datetime
import mysql
import mysql.connector
from PyQt5.QtGui import (
    QLinearGradient,
    QColor,
    QGradient
)
from PyQt5.QtWidgets import QSystemTrayIcon
from datetime import datetime

def connect_to_db(db_host:str, db_user:str, db_name:str, db_pass:str, dicttrue:bool) -> tuple:
    """
    connect_to_db Establishes connection to database using provided parameters and credentials, and returns database and cursor objects for querying.

    Here's one of the webpages with some basic information on the alternative method of dealing with the MySQL database: <link>https://www.tutorialspoint.com/pyqt5/pyqt5_database_handling.htm</link>

    Args:
        db_host (str): hostname or IP address of database server.
        db_user (str): database username
        db_name (str): database name (name of schema), ex: `printers_db`
        db_pass (str): database password for database user
        dicttrue (bool): True if you want the results returned as a dictionary, False if you want a list

    Returns:
        tuple: contains database and cursor objects for querying.
    """
    database = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database=db_name)

    cursorObject = database.cursor(dictionary=dicttrue)
    cursorObject.execute("SET sql_mode='';")

    return database,cursorObject


def write_log(logfile:str="logfile", action:str="LOG UPDATE", comment:str="The log was updated.", prt:bool=True):
    """
    write_log Universal "write to log" function that all files in the project can use to write to the log file specified in the config variables.

    Some documentation on the application logs, and standardization of terms used in said application logs is definitely needed.

    Args:
        logfile (str, optional): txt file in which to append the entry. Defaults to "logfile".
        action (str, optional): a "heading" for the entry, written in ALL CAPS in the log. Preceds the comment of the entry. Defaults to "LOG UPDATE".
        comment (str, optional): The action / "heading" provides the bullet point of the entry, the comment provides any additional details. Defaults to "The log was updated.".
        prt (bool, optional): If True, the function will also cause the entry to be printed to the console. Defaults to True.
    """
    dt = datetime.now()
    timestamp = dt.strftime("%B %d, %Y - %I:%M %p")
    
    with open(logfile, 'a+') as thelog:
        thelog.write(f"{timestamp} : {action.upper()}  {comment}\n")
        
    if prt: 
        print(f"{timestamp} : {action.upper()}  {comment}")
    

def initialize_config(object):
    """
    initialize_config Take any object as an argument, and apply all variables from the configuration file (./config/config.yaml) to the object.

    This function is used throughout this project to apply the configuration variables to basically all of the .py files.

    Args:
        object (object): any object.
    """
    with open('config/config.yaml') as f:
        config = yaml.safe_load(f)
    
    # -- APP variables --
    object.apiurl = config['app']['apiurl']
    object.campus = config['app']['campus']
    object.icon = config['app']['icon']
    object.searchmode = config['app']['searchmode']
    object.theme = config['app']['theme']
    object.light_themes = config['app']['lightthemes'].split(",")
    object.dark_themes = config['app']['darkthemes'].split(",")

    # SET THE default ICON COLOR BASED ON THEME
    if object.theme in object.light_themes:
        object.default_icon_color = "#333333"
    elif object.theme in object.dark_themes:
        object.default_icon_color = "#e7e7e7"
    else:
        object.default_icon_color = "#444444"


    # APP NAME
    object.app_name = config['app']['name']
    # VERSION
    object.version = config['app']['version']

    # -- LOG variables --
    object.logfile = os.path.abspath(config['logs']['main'])
    # object.housekeeping = os.path.abspath(config['logs']['housekeeping'])

    # -- DATABASE variables --
    object.dbhost = config['database']['host']
    object.dbname = config['database']['name']
    object.dbpass = config['database']['password']
    object.dbport = config['database']['port']
    object.tablename = config['database']['tablename']
    object.dbuser = config['database']['username']
    
    object.jsondir = config['directories']['json']
    
    object.success = config['sounds']['success']
    object.fail = config['sounds']['fail']

    object.safety_net = config['preferences']['safetynet']
    object.mute = config['preferences']['mute']
    column_choices = config['preferences']['selectedcolumns']

    object.selected_columns = column_choices.split(",")

    index_choices = config['preferences']['selectedindices']
    object.chosen_indices = index_choices.split(",")
    object.columns = {
        "0": ["brand", "mfr"],
        "1": ["description", "item name"],
        "2": ["printers", "compatible printers"],
        "3": ["code"],
        "4": ["upc"],
        "5": ["stock"],
        "6": ["part_num"],
        "7": ["color"],
        "8": ["yield"],
        "9": ["type", "t"],
        "10": ["comments"],
        "11": ["linked_codes", "linked codes"],
        "12": ["needed"]
    }
    object.guide_file = config['docs']['guide'] 
    object.docs_file = config['docs']['pdoc']

def suppress_qt_warnings():
    """
    suppress_qt_warnings supresses Qt warning that print to console at app startup.
    """
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

def gather_model_data(object, manufacturer:str=""):
    """
    gather_table_data Gathers data for tables based on manufacturer. This is the function that is called when a button is clicked on the main page.

    Args:
        manufacturer (str): name of manufacturer, that will be linked to the 'brand' column in the inventory table in the database.
    """
    # set current_table
    current_table = manufacturer
    if current_table:

        # connect to db to get spreadsheet data for model:
        database, cursorObject = connect_to_db(db_host=object.dbhost,
                                            db_user=object.dbuser,
                                            db_name=object.dbname, db_pass=object.dbpass, dicttrue=False)
        # select these columns and the sum of the stock column in case there are multiple upcs that cover the same toner model code
        if manufacturer in ["dell", "hp", "lexmark"]:
            query = f"SELECT description,code,SUM(stock),part_num,type FROM inventory WHERE brand=\'{manufacturer}\' GROUP BY description,code,part_num,type"
        else:
            query = f"SELECT description,code,SUM(stock),part_num,type FROM inventory WHERE brand NOT IN ('dell','hp','lexmark') GROUP BY description,code,part_num,type"

        cursorObject.execute(query)
        # fetch all results:
        results = cursorObject.fetchall()
        results_2dlist = []

        # turn inner tuples into lists
        for tuple in results:
            # convert the Decimal to a str number
            description = tuple[0]
            modelcode = tuple[1]
            stock = str(tuple[2])
            part_num = tuple[3]
            itemtype = tuple[4]
            edit = ""

            # append it all to the list, in a list
            results_2dlist.append(
                [description, modelcode, stock, part_num, itemtype])
        # sort the 2d list
        results_2dlist = sorted(results_2dlist, key=lambda x: x[1])

        # create TableModel for data
        # model = SortingTableModel(
        #     headers=["name".upper(), "code".upper(), "stock".upper(), "part".upper(), "type".upper()], model_data=results_2dlist)

        database.close()
        # self.build_table_window(maker=manufacturer)
        return results_2dlist
    else:
        print("table wasn't being displayed")
        return None
    
def commit_to_db(input_object, item_dict:dict, line_edits:dict, systemtray:QSystemTrayIcon=None) -> bool:

    new_dict = {}
    # get all values from line edits:
    for key, value in line_edits.items():
        new_dict[key] = value.text()
    # connect to database
    db, cursor = connect_to_db(
        db_host=input_object.dbhost,
        db_user=input_object.dbuser,
        db_name=input_object.dbname,
        db_pass=input_object.dbpass,
        dicttrue=True,
    )
    # try:
    form_query = "UPDATE inventory SET "
    for key, value in new_dict.items():
        # if the column only accepts INT datatype, then change it to an INT
        if (key in ["stock", "needed"]) and (value != 'None'):
            try:
                form_query += f"{key} = {int(value)}, "
            except ValueError:
                form_query += f"{key} = '', "
        else:
            form_query += f"{key} = '{value}', "
    if form_query.endswith(", "):
        form_query = form_query[:-2]
    form_query += f" WHERE code = '{item_dict['code']}' AND upc = '{item_dict['upc']}'"
    print(form_query)
    # update_query = f"UPDATE inventory SET brand='{new_dict['brand']}, 'description = '{new_dict['description']}', printers = '{new_dict['printers']}', code = '{new_dict['code']}', upc = '{new_dict['upc']}', stock = '{new_dict['stock']}', part_num = '{new_dict['part_num']}', color = '{new_dict['color']}', brand = '{new_dict['brand']}', yield = '{new_dict['yield']}', type = '{new_dict['type']}' WHERE code = '{item_dict['code']}' AND upc = '{item_dict['upc']}'"
    cursor.execute(form_query)
    db.commit()

    systemtray.showMessage(
        "Updated Item",
        f"Successfully updated item {item_dict['code']} / {item_dict['upc']}",
        QSystemTrayIcon.Information,
        3000,
    )
    write_log(input_object.logfile, "UPDATE", comment= f"Successfully updated item {item_dict['code']} / {item_dict['upc']}")
    return True
