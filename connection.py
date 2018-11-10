from psycopg2 import pool


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

print("test")