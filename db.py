import mysql.connector
from mysql.connector import Error
import logging

logger = logging.getLogger(__name__)

def get_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='lever_db',
            user='username',
            password='password' 
        )
        
        if connection.is_connected():
            return connection
            
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        raise e

def test_connection():
    try:
        conn = get_connection()
        if conn.is_connected():
            print("Database connection successful!")
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE()")
            db = cursor.fetchone()
            print(f"Connected to database: {db[0]}")
            cursor.close()
            conn.close()
            return True
    except Error as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()



