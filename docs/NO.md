# Norway (NO)

**Feasibility: Tier 1**

## Portal

- **Name**: Doffin
- **URL**: https://doffin.no/
- **API (dev)**: https://dof-notices-dev-api.developer.azure-api.net/
- **API (prod)**: https://dof-notices-prod-api.developer.azure-api.net/
- **Open data**: https://data.norge.no/en/datasets/a77b0408-85f9-3e12-8a66-8d500b492e9d/kunngjoringer-av-offentlig-anskaffelser
- **eForms SDK Norway**: https://github.com/anskaffelser/eforms-sdk-nor
- **Managed by**: Norwegian Digitalisation Agency (DFO)

## Data Access

- **Method**: REST API (Notices API + Public API)
- **Format**: JSON, XML
- **Auth**: Free API key (register on Azure APIM portal for each environment)
- **OCDS**: No

## Coverage

All public procurement tenders, bids, and awards.

## Language

Norwegian

## Notes

- Two independent environments (dev/prod); each requires separate registration
- Doffin is implementing eForms via Norwegian SDK
- API mimics TED API structure
- Well-structured API on Azure APIM, eForms-compatible
