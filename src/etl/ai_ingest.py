import re
import json
from typing import List, Dict, Any

from src.scrapers.ai.firecrawl_client import crawl_domain_and_extract_contacts
from src.db.connection import get_db_connection


GENERIC_PREFIXES = ("info@", "contact@", "support@", "no-reply@", "noreply@")


def is_valid_email(email: str) -> bool:
    """
    Basic sanity check for email format.
    Not perfect, but enough to filter garbage.
    """
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


def validate_ai_contacts(
    contacts: List[Dict[str, Any]],
    domain_source: str,
    llm_source: str = "firecrawl_crawl_v1",
) -> List[Dict[str, Any]]:
    """
    Take raw contacts from Firecrawl and prepare rows for RAW_CONTACTS_AI_STAGING.
    Adds IS_SUSPECT / SUSPECT_REASON and fills in SOURCE/RAW_URL.
    """
    staging_rows: List[Dict[str, Any]] = []

    for c in contacts:
        email = (c.get("email") or "").strip().lower()
        org_name = (c.get("org_name") or "").strip()
        full_name = (c.get("full_name") or "").strip() or None

        # Hard drop: no email or invalid email.
        if not email or not is_valid_email(email):
            continue

        is_suspect = False
        suspect_reason = None

        # Flag generic catch-all inboxes as suspect.
        if email.startswith(GENERIC_PREFIXES):
            is_suspect = True
            suspect_reason = "generic_email"

        # Flag missing org name.
        if not org_name:
            is_suspect = True
            suspect_reason = (suspect_reason or "missing_org_name")

        # You can add more rules later (domain mismatch, etc.)

        staging_rows.append(
            {
                "full_name": full_name,
                "email": email,
                "phone": (c.get("phone") or "").strip() or None,
                "org_name": org_name or None,
                "org_type": (c.get("org_type") or "").strip() or None,
                "role_title": (c.get("role_title") or "").strip() or None,
                "location_city": (c.get("location_city") or "").strip() or None,
                "location_country": (c.get("location_country") or "").strip() or None,
                "source": f"firecrawl::{domain_source}",
                "raw_url": c.get("raw_url") or domain_source,
                "is_suspect": is_suspect,
                "suspect_reason": suspect_reason,
                "llm_source": llm_source,
                # For now we don't keep per-contact raw JSON, but you could later.
                "raw_json": None,
            }
        )

    return staging_rows


def insert_ai_staging(rows: List[Dict[str, Any]]) -> None:
    """
    Bulk insert validated AI rows into RAW_CONTACTS_AI_STAGING.
    """
    if not rows:
        print("No AI contacts to insert into RAW_CONTACTS_AI_STAGING.")
        return

    sql = """
        INSERT INTO RAW_CONTACTS_AI_STAGING (
            FULL_NAME,
            EMAIL,
            PHONE,
            ORG_NAME,
            ORG_TYPE,
            ROLE_TITLE,
            LOCATION_CITY,
            LOCATION_COUNTRY,
            SOURCE,
            RAW_URL,
            IS_SUSPECT,
            SUSPECT_REASON,
            LLM_SOURCE,
            RAW_JSON
        )
        VALUES (
            %(full_name)s,
            %(email)s,
            %(phone)s,
            %(org_name)s,
            %(org_type)s,
            %(role_title)s,
            %(location_city)s,
            %(location_country)s,
            %(source)s,
            %(raw_url)s,
            %(is_suspect)s,
            %(suspect_reason)s,
            %(llm_source)s,
            PARSE_JSON(%(raw_json)s)
        );
    """

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # If raw_json is None, json.dumps(None) -> 'null', which PARSE_JSON accepts.
        for row in rows:
            if row.get("raw_json") is None:
                row["raw_json"] = json.dumps(None)
            else:
                row["raw_json"] = json.dumps(row["raw_json"])

        cur.executemany(sql, rows)
        conn.commit()
        print(f"Inserted {len(rows)} AI contact(s) into RAW_CONTACTS_AI_STAGING.")
    finally:
        cur.close()
        conn.close()


def run_firecrawl_ai_ingest(domain_url: str, max_pages: int = 5) -> None:
    """
    High-level orchestration:
    1) Call Firecrawl to crawl a domain and extract contacts.
    2) Validate and flag them.
    3) Insert into RAW_CONTACTS_AI_STAGING.
    """
    print(f"Starting Firecrawl AI ingest for domain: {domain_url} (max_pages={max_pages})")
    contacts = crawl_domain_and_extract_contacts(domain_url, max_pages=max_pages)
    print(f"Firecrawl returned {len(contacts)} raw contact candidate(s).")

    staging_rows = validate_ai_contacts(contacts, domain_source=domain_url)
    print(f"{len(staging_rows)} contact(s) passed basic validation (some may be suspect).")

    insert_ai_staging(staging_rows)
    print("Firecrawl AI ingest completed.")


if __name__ == "__main__":
    # For now, hardcode a test domain or leave as a placeholder.
    TEST_DOMAIN = "https://example.com"
    run_firecrawl_ai_ingest(TEST_DOMAIN, max_pages=3)
