# Finland (FI)

**Feasibility: Tier 1**

## Portal

- **Name**: Hilma
- **URL**: https://www.hankintailmoitukset.fi/en/
- **API Portal**: https://hns-hilma-prod-apim.developer.azure-api.net/
- **GitHub**: https://github.com/Hankintailmoitukset/hilma-api

## Data Access

- **Method**: REST API (AVP API for open data, ETS API for sending notices)
- **Format**: JSON, XML
- **Auth**: AVP API is free, no approval needed; ETS API requires subscription approval
- **OCDS**: No

## Coverage

All public procurement notices (above and below EU thresholds).

## Language

Finnish, English (portal and API)

## Notes

- Well-documented free API with GitHub repo
- Azure API Management developer portal with Swagger
- Owner: Ministry of Finance, maintained by Hansel Ltd
- Community R package: https://rdrr.io/github/hansel-oy/hilma/
