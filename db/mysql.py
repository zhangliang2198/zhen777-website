import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="8.219.53.116",
        user="root",
        password="Meili163!!",
        database="openai",
    )
    return connection
