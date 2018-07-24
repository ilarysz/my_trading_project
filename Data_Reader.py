from Connection import Database, CursorCreator
import pandas as pd
from Utils import connection_data

Database.create_pool(**connection_data)


class DataHandler:

    def __init__(self):
        self.data_frame = None
        self.database = ['core', 'api_point', 'api_history']

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
            # self.data_frame['changed'] = 1
            # self.data_frame.loc[1, 'o'] = 120.0
            return self.data_frame

    def write_to_db(self, choice):
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
        for pos, item in enumerate(temp):
            if not (isinstance(item, str) or isinstance(item, float) or isinstance(item, int)):
                temp[pos] = float(temp[pos])
        return temp


record = DataHandler()
record.create_df(1)
record.write_to_db(1)
