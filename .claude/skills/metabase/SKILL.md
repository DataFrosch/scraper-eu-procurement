---
name: metabase
description: Create Metabase visualizations and dashboards via the REST API using curl. Use when asked to build charts, dashboards, questions, or analyze data visually in Metabase.
argument-hint: "[what to create or do]"
---

# Metabase API Skill

Build visualizations and dashboards in Metabase using curl against the REST API.

## Setup

Use the `mb.sh` helper script (handles auth and headers automatically):

```bash
.claude/skills/metabase/mb.sh GET /api/endpoint                  # GET request
.claude/skills/metabase/mb.sh POST /api/endpoint '{"json":...}'  # POST with body
.claude/skills/metabase/mb.sh PUT /api/endpoint '{"json":...}'   # PUT with body
```

It loads `METABASE_URL` and `METABASE_API_KEY` from `.env` automatically.

## Workflow

### 1. Discover the database ID

```bash
.claude/skills/metabase/mb.sh GET /api/database | jq '.data[] | {id, name, engine}'
```

### 2. Inspect the schema

```bash
.claude/skills/metabase/mb.sh GET "/api/database/{DB_ID}/metadata?include_hidden=false" | jq '.tables[] | {id, name, schema}'
```

### 3. Run a test query

```bash
.claude/skills/metabase/mb.sh POST /api/dataset '{"database": 2, "type": "native", "native": {"query": "SELECT 1"}}' | jq '.data.rows'
```

### 4. Create a card (saved question with visualization)

```bash
.claude/skills/metabase/mb.sh POST /api/card '{
  "name": "Card Name",
  "description": "What this shows",
  "collection_id": COLLECTION_ID_OR_NULL,
  "dataset_query": {
    "database": DB_ID,
    "type": "native",
    "native": {"query": "SELECT ..."}
  },
  "display": "bar",
  "visualization_settings": {}
}'
```

### 5. Create a dashboard

```bash
.claude/skills/metabase/mb.sh POST /api/dashboard '{
  "name": "Dashboard Name",
  "description": "What this dashboard shows",
  "collection_id": COLLECTION_ID_OR_NULL,
  "parameters": []
}'
```

### 6. Add cards to the dashboard

Uses a 24-column grid. Use `PUT` with **all** cards at once (this replaces the full card set). New cards use negative IDs.

```bash
.claude/skills/metabase/mb.sh PUT /api/dashboard/{DASHBOARD_ID}/cards '{
  "cards": [
    {
      "id": -1,
      "card_id": CARD_ID,
      "row": 0, "col": 0,
      "size_x": 12, "size_y": 8,
      "series": [],
      "visualization_settings": {},
      "parameter_mappings": []
    }
  ],
  "ordered_tabs": []
}'
```

**IMPORTANT**: To add cards to an existing dashboard, first `GET /api/dashboard/{id}` to retrieve current `ordered_cards`, then include them all in the PUT along with new cards (using negative IDs for new ones). Omitting existing cards deletes them.

## Display Types

| `display` value | Use for |
|---|---|
| `bar` | Categorical comparisons |
| `line` | Trends over time |
| `area` | Trends with volume emphasis |
| `row` | Horizontal bar (ranked lists) |
| `pie` | Part-of-whole |
| `scalar` | Single KPI number |
| `smartscalar` | KPI with trend |
| `table` | Detailed data |
| `pivot` | Cross-tabulation |
| `combo` | Mixed bar + line |
| `scatter` | Correlation |
| `funnel` | Conversion steps |
| `gauge` | Progress toward goal |
| `progress` | Simple progress bar |
| `waterfall` | Cumulative changes |
| `map` | Geographic data |

## Visualization Settings by Chart Type

**Column names in native queries are lowercase** (e.g., SQL `count(*) as total` becomes `"total"` in settings). PostgreSQL folds identifiers to lowercase.

### Bar / Line / Area

```json
{
  "graph.dimensions": ["year"],
  "graph.metrics": ["count"],
  "graph.show_values": true,
  "graph.x_axis.title_text": "Year",
  "graph.y_axis.title_text": "Count",
  "graph.x_axis.scale": "ordinal",
  "stackable.stack_type": null
}
```

`stackable.stack_type`: `null` (default), `"stacked"`, `"normalized"` (100%).

### Pie

```json
{
  "pie.dimension": "category",
  "pie.metric": "count",
  "pie.show_legend": true,
  "pie.show_total": true,
  "pie.percent_visibility": "inside"
}
```

### Scalar

```json
{
  "scalar.field": "total"
}
```

### Table

```json
{
  "column_settings": {
    "[\"name\",\"value\"]": {
      "number_style": "currency",
      "currency": "EUR"
    }
  }
}
```

### Row (horizontal bar)

```json
{
  "graph.dimensions": ["category"],
  "graph.metrics": ["count"]
}
```

### Series customization (bar/line/area)

```json
{
  "series_settings": {
    "count": {"color": "#509EE3", "title": "Custom Name"}
  }
}
```

## Collections

Create a collection to organize related cards and dashboards:

```bash
.claude/skills/metabase/mb.sh POST /api/collection '{"name": "Collection Name", "color": "#509EE3"}'
```

## Text Cards on Dashboards

Add section headers or descriptions to dashboards:

```json
{
  "id": -99,
  "card_id": null,
  "row": 0, "col": 0,
  "size_x": 24, "size_y": 2,
  "visualization_settings": {
    "virtual_card": {
      "display": "text",
      "visualization_settings": {},
      "dataset_query": {}
    },
    "text": "## Section Title\nDescription text"
  },
  "parameter_mappings": []
}
```

## Other Useful Endpoints

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

## Project-Specific Notes

- **tedawards database ID**: `2` (ID 1 is the Metabase sample H2 database)
- **Column names are lowercase**: PostgreSQL folds unquoted identifiers to lowercase. Use `"year"` not `"YEAR"` in visualization_settings.
- **Award value filtering**: TED data contains nonsense monetary values (up to 10^20). For sane analysis, filter with `awarded_value >= 1 AND awarded_value < 1000000000`.
- **Cancelled-award markers**: Some "contractors" are actually status labels from non-awarded lots. Filter these in analysis queries: `LOWER(ct.official_name) NOT IN ('infructueux', 'sans suite', 'lot infructueux', 'sans objet', 'no adjudicado')`.

## Tips

- **Always use native SQL** for creating cards via API (MBQL is unstable across versions).
- **Test queries first** with `POST /api/dataset` before saving as a card.
- **Pipe through `jq`** for readable output: `| jq '.id'` to extract IDs.
- **visualization_settings is largely undocumented** — to discover settings for a specific chart type, configure it in the Metabase UI and inspect the PUT request in browser dev tools.
- **POST /api/dataset returns max 2000 rows** — use `POST /api/dataset/:export-format` (json/csv/xlsx) for larger exports.
- **PUT /api/dashboard/:id/cards replaces ALL cards** — to add to an existing dashboard, first GET the dashboard, include all existing cards, then add new ones with negative IDs.
