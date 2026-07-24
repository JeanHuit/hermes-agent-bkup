#!/usr/bin/env python3
"""Zotero MCP Server — wraps the Zotero Web API (api.zotero.org) for Hermes Agent.

Requires ZOTERO_TOKEN environment variable (your Zotero API key).
Get one at https://www.zotero.org/settings/keys
"""

import json
import os
from functools import lru_cache
from typing import Optional, Any

import httpx
from mcp.server.fastmcp import FastMCP

# ── Web API config (derived from ZOTERO_TOKEN) ──────────────────────────

ZOTERO_TOKEN = os.environ.get("ZOTERO_TOKEN", "")
ZOTERO_WEB_BASE = "https://api.zotero.org"


@lru_cache(maxsize=1)
def _resolve_user_id() -> str:
    """Resolve the Zotero user ID from the API token (cached)."""
    if not ZOTERO_TOKEN:
        raise RuntimeError(
            "ZOTERO_TOKEN is not set. Get your API key at "
            "https://www.zotero.org/settings/keys and set ZOTERO_TOKEN in your environment."
        )
    resp = httpx.get(
        f"{ZOTERO_WEB_BASE}/keys/{ZOTERO_TOKEN}",
        headers={"Zotero-API-Key": ZOTERO_TOKEN},
        timeout=15.0,
    )
    resp.raise_for_status()
    return str(resp.json()["userID"])


def get_client() -> httpx.Client:
    """Create an HTTP client for the Zotero Web API."""
    user_id = _resolve_user_id()
    return httpx.Client(
        base_url=f"{ZOTERO_WEB_BASE}/users/{user_id}",
        headers={
            "Zotero-API-Key": ZOTERO_TOKEN,
            "Zotero-API-Version": "3",
        },
        timeout=30.0,
    )


mcp = FastMCP(
    "zotero",
    instructions="""MCP server for Zotero research library management.
    Uses the Zotero Web API (api.zotero.org) for all operations.
    Requires ZOTERO_TOKEN environment variable (your Zotero API key).
    Get one at https://www.zotero.org/settings/keys
    Your user ID is auto-resolved from the token.""",
)


# ── Helpers ─────────────────────────────────────────────────────────────


def format_item(item: dict) -> dict:
    """Extract relevant fields from a Zotero item for cleaner output."""
    data = item.get("data", {})
    result = {
        "key": data.get("key"),
        "itemType": data.get("itemType"),
        "title": data.get("title"),
        "creators": [
            f"{c.get('lastName', '')}, {c.get('firstName', '')}" if c.get("creatorType") == "author"
            else f"{c.get('name', '')} ({c.get('creatorType', '')})"
            for c in data.get("creators", [])
        ],
        "date": data.get("date"),
        "abstractNote": data.get("abstractNote", "")[:200] if data.get("abstractNote") else None,
        "tags": [t.get("tag") for t in data.get("tags", [])],
        "url": data.get("url"),
        "DOI": data.get("DOI"),
    }
    return {k: v for k, v in result.items() if v is not None and v != []}


def _venue_field(item_type: str) -> str:
    """Map the venue/publication field name based on Zotero item type.

    - journalArticle  → publicationTitle
    - conferencePaper → proceedingsTitle
    - thesis          → university
    - book/bookSection → publisher is separate; no venue mapping needed
    """
    if item_type == "conferencePaper":
        return "proceedingsTitle"
    if item_type == "thesis":
        return "university"
    return "publicationTitle"


def _parse_creators(creators_str: Optional[str]) -> list[dict]:
    """Parse semicolon-separated 'LastName, FirstName' strings into Zotero creator dicts."""
    if not creators_str:
        return []
    result = []
    for c in creators_str.split(";"):
        c = c.strip()
        if not c:
            continue
        if "," in c:
            parts = c.split(",", 1)
            result.append({
                "creatorType": "author",
                "lastName": parts[0].strip(),
                "firstName": parts[1].strip(),
            })
        else:
            result.append({
                "creatorType": "author",
                "name": c,
            })
    return result


# ── Tools ───────────────────────────────────────────────────────────────


@mcp.tool()
def search_items(
    query: str,
    limit: int = 10,
    item_type: Optional[str] = None,
    tag: Optional[str] = None,
    sort: str = "dateModified",
    direction: str = "desc",
) -> str:
    """Search for items in your Zotero library.

    Args:
        query: Search term (searches title, creator, and optionally full text)
        limit: Maximum number of results (1-100, default 10)
        item_type: Filter by item type (e.g., 'book', 'journalArticle', 'conferencePaper')
        tag: Filter by tag
        sort: Sort field (dateAdded, dateModified, title, creator, itemType, date)
        direction: Sort direction ('asc' or 'desc')

    Returns:
        JSON string with matching items.
    """
    params: dict[str, Any] = {"q": query, "limit": min(limit, 100), "sort": sort, "direction": direction}
    if item_type:
        params["itemType"] = item_type
    if tag:
        params["tag"] = tag

    with get_client() as client:
        resp = client.get("/items/top", params=params)
        resp.raise_for_status()
        items = resp.json()
        total = resp.headers.get("Total-Results", str(len(items)))
        results = [format_item(item) for item in items]
        return json.dumps({"total": total, "count": len(results), "items": results}, indent=2)


@mcp.tool()
def get_item(item_key: str, include_children: bool = False) -> str:
    """Get detailed information about a specific item.

    Args:
        item_key: The Zotero item key (e.g., '9DYCP9GT')
        include_children: Whether to include child items (attachments, notes)

    Returns:
        JSON string with full item details.
    """
    with get_client() as client:
        resp = client.get(f"/items/{item_key}")
        resp.raise_for_status()
        item = resp.json()

        result = {
            "item": format_item(item),
            "fullData": item.get("data", {}),
        }

        if include_children:
            children_resp = client.get(f"/items/{item_key}/children")
            children_resp.raise_for_status()
            result["children"] = [
                {
                    "key": c.get("data", {}).get("key"),
                    "itemType": c.get("data", {}).get("itemType"),
                    "title": c.get("data", {}).get("title"),
                    "contentType": c.get("data", {}).get("contentType"),
                    "filename": c.get("data", {}).get("filename"),
                }
                for c in children_resp.json()
            ]

        return json.dumps(result, indent=2)


@mcp.tool()
def get_bibliography(
    item_keys: str,
    style: str = "apa",
    format: str = "html",
) -> str:
    """Get formatted bibliography for one or more items.

    Args:
        item_keys: Comma-separated item keys (e.g., 'ABC1234,DEF5678')
        style: Citation style (apa, chicago-note-bibliography, mla, etc.)
        format: Output format ('html', 'text', 'latex', or 'rtf')

    Returns:
        Formatted bibliography string.
    """
    keys = [k.strip() for k in item_keys.split(",")]
    results = []

    with get_client() as client:
        for key in keys:
            resp = client.get(
                f"/items/{key}",
                params={"format": "json", "include": "bib", "style": style},
            )
            resp.raise_for_status()
            item = resp.json()
            bib = item.get("bibliography", "")
            if format == "text":
                import re
                bib = re.sub(r"<[^>]+>", "", bib)
            results.append({"key": key, "bibliography": bib})

    return json.dumps(results, indent=2)


@mcp.tool()
def list_collections(top_only: bool = False) -> str:
    """List all collections in your Zotero library.

    Args:
        top_only: If True, only return top-level collections

    Returns:
        JSON string with collection list.
    """
    endpoint = "/collections/top" if top_only else "/collections"
    with get_client() as client:
        resp = client.get(endpoint, params={"limit": 100})
        resp.raise_for_status()
        collections = resp.json()

        results = [
            {
                "key": c.get("data", {}).get("key"),
                "name": c.get("data", {}).get("name"),
                "parentCollection": c.get("data", {}).get("parentCollection", False),
                "numItems": c.get("meta", {}).get("numItems", 0),
            }
            for c in collections
        ]
        return json.dumps(results, indent=2)


@mcp.tool()
def create_collection(
    name: str,
    parent_collection: Optional[str] = None,
) -> str:
    """Create a new collection in your Zotero library.

    Args:
        name: Name of the collection
        parent_collection: Key of parent collection (optional, for subcollections)

    Returns:
        JSON string with the created collection info.
    """
    data: dict[str, Any] = {"name": name}
    if parent_collection:
        data["parentCollection"] = parent_collection

    with get_client() as client:
        resp = client.post("/collections", json=[data])
        resp.raise_for_status()
        result = resp.json()
        successful = result.get("successful", {})
        if successful:
            first = list(successful.values())[0]
            return json.dumps({
                "key": first.get("key"),
                "name": name,
                "version": first.get("version"),
            }, indent=2)
        return json.dumps(result, indent=2)


@mcp.tool()
def add_item_to_collection(
    collection_key: str,
    item_key: str,
) -> str:
    """Add an existing item to a collection.

    Args:
        collection_key: The collection key
        item_key: The item key to add

    Returns:
        JSON string with status.
    """
    with get_client() as client:
        resp = client.post(
            f"/collections/{collection_key}/items",
            content=item_key,
            headers={"Content-Type": "text/plain"},
        )
        resp.raise_for_status()
        return json.dumps({"success": True, "item_key": item_key, "collection_key": collection_key})


@mcp.tool()
def get_collection_items(
    collection_key: str,
    limit: int = 25,
    item_type: Optional[str] = None,
    sort: str = "dateModified",
    direction: str = "desc",
) -> str:
    """Get items in a specific collection.

    Args:
        collection_key: The collection key
        limit: Maximum results (1-100)
        item_type: Filter by item type
        sort: Sort field
        direction: Sort direction

    Returns:
        JSON string with items in the collection.
    """
    params: dict[str, Any] = {"limit": min(limit, 100), "sort": sort, "direction": direction}
    if item_type:
        params["itemType"] = item_type

    with get_client() as client:
        resp = client.get(
            f"/collections/{collection_key}/items/top",
            params=params,
        )
        resp.raise_for_status()
        items = resp.json()
        total = resp.headers.get("Total-Results", str(len(items)))
        results = [format_item(item) for item in items]
        return json.dumps({"total": total, "count": len(results), "items": results}, indent=2)


@mcp.tool()
def list_tags() -> str:
    """List all tags in your Zotero library.

    Returns:
        JSON string with all tags and their item counts.
    """
    with get_client() as client:
        resp = client.get("/tags", params={"limit": 500})
        resp.raise_for_status()
        tags = resp.json()

        results = [
            {"tag": t.get("meta", {}).get("type", ""), "name": t.get("data", {}).get("tag"), "numItems": t.get("meta", {}).get("numItems", 0)}
            for t in tags
        ]
        return json.dumps(results, indent=2)


@mcp.tool()
def add_item(
    item_type: str,
    title: str,
    creators: Optional[str] = None,
    abstract_note: Optional[str] = None,
    date: Optional[str] = None,
    url: Optional[str] = None,
    doi: Optional[str] = None,
    tags: Optional[str] = None,
    publication_title: Optional[str] = None,
    volume: Optional[str] = None,
    issue: Optional[str] = None,
    pages: Optional[str] = None,
    publisher: Optional[str] = None,
    isbn: Optional[str] = None,
    issn: Optional[str] = None,
) -> str:
    """Add a new item to your Zotero library.

    Args:
        item_type: Type of item ('book', 'journalArticle', 'conferencePaper', 'webpage', 'report', 'thesis', etc.)
        title: Title of the item
        creators: Semicolon-separated list of creators in 'LastName, FirstName' format
        abstract_note: Abstract or description
        date: Publication date
        url: URL
        doi: DOI
        tags: Comma-separated tags
        publication_title: Journal/book title (maps to proceedingsTitle for conferencePaper, university for thesis)
        volume: Volume number
        issue: Issue number
        pages: Page range
        publisher: Publisher name
        isbn: ISBN
        issn: ISSN

    Returns:
        JSON string with the created item.
    """
    item_data: dict[str, Any] = {
        "itemType": item_type,
        "title": title,
        "creators": _parse_creators(creators),
        "tags": [],
    }

    if tags:
        item_data["tags"] = [{"tag": t.strip()} for t in tags.split(",")]

    # Optional fields
    venue_key = _venue_field(item_type)
    optional_fields: dict[str, Any] = {
        "abstractNote": abstract_note,
        "date": date,
        "url": url,
        "DOI": doi,
        venue_key: publication_title,
        "volume": volume,
        "issue": issue,
        "pages": pages,
        "publisher": publisher,
        "ISBN": isbn,
        "ISSN": issn,
    }
    for key, value in optional_fields.items():
        if value:
            item_data[key] = value

    with get_client() as client:
        resp = client.post("/items", json=[item_data])
        resp.raise_for_status()
        result = resp.json()

        # Extract created item key from response
        successful = result.get("successful", {}) or result.get("success", {})
        if successful:
            first_val = list(successful.values())[0]
            if isinstance(first_val, dict):
                item_key = first_val.get("key", "")
            else:
                item_key = str(first_val)
            return json.dumps({"key": item_key, "title": title, "itemType": item_type, "raw": result}, indent=2)
        return json.dumps(result, indent=2)


@mcp.tool()
def update_item(
    item_key: str,
    title: Optional[str] = None,
    abstract_note: Optional[str] = None,
    date: Optional[str] = None,
    url: Optional[str] = None,
    doi: Optional[str] = None,
    tags: Optional[str] = None,
    publication_title: Optional[str] = None,
    volume: Optional[str] = None,
    issue: Optional[str] = None,
    pages: Optional[str] = None,
    publisher: Optional[str] = None,
) -> str:
    """Update an existing item in your Zotero library.

    Args:
        item_key: The item key to update
        title: New title (optional)
        abstract_note: New abstract (optional)
        date: New date (optional)
        url: New URL (optional)
        doi: New DOI (optional)
        tags: Comma-separated tags to set (optional)
        publication_title: New publication title (optional)
        volume: New volume (optional)
        issue: New issue (optional)
        pages: New pages (optional)
        publisher: New publisher (optional)

    Returns:
        JSON string with update status.
    """
    with get_client() as client:
        # Get current item to read version and preserve existing data
        resp = client.get(f"/items/{item_key}")
        resp.raise_for_status()
        item = resp.json()
        item_data = item.get("data", {})
        version = item.get("version", 0)

        updates = {
            "title": title,
            "abstractNote": abstract_note,
            "date": date,
            "url": url,
            "DOI": doi,
            "publicationTitle": publication_title,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "publisher": publisher,
        }
        for key, value in updates.items():
            if value is not None:
                item_data[key] = value

        if tags is not None:
            item_data["tags"] = [{"tag": t.strip()} for t in tags.split(",")]

        resp = client.put(
            f"/items/{item_key}",
            json=item_data,
            headers={"If-Unmodified-Since-Version": str(version)},
        )
        resp.raise_for_status()
        return json.dumps({"success": True, "item": format_item(resp.json())}, indent=2)


@mcp.tool()
def delete_item(item_key: str) -> str:
    """Delete an item from your Zotero library (moves to trash).

    Args:
        item_key: The item key to delete

    Returns:
        JSON string with deletion status.
    """
    with get_client() as client:
        resp = client.delete(f"/items/{item_key}")
        resp.raise_for_status()
        return json.dumps({"success": True, "deleted": item_key}, indent=2)


@mcp.tool()
def get_recent_items(limit: int = 10, sort: str = "dateModified") -> str:
    """Get recently modified items in your library.

    Args:
        limit: Number of items to return (1-100)
        sort: Sort by 'dateModified' or 'dateAdded'

    Returns:
        JSON string with recent items.
    """
    with get_client() as client:
        resp = client.get(
            "/items/top",
            params={"limit": min(limit, 100), "sort": sort, "direction": "desc"},
        )
        resp.raise_for_status()
        items = resp.json()
        results = [format_item(item) for item in items]
        return json.dumps(results, indent=2)


@mcp.tool()
def get_item_children(item_key: str) -> str:
    """Get child items (attachments, notes) of a specific item.

    Args:
        item_key: The parent item key

    Returns:
        JSON string with child items.
    """
    with get_client() as client:
        resp = client.get(f"/items/{item_key}/children")
        resp.raise_for_status()
        children = resp.json()

        results = [
            {
                "key": c.get("data", {}).get("key"),
                "itemType": c.get("data", {}).get("itemType"),
                "title": c.get("data", {}).get("title"),
                "contentType": c.get("data", {}).get("contentType"),
                "filename": c.get("data", {}).get("filename"),
                "linkMode": c.get("data", {}).get("linkMode"),
                "url": c.get("data", {}).get("url"),
            }
            for c in children
        ]
        return json.dumps(results, indent=2)


@mcp.tool()
def export_items(
    item_keys: Optional[str] = None,
    collection_key: Optional[str] = None,
    format: str = "bibtex",
) -> str:
    """Export items in various formats (BibTeX, RIS, CSV, etc.).

    Args:
        item_keys: Comma-separated item keys (optional, exports all if not provided)
        collection_key: Export items from a specific collection (optional)
        format: Export format ('bibtex', 'ris', 'csv', 'endnote', 'mods', 'refer')

    Returns:
        Exported content string.
    """
    params: dict[str, Any] = {"format": format}
    if item_keys:
        params["itemKey"] = item_keys
    elif collection_key:
        with get_client() as client:
            resp = client.get(
                f"/collections/{collection_key}/items/top",
                params={"limit": 100},
            )
            resp.raise_for_status()
            keys = [item["data"]["key"] for item in resp.json()]
            if keys:
                params["itemKey"] = ",".join(keys)

    with get_client() as client:
        endpoint = f"/collections/{collection_key}/items/top" if collection_key else "/items/top"
        resp = client.get(endpoint, params=params)
        resp.raise_for_status()
        return resp.text


if __name__ == "__main__":
    mcp.run()
