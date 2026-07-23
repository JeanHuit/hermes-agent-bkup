# Zotero MCP Server for Hermes Agent

A Model Context Protocol (MCP) server that gives Hermes Agent full access to your Zotero research library — search, read, create, update, and delete references, manage collections, and export bibliographies.

## Architecture

This MCP server uses a **dual API** approach:

- **Read operations** (search, get, list) → Zotero Local API at `localhost:23119/api`
- **Write operations** (create, update, delete collections & items) → Zotero Web API at `api.zotero.org`

The local API is fast and requires no authentication but is read-only for collections. The Web API requires an API key and handles all writes.

## Prerequisites

1. **Zotero Desktop** installed and running (provides the local API on port 23119)
2. **Python 3.10+** with `httpx` and `mcp` packages
3. **Zotero API key** from https://www.zotero.org/settings/keys/new

## Step 1: Generate a Zotero API Key

1. Go to https://www.zotero.org/settings/keys/new
2. Check **Allow library access** (required for reading/writing items)
3. Check **Allow write access** (required for creating/editing items and collections)
4. Set **Default Permissions** to "Allow library access" and "Allow write access"
5. Click **Save Key**
6. Copy the generated key (starts with something like `8rPsNcn3...`)

## Step 2: Install Python Dependencies

```bash
pip install httpx mcp
```

## Step 3: Place the Server

Copy `server.py` to a permanent location:

```bash
mkdir -p ~/.hermes/mcp-servers/zotero
cp server.py ~/.hermes/mcp-servers/zotero/server.py
```

## Step 4: Store Your API Key

Add the token to your Hermes `.env` file:

```bash
echo "ZOTERO_TOKEN=your_api_key_here" >> ~/.hermes/.env
```

The `.env` file should already exist at `~/.hermes/.env`. The server reads `ZOTERO_TOKEN` from this file at runtime.

## Step 5: Register the MCP Server in Hermes Config

Add the following to `~/.hermes/config.yaml` under the `mcp_servers:` section:

```yaml
mcp_servers:
  zotero:
    command: python3
    args:
      - /home/jeanhuit/.hermes/mcp-servers/zotero/server.py
    enabled: true
```

Adjust the path if you placed `server.py` elsewhere.

## Step 6: Restart Hermes

The MCP server is loaded at session start. Restart Hermes for the changes to take effect:

```bash
# If running as a service
hermes restart

# Or simply start a new session
hermes
```

## Step 7: Verify

Start a conversation and try:

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

## Item Types

Common `item_type` values for `add_item`:

- `book` — Monographs
- `journalArticle` — Journal papers
- `conferencePaper` — Conference proceedings (use `proceedingsTitle` not `publicationTitle`)
- `preprint` — Preprints (arXiv, SSRN, etc.)
- `webpage` — Web pages, blog posts, tweets
- `report` — Technical reports
- `thesis` — Dissertations
- `manuscript` — Unpublished manuscripts

**Important:** For `conferencePaper` items, use the `proceedingsTitle` parameter (not `publicationTitle`) when adding via the Web API. The local API accepts `publicationTitle` for all types, but the Web API is strict about field names per item type.

## Troubleshooting

### "Connection refused" on localhost:23119
Zotero Desktop is not running. Start Zotero and ensure the "Allow other applications on this computer to communicate with Zotero" option is enabled in Edit → Preferences → Advanced → Local Files.

### "401 Unauthorized" on api.zotero.org
Your API key is invalid or expired. Generate a new one at https://www.zotero.org/settings/keys.

### "Endpoint does not support method" for collection creation
The local API does not support POST for collections. The server falls back to the Web API for writes. Ensure `ZOTERO_TOKEN` is set in `~/.hermes/.env`.

### Items created via Web API don't appear in Zotero
Sync Zotero: Edit → Preferences → Sync → Sync Now. The Web API writes go through the sync mechanism.
