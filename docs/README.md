# EU National Procurement Portals

Research date: 2026-02-14

## Goal

Build per-country scrapers that pull below-threshold procurement data from national portals into our own infrastructure. TED already covers above-threshold EU procurement — national portals add the rest. One scraper per country, each mapping to our shared schema.

## Feasibility Tiers

- **Tier 1**: Public API with documentation, feasible for autonomous scraping
- **Tier 2**: API or structured data exists but needs registration, has poor docs, or requires extra effort
- **Tier 3**: Web-only, restricted access, or very difficult to scrape programmatically

## Summary Table

| Country | Code | Portal | Access Method | OCDS | Tier |
|---------|------|--------|--------------|------|------|
| Austria | AT | ausschreibungen.usp.gv.at | Open data portal | No | 2 |
| Belgium | BE | publicprocurement.be | Web-only (registration) | No | 3 |
| Bulgaria | BG | app.eop.bg | Open data portal | No | 2 |
| Croatia | HR | eojn.hr | Monthly OCDS export | Partial | 2 |
| Cyprus | CY | eprocurement.gov.cy | Web-only (registration) | No | 3 |
| Czech Republic | CZ | vvz.nipez.cz | XML open data | No | 2 |
| Denmark | DK | udbud.dk | Web-only | No | 3 |
| Estonia | EE | riigihanked.riik.ee | Open data portal | No | 2 |
| Finland | FI | hankintailmoitukset.fi | REST API (Azure APIM) | No | 1 |
| France | FR | boamp.fr + data.gouv.fr | REST API + bulk download | No (own standard) | 1 |
| Germany | DE | oeffentlichevergabe.de | eForms data service | Emerging | 2 |
| Greece | GR | eprocurement.gov.gr | REST API (Basic Auth) | No | 2 |
| Hungary | HU | kozbeszerzes.hu | CSV export | No | 3 |
| Ireland | IE | etenders.gov.ie | API + open data | No | 2 |
| Italy | IT | dati.anticorruzione.it | REST API (Swagger) | **Yes** | 1 |
| Latvia | LV | eis.gov.lv | Open data portal (CSV) | No | 2 |
| Lithuania | LT | viesiejipirkimai.lt | API + downloads | **Yes** | 1 |
| Luxembourg | LU | pmp.b2g.etat.lu | Limited open data | No | 3 |
| Malta | MT | etenders.gov.mt | Web-only (registration) | No | 3 |
| Netherlands | NL | tenderned.nl | REST API (Swagger) | **Yes** | 1 |
| Poland | PL | ezamowienia.gov.pl | REST API | No | 1 |
| Portugal | PT | base.gov.pt | Bulk download (OCDS) | **Yes** | 1 |
| Romania | RO | e-licitatie.ro | OCDS API | Partial | 2 |
| Slovakia | SK | uvo.gov.sk | CSV / SQL dump | No | 2 |
| Slovenia | SI | enarocanje.si | OCDS via OPSI | **Yes** | 2 |
| Spain | ES | contrataciondelestado.es | Atom/XML feed | No (CODICE) | 2 |
| Sweden | SE | upphandlingsmyndigheten.se | CSV statistics | No | 3 |
| **UK** | GB | find-tender.service.gov.uk | REST API (OCDS) | **Yes** | 1 |
| **Norway** | NO | doffin.no | REST API (Azure APIM) | No | 1 |
| **Switzerland** | CH | simap.ch | API (new 2024) | No | 2 |

## By Tier

**Tier 1** (9): FI, FR, IT, LT, NL, PL, PT, GB, NO
**Tier 2** (14): AT, BG, HR, CZ, EE, DE, GR, IE, LV, RO, SK, SI, ES, CH
**Tier 3** (7): BE, CY, DK, HU, LU, MT, SE

## OCDS Adopters

Full: IT, LT, NL, PT, GB
Partial: HR, RO, SI

## Useful References

- **OCP Data Registry** — registry of OCDS publishers at data.open-contracting.org
- **Kingfisher Collect** — Scrapy-based OCDS collector with existing spiders, useful as reference implementations

## Standards

- **OCDS** (Open Contracting Data Standard) — common schema for procurement lifecycle
- **eForms** — EU standard for procurement notices (mandatory since Oct 2023)
- **CODICE** — Spanish national XML standard
- **DECP** — French national schema for essential procurement data
