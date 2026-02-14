# Germany (DE)

**Feasibility: Tier 2**

## Portals

1. **service.bund.de**: https://www.service.bund.de/ (centralized tender search)
2. **DTVP** (Deutsches Vergabeportal): https://en.dtvp.de/
3. **Datenservice oeffentlicher Einkauf**: https://oeffentlichevergabe.de (eForms-based data service)
4. **bund.dev**: https://bund.dev/ (federal API portal)
5. **GitHub**: https://github.com/bundesAPI (Federal Open Data Office)

## Data Access

- **Method**: eForms data service + bund.dev API portal
- **Format**: JSON, CSV, XML
- **Auth**: Open
- **OCDS**: Emerging (via XBeschaffung bridge to OCDS)
- **OCP Registry**: https://data.open-contracting.org/en/publication/136
- **Download sizes**: 2024 data = 166 MB, 2025 data = 190 MB (JSON/CSV)

## Coverage

Federal, state, and local procurement. Fragmented across multiple platforms.

## Language

German

## Notes

- **XBeschaffung Standard**: New German data standard implementing eForms fields, interoperable with OCDS
- Historically very fragmented landscape with multiple competing platforms (vergabe24.de, evergabe-online.de, etc.)
- The oeffentlichevergabe.de data service is relatively new and consolidating
- Existing Apify scraper: https://apify.com/stephaniehhnbrg/public-tender-scraper-germany
- Rapidly improving with eForms/XBeschaffung — main challenge is historical fragmentation
