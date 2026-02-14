# Poland (PL)

**Feasibility: Tier 1**

## Portal

- **Name**: e-Zamowienia / BZP (Biuletyn Zamowien Publicznych)
- **URL**: https://ezamowienia.gov.pl/en/ (platform) / https://bzp.uzp.gov.pl/ (bulletin)
- **API**: http://ezamowienia.gov.pl/mo-board/api/v1/notice
- **WebService**: https://bzp.uzp.gov.pl/WebService.aspx
- **Search**: https://searchbzp.uzp.gov.pl/
- **Integration docs**: https://ezamowienia.gov.pl/pl/integracja/

## Data Access

- **Method**: REST API for reading notices and statistics (no auth for read-only)
- **Format**: JSON
- **Auth**: Open for reading; integration tests required for write APIs
- **OCDS**: No

## Coverage

All domestic procurement notices published in BZP (below EU thresholds). Since Jan 2022, BZP is integrated into e-Zamowienia.

## Language

Polish

## Notes

- Public API, no auth for reading, well-structured
- Documentation in Polish but API is straightforward
- WebService also available at bzp.uzp.gov.pl
