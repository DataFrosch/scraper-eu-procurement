# Visualization Reference

Settings sourced from Metabase frontend source code (`frontend/src/metabase/visualizations/`). Metabase has no official API docs for these — the source code is the only reference.

## Display Types

| `display` value | Use for |
|---|---|
| `bar` | Categorical comparisons |
| `line` | Trends over time |
| `area` | Trends with volume emphasis |
| `row` | Horizontal bar (ranked lists) |
| `combo` | Mixed bar + line on same chart |
| `pie` | Part-of-whole |
| `scalar` | Single KPI number |
| `smartscalar` | KPI with trend comparison |
| `table` | Detailed data |
| `pivot` | Cross-tabulation |
| `scatter` | Correlation / bubble charts |
| `funnel` | Conversion steps |
| `gauge` | Progress toward goal with ranges |
| `progress` | Simple progress bar |
| `waterfall` | Cumulative changes |
| `map` | Geographic data (region/pin/heat) |
| `sankey` | Flow between categories |

## Visualization Settings by Chart Type

**Column names in native queries are lowercase** (e.g., SQL `count(*) as total` becomes `"total"` in settings). PostgreSQL folds identifiers to lowercase.

### Bar / Line / Area / Combo / Row

These all share the same graph settings. Combo charts additionally use per-series `display` to mix bar + line.

```json
{
  "graph.dimensions": ["year"],
  "graph.metrics": ["count"],
  "graph.show_values": true,
  "graph.x_axis.title_text": "Year",
  "graph.y_axis.title_text": "Count",
  "graph.x_axis.scale": "ordinal",
  "graph.x_axis.axis_enabled": true,
  "graph.y_axis.axis_enabled": true,
  "graph.y_axis.auto_range": true,
  "graph.y_axis.min": 0,
  "graph.y_axis.max": 1000,
  "graph.show_goal": false,
  "graph.goal_value": 100,
  "graph.goal_label": "Target",
  "graph.show_trendline": false,
  "stackable.stack_type": null,
  "graph.label_value_formatting": "auto"
}
```

| Key | Values |
|---|---|
| `stackable.stack_type` | `null` (default), `"stacked"`, `"normalized"` (100%) |
| `graph.x_axis.scale` | `"ordinal"`, `"timeseries"`, `"linear"`, `"pow"`, `"log"` |
| `graph.x_axis.axis_enabled` | `true`, `false`, `"compact"`, `"rotate-45"`, `"rotate-90"` |
| `graph.y_axis.scale` | `"linear"`, `"pow"`, `"log"` |
| `graph.label_value_formatting` | `"auto"`, `"compact"`, `"full"` |

### Scatter

Uses standard graph settings plus:

```json
{
  "graph.dimensions": ["x_col"],
  "graph.metrics": ["y_col"],
  "scatter.bubble": "size_col"
}
```

### Pie

```json
{
  "pie.dimension": "category",
  "pie.metric": "count",
  "pie.show_legend": true,
  "pie.show_total": true,
  "pie.show_labels": false,
  "pie.percent_visibility": "inside",
  "pie.decimal_places": 1,
  "pie.slice_threshold": 2.5,
  "pie.sort_rows": true,
  "pie.colors": {"Category A": "#509EE3", "Category B": "#88BF4D"}
}
```

| Key | Values |
|---|---|
| `pie.percent_visibility` | `"off"`, `"legend"`, `"inside"`, `"both"` |
| `pie.slice_threshold` | Minimum % to show as own slice (smaller grouped into "Other") |

### Scalar

```json
{
  "scalar.field": "total",
  "scalar.compact_primary_number": false
}
```

### SmartScalar (Trend)

```json
{
  "scalar.field": "total",
  "scalar.comparisons": [
    {"id": "1", "type": "previousPeriod"},
    {"id": "2", "type": "staticNumber", "value": 1000, "label": "Target"}
  ],
  "scalar.switch_positive_negative": false,
  "scalar.compact_primary_number": false
}
```

Comparison types: `"previousValue"`, `"previousPeriod"`, `"periodsAgo"`, `"anotherColumn"`, `"staticNumber"`.

### Table

```json
{
  "table.columns": [
    {"name": "col_name", "fieldRef": ["field", "col_name", {"base-type": "type/Text"}], "enabled": true}
  ],
  "column_settings": {
    "[\"name\",\"value\"]": {
      "number_style": "currency",
      "currency": "EUR"
    }
  },
  "table.column_formatting": [],
  "table.pivot": false
}
```

### Pivot Table

```json
{
  "pivot_table.column_split": {
    "rows": ["category"],
    "columns": ["year"],
    "values": ["total"]
  },
  "pivot.show_row_totals": true,
  "pivot.show_column_totals": true
}
```

### Funnel

```json
{
  "funnel.dimension": "step",
  "funnel.metric": "count",
  "funnel.type": "funnel",
  "funnel.rows": [
    {"key": "Step 1", "name": "Step 1", "enabled": true},
    {"key": "Step 2", "name": "Step 2", "enabled": true}
  ]
}
```

`funnel.type`: `"funnel"` (default for single series) or `"bar"` (default for multi-series).

### Gauge

```json
{
  "scalar.field": "value",
  "gauge.segments": [
    {"min": 0, "max": 50, "color": "#ED6E6E", "label": "Low"},
    {"min": 50, "max": 80, "color": "#F9CF48", "label": "Medium"},
    {"min": 80, "max": 100, "color": "#84BB4C", "label": "High"}
  ]
}
```

### Progress

```json
{
  "progress.value": "current",
  "progress.goal": 100,
  "progress.color": "#84BB4C"
}
```

### Waterfall

Uses standard graph data/axis settings plus:

```json
{
  "graph.dimensions": ["month"],
  "graph.metrics": ["change"],
  "waterfall.increase_color": "#88BF4D",
  "waterfall.decrease_color": "#EF8C8C",
  "waterfall.total_color": "#509EE3",
  "waterfall.show_total": true
}
```

### Map

```json
{
  "map.type": "pin",
  "map.pin_type": "markers",
  "map.latitude_column": "lat",
  "map.longitude_column": "lng",
  "map.metric_column": "value"
}
```

| Key | Values |
|---|---|
| `map.type` | `"region"`, `"pin"`, `"grid"` |
| `map.pin_type` | `"tiles"`, `"markers"`, `"heat"`, `"grid"` |

Region maps use `map.region` (`"us_states"`, `"world_countries"`, etc.), `map.dimension`, `map.metric`.

Heat maps additionally support `map.heat.radius`, `map.heat.blur`, `map.heat.min-opacity`, `map.heat.max-zoom`.

### Sankey

```json
{
  "sankey.source": "from_col",
  "sankey.target": "to_col",
  "sankey.value": "amount",
  "sankey.node_align": "justify",
  "sankey.show_edge_labels": false,
  "sankey.edge_color": "source",
  "sankey.label_value_formatting": "auto"
}
```

| Key | Values |
|---|---|
| `sankey.node_align` | `"left"`, `"right"`, `"justify"` |
| `sankey.edge_color` | `"gray"`, `"source"`, `"target"` |
| `sankey.label_value_formatting` | `"auto"`, `"compact"`, `"full"` |

## Series Customization

Per-series settings nested inside `series_settings`, keyed by series name:

```json
{
  "series_settings": {
    "count": {
      "title": "Custom Name",
      "color": "#509EE3",
      "display": "line",
      "axis": "right",
      "show_series_values": true,
      "line.interpolate": "linear",
      "line.style": "solid",
      "line.size": "M",
      "line.marker_enabled": true,
      "line.missing": "interpolate"
    }
  }
}
```

| Key | Values |
|---|---|
| `display` | `"line"`, `"area"`, `"bar"` (for combo charts) |
| `axis` | `null`, `"left"`, `"right"` |
| `line.interpolate` | `"linear"`, `"cardinal"`, `"step-after"` |
| `line.style` | `"solid"`, `"dashed"`, `"dotted"` |
| `line.size` | `"S"`, `"M"`, `"L"` |
| `line.missing` | `"zero"`, `"none"`, `"interpolate"` |
