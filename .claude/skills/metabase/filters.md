# Dashboard Filters

Dashboard filters connect dashboard-level parameter widgets to template tags in native SQL cards.

## 1. Add template tags to SQL queries

Use `{{tag_name}}` in SQL. Wrap in `[[ ]]` to make the clause optional (omitted when no filter value provided):

```sql
SELECT * FROM awards a
JOIN contracts c ON a.contract_id = c.id
JOIN documents d ON c.doc_id = d.doc_id
WHERE 1=1
  [[AND d.source_country = {{country}}]]
  [[AND EXTRACT(YEAR FROM d.publication_date) = {{year}}]]
```

Template tags are defined in `dataset_query.native.template-tags`:

```json
{
  "dataset_query": {
    "database": DB_ID,
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

### Template tag types

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

## 2. Add parameters to a dashboard

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

### Parameter fields

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

### Parameter types

| sectionId | Types |
|---|---|
| `date` | `date/single`, `date/range`, `date/relative`, `date/month-year`, `date/quarter-year`, `date/all-options` |
| `string` | `string/=`, `string/!=`, `string/contains`, `string/does-not-contain`, `string/starts-with`, `string/ends-with` |
| `number` | `number/=`, `number/!=`, `number/between`, `number/>=`, `number/<=` |
| `location` | `location/city`, `location/state`, `location/zip_code`, `location/country` |
| `id` | `id` |
| `temporal-unit` | `temporal-unit` — lets users change date grouping (day/week/month/quarter/year) |

## 3. Wire filters to cards via parameter_mappings

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

## Complete filter example

```bash
# 1. Create card with template tags
.claude/skills/metabase/mb.sh POST /api/card '{
  "name": "Awards by Country (Filtered)",
  "collection_id": 6,
  "dataset_query": {
    "database": DB_ID,
    "type": "native",
    "native": {
      "query": "SELECT d.source_country, COUNT(*) as cnt FROM awards a JOIN contracts c ON a.contract_id = c.id JOIN documents d ON c.doc_id = d.doc_id WHERE 1=1 [[AND d.source_country = {{country}}]] GROUP BY 1 ORDER BY 2 DESC",
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

## Gotchas

- The `name` in a template tag, its key in the `template-tags` object, and the `{{name}}` in SQL must all match exactly.
- `PUT /api/card/:id` requires the **full** `dataset_query` including SQL — you can't patch just the template-tags.
- Basic `date` tags only support a single date picker. For range/relative date filters, use two `date` tags (start/end) or a `dimension` tag.
- Dashboard parameters can exist without being wired to any card — they render as widgets but do nothing until mapped.
