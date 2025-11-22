from src.db.connection import get_db_connection


def run_raw_to_contacts():
    """
    Transform data from RAW_CONTACTS into CONTACTS.

    - Normalizes email to lowercase
    - Derives NATIONAL_OR_INTERNATIONAL from LOCATION_COUNTRY
    - Upserts into CONTACTS keyed by EMAIL
    """
    merge_sql = """
        MERGE INTO CONTACTS AS c
        USING (
            SELECT
                LOWER(TRIM(EMAIL)) AS EMAIL,
                FULL_NAME AS FULL_NAME,
                PHONE AS PHONE,
                LOCATION_CITY AS LOCATION_CITY,
                LOCATION_COUNTRY AS LOCATION_COUNTRY,
                CASE
                    WHEN UPPER(LOCATION_COUNTRY) IN ('US', 'USA', 'UNITED STATES', 'UNITED STATES OF AMERICA') THEN 'US'
                    ELSE 'International'
                END AS NATIONAL_OR_INTERNATIONAL,
                CURRENT_TIMESTAMP() AS UPDATED_AT
            FROM RAW_CONTACTS
            WHERE EMAIL IS NOT NULL
        ) AS r
        ON c.EMAIL = r.EMAIL
        WHEN MATCHED THEN UPDATE SET
            c.FULL_NAME = COALESCE(r.FULL_NAME, c.FULL_NAME),
            c.PHONE = COALESCE(r.PHONE, c.PHONE),
            c.LOCATION_CITY = COALESCE(r.LOCATION_CITY, c.LOCATION_CITY),
            c.LOCATION_COUNTRY = COALESCE(r.LOCATION_COUNTRY, c.LOCATION_COUNTRY),
            c.NATIONAL_OR_INTERNATIONAL = COALESCE(r.NATIONAL_OR_INTERNATIONAL, c.NATIONAL_OR_INTERNATIONAL),
            c.UPDATED_AT = r.UPDATED_AT
        WHEN NOT MATCHED THEN INSERT (
            FULL_NAME,
            EMAIL,
            PHONE,
            LOCATION_CITY,
            LOCATION_COUNTRY,
            NATIONAL_OR_INTERNATIONAL,
            CREATED_AT,
            UPDATED_AT
        )
        VALUES (
            r.FULL_NAME,
            r.EMAIL,
            r.PHONE,
            r.LOCATION_CITY,
            r.LOCATION_COUNTRY,
            r.NATIONAL_OR_INTERNATIONAL,
            r.UPDATED_AT,
            r.UPDATED_AT
        );
    """

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(merge_sql)
        conn.commit()
        print("RAW_CONTACTS → CONTACTS transform completed.")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_raw_to_contacts()
