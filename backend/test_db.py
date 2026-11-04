
from database import get_connection

connection = get_connection()

if connection:
    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE()")
    print("Connected Database:", cursor.fetchone()[0])

    cursor.close()
    connection.close()
    print("Connection Closed Successfully")
else:
    print("Database Connection Failed")
