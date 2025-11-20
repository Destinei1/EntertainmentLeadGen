import os
from dotenv import load_dotenv
import snowflake.connector

# Load environment variables from .env
load_dotenv()

def get_db_connection():
    """
    Creates and returns a Snowflake database connection using credentials
    stored in the .env file.
    """
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )
    return conn


def test_connection():
    """
    Tests the Snowflake connection by running a simple query.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();"
        )
        row = cur.fetchone()
        print("SNOWFLAKE CONNECTION SUCCESSFUL:")
        print("  USER:", row[0])
        print("  ROLE:", row[1])
        print("  WAREHOUSE:", row[2])
        print("  DATABASE:", row[3])
        print("  SCHEMA:", row[4])
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    test_connection()
