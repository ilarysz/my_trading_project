# Third-party libraries
import pandas as pd
from psycopg2 import pool
# Custom packages
from shared_variables_secret import connection_data


class Database:
    """Class manages connection pool with database"""
    connection_pool = None

    # Establishes connection with database
    @classmethod
    def create_pool(cls, minimum_l, maximum_l, database_l, user_l, password_l, host_l):
        cls.connection_pool = pool.SimpleConnectionPool(minimum_l, maximum_l, database=database_l, user=user_l,
                                                        password=password_l, host=host_l)

    # Get connection from connection pool and return it
    @classmethod
    def get_conn(cls):
        return cls.connection_pool.getconn()

    # Return the connection to pool
    @classmethod
    def put_conn(cls, connection):
        cls.connection_pool.putconn(connection)


class CursorCreator:
    """Class manages getting separate connections and cursors"""

    def __init__(self):
        self.cursor = None
        self.connection = None
        self.cursor = None

    def __enter__(self):
        # To evade problems with not committing/closing connection cursor is prepared to be used with "with"
        # Retrieve one connection from the pool, prepare cursor and return it
        self.connection = Database.get_conn()
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        # After execution cursor is always about to be closed, connection committed and returned to available pool
        self.cursor.close()
        self.connection.commit()
        Database.put_conn(self.connection)


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

    @staticmethod
    def execute_db_request(custom_command, get_data=True):
        with CursorCreator() as cursor_1:
            cursor_1.execute(custom_command)
            if get_data:
                return cursor_1.fetchall()

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


# On import of file, always create pool to local db basing on the data contained in "shared_variables_secret.py"
Database.create_pool(**connection_data)
