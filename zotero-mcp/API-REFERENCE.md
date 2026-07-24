# Zotero MCP Server — API Reference

Web API-only MCP server wrapping the Zotero Web API (api.zotero.org).

## Setup

Requires one environment variable:

- `ZOTERO_TOKEN` — your Zotero API key from https://www.zotero.org/settings/keys

The user ID is auto-resolved from the token — no manual `ZOTERO_USER_ID` needed.

## API Details

- Base URL: `https://api.zotero.org/users/{userID}/`
- Auth: `Zotero-API-Key: {ZOTERO_TOKEN}` header
- API version: 3 (header: `Zotero-API-Version: 3`)
- All operations (read + write) go through the Web API

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/items/top` | GET | Top-level items |
| `/items` | POST | Create items (JSON array body) |
| `/items/<key>` | GET | Single item |
| `/items/<key>` | PUT | Update item (requires If-Unmodified-Since-Version) |
| `/items/<key>` | DELETE | Move to trash |
| `/items/<key>/children` | GET | Child items (attachments, notes) |
| `/collections` | GET | All collections |
| `/collections/top` | GET | Top-level collections only |
| `/collections` | POST | Create collection (JSON array of data dicts) |
| `/collections/<key>/items` | POST | Add item to collection (**text/plain** body, raw key) |
| `/collections/<key>/items/top` | GET | Items in a collection |
| `/tags` | GET | All tags |

## Item Type Field Quirks

**Pitfall**: Different Zotero item types use different field names for publication venue:

| Item Type | Venue Field | Example |
|-----------|-------------|---------|
| `journalArticle` | `publicationTitle` | "IEEE Computer" |
| `conferencePaper` | `proceedingsTitle` | "NeurIPS 2022" |
| `book` / `bookSection` | `publisher` | "Addison-Wesley" |
| `thesis` | `university` | "University of California" |
| `preprint` | (none) | Use `url` for arXiv link |
| `webpage` | (none) | Use `url` |
| `report` | (none) | No publisher/university field |

Using the wrong field returns 400: "not a valid field for type '...'".

## Web API Write Format

### Create items:
```
POST /users/{id}/items
Content-Type: application/json
[{"itemType": "book", "title": "...", ...}]
```

Response:
```json
{
  "successful": {"0": {"key": "ABC123", "version": 1}},
  "success": {"0": "ABC123"},
  "failed": {},
  "unchanged": {}
}
```

### Create collection:
```
POST /users/{id}/collections
Content-Type: application/json
[{"name": "Collection Name"}]
```

### Add item to collection (CRITICAL):
```
POST /users/{id}/collections/{key}/items
Content-Type: text/plain
ABC123
```
- Body is the **raw item key** as text/plain — NOT JSON, NOT an array.
- Returns HTTP 204 on success.
- JSON formats (`{"items": [...]}`, `["key"]`, etc.) return 400 or 500.

## Server Location

`~/.hermes/mcp-servers/zotero/server.py`

## Configuration (config.yaml)

```yaml
mcp_servers:
  zotero:
    command: python3
    args:
      - /home/jeanhuit/.hermes/mcp-servers/zotero/server.py
    enabled: true
```

The `ZOTERO_TOKEN` env var is inherited from the Hermes process environment.
