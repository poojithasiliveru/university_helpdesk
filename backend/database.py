import mysql.connector
from config import DB_CONFIG


def get_connection():

    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            print("MySQL Connected Successfully")

        return connection

    except mysql.connector.Error as error:

        print("Database Connection Error:", error)

        return None