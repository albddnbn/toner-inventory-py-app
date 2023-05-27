import requests
import json
from utils.toner_utils import connect_to_db, write_log, initialize_config
import os
import PyQt5.QtWidgets as qtw

class ItemLookup:
    def __init__(self, input_code:str, systemtray:qtw.QSystemTrayIcon=None):
        """
        __init__ looks up codes that are scanned into the app using a barcode scanner (or by importing a csv).

        Args:
            input_code (str): the code being scanned in, and looked up
            systemtray (qtw.QSystemTrayIcon, optional): the app's system tray icon. Defaults to None.
        """
        initialize_config(self)
        self.input = input_code
        self.systemtray = systemtray

    def look_up_code(self) -> bool:
        """
        look_up_code attempts to link the scanned in code to an item present in database or from API.

        Logs statements to file and sometimes to console depending on your 'prt' value. True means the app WILL print to console.

        Returns:
            bool: True or False as to whether the code was successfully added to the database
        """
        self.input = self.input.lower()
        # run search of input code
        write_log(self.logfile, "LOOKING UP",
                  f"Looking up entry: {self.input}", prt=True)
        result = self.look_up_item(self.input.strip())
        if result:
            write_log(self.logfile, "SCAN SUCCESS",
                      f"Stock was increased by 1 for {self.input}.", prt=True)
            return True
        elif not result:
            write_log(self.logfile, "SCAN ERROR",
                      f"Entry {self.input} needs to be added to database manually.", prt=True)
            return False

    def look_up_item(self, code:str) -> bool:
        """
        look_up_item first check local directory, then check local database, then look up using apiurl configured in config.yaml.

        Args:
            code (str): The code / string of text scanned in by user.
        """
        db_results = self.check_local_db(code)
        if db_results[0] == True:
            if db_results[1] == "linked_codes":
                update_query = f"UPDATE inventory SET stock = stock + 1 WHERE FIND_IN_SET(\'{code}\', LOWER(linked_codes))"
            else:
                update_query = f"UPDATE inventory SET stock = stock + 1 WHERE {db_results[1]} = \'{code}\'"
            write_log(self.logfile, "ITEM LINKED",
                      f"Scanned item linked: {code}, found using {db_results[1]} col.", prt=True)

            db, cursor = connect_to_db(
                db_host=self.dbhost,
                db_user=self.dbuser,
                db_name=self.dbname,
                db_pass=self.dbpass,
                dicttrue=True,
            )

            cursor.execute(update_query)
            db.commit()

            write_log(self.logfile, "DB UPDATE",
                      f"Scanned item updated: {code}, stock + 1", prt=True)
            return True

        elif self.api_lookup(code):
            return True
        else:
            write_log(self.logfile, "ITEM NOT FOUND",
                      f"Scanned item not found: {code}", prt=True)

            return False

    def check_local_db(self, code: str) -> tuple:
        """
        check_local_db check local database for the upc code that was just scanned.

        Args:
            code (str): upc code that was just scanned.

        Returns:
            tuple: first element is bool corresponding to positive or negative result of search, and the second element is the column from inventory table that matched the scanned upc code.
        """
        db, cursor = connect_to_db(
            db_host=self.dbhost,
            db_user=self.dbuser,
            db_name=self.dbname,
            db_pass=self.dbpass,
            dicttrue=False,
        )

        # search in FOUR columns starting with most likely - upc, part_num, code, and finally linked_codes (see explanation of linked_codes in readme)
        upc_query = f"SELECT * FROM inventory WHERE (upc=\'{code}\') AND (upc IS NOT NULL) AND (upc != \'\')"
        partnum_query = f"SELECT * FROM inventory WHERE (part_num = \'{code}\') AND (part_num IS NOT NULL) AND (part_num != \'\')"
        code_query = f"SELECT * FROM inventory WHERE (code = \'{code}\') AND (code IS NOT NULL) AND (code != \'\')"
        linked_codes_query = f"SELECT * FROM inventory WHERE  FIND_IN_SET('{code.lower()}', LOWER(linked_codes))"

        cursor.execute(upc_query)
        upc_result = cursor.fetchall()

        db.commit()
        # check UPC column for scanned code
        if upc_result:
            return True, "upc"
        else:
            cursor.execute(code_query)
            code_result = cursor.fetchall()
            # check 'code' column
            if code_result:
                return True, "code"
            else:
                cursor.execute(partnum_query)

                partnum_result = cursor.fetchall()
                # check 'part_num' column
                if partnum_result:

                    return True, "part_num"
                else:

                    cursor.execute(linked_codes_query)
                    linked_codes_result = cursor.fetchall()
                    # check 'linked_codes' column
                    if linked_codes_result:
                        return True, "linked_codes"
                    # otherwise, return False, which means the lookup will proceed to the api
                    else:

                        return False, ""

    def api_lookup(self, code: str) -> bool:
        """
        api_lookup looks up the upc code using the apiurl configured in config.yaml and then inserts into database with stock of 1. Saves resulting json file to local storage.

        upcitemdb.com api is currently being used: https://upcitemdb.com/api

        Args:
            code (str): upc code that was just scanned.

        Returns:
            bool: boolean based on whether the api lookup was successful or not.
        """
        db, cursor = connect_to_db(
            db_host=self.dbhost,
            db_user=self.dbuser,
            db_name=self.dbname,
            db_pass=self.dbpass,
            dicttrue=True,
        )

        response = requests.get(f"{self.apiurl}{code}")
        data = response.json()
        if data["code"] == "OK":
            # if there is content in the json:
            if data["total"] > 0:
                # create filepath for the json file (api sends json of data about the scanned item if the item is found)
                jsonfilepath = os.path.join(self.jsondir, f"{code}.json")

                # then save to json file and return the data
                with open(jsonfilepath, 'w') as jsonfile:
                    json.dump(data, jsonfile)
                # parse the product info:
                theupc, item_brand, item_name, item_desc, item_code, item_color, item_type = self.parse_info(
                    data, code)
                # now use the variables to insert the new item into the database table with stock of 1
                try:
                    insert_statement = f"INSERT INTO inventory (description,printers,code,upc,stock,part_num,color,brand,yield,type) VALUES (\'{item_name}\','',\'{item_code}\',\'{theupc}\', \'{1}\', '', \'{item_color}\',\'{item_brand}\', '', \'{item_type}\')"
                    cursor.execute(insert_statement)
                    db.commit()
                    return True
                # I don't think this try catch is necessary, but keep for now
                except:
                    return False

    def parse_info(self, data:dict, upc:str) -> tuple:
        """
        parse_info Parse information from a json response file from upc lookup API.

        Args:
            data (dictionary): json data from upc lookup API
            upc (str): upc code of the item

        Returns:
            tuple: important information about item including name, item type, color, etc.
        """
        # get info dictionary from the items key (to see example of what resulting json looks like, check json directory)
        info = data['items'][0]
        item_name = info['title']
        name_split = item_name.split(" ")
        name_split = [x.lower() for x in name_split]

        # item name/description
        item_desc = info['description']
        split_desc = item_desc.split(" ")
        split_desc = [word.lower() for word in split_desc]

        # manufacturer
        try:
            item_brand = info['brand'].lower()
        except:
            item_brand = ""
        # if item brand isn't already one of the major ones, then do some further checks on the name and description
        if item_brand not in ["dell", "hp", "lexmark", "sharp", "canon", "epson"]:
            if item_brand == "hewlett packard":
                item_brand = "hp"
            else:
                # check if dell/hp/lexmark is in the name or description
                for manufacturer in ["dell", "hp", "lexmark", "epson", "canon", "hewlett"]:
                    if manufacturer in name_split:
                        item_brand = manufacturer
                    else:
                        if manufacturer in split_desc:
                            item_brand = manufacturer

        item_code = info['model']

        item_color = self.parse_color(info, upc)
        item_type = self.parse_type(info, upc)

        # chop description down a bit if its too long - already storing the whole thing in the json file
        if len(item_desc) >= 250:
            # chop off first 250 characters of the item description, split it up by spaces (into words), then chop off the last word in case it's cut off
            item_desc = item_desc[:249].split(" ")[:-1]
            # join the item description list back together into a string
            item_desc = " ".join(item_desc)

        # do basically the same with item names
        split_name = item_name.split(" ")
        characters = 0
        item_name = ""
        for word in split_name:
            if (characters <= 250) and (characters + len(word) <= 250):
                characters += len(word)
                item_name += f" {word}"

        # return variables:
        return upc, item_brand, item_name, item_desc, item_code, item_color, item_type

    def parse_color(self, info_data:dict, upc:str) -> str:
        """
        parse_color Attempts to parse the color of the item from title and description if not explicitly listed in the color property of the json from api lookup.

        Args:
            info_data (dict): chunk of data from the json file from the api lookup
            upc (str): upc code of the item

        Returns:
            str: corresponding to item color, ex: "cyan", "magenta", "yellow", "black", "photo black", "matte black"..
        """
        split_title = info_data['title'].split(" ")
        split_title = [word.lower()
                       for word in split_title]  # make all words lowercase
        split_desc = info_data['description'].split(" ")
        split_desc = [word.lower()
                      for word in split_desc]  # make all words lowercase

        if info_data['color'].lower() in ['magenta', 'yellow', 'cyan', 'black', 'photo black', 'matte black']:
            item_color = info_data['color']
        else:
            if 'magenta' in split_title:
                item_color = 'magenta'
            elif 'yellow' in split_title:
                item_color = 'yellow'
            elif 'cyan' in split_title:
                item_color = 'cyan'
            elif 'black' in split_title:
                if 'photo black' in split_title:
                    item_color = 'photo black'
                elif 'matte black' in split_title:
                    item_color = 'matte black'
                else:
                    item_color = 'black'
            # if script didnt find a color listed in the item name, check the description
            else:
                if 'magenta' in split_desc:
                    item_color = 'magenta'
                elif 'yellow' in split_desc:
                    item_color = 'yellow'
                elif 'cyan' in split_desc:
                    item_color = 'cyan'
                elif 'black' in split_desc:
                    if 'photo black' in split_desc:
                        item_color = 'photo black'
                    elif 'matte black' in split_desc:
                        item_color = 'matte black'
                    else:
                        item_color = 'black'
                else:
                    # turn this into print function
                    item_color = "null"
        return item_color

    def parse_type(self, info_data:dict, upc:str) -> str:
        """
        parse_type Attempts to parse the type of the item from title and description if not explicitly listed in the type property of the json from api lookup.

        Args:
            info_data (dict): chunk of data from the json file from the api lookup
            upc (str): upc code of the item

        Returns:
           item_type (str): type of item, ex: "toner", "ink", "drum", "paper", "fuser", "waste"..
        """
        split_title = info_data['title'].split(" ")
        split_desc = info_data['description'].split(" ")
        # create item_type variable, set to blank for now while item type is discerned
        item_type = ""
        # GET THE ITEM TYPE:
        for itype in ["toner", "ink", "drum", "imaging", "fuser", "waste"]:
            if itype in split_title:
                # if its on "imaging" iteration of the for loop and it pops, check for the word "unit" too before assigning it to imaging unit type
                if itype == "imaging":
                    # if "unit" in split_title: --> this would check for the word 'unit' as well as 'imaging'
                    item_type = "drum"
                else:
                    item_type = itype
            # if it cant find the item type in the name, check description (this may not work perfectly)
            else:
                if itype in split_desc:
                    if itype == "imaging":
                        item_type = "drum"
                    else:
                        item_type = itype
        return item_type
