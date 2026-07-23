#!/usr/bin/env python3
"""Zotero MCP Server - Dual API wrapper for Hermes Agent.

Uses the Zotero Local API (localhost:23119/api) for reads and the
Zotero Web API (api.zotero.org) for writes when ZOTERO_TOKEN is set.
Falls back to local-only mode for reads if the Web API is unavailable.
"""

import json
import os
import re
from typing import Optional, Any

import httpx
from mcp.server.fastmcp import FastMCP

# Configuration
ZOTERO_LOCAL_URL = os.environ.get("ZOTERO_API_URL", "http://127.0.0.1:23119/api")
ZOTERO_WEB_URL = "https://api.zotero.org"
ZOTERO_USER = "0"  # Local API user (always 0 for current user)
ZOTERO_USER_ID: Optional[str] = None  # Resolved at startup from token
ZOTERO_TOKEN = os.environ.get("ZOTERO_TOKEN", "")

mcp = FastMCP(
    "zotero",
    instructions="""MCP server for Zotero research library management.
    Uses the local API for reads and the Web API for writes (collections,
    items). Requires Zotero Desktop running locally and a ZOTERO_TOKEN
    in ~/.hermes/.env for write operations.""",
)


def _resolve_user_id() -> Optional[str]:
    """Resolve the numeric user ID from the Web API using the token."""
    if not ZOTERO_TOKEN:
        return None
    try:
        with httpx.Client(timeout=10) as c:
            r = c.get(f"{ZOTERO_WEB_URL}/users/self", headers={"Zotero-API-Key": ZOTERO_TOKEN})
            if r.status_code == 200:
                return str(r.json().get("id"))
    except Exception:
        pass
    return None


# Resolve user ID at module load
if ZOTERO_TOKEN:
    ZOTERO_USER_ID = _resolve_user_id()


def get_local_client() -> httpx.Client:
    """HTTP client for the Zotero local API (reads)."""
    return httpx.Client(
        base_url=ZOTERO_LOCAL_URL,
        headers={"Zotero-API-Version": "3"},
        timeout=30.0,
    )


def get_web_client() -> httpx.Client:
    """HTTP client for the Zotero Web API (writes)."""
    return httpx.Client(
        base_url=ZOTERO_WEB_URL,
        headers={
            "Zotero-API-Key": ZOTERO_TOKEN,
            "Zotero-API-Version": "3",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


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


# ---------------------------------------------------------------------------
# READ TOOLS (use local API)
# ---------------------------------------------------------------------------

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

    with get_local_client() as client:
        resp = client.get(f"/users/{ZOTERO_USER}/items/top", params=params)
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
    with get_local_client() as client:
        resp = client.get(f"/users/{ZOTERO_USER}/items/{item_key}")
        resp.raise_for_status()
        item = resp.json()
        result = {"item": format_item(item), "fullData": item.get("data", {})}

        if include_children:
            children_resp = client.get(f"/users/{ZOTERO_USER}/items/{item_key}/children")
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
    with get_local_client() as client:
        for key in keys:
            resp = client.get(
                f"/users/{ZOTERO_USER}/items/{key}",
                params={"format": "json", "include": "bib", "style": style},
            )
            resp.raise_for_status()
            item = resp.json()
            bib = item.get("bibliography", "")
            if format == "text":
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
    with get_local_client() as client:
        resp = client.get(f"/users/{ZOTERO_USER}{endpoint}", params={"limit": 100})
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

    with get_local_client() as client:
        resp = client.get(
            f"/users/{ZOTERO_USER}/collections/{collection_key}/items/top",
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
    with get_local_client() as client:
        resp = client.get(f"/users/{ZOTERO_USER}/tags", params={"limit": 500})
        resp.raise_for_status()
        tags = resp.json()
        results = [
            {"name": t.get("data", {}).get("tag"), "numItems": t.get("meta", {}).get("numItems", 0)}
            for t in tags
        ]
        return json.dumps(results, indent=2)


@mcp.tool()
def get_recent_items(limit: int = 10, sort: str = "dateModified") -> str:
    """Get recently modified items in your library.

    Args:
        limit: Number of items to return (1-100)
        sort: Sort by 'dateModified' or 'dateAdded'

    Returns:
        JSON string with recent items.
    """
    with get_local_client() as client:
        resp = client.get(
            f"/users/{ZOTERO_USER}/items/top",
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
    with get_local_client() as client:
        resp = client.get(f"/users/{ZOTERO_USER}/items/{item_key}/children")
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


# ---------------------------------------------------------------------------
# WRITE TOOLS (use Web API — requires ZOTERO_TOKEN)
# ---------------------------------------------------------------------------

def _require_web() -> httpx.Client:
    """Return a Web API client or raise if token not configured."""
    if not ZOTERO_TOKEN or not ZOTERO_USER_ID:
        raise RuntimeError(
            "ZOTERO_TOKEN not set. Add it to ~/.hermes/.env for write operations."
        )
    return get_web_client()


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
    coll_data: dict[str, Any] = {"name": name}
    if parent_collection:
        coll_data["parentCollection"] = parent_collection

    with _require_web() as client:
        resp = client.post(
            f"/users/{ZOTERO_USER_ID}/collections",
            json=[{"data": coll_data}],
        )
        resp.raise_for_status()
        result = resp.json()
        successful = result.get("successful", {})
        if successful:
            item = list(successful.values())[0]
            return json.dumps({
                "key": item.get("key"),
                "name": item.get("data", {}).get("name"),
                "version": item.get("version"),
            }, indent=2)
        return json.dumps({"error": result.get("failed", "Unknown error")}, indent=2)


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
    with _require_web() as client:
        # Get current collection version
        resp = client.get(f"/users/{ZOTERO_USER_ID}/collections/{collection_key}")
        resp.raise_for_status()
        coll = resp.json()
        version = coll.get("version", 0)

        # Add item to collection
        resp2 = client.post(
            f"/users/{ZOTERO_USER_ID}/collections/{collection_key}/items",
            json={"items": [{"key": item_key}], "version": version},
        )
        resp2.raise_for_status()
        return json.dumps({"success": True, "item_key": item_key, "collection_key": collection_key})


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
    proceedings_title: Optional[str] = None,
    volume: Optional[str] = None,
    issue: Optional[str] = None,
    pages: Optional[str] = None,
    publisher: Optional[str] = None,
    isbn: Optional[str] = None,
    issn: Optional[str] = None,
    place: Optional[str] = None,
) -> str:
    """Add a new item to your Zotero library.

    Args:
        item_type: Type of item ('book', 'journalArticle', 'conferencePaper', 'webpage', 'report', etc.)
        title: Title of the item
        creators: Semicolon-separated list of creators in 'LastName, FirstName' format
        abstract_note: Abstract or description
        date: Publication date
        url: URL
        doi: DOI
        tags: Comma-separated tags
        publication_title: Journal/book title (for journalArticle, book, etc.)
        proceedings_title: Conference proceedings title (for conferencePaper)
        volume: Volume number
        issue: Issue number
        pages: Page range
        publisher: Publisher name
        isbn: ISBN
        issn: ISSN
        place: Place of publication

    Returns:
        JSON string with the created item.
    """
    item_data: dict[str, Any] = {
        "itemType": item_type,
        "title": title,
        "creators": [],
        "tags": [],
    }

    if creators:
        for c in creators.split(";"):
            c = c.strip()
            if "," in c:
                parts = c.split(",", 1)
                item_data["creators"].append({
                    "creatorType": "author",
                    "lastName": parts[0].strip(),
                    "firstName": parts[1].strip(),
                })
            else:
                item_data["creators"].append({
                    "creatorType": "author",
                    "name": c,
                })

    if tags:
        item_data["tags"] = [{"tag": t.strip()} for t in tags.split(",")]

    optional_fields = {
        "abstractNote": abstract_note,
        "date": date,
        "url": url,
        "DOI": doi,
        "publicationTitle": publication_title,
        "proceedingsTitle": proceedings_title,
        "volume": volume,
        "issue": issue,
        "pages": pages,
        "publisher": publisher,
        "ISBN": isbn,
        "ISSN": issn,
        "place": place,
    }
    for key, value in optional_fields.items():
        if value:
            item_data[key] = value

    with _require_web() as client:
        resp = client.post(
            f"/users/{ZOTERO_USER_ID}/items",
            json=[{"items": [item_data]}],
        )
        resp.raise_for_status()
        result = resp.json()
        successful = result.get("successful", {})
        if successful:
            item = list(successful.values())[0]
            return json.dumps({
                "key": item.get("key"),
                "title": item.get("data", {}).get("title"),
                "itemType": item.get("data", {}).get("itemType"),
                "version": item.get("version"),
            }, indent=2)
        return json.dumps({"error": result.get("failed", "Unknown error")}, indent=2)


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
    proceedings_title: Optional[str] = None,
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
        proceedings_title: New proceedings title (optional)
        volume: New volume (optional)
        issue: New issue (optional)
        pages: New pages (optional)
        publisher: New publisher (optional)

    Returns:
        JSON string with update status.
    """
    with _require_web() as client:
        # Get current item
        resp = client.get(f"/users/{ZOTERO_USER_ID}/items/{item_key}")
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
            "proceedingsTitle": proceedings_title,
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
            f"/users/{ZOTERO_USER_ID}/items/{item_key}",
            json=item_data,
            headers={"If-Unmodified-Since-Version": str(version)},
        )
        resp.raise_for_status()
        updated = resp.json()
        return json.dumps({"success": True, "item": format_item(updated)}, indent=2)


@mcp.tool()
def delete_item(item_key: str) -> str:
    """Delete an item from your Zotero library (moves to trash).

    Args:
        item_key: The item key to delete

    Returns:
        JSON string with deletion status.
    """
    with _require_web() as client:
        resp = client.delete(f"/users/{ZOTERO_USER_ID}/items/{item_key}")
        resp.raise_for_status()
        return json.dumps({"success": True, "deleted": item_key}, indent=2)


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
    with get_local_client() as client:
        if collection_key:
            resp = client.get(
                f"/users/{ZOTERO_USER}/collections/{collection_key}/items/top",
                params={"limit": 100},
            )
            resp.raise_for_status()
            keys = [item["data"]["key"] for item in resp.json()]
            if keys:
                item_keys = ",".join(keys)

        params: dict[str, Any] = {"format": format}
        if item_keys:
            params["itemKey"] = item_keys

        resp = client.get(f"/users/{ZOTERO_USER}/items/top", params=params)
        resp.raise_for_status()
        return resp.text


if __name__ == "__main__":
    mcp.run()
