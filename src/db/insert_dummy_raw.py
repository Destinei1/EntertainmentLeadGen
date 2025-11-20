from .connection import get_db_connection

def insert_dummy_raw_contact():
    """
    Insert one dummy contact into RAW_CONTACTS to prove
    end-to-end Snowflake write works.
    """
    dummy = {
        "full_name": "Test Writer",
        "email": "test.writer@example.com",
        "phone": "+1-555-123-4567",
        "org_name": "Test Underground Mag",
        "org_type": "publication",   # could be 'radio', 'blog', 'label', etc.
        "role_title": "Music Writer",
        "location_city": "London",
        "location_country": "UK",
        "source": "manual_dummy_seed",
        "raw_url": "https://example.com/test-writer-profile"
    }

    sql = """
        INSERT INTO RAW_CONTACTS (
            FULL_NAME,
            EMAIL,
            PHONE,
            ORG_NAME,
            ORG_TYPE,
            ROLE_TITLE,
            LOCATION_CITY,
            LOCATION_COUNTRY,
            SOURCE,
            RAW_URL
        )
        VALUES (%(full_name)s,
                %(email)s,
                %(phone)s,
                %(org_name)s,
                %(org_type)s,
                %(role_title)s,
                %(location_city)s,
                %(location_country)s,
                %(source)s,
                %(raw_url)s);
    """

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, dummy)
        conn.commit()
        print("Inserted dummy raw contact into RAW_CONTACTS.")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    insert_dummy_raw_contact()
