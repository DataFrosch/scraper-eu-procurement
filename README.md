# Awards Scraper

A Python scraper for EU procurement contract award notices from [TED Europa](https://ted.europa.eu/) and other national procurement portals. Extracts contract award notices from XML-formatted data, covering **January 2011 to present**.

## Quick Start

```bash
# Install dependencies
uv sync

# Start PostgreSQL database
docker compose up -d

# Download packages for a year (skips already downloaded)
uv run awards download --start-year 2024

# Import into database
uv run awards import --start-year 2024
```

Both commands accept `--start-year` and `--end-year` for processing year ranges.

### Configuration

Environment variables (set in `.env`):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://awards:awards@localhost:5432/awards` | PostgreSQL connection string |
| `TED_DATA_DIR` | `./data` | Directory for downloaded packages |
| `LOG_LEVEL` | `INFO` | Logging level |

## Database

PostgreSQL 18 via Docker Compose, managed with SQLAlchemy ORM.

### Schema

- `documents` — Award notice metadata
- `contracting_bodies` — Buyer organizations (deduplicated lookup table)
- `contracts` — Procurement contracts
- `cpv_codes` / `contract_cpv_codes` — CPV classification codes and junction table
- `awards` — Award decisions, values, and tender counts
- `contractors` — Winning companies (deduplicated lookup table)
- `award_contractors` — Award-contractor junction table

### Dump & Restore

```bash
make dump
make restore FILE=dumps/awards_20260211_120000.dump
```

## Data Methodology

- **Entity deduplication**: Contractors and contracting bodies use shared lookup tables with exact-match deduplication (all fields must match). No fuzzy matching — further entity resolution belongs in a separate analysis layer.
- **Monetary values**: Parsed as-is with no size caps. TED contains nonsensical placeholder values (e.g. strings of 9s) — outlier filtering is left to the analysis stage.
- **Language**: All documents processed regardless of language. Names and titles stored in the original submission language.

## Architecture

- **Portals** — Data source modules (`portals/ted/` for TED Europa):
  - Format auto-detection via `try_parse_award()` (reads first 3KB)
  - `ted_v2` — TED 2.0 R2.0.7/R2.0.8/R2.0.9 (2011–2024)
  - `eforms_ubl` — eForms UBL ContractAwardNotice (2025+)
- **Package numbering** — TED uses sequential Official Journal (OJ S) issue numbers, not calendar dates. Format: `{year}{issue:05d}` (e.g. `202400001`). A typical year has ~250 issues. The scraper stops after 10 consecutive 404s.
- **Idempotent imports** — Re-importing a document is a no-op (skipped if `doc_id` exists).
