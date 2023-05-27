from utils.toner_utils import write_log, connect_to_db, initialize_config


# this script is meant to be used on a database, after someone has just scanned a bunch of items, and alot of them had to be looked up through the api.
# As of 5/4/23, if this happens the description column (the 'names' of the items) will look very messy and not uniform. There are other columns, like 'printers' that will also be empty.
# Columns like 'color', 'type', 'brand', and several others will ideally be filled. The lookup script attempts to parse them from the api's json responses, but it is not perfect.

# this is a command line program.
class DBHousekeeping:
    def __init__(self):
        """
        __init__ goes through all item entries in the table, and tries to fill it any empty or definitely incorrect columns.

        Example of 'Definitely incorrect' columns would be - if an entry's 'brand' column value gets assigned to 'premium' because the toner is made by premium compatibles. The brand should be the manufacturer of the actual printer.
        """
        initialize_config(self)
        # create database connection
        self.db, self.cursor = connect_to_db(
            db_host=self.dbhost,
            db_user=self.dbuser,
            db_name=self.dbname,
            db_pass=self.dbpass,
            dicttrue=True,
        )
        # TODO: see if you can combine these three into one function since they all have the same structure
        # strip leading/trailing spaces from description column
        self.strip_spaces()
        # TODO: add list of approved item types to the guide
        # change all types to approved values (toner, ink, drum, fuser, roller, waste)
        self.fill_types()
        self.fill_brands()
        self.fill_colors()

    def strip_spaces(self):
        """
        strip_spaces trim any leading or trailing spaces in the column values of the 'description' column.
        """

        # sometimes, there are blank spaces at beginning of column descriptions
        update_query = f"UPDATE inventory SET description = TRIM(description)"
        self.cursor.execute(update_query)
        self.db.commit()
        write_log(logfile=self.logfile, action="STRIP SPACES",
                  message="Stripped spaces from description column")

    def fill_types(self):
        """
        fill_types query the database for all items that have a null or empty type column, and then tries to parse the type from the description column.

        _extended_summary_
        """
        # list of item types
        # TODO: there may be a better order, this is my first guess
        item_types = {
            "maintkit": ['maintenance', 'maintenancekit', 'maint kit', 'maintkit'],
            "drum": ['drum', 'imagingunit', 'imaging'],
            "fuser": ['fuser', 'fusing'],
            "ink": ['ink'],
            "toner": ['toner'],
            "paper": ['paper'],
            "roller": ['roller', 'feedroller', 'feed roller', 'transfer', 'pickup', 'pick up']
        }
        # first get all items that dont have type column filled in
        self.cursor.execute(
            "SELECT * FROM inventory WHERE (type IS NULL) OR (type = '')")
        items = self.cursor.fetchall()
        # for each item dictoinary, get the description column, and parse the type from it
        for item in items:
            item_description = item["description"]
            # for each item type, check if it is in the description
            for item_type in item_types.keys():
                # for each keyword in the item type, check if it is in the description
                for keyword in item_types[item_type]:
                    if keyword in item_description.lower():
                        # if it is, update the item's type column
                        self.cursor.execute(
                            f"UPDATE inventory SET type = {item_type} WHERE upc = {item['upc']}")
                        # log the change
                        write_log(logfile=self.logfile, action="TYPE ASSIGNMENT",
                                  message=f"Updated item type for item w/upc: {item['upc']} to {item_type}")
                        break

    def fill_brands(self):
        """
        fill_brands queries the database for all items that have a null or empty brand column, and then tries to parse the brand from the description column.

        _extended_summary_
        """
        # do the same thing as fill types except with the company names 'dell', 'lexmark', ['hp', 'hewlett packard']
        manufacturers = {
            "dell": ['dell'],
            "lexmark": ['lexmark'],
            "hp": ['hp', 'hewlett packard'],
            "canon": ['canon'],
            "xerox": ['xerox'],
            "sharp": ['sharp'],
            "brother": ['brother'],
            "epson": ['epson']
        }
        # first get all items that dont have brand column filled in
        self.cursor.execute(
            "SELECT * FROM inventory WHERE (brand IS NULL) OR (brand = '') OR (brand NOT IN ('dell', 'lexmark', 'hp', 'canon', 'xerox', 'sharp', 'brother', 'epson', 'dell/lexmark'))")
        items = self.cursor.fetchall()
        # for each item dictoinary, get the description column, and parse the type from it
        for item in items:
            item_description = item["description"]
            # for each item type, check if it is in the description
            for item_type in manufacturers.keys():
                # for each keyword in the item type, check if it is in the description
                for manufacturer in manufacturers[item_type]:
                    if manufacturer in item_description.lower():
                        # if it is, update the item's type column
                        self.cursor.execute(
                            f"UPDATE inventory SET brand = {manufacturer} WHERE upc = {item['upc']}")
                        # log the change
                        write_log(logfile=self.logfile, action="TYPE ASSIGNMENT",
                                  message=f"Updated item manufacturer (brand) for item w/upc: {item['upc']} to {manufacturer}")
                        break
    def make_lowercase(self):
        """
        make_lowercase some columns are kept completely lowercase for uniformity, like the 'brand' (manufacturer) column, type column.

        _extended_summary_
        """
        # update the inventory table where the brand column is not null, set it to LOWER()
        self.cursor.execute(
            "UPDATE inventory SET brand = LOWER(brand)")
        self.db.commit()
        write_log(logfile=self.logfile, action="MAKE LOWERCASE", comment="Made brand column lowercase")
        # type column, lowercase
        self.cursor.execute(
            "UPDATE inventory SET type = LOWER(type)")
        self.db.commit()
        write_log(logfile=self.logfile, action="MAKE LOWERCASE", comment="Made type column lowercase")
        
    def fill_colors(self):
        """
        fill_colors queries the database for all items that have a null or empty color column, and then tries to parse the color from the description column.

        _extended_summary_
        """
        # do the same thing as fill types except with the company names 'dell', 'lexmark', ['hp', 'hewlett packard']
        colors = {
            "black": ['black'],
            "cyan": ['cyan'],
            "magenta": ['magenta'],
            "yellow": ['yellow'],
            "photo black": ['photo black'],
            "matte black": ['matte black'],
            "grey": ['grey', 'gray']
        }
        # first get all items that dont have brand column filled in
        self.cursor.execute(
            "SELECT * FROM inventory WHERE (color IS NULL) OR (color = '') OR (color NOT IN ('black', 'cyan', 'magenta', 'yellow'))")
        items = self.cursor.fetchall()
        # for each item dictoinary, get the description column, and parse the type from it
        for item in items:
            item_description = item["description"]
            # for each item type, check if it is in the description
            for item_type in colors.keys():
                # for each keyword in the item type, check if it is in the description
                for color in colors[item_type]:
                    if color in item_description.lower():
                        # if it is, update the item's type column
                        self.cursor.execute(
                            f"UPDATE inventory SET color = {color} WHERE upc = {item['upc']}")
                        # log the change
                        write_log(logfile=self.logfile, action="TYPE ASSIGNMENT",
                                  message=f"Updated item color for item w/upc: {item['upc']} to {color}")
                        break

    def fill_printers(self):
        """
        fill_printers EXPERIMENTAL FEATURE: since this is experimental, it's not fully automated. It still needs some user interaction before making changes to database. This function queries the database for all items that have a null or empty printer column, and then tries to parse the printer models from the description column.

        The idea is that the function will use items that have their compatible printers filled in, and compare their descriptions to the descriptions of items that don't have their compatible printers filled in. If the descriptions are the same or similar, then the function will copy over the compatible printers value. The function will only fill in compatible printers values for items that had them set to blank or null.
        """
        # IDEAS FOR FINDING WHICH PRINTER MODELS AN ITEM IS COMPATIBLE WITH:
        # 1. comparison between items - if an item is toner and has c3760 in the name, chances are it's compatible with the same printers that other c3760 toners are compatible with
        # 2. http request out to the manufacturer website...for ex: dells website - all the toner models pages are in the same format - look at the id or class of the element
        # that holds the comma-separated string of printer models that are compatible with that item.
        # - grab the text and normalize it.
        # 3. dell, lexmark, hp, etc. APIs?
        select_all_items = "SELECT description,printers,code,upc,part_num FROM inventory"
        self.cursor.execute(select_all_items)
        items = self.cursor.fetchall()
        items_copy = items
        items_without_printers = []
        # for each item, check if it has a printer model
        for item in items:
            if item['printers'] is None or item['printers'] == '':
                items_without_printers.append(item)
                items_copy.remove(item)

        # for each item without a printer model, check if it has a description
        for item in items_without_printers:
            split_description = item['description'].split()
            for item_with_printer in items_copy:
                # check if the items have same brand, type, and color, if they don't then skip to next item
                if item['brand'] != item_with_printer['brand'] or item['type'] != item_with_printer['type'] or item['color'] != item_with_printer['color']:
                    continue
                # split the description of the item with printer
                split_description_with_printer = item_with_printer['description'].split()
                # if at least 2 words in the without printers description are in description with printers, ask to copy over printers value
                if len(set(split_description).intersection(split_description_with_printer)) >= 2:
                    # ask to copy over the printer model
                    print(
                        f"Found a match between item w/upc: {item['upc']} and item w/upc: {item_with_printer['upc']}")
                    print(
                        f"Item w/upc: {item['upc']} has description: {item['description']}\n\tprinters: {item_with_printer['printers']}")
                    print(
                        f"Item w/upc: {item_with_printer['upc']} has description: {item_with_printer['description']}\n\tprinters: {item['printers']}")
 
                    answer = input("Would you like to copy over the printer model? (y/n or hit ENTER to skip)")
                    # keep user in loop until they hit enter, y, or n
                    while answer not in ['y', 'n', '']:
                        answer = input(
                            "Invalid input. Would you like to copy over the printer model? (y/n or hit ENTER to skip)")
                    if answer.lower() == 'y':
                        # copy over the printer model only if user says yes
                        self.cursor.execute(
                            f"UPDATE inventory SET printers = {item_with_printer['printers']} WHERE upc = {item['upc']}")
                        # log the change
                        write_log(logfile=self.logfile, action="PRINTER ASSIGNMENT",
                                  message=f"Updated item printer for item w/upc: {item['upc']} to {item_with_printer['printers']}")
                        break


if __name__ == "__main__":
    DBHousekeeping()
