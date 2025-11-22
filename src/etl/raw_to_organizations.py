from src.db.connection import get_db_connection


def run_raw_to_organizations():
    """
    Transform data from RAW_CONTACTS into ORGANIZATIONS.

    - Uses ORG_NAME + ORG_TYPE as a natural key
    - Pulls website from RAW_URL (best-effort)
    - Upserts into ORGANIZATIONS
    """
    merge_sql = """
        MERGE INTO ORGANIZATIONS AS o
        USING (
            SELECT
                TRIM(ORG_NAME) AS NAME,
                TRIM(ORG_TYPE) AS ORG_TYPE,
                ANY_VALUE(RAW_URL) AS WEBSITE,
                ANY_VALUE(LOCATION_COUNTRY) AS COUNTRY,
                ANY_VALUE(LOCATION_CITY) AS CITY
            FROM RAW_CONTACTS
            WHERE ORG_NAME IS NOT NULL
            GROUP BY TRIM(ORG_NAME), TRIM(ORG_TYPE)
        ) AS r
        ON UPPER(o.NAME) = UPPER(r.NAME)
           AND UPPER(COALESCE(o.ORG_TYPE, '')) = UPPER(COALESCE(r.ORG_TYPE, ''))
        WHEN MATCHED THEN UPDATE SET
            o.WEBSITE = COALESCE(r.WEBSITE, o.WEBSITE),
            o.COUNTRY = COALESCE(r.COUNTRY, o.COUNTRY),
            o.CITY    = COALESCE(r.CITY, o.CITY)
        WHEN NOT MATCHED THEN INSERT (
            NAME,
            ORG_TYPE,
            WEBSITE,
            COUNTRY,
            CITY
        )
        VALUES (
            r.NAME,
            r.ORG_TYPE,
            r.WEBSITE,
            r.COUNTRY,
            r.CITY
        );
    """

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(merge_sql)
        conn.commit()
        print("RAW_CONTACTS → ORGANIZATIONS transform completed.")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_raw_to_organizations()
