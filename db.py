import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",   
        port=3306,
        user="devop",
        password="root123@",
        database="lever_db",
        auth_plugin="mysql_native_password"
    )



