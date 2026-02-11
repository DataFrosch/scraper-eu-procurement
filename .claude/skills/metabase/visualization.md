# Visualization Reference

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
