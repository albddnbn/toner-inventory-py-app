import os
import csv
from datetime import datetime
from utils.toner_utils import initialize_config, connect_to_db, write_log


class DataBackup:
    def __init__(self):
        """
        __init__ backs up the database to a csv file. As of 4/29/23, can be called from the toolbar by clicking the backup button.

        In the future, it would be a good idea to add this as a scheduled task in addition to having it as a button on the toolbar.
        """
        initialize_config(self)
        thetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.csvname = f"{self.tablename}_{thetime}.csv"
        write_log(logfile=self.logfile, action="BACKUP",
                  comment=f"Backup started: output/{self.csvname}", prt=True)

        db, cursor = connect_to_db(
            db_host=self.dbhost,
            db_user=self.dbuser,
            db_name=self.dbname,
            db_pass=self.dbpass,
            dicttrue=False,
        )

        # select everything
        cursor.execute(f"SELECT * FROM `{self.tablename}`")
        self.data = cursor.fetchall()
        # get ddate time in formatted string
        thetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.csvname = f"{self.tablename}_{thetime}.csv"
        # write it all to a csv
        with open(os.path.join("output", self.csvname), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([i[0] for i in cursor.description])
            writer.writerows(self.data)
        cursor.close()
        db.close()


if __name__ == "__main__":
    DataBackup()
