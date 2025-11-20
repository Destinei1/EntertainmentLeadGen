import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load variables from .env at project root
load_dotenv()

def get_db_connection():
    """
    Establish a connection to the Postgres database using credentials from .env.
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    return conn

def test_connection():
    """
    Run a simple SELECT 1 query to verify the database connection works.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT 1;")
            result = cur.fetchone()
            print("DB connection OK:", result)
    finally:
        conn.close()

if __name__ == "__main__":
    test_connection()
