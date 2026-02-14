# France (FR)

**Feasibility: Tier 1**

## Portals

1. **BOAMP** (Official Public Procurement Bulletin): https://www.boamp.fr/
2. **DECP** (Donnees Essentielles de la Commande Publique): consolidated on data.gouv.fr
3. **PLACE** (plateforme des achats de l'Etat): https://www.marches-publics.gouv.fr/ (for tendering)

## Data Access

### BOAMP API
- **URL**: https://www.boamp.fr/pages/api-boamp/
- **OpenDataSoft**: https://boamp-datadila.opendatasoft.com/explore/dataset/boamp/api/
- **Published by**: DILA (Direction de l'Information Legale et Administrative)
- **Format**: JSON, CSV, Excel
- **Auth**: Open, free, Licence Ouverte v2.0
- **Updates**: Same-day publication, twice daily, 7 days/week

### DECP (Award Data)
- **URL**: https://www.data.gouv.fr/datasets/donnees-essentielles-de-la-commande-publique-fichiers-consolides
- **API**: data.gouv.fr tabular API (JSON), rate limit 100 req/sec
- **Bulk download**: Parquet and CSV
- **Coverage**: All contracts >40k EUR (mandatory since 2019, on data.gouv.fr since Jan 2024)
- **Also at**: https://data.economie.gouv.fr/explore/dataset/decp-v3-marches-valides/api/

## OCDS

No (uses own DECP national schema, not OCDS).

## Coverage

BOAMP covers calls for competition, adapted procedures, award notices. DECP covers essential data of awarded contracts >40k EUR.

## Language

French

## Notes

- Two complementary data sources: BOAMP for notices, DECP for awards
- Bulk Parquet/CSV downloads available — efficient for large imports
- Excellent API documentation
- DECP schema regulated by arrete du 22/03/2019, updated 22/12/2022
