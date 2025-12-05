import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv()


def get_firecrawl_client() -> Firecrawl:
    """
    Initialize and return a Firecrawl client using the API key
    from the environment.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise RuntimeError("FIRECRAWL_API_KEY is not set in the environment/.env")

    return Firecrawl(api_key=api_key)


def crawl_domain_and_extract_contacts(
    domain_url: str,
    max_pages: int = 10,
) -> List[Dict[str, Any]]:
    """
    Use Firecrawl to crawl up to `max_pages` from the given domain_url
    and extract contact-like data using a JSON schema.

    This does NOT insert into Snowflake.
    It just returns a list of Python dicts that you can validate and
    then insert into your AI staging table.
    """
    client = get_firecrawl_client()

    # JSON schema describing the contact structure we want Firecrawl to return
    contact_schema = {
        "type": "object",
        "properties": {
            "full_name": {"type": "string"},
            "email": {"type": "string"},
            "role_title": {"type": "string"},
            "org_name": {"type": "string"},
            "org_type": {"type": "string"},
            "location_city": {"type": "string"},
            "location_country": {"type": "string"},
        },
        "required": ["email", "org_name"],
    }

    # Firecrawl crawl call:
    # - domain_url can be a site root ("https://example.com")
    # - max_pages controls crawl depth/size
    # - We ask Firecrawl to return data that matches our contact_schema
    result = client.crawl(
        url=domain_url,
        limit=max_pages,
        extract={
            "schema": contact_schema,
        },
    )

    # The exact shape of `result` depends on Firecrawl's API,
    # but typically you'll get something like a list of pages
    # each with an "extracted" field that contains the JSON we want.
    contacts: List[Dict[str, Any]] = []

    # This loop may need to be adjusted depending on final API shape,
    # but the idea is: traverse all results and collect contact records.
    for page in result.get("results", []):
        extracted = page.get("extracted")
        if not extracted:
            continue

        # If Firecrawl returns a single object, wrap it into a list
        # If it returns a list already, iterate it directly
        if isinstance(extracted, dict):
            extracted_list = [extracted]
        else:
            extracted_list = extracted

        for item in extracted_list:
            # We trust Firecrawl to respect the schema, but still guard
            email = (item.get("email") or "").strip()
            org_name = (item.get("org_name") or "").strip()

            if not email or not org_name:
                # Skip completely unusable items at this stage
                continue

            contacts.append(
                {
                    "full_name": (item.get("full_name") or "").strip() or None,
                    "email": email.lower(),
                    "role_title": (item.get("role_title") or "").strip() or None,
                    "org_name": org_name,
                    "org_type": (item.get("org_type") or "").strip() or None,
                    "location_city": (item.get("location_city") or "").strip() or None,
                    "location_country": (item.get("location_country") or "").strip() or None,
                    # You can add more metadata here later if needed
                }
            )

    return contacts
