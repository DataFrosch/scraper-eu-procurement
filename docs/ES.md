# Spain (ES)

**Feasibility: Tier 2**

## Portal

- **Name**: PLACSP (Plataforma de Contratacion del Sector Publico)
- **URL**: https://contrataciondelestado.es/ / https://contrataciondelsectorpublico.gob.es/
- **Open data**: https://contrataciondelsectorpublico.gob.es/wps/portal/DatosAbiertos
- **Web services**: https://contrataciondelestado.es/wps/portal/servicioswebPLACSP
- **Tool docs**: https://contrataciondelestado.es/datosabiertos/DGPE_PLACSP_OpenPLACSP_v.1.3.pdf
- **datos.gob.es**: https://datos.gob.es/en/catalogo/l01241152-licitaciones

## Data Access

- **Method**: Atom/XML feeds (daily updates, monthly/annual files); CODICE web services for B2B integration
- **Format**: XML (.atom extension), CODICE format
- **Auth**: Open for data feeds; B2B integration requires setup
- **OCDS**: No (uses CODICE, a Spanish national standard)

## Coverage

All public sector procurement since 2012. Central platform for all contracting authorities.

## Language

Spanish

## Notes

- CODICE is not OCDS-compatible; requires custom XML parser
- Key data fields: tender status, contract purpose, estimated amount, CPV code, place of execution, successful bidder, award amount, number of bidders
- Academic paper: https://www.sciencedirect.com/science/article/pii/S1877050919322513
- Good historical coverage but non-standard format
