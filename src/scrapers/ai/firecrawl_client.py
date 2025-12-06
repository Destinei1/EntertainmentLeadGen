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
    max_pages: int = 10, # this isnt going to be used by extract, kept for future tuning
) -> List[Dict[str, Any]]:
    """
    Use Firecrawl to crawl up to `max_pages` from the given domain_url
    and extract contact-like data using a JSON schema.

    This does NOT insert into Snowflake.
    It just returns a list of Python dicts that you can validate and
    then insert into your AI staging table.
    """
    client = get_firecrawl_client()

    # Decide whether to treat this as a single page or wildcard crawl.
    # If user didn't add /* but wants multi-page, they can pass it explicitly.
    urls = [domain_url]

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
            # optional: capture the page URL per contact if Firecrawl infers it
            "raw_url": {"type": "string"},
        },
        "required": ["email", "org_name"],
    }

    schema = {
        "type": "object",
        "properties": {
            "contacts": {
                "type": "array",
                "items": contact_item_schema,
            }
        },
        "required": ["contacts"],
    }

    prompt = (
        "Extract a list of media / music / radio / blog / venue contacts from these pages. "
        "Each contact should be a person or generic press inbox that could receive music "
        "press releases: include full_name (if available), email, role_title, org_name, "
        "org_type, city and country. If the page has multiple relevant contacts, "
        "include each as a separate item in the 'contacts' list."
    )

    # Firecrawl crawl call:
    # - domain_url can be a site root ("https://example.com")
    # - max_pages controls crawl depth/size
    # - We ask Firecrawl to return data that matches our contact_schema
    result = client.extract(
        url=urls,
        prompt=prompt,
        schema=schema
        # limit=max_pages,
       
    )

    # not sure on the SDK version, so the results can either be a dict or an object with .data
    data = getattr(result, "data", None) or result.get("data", {})
    contacts_raw = data.get("contacts", [])

    contacts: List[Dict[str, Any]] = []
    for item in contacts_raw:
        if not isinstance(item, dict):
            continue

        email = (item.get("email") or "").strip().lower()
        org_name = (item.get("org_name") or "").strip()

        if not email or not org_name:
            continue

        contacts.append(
            {
                "full_name": (item.get("full_name") or "").strip() or None,
                "email": email,
                "role_title": (item.get("role_title") or "").strip() or None,
                "org_name": org_name,
                "org_type": (item.get("org_type") or "").strip() or None,
                "location_city": (item.get("location_city") or "").strip() or None,
                "location_country": (item.get("location_country") or "").strip() or None,
                # If Firecrawl gives us a per-contact raw_url, keep it;
                # otherwise we fall back to the domain_url at the ETL layer.
                "raw_url": (item.get("raw_url") or "").strip() or None,
            }
        )

    return contacts
