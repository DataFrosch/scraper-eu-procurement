# EU National Procurement Portals

Research date: 2026-02-14
Schema mapping completed: 2026-02-15

## Goal

Build per-country scrapers that pull below-threshold procurement data from national portals into our own infrastructure. TED already covers above-threshold EU procurement — national portals add the rest. One scraper per country, each mapping to our shared schema.

Each country's `.md` file contains a `## Schema Mapping` section with field-by-field mappings to our Pydantic schema (`awards/schema.py`), code normalization tables, and implementation notes.

## Feasibility Tiers

- **Tier 1**: Public API with documentation, feasible for autonomous scraping
- **Tier 2**: API or structured data exists but needs registration, has poor docs, or requires extra effort
- **Tier 3**: Web-only, restricted access, or very difficult to scrape programmatically

## Summary Table

| Country | Code | Portal | Data Format | Parser Strategy | Tier |
|---------|------|--------|-------------|-----------------|------|
| Austria | AT | ausschreibungen.usp.gv.at | Custom German XML | Custom (federated 3-layer) | 2 |
| Belgium | BE | publicprocurement.be | Unknown | Needs investigation | 3 |
| Bulgaria | BG | app.eop.bg | CSV (Bulgarian) | Custom CSV (portal blocks access) | 2 |
| Croatia | HR | eojn.hr | OCDS JSON | Shared OCDS parser | 2 |
| Cyprus | CY | eprocurement.gov.cy | HTML only | Not feasible yet | 3 |
| Czech Republic | CZ | vvz.nipez.cz | Custom XML/CSV | Custom (ref: kokes/od) | 2 |
| Denmark | DK | udbud.dk | SPA (hidden API?) | Needs reverse-engineering | 3 |
| Estonia | EE | riigihanked.riik.ee | eForms XML + TED v2 XML | **Reuse existing parsers** | 2 |
| Finland | FI | hankintailmoitukset.fi | eForms XML (SDK 1.13) | **Reuse `eforms_ubl.py`** | 1 |
| France | FR | data.gouv.fr (DECP) | Parquet/CSV (tabular) | Custom tabular parser | 1 |
| Germany | DE | oeffentlichevergabe.de | eForms XML | **Reuse `eforms_ubl.py`** | 2 |
| Greece | GR | eprocurement.gov.gr | Custom JSON API | Custom (Basic Auth, 180-day windows) | 2 |
| Hungary | HU | kozbeszerzes.hu | Static CSV | Limited (data stopped 2022) | 3 |
| Ireland | IE | etenders.gov.ie | CSV (single file) | Custom CSV | 2 |
| Italy | IT | dati.anticorruzione.it | OCDS JSON | Shared OCDS parser | 1 |
| Latvia | LV | eis.gov.lv | CSV (Latvian, 2 files) | Custom CSV (join on ID) | 2 |
| Lithuania | LT | opentender.eu/lt | OCDS JSONL | Shared OCDS parser | 1 |
| Luxembourg | LU | pmp.b2g.etat.lu | CSV (single agency) | Not feasible (coverage too limited) | 3 |
| Malta | MT | etenders.gov.mt | HTML only | Not feasible yet | 3 |
| Netherlands | NL | tenderned.nl | OCDS JSONL or eForms XML | Shared OCDS parser or reuse eForms | 1 |
| Poland | PL | ezamowienia.gov.pl | Custom JSON API | Custom (API needs exploration) | 1 |
| Portugal | PT | base.gov.pt | OCDS JSON (CKAN) | Shared OCDS parser | 1 |
| Romania | RO | e-licitatie.ro | OCDS JSON | Shared OCDS parser | 2 |
| Slovakia | SK | uvo.gov.sk | JSON API or OCDS JSONL | Custom API or shared OCDS | 2 |
| Slovenia | SI | enarocanje.si | OCDS JSON (TBFY) | Shared OCDS parser | 2 |
| Spain | ES | contrataciondelestado.es | CODICE XML (Atom feed) | Custom UBL-based parser | 2 |
| Sweden | SE | upphandlingsmyndigheten.se | None (write-only API) | **Not implementable** | 3 |
| **UK** | GB | find-tender.service.gov.uk | OCDS JSON | Shared OCDS parser | 1 |
| **Norway** | NO | doffin.no | eForms XML | **Reuse `eforms_ubl.py`** | 1 |
| **Switzerland** | CH | simap.ch | Custom JSON API | Custom (OAuth 2.0/PKCE) | 2 |

## By Tier

**Tier 1** (9): FI, FR, IT, LT, NL, PL, PT, GB, NO
**Tier 2** (14): AT, BG, HR, CZ, EE, DE, GR, IE, LV, RO, SK, SI, ES, CH
**Tier 3** (7): BE, CY, DK, HU, LU, MT, SE

## Implementation Groups

### Reuse existing parsers (easiest — download logic only)
EE (both `eforms_ubl.py` and `ted_v2.py`), FI, NO, DE (eForms), NL (eForms path)

### Shared OCDS parser needed
IT, LT, PT, GB, HR, RO, SI, NL (OCDS path), SK (fallback)

Each has quirks (party resolution, country name languages, data quality) but the core
parsing logic is the same: OCDS JSON → `AwardDataModel`.

### Custom parsers needed
FR (DECP tabular), PL (JSON API), ES (CODICE XML), AT (federated German XML),
CZ (custom XML/CSV), GR (JSON API), BG (CSV), LV (CSV), IE (CSV), CH (JSON API),
SK (UVOstat JSON API)

### Not feasible yet
SE (no read API), LU (single agency), MT/CY (HTML-only, auth-gated),
BE (unknown), DK (SPA, needs reverse-engineering), HU (stale CSV, stopped 2022)

## Cross-cutting Findings

### Schema gaps (flagged by nearly every country)
- **Organization identifiers** (SIRET, KVK, NIF, NIP, ICO, OIB, EIK, Y-tunnus, UID, CVR, etc.) — consistently available, not in schema. High value for entity deduplication.
- **Award dates** — available in most portals, not in schema
- **Lot-level data** — many portals structure data by lot
- **Contract periods/duration** — widely available
- **Estimated/tender values** — useful for analysis

### Parser notes
- **`tenders_received`** is available in eForms but our existing parser doesn't extract it yet
- **Country code normalization** needed for OCDS portals (free-text names in local languages → ISO alpha-2)
- **Currency transitions**: HR (HRK→EUR 2023), LT (LTL→EUR 2015), LV (LVL→EUR 2014)

## OCDS Adopters

Full: IT, LT, NL, PT, GB
Partial: HR, RO, SI

## Useful References

- **OCP Data Registry** — registry of OCDS publishers at data.open-contracting.org
- **Kingfisher Collect** — Scrapy-based OCDS collector with existing spiders, useful as reference implementations
- **kokes/od** — Python parser for Czech ISVZ data
- **OffeneVergaben-Scraper** — PHP/Laravel scraper for Austrian Kerndaten

## Standards

- **OCDS** (Open Contracting Data Standard) — common schema for procurement lifecycle
- **eForms** — EU standard for procurement notices (mandatory since Oct 2023)
- **CODICE** — Spanish national XML standard (UBL-based)
- **DECP** — French national schema for essential procurement data
