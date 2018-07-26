from Connection import Database, CursorCreator
import pandas as pd
from Utils import connection_data

import Trading_Engine

Database.create_pool(**connection_data)


class DataHandler:

    def __init__(self):
        self.data_frame = None
        self.database = ['core', 'api_point', 'api_history']
        self.engine_object = None
        self.enginge_dict = None

    def __repr__(self):
        if self.data_frame.any:
            return 'Object handles table with following columns {}'.format(self.data_frame.columns)
        else:
            return 'Object without loaded table'

    def create_df(self, choice):
        """Creates data frame from loaded records"""
        with CursorCreator() as cursor_1:
            cursor_1.execute('SELECT * FROM %s' % self.database[choice])
            self.data_frame = pd.DataFrame(cursor_1.fetchall())
            cursor_1.execute("select column_name from information_schema.columns where table_name='%s'" %
                             self.database[choice])
            result = cursor_1.fetchall()
            self.data_frame.columns = [(lambda x: x[0])(x) for x in result]
            # Lines for testing purposes:
            self.data_frame['changed'] = 1
            # self.data_frame.loc[1, 'o'] = 120.0
            return self.data_frame

    def write_to_db(self, choice):
        """Basing on the input from the interface loads data from the given table"""
        # Old code not prepared to handle every data frame, shall be deleted if everything is working
        # in the newer lines
        # extracted = self.data_frame.iloc[-1]['id']
        # temp = []
        # with CursorCreator() as cursor_2:
        #     for row in range(0, extracted[0], 1):
        #         for item in range(0, 7, 1):
        #             temp.append(self.data_frame.iloc[row][item])
        #         cursor_2.execute("INSERT INTO writing VALUES (%s, %s, %s, %s, %s, %s, %s)",
        #                          (int(temp[0]), str(temp[1]), str(temp[2]), float(temp[3]), float(temp[4]),
        #                           float(temp[5]), float(temp[6])))
        #         temp = []

        # First function checks number of rows and then for each "changed" column
        # If it equals "1" whole row is replaced with that carried by data frame
        # Changed column is omitted when data frame is written into database
        with CursorCreator() as cursor_2:
            for x in range(self.data_frame.iloc[-1]['id']):
                if self.data_frame.iloc[x]['changed'] == 1:
                    temp = [x for x in self.data_frame.iloc[x][:-1]]
                    temp = self.convert(temp)
                    cursor_2.execute("DELETE FROM %s WHERE id=%s" % (self.database[choice], x+1))
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

    def read_from_api(self, request_type, pair_choice, streaming_type='pricing'):
        """Function used to gather data from the Oanda API"""
        # Functions calls objects from Trading Engine basing on the input from interface
        # Objects shall live only inside DataHandler, returned for printing purposes
        if request_type == 'history':
            self.engine_object = Trading_Engine.RequestInstrument()
            self.data_frame = self.engine_object.perform_request(pair_choice)
            return self.data_frame
        elif request_type == 'pricing':
            self.engine_object = Trading_Engine.RequestPricing()
            self.enginge_dict = self.engine_object.perform_request(streaming_type, pair_choice)
            return self.enginge_dict
        else:
            print("Wrong command {}".format(request_type))


# record = DataHandler()
# record.create_df(1)
# record.write_to_db(1)

# r_api = DataHandler()
# r_api.read_from_api('pricing', 1, 'pricing')

# r_api = DataHandler()
# print(r_api.read_from_api('history', 2))
