---
name: metabase
description: Create Metabase visualizations and dashboards via the REST API using curl. Use when asked to build charts, dashboards, questions, or analyze data visually in Metabase.
argument-hint: "[what to create or do]"
allowed-tools: Bash, Read, Grep, Glob
---

# Metabase API Skill

Build visualizations and dashboards in Metabase using curl against the REST API.

**User request:** $ARGUMENTS

## Existing state

Collections:
!`.claude/skills/metabase/mb.sh GET /api/collection 2>/dev/null | jq -r '.[] | select(.personal_owner_id == null and .id != 1) | "\(.id): \(.name)"' 2>/dev/null || echo "(could not fetch collections)"`

Dashboards:
!`.claude/skills/metabase/mb.sh GET /api/dashboard 2>/dev/null | jq -r '.[] | "\(.id): \(.name) [collection: \(.collection_id)]"' 2>/dev/null || echo "(could not fetch dashboards)"`

## API helper

All API calls go through `mb.sh` (handles auth from `.env` automatically):

```bash
.claude/skills/metabase/mb.sh GET /api/endpoint
.claude/skills/metabase/mb.sh POST /api/endpoint '{"json":...}'
.claude/skills/metabase/mb.sh PUT /api/endpoint '{"json":...}'
```

## Workflow

1. **Inspect schema** if you need to discover tables/columns:
   ```bash
   .claude/skills/metabase/mb.sh GET "/api/database/DB_ID/metadata?include_hidden=false" | jq '.tables[] | {id, name, schema}'
   ```

2. **Test query** before saving — catches SQL errors early:
   ```bash
   .claude/skills/metabase/mb.sh POST /api/dataset '{"database": DB_ID, "type": "native", "native": {"query": "SELECT ..."}}' | jq '.data.rows'
   ```

3. **Create card** (saved question with visualization):
   ```bash
   .claude/skills/metabase/mb.sh POST /api/card '{
     "name": "Card Name",
     "collection_id": COLLECTION_ID_OR_NULL,
     "dataset_query": {"database": DB_ID, "type": "native", "native": {"query": "SELECT ..."}},
     "display": "bar",
     "visualization_settings": {}
   }'
   ```

4. **Create dashboard** (if needed):
   ```bash
   .claude/skills/metabase/mb.sh POST /api/dashboard '{"name": "Dashboard Name", "collection_id": COLLECTION_ID_OR_NULL, "parameters": []}'
   ```

5. **Add cards to dashboard** — uses a 24-column grid, negative IDs for new cards:
   ```bash
   .claude/skills/metabase/mb.sh PUT /api/dashboard/{DASH_ID}/cards '{
     "cards": [{"id": -1, "card_id": CARD_ID, "row": 0, "col": 0, "size_x": 12, "size_y": 8, "series": [], "visualization_settings": {}, "parameter_mappings": []}],
     "ordered_tabs": []
   }'
   ```

**IMPORTANT**: `PUT /api/dashboard/:id/cards` replaces ALL cards. To add to an existing dashboard, first `GET /api/dashboard/{id}`, include all existing `ordered_cards`, then add new ones with negative IDs.

## Visualization settings

For Metabase-specific `display` values and their `visualization_settings` JSON keys, see [visualization.md](visualization.md).

## Collections

Create a collection to organize related cards and dashboards:

```bash
.claude/skills/metabase/mb.sh POST /api/collection '{"name": "Collection Name", "color": "#509EE3"}'
```

## Text cards on dashboards

Add section headers or descriptions:

```json
{
  "id": -99, "card_id": null,
  "row": 0, "col": 0, "size_x": 24, "size_y": 2,
  "visualization_settings": {
    "virtual_card": {"display": "text", "visualization_settings": {}, "dataset_query": {}},
    "text": "## Section Title\nDescription text"
  },
  "parameter_mappings": []
}
```

## Dashboard filters

For adding filter widgets that connect to SQL template tags, see [filters.md](filters.md).

## Click behavior (crossfiltering & navigation)

For configuring what happens when users click chart elements, see [click-behavior.md](click-behavior.md).

## Other useful endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/card/:id` | Get card details |
| `PUT` | `/api/card/:id` | Update a card |
| `DELETE` | `/api/card/:id` | Delete a card |
| `GET` | `/api/dashboard/:id` | Get dashboard with all cards |
| `PUT` | `/api/dashboard/:id` | Update dashboard metadata |
| `DELETE` | `/api/dashboard/:id` | Delete a dashboard |
| `GET` | `/api/collection` | List collections |
| `GET` | `/api/collection/:id/items` | List items in a collection |
| `POST` | `/api/card/:id/query` | Execute a saved card's query |

## Tips

- **Always use native SQL** for creating cards via API (MBQL is unstable across versions)
- **Test queries first** with `POST /api/dataset` before saving as a card
- **Pipe through `jq`** for readable output: `| jq '.id'` to extract IDs
- **visualization_settings is largely undocumented** — to discover settings for a specific chart type, configure it in the Metabase UI and inspect the PUT request in browser dev tools
- **POST /api/dataset returns max 2000 rows** — use `POST /api/dataset/:export-format` (json/csv/xlsx) for larger exports
