import mysql
import mysql.connector
from utils.toner_utils import initialize_config, connect_to_db


class checkPrinters:
    def __init__(self):
        """
        __init__ this script will print out a list of all the printer models listed in the 'printers' column of the database (unique values only).

        It doesn't take upper/lower case into account - they will show as different models.
        """
        self.config = initialize_config(self)

        db, cursor = connect_to_db(
            db_host=self.dbhost,
            db_user=self.dbuser,
            db_name=self.dbname,
            db_pass=self.dbpass,
            dicttrue=True,
        )
        cursor.execute("SELECT * FROM inventory")
        self.items = cursor.fetchall()
        cursor.close()
        db.close()

        printers_list = []
        for item in self.items:
            if item["printers"] == "" or item["printers"] == None:
                continue
            models_list = item["printers"].split(",")
            models_list = [f"{item['brand']} {prt_model}" for prt_model in models_list]
            for model in models_list:
                if model not in printers_list:
                    printers_list.append(model)
        
        for printer in printers_list:
            print(printer)



if __name__ == "__main__":
    checkPrinters()