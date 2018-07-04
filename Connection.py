from psycopg2 import pool


class Database:
    connection_pool = None
    tests = None

    @classmethod
    def create_pool(cls, minimum_l, maximum_l, database_l, user_l, password_l, host_l):
        cls.connection_pool = pool.SimpleConnectionPool(minimum_l, maximum_l, database=database_l, user=user_l,
                                                         password=password_l, host=host_l)

    @classmethod
    def get_conn(cls):
        return cls.connection_pool.getconn()

    @classmethod
    def put_conn(cls, connection):
        cls.connection_pool.putconn(connection)


class CursorCreator:
    def __init__(self):
        self.cursor = None
        self.connection = None
        self.cursor = None

    def __enter__(self):
        self.connection = Database.get_conn()
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.connection.commit()
        Database.put_conn(self.connection)
