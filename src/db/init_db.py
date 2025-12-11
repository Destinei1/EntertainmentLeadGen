from pathlib import Path
from .connection import get_db_connection

def run_schema():
    """
    Executes sql/schema_v1.sql in Snowflake, creating the core tables.
    """
    # Locate schema file
    schema_path = Path(__file__).resolve().parents[2] / "sql" / "schema_v1.sql"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Split SQL into separate statements
    statements = [s.strip() for s in schema_sql.split(";") if s.strip()]

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            for stmt in statements:
                cur.execute(stmt)
            print("Schema created / updated successfully in Snowflake.")
        finally:
            cur.close()
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    run_schema()
# this doesnt need to be ran multiple times, we only need to create the data model once