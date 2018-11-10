from connection import Database, CursorCreator
import pandas as pd
from utils import connection_data
import trading_engine

# On import of file, always create pool to local db basing on the data contained in "utils.py"
Database.create_pool(**connection_data)


class DataHandler:

    def __init__(self):
        self.data_frame = None
        # Available connection points, core = connection to server db
        self.database = ['core', 'api_point', 'api_history']
        self.engine_object = None
        self.engine_dict = None

    def __repr__(self):
        # Return information about table currently loaded
        if self.data_frame.any:
            return 'Object handles table with following columns {}'.format(self.data_frame.columns)
        else:
            return 'Object without loaded table'

    def create_df(self, database_to_read=0, read_method='default', custom_command=None):
        """Creates data frame from loaded records"""
        # Default allows to create DF selecting all data from the given SQL table and loading columns names from schema
        if read_method == 'default':
            with CursorCreator() as cursor_1:
                # Select all columns from the database and write them to data_frame
                cursor_1.execute('SELECT * FROM %s' % self.database[database_to_read])
                self.data_frame = pd.DataFrame(cursor_1.fetchall())
                # Download information about column names from schema and rename columns in self.data_frame
                cursor_1.execute("SELECT column_name FROM information_schema.columns WHERE table_name='%s'" %
                                 self.database[database_to_read])
                result = cursor_1.fetchall()
                # Only first record from results contain relevant information
                self.data_frame.columns = [(lambda x: x[0])(x) for x in result]
                # Changed contains information if there were any changes during operating on given dataframe
                # It will be used during writing to db
                self.data_frame['changed'] = 0
                return self.data_frame

        # Pass own command
        elif read_method == 'custom' and custom_command:
            with CursorCreator() as cursor_1:
                cursor_1.execute(custom_command)
                # Retrieve data
                self.data_frame = pd.DataFrame(cursor_1.fetchall())
                # Changed contains information if there were any changes during operating on given dataframe
                # It will be used during writing to db
                # Try/except clause is used because in case of custom command "changed" may be irrelevant
                try:
                    self.data_frame['changed'] = 0
                    return self.data_frame
                except TypeError:
                    return self.data_frame

        else:
            raise RuntimeError("Wrong read method passed to create_df function or no custom command present")

    def write_to_db(self, choice=0):
        """Basing on the input from the interface loads data from the given table"""
        # Check number of rows and then for each "changed" column
        # If it equals "1" whole row is replaced with that carried by data frame
        # Changed column is omitted when data frame is written into database
        with CursorCreator() as cursor_2:
            for x in range(self.data_frame.iloc[-1]['id']):
                if self.data_frame.iloc[x]['changed'] == 1:
                    temp = [x for x in self.data_frame.iloc[x][:-1]]
                    temp = self.convert(temp)
                    cursor_2.execute("DELETE FROM %s WHERE id=%s" % (self.database[choice], x + 1))
                    cursor_2.execute("INSERT INTO %s VALUES %s" % (self.database[choice], tuple(temp)))
                else:
                    continue

    @staticmethod
    def convert(temp):
        """Prepares data frame carried by the DataHandler to be written into database"""
        # Data frame cells are not passed correctly if not converted before the passing
        # Problem regards float numbers
        for pos, item in enumerate(temp):
            if not (isinstance(item, str) or isinstance(item, float) or isinstance(item, int)):
                temp[pos] = float(temp[pos])
        return temp

    def read_from_api(self, request_type='history', pair_choice=0, candles_count=150, set_granularity='H1',
                      streaming_type='pricing'):
        """Function used to gather data from the Oanda API"""
        # Functions calls objects from Trading Engine basing on the input from interface
        # Objects shall live only inside DataHandler, returned for printing purposes
        if request_type == 'history':
            self.engine_object = trading_engine.RequestInstrument()
            self.data_frame = self.engine_object.perform_request(candles_count, set_granularity, pair_choice)
            return self.data_frame
        elif request_type == 'pricing':
            self.engine_object = trading_engine.RequestPricing()
            self.engine_dict = self.engine_object.perform_request(streaming_type, pair_choice)
            return self.engine_dict
        else:
            print("Wrong command {}".format(request_type))
