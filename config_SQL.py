import mysql.connector
from mysql.connector import errorcode

config = {
    'host': '127.0.0.1',
    'user' : 'root',
    'password' : 'MyNewPass',
    'database' : 'NHKdb'
}

DB_NAME = 'NHKdb'
METADATA_TABLE = 'metadata'
DATA_TABLE = 'nhk_data'



def create_database(cursor):
    try:
        cursor.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8mb4'")
        print(f"Database {DB_NAME} created successfully.")
    except mysql.connector.Error as err:
        print(f"Failed to create database: {err}")

def initialize_mysql():
    try:
        # Connect without specifying a database (so we can create one)
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        # Create database if it doesn't exist
        try:
            cursor.execute(f"USE {DB_NAME}")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                create_database(cursor)
                cnx.database = DB_NAME
            else:
                raise

        # Create metadata table
        for table_name, ddl in TABLES.items():
            try:
                cursor.execute(ddl)
                print(f"Table '{table_name}' is ready.")
            except mysql.connector.Error as err:
                print(f"Failed creating table {table_name}: {err}")

        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")

if __name__ == "__main__":
    initialize_mysql()