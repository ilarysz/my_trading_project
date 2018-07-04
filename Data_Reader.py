from Connection import Database, CursorCreator
from datetime import datetime
import pandas as pd
import numpy as np
from Utils import connection_data

Database.create_pool(**connection_data)


class DataHandler:

    def __init__(self):
        self.data_frame = None

    def __repr__(self):
        if self.data_frame.any:
            return 'Object handles table with following columns {}'.format(self.data_frame.columns)
        else:
            return 'Object without loaded table'

    def create_df(self):
        """Creates data frame from loaded records"""
        with CursorCreator() as cursor_1:
            cursor_1.execute('SELECT * FROM main_quotes')
            result = cursor_1.fetchall()
            self.data_frame = pd.DataFrame(result)
            cursor_1.execute("select column_name from information_schema.columns where table_name='main_quotes';")
            result = cursor_1.fetchall()
            result = [(lambda x: x[0])(x) for x in result]
            self.data_frame.columns = [result]
            return self.data_frame

    def write_to_db(self):
        extracted = self.data_frame.iloc[-1]['id']
        temp = []
        with CursorCreator() as cursor_2:
            cursor_2.execute("DELETE FROM writing WHERE id>0")
            for row in range(0, extracted[0], 1):
                for item in range(0, 7, 1):
                    temp.append(self.data_frame.iloc[row][item])
                cursor_2.execute("INSERT INTO writing VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                 (int(temp[0]), str(temp[1]), str(temp[2]), float(temp[3]), float(temp[4]), float(temp[5]), float(temp[6])))
                temp = []


#record = DataHandler()
#record.create_df()
#record.write_to_db()
