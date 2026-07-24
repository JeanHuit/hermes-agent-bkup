# Zotero MCP Server for Hermes Agent

A Model Context Protocol (MCP) server that gives Hermes Agent full access to your Zotero research library — search, read, create, update, and delete references, manage collections, and export bibliographies.

## Architecture

**Web API-only** — all operations go through `api.zotero.org`. No local API dependency.

- Authentication: `ZOTERO_TOKEN` environment variable (your Zotero API key)
- User ID: auto-resolved from the token — no manual `ZOTERO_USER_ID` needed
- All reads and writes use the same Web API endpoint

## Prerequisites

1. **Zotero account** with an API key from https://www.zotero.org/settings/keys
2. **Python 3.10+** with `httpx` and `mcp` packages
3. **Internet access** to reach api.zotero.org

## Step 1: Generate a Zotero API Key

1. Go to https://www.zotero.org/settings/keys/new
2. Check **Allow library access** (required for reading/writing items)
3. Check **Allow write access** (required for creating/editing items and collections)
4. Click **Save Key**
5. Copy the generated key

## Step 2: Install Python Dependencies

```bash
pip install httpx mcp
```

## Step 3: Place the Server

```bash
mkdir -p ~/.hermes/mcp-servers/zotero
cp server.py ~/.hermes/mcp-servers/zotero/server.py
```

## Step 4: Store Your API Key

Add the token to your Hermes `.env` file:

```bash
echo "ZOTERO_TOKEN=your_api_key_here" >> ~/.hermes/.env
```

The server reads `ZOTERO_TOKEN` from the environment at runtime.

## Step 5: Register the MCP Server in Hermes Config

Add to `~/.hermes/config.yaml` under `mcp_servers:`:

```yaml
mcp_servers:
  zotero:
    command: python3
    args:
      - /home/jeanhuit/.hermes/mcp-servers/zotero/server.py
    enabled: true
```

## Step 6: Restart Hermes

```bash
hermes restart
```

## Step 7: Verify

> "List my Zotero collections"
> "Search for papers about large language models"
> "Create a collection called 'Reading List'"

## Available Tools

| Tool | Description |
|------|-------------|
| `search_items` | Search library by keyword, type, or tag |
| `get_item` | Get full details of a specific item |
| `get_item_children` | Get attachments/notes for an item |
| `get_bibliography` | Get formatted citation (APA, MLA, Chicago, etc.) |
| `list_collections` | List all collections |
| `create_collection` | Create a new collection (or subcollection) |
| `get_collection_items` | List items in a collection |
| `add_item_to_collection` | Move an item into a collection |
| `add_item` | Add a new reference to the library |
| `update_item` | Edit an existing item's fields |
| `delete_item` | Move an item to trash |
| `list_tags` | List all tags with counts |
| `get_recent_items` | Get recently modified items |
| `export_items` | Export as BibTeX, RIS, CSV, etc. |

## Item Types & Field Quirks

Common `item_type` values for `add_item`:

| Type | Venue field | Notes |
|------|------------|-------|
| `journalArticle` | `publicationTitle` | Journal name |
| `conferencePaper` | `proceedingsTitle` | NOT `publicationTitle` |
| `book` | `publisher` | Publisher name |
| `thesis` | `university` | NOT `publisher` |
| `preprint` | _(none)_ | Use `url` for arXiv link |
| `webpage` | _(none)_ | Blog posts, tweets, etc. |
| `report` | _(none)_ | No publisher/university field |

The server handles field name mapping automatically. Just pass `publication_title` and the server routes it to the correct field per item type.

## Adding Items to Collections

The Web API requires a specific format: `POST` with `Content-Type: text/plain` and the raw item key as the body.

```bash
curl -X POST "https://api.zotero.org/users/{id}/collections/{key}/items" \
  -H "Zotero-API-Key: $ZOTERO_TOKEN" \
  -H "Content-Type: text/plain" \
  -d "ABC1234"
```

Returns HTTP 204 on success. JSON-formatted bodies are rejected.

## Troubleshooting

### "401 Unauthorized"
Your API key is invalid or expired. Generate a new one at https://www.zotero.org/settings/keys.

### Items created via MCP don't appear in Zotero Desktop
Sync your Zotero client: File → Sync with Zotero Server (or Ctrl+Shift+Y). Web API writes sync down from the server.

### "ZOTERO_TOKEN is not set"
Ensure the token is in `~/.hermes/.env` and the Hermes process was started after adding it.

## Reference

Full API reference: see `API-REFERENCE.md`
