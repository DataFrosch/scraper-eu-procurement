# Click Behavior (Crossfiltering & Navigation)

Click behavior is configured on the **dashcard** (not the saved card) via `visualization_settings.click_behavior` in the `PUT /api/dashboard/:id/cards` payload.

## Click behavior types

| `type` | Action |
|---|---|
| `"crossfilter"` | Click sets dashboard filter(s) |
| `"link"` | Navigate to another dashboard, question, or URL |
| `"actionMenu"` | Default drill-through menu (same as omitting click_behavior) |

## Chart-level vs column-level

- **Charts** (bar, line, pie, row, etc.): `click_behavior` goes directly in the dashcard's `visualization_settings`
- **Tables**: `click_behavior` goes per-column inside `column_settings`, keyed by `["name","column_name"]` for native SQL cards

## Crossfilter: click chart element → set dashboard filter

The `parameterMapping` maps a column from the clicked element to a dashboard filter parameter:

```json
{
  "visualization_settings": {
    "click_behavior": {
      "type": "crossfilter",
      "parameterMapping": {
        "DASHBOARD_PARAM_ID": {
          "id": "DASHBOARD_PARAM_ID",
          "source": {
            "type": "column",
            "id": "column_name",
            "name": "Column Display Name"
          },
          "target": {
            "type": "parameter",
            "id": "DASHBOARD_PARAM_ID"
          }
        }
      }
    }
  }
}
```

- `source.id` is the column name from the query result (lowercase for native SQL)
- `source.type` is `"column"` (value comes from the clicked element)
- `target.id` matches the dashboard parameter `id`
- The key in `parameterMapping` also matches the dashboard parameter `id`

**Example**: click a bar on the country chart → set the Country filter:

```json
{
  "id": 44,
  "card_id": 44,
  "visualization_settings": {
    "click_behavior": {
      "type": "crossfilter",
      "parameterMapping": {
        "p_country": {
          "id": "p_country",
          "source": {"type": "column", "id": "country", "name": "Country"},
          "target": {"type": "parameter", "id": "p_country"}
        }
      }
    }
  }
}
```

## Crossfilter on table columns

For tables, set click behavior per column in `column_settings`:

```json
{
  "visualization_settings": {
    "column_settings": {
      "[\"name\",\"country\"]": {
        "click_behavior": {
          "type": "crossfilter",
          "parameterMapping": {
            "p_country": {
              "id": "p_country",
              "source": {"type": "column", "id": "country", "name": "Country"},
              "target": {"type": "parameter", "id": "p_country"}
            }
          }
        }
      }
    }
  }
}
```

## Navigate to another dashboard

```json
{
  "click_behavior": {
    "type": "link",
    "linkType": "dashboard",
    "targetId": 5,
    "parameterMapping": {
      "target_param_id": {
        "id": "target_param_id",
        "source": {"type": "column", "id": "country", "name": "Country"},
        "target": {"type": "parameter", "id": "target_param_id"}
      }
    }
  }
}
```

- `targetId` is the destination dashboard ID
- `target.id` is a parameter ID from the **destination** dashboard's `parameters` array

## Navigate to a URL

```json
{
  "click_behavior": {
    "type": "link",
    "linkType": "url",
    "linkTemplate": "https://example.com/details/{{country}}/{{year}}"
  }
}
```

`{{column_name}}` placeholders are replaced with values from the clicked row.
