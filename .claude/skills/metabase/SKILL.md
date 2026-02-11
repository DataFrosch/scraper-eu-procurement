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

## Dashboard Filters

Dashboard filters connect dashboard-level parameter widgets to template tags in native SQL cards.

### 1. Add template tags to SQL queries

Use `{{tag_name}}` in SQL. Wrap in `[[ ]]` to make the clause optional (omitted when no filter value provided):

```sql
SELECT * FROM awards a
JOIN contracts c ON a.contract_id = c.id
JOIN ted_documents d ON c.ted_doc_id = d.doc_id
WHERE 1=1
  [[AND d.source_country = {{country}}]]
  [[AND EXTRACT(YEAR FROM d.publication_date) = {{year}}]]
```

Template tags are defined in `dataset_query.native.template-tags`:

```json
{
  "dataset_query": {
    "database": 2,
    "type": "native",
    "native": {
      "query": "... WHERE 1=1 [[AND d.source_country = {{country}}]]",
      "template-tags": {
        "country": {
          "id": "unique-uuid-here",
          "name": "country",
          "display-name": "Country",
          "type": "text"
        }
      }
    }
  }
}
```

**Template tag types:**

| `type` | SQL usage | Value format |
|---|---|---|
| `text` | `= {{tag}}` | String (auto-quoted) |
| `number` | `>= {{tag}}` | Number (no quoting) |
| `date` | `>= {{tag}}` | `"YYYY-MM-DD"` |
| `dimension` | `WHERE {{tag}}` (full clause generated) | Depends on widget-type |

**Dimension (field filter)** is more powerful but requires a field ID:

```json
{
  "country_filter": {
    "id": "uuid-here",
    "name": "country_filter",
    "display-name": "Country",
    "type": "dimension",
    "dimension": ["field", FIELD_ID, null],
    "widget-type": "string/="
  }
}
```

### 2. Add parameters to a dashboard

Parameters define the filter widgets at the top of the dashboard:

```json
{
  "parameters": [
    {
      "id": "param_country",
      "name": "Country",
      "slug": "country",
      "type": "string/=",
      "sectionId": "string",
      "required": false,
      "default": null,
      "isMultiSelect": true
    },
    {
      "id": "param_year",
      "name": "Year",
      "slug": "year",
      "type": "number/=",
      "sectionId": "number",
      "isMultiSelect": false
    },
    {
      "id": "param_date",
      "name": "Date Range",
      "slug": "date_range",
      "type": "date/all-options",
      "sectionId": "date"
    }
  ]
}
```

**Parameter fields:**

| Field | Description |
|---|---|
| `id` | Unique string — referenced by `parameter_mappings` |
| `name` | Display label |
| `slug` | URL-safe key (used in `?slug=value` URLs) |
| `type` | Widget type (see table below) |
| `sectionId` | Groups in UI sidebar |
| `required` | If `true`, dashboard won't load without a value |
| `default` | Pre-filled value: string, number, or array (e.g., `["DE", "FR"]`) |
| `isMultiSelect` | `true` (default) allows selecting multiple values, `false` for single-select |
| `values_query_type` | `"list"` for dropdown, `"search"` for search box, `null` for text input |
| `values_source_type` | `"card"` (from a saved question), `"static-list"`, or `null` (from connected field) |
| `values_source_config` | Config for dropdown source (see below) |

**Dropdown from a saved question:**

```json
{
  "values_query_type": "list",
  "values_source_type": "card",
  "values_source_config": {
    "card_id": 50,
    "value_field": ["field", "column_name", {"base-type": "type/Text"}]
  }
}
```

**Dropdown from a static list:**

```json
{
  "values_query_type": "list",
  "values_source_type": "static-list",
  "values_source_config": {
    "values": [["DE", "Germany"], ["FR", "France"], ["PL", "Poland"]]
  }
}
```

**Parameter types:**

| sectionId | Types |
|---|---|
| `date` | `date/single`, `date/range`, `date/relative`, `date/month-year`, `date/quarter-year`, `date/all-options` |
| `string` | `string/=`, `string/!=`, `string/contains`, `string/does-not-contain`, `string/starts-with`, `string/ends-with` |
| `number` | `number/=`, `number/!=`, `number/between`, `number/>=`, `number/<=` |
| `location` | `location/city`, `location/state`, `location/zip_code`, `location/country` |
| `id` | `id` |
| `temporal-unit` | `temporal-unit` — lets users change date grouping (day/week/month/quarter/year) |

### 3. Wire filters to cards via parameter_mappings

Each dashcard has a `parameter_mappings` array connecting dashboard parameters to card template tags:

```json
{
  "parameter_mappings": [
    {
      "parameter_id": "param_country",
      "card_id": 42,
      "target": ["variable", ["template-tag", "country"]]
    }
  ]
}
```

**Target format depends on card type:**

| Tag type | Target format |
|---|---|
| `text`, `number`, `date` | `["variable", ["template-tag", "tag_name"]]` |
| `dimension` | `["dimension", ["template-tag", "tag_name"]]` |

### Complete filter example

```bash
# 1. Create card with template tags
.claude/skills/metabase/mb.sh POST /api/card '{
  "name": "Awards by Country (Filtered)",
  "collection_id": 6,
  "dataset_query": {
    "database": 2,
    "type": "native",
    "native": {
      "query": "SELECT d.source_country, COUNT(*) as cnt FROM awards a JOIN contracts c ON a.contract_id = c.id JOIN ted_documents d ON c.ted_doc_id = d.doc_id WHERE 1=1 [[AND d.source_country = {{country}}]] GROUP BY 1 ORDER BY 2 DESC",
      "template-tags": {
        "country": {
          "id": "f1a2b3c4-0000-0000-0000-000000000001",
          "name": "country",
          "display-name": "Country",
          "type": "text"
        }
      }
    }
  },
  "display": "row",
  "visualization_settings": {"graph.dimensions": ["source_country"], "graph.metrics": ["cnt"]}
}'

# 2. Create dashboard with parameter
.claude/skills/metabase/mb.sh POST /api/dashboard '{
  "name": "Filtered Dashboard",
  "collection_id": 6,
  "parameters": [
    {"id": "p_country", "name": "Country", "slug": "country", "type": "string/=", "sectionId": "string"}
  ]
}'

# 3. Add card to dashboard with parameter mapping
.claude/skills/metabase/mb.sh PUT /api/dashboard/{DASH_ID}/cards '{
  "cards": [{
    "id": -1,
    "card_id": CARD_ID,
    "row": 0, "col": 0, "size_x": 24, "size_y": 8,
    "series": [],
    "visualization_settings": {},
    "parameter_mappings": [
      {"parameter_id": "p_country", "card_id": CARD_ID, "target": ["variable", ["template-tag", "country"]]}
    ]
  }],
  "ordered_tabs": []
}'
```

### Gotchas

- The `name` in a template tag, its key in the `template-tags` object, and the `{{name}}` in SQL must all match exactly.
- `PUT /api/card/:id` requires the **full** `dataset_query` including SQL — you can't patch just the template-tags.
- Basic `date` tags only support a single date picker. For range/relative date filters, use two `date` tags (start/end) or a `dimension` tag.
- Dashboard parameters can exist without being wired to any card — they render as widgets but do nothing until mapped.

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
