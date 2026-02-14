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

## Schema Mapping

### Recommended Data Source

Use **DECP consolidated tabular files** (Parquet or CSV) from data.gouv.fr as the primary data source. This is the award-focused dataset that best matches our schema's purpose. The data.economie.gouv.fr API (`decp-v3-marches-valides`) exposes the same data via an OpenDataSoft REST API and can be used for incremental updates.

BOAMP is primarily a *notices* portal (calls for competition, adapted procedures). While it includes some award notices, DECP is the canonical source for awarded contract data and is the right choice for this scraper.

### Data Format Notes

- **Format**: Parquet (recommended for bulk) or CSV; API returns JSON
- **Encoding**: UTF-8
- **Row structure**: One row per (contract, contractor, modification). A single contract with 3 contractors produces 3 rows. Filter to `modification_id = 0` (or equivalent) to get initial award data only.
- **Unique key**: `uid` = concatenation of buyer SIRET (`acheteur.id`) + market identifier (`id`). This is unique per contract nationally.
- **Currency**: Always EUR (France uses the euro; the DECP schema has no currency field).
- **Dates**: ISO 8601 format (`YYYY-MM-DD`).
- **Nested fields**: In the tabular format, nested JSON objects are flattened with dot notation (e.g., `acheteur.id`, `acheteur.nom`, `titulaire.id`, `titulaire.denominationSociale`, `lieuExecution.code`).

### DECP Tabular Fields

The consolidated tabular DECP dataset contains the following columns (confirmed from decp.info and data.gouv.fr documentation):

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Market identifier (unique per buyer, 1-16 chars) |
| `uid` | string | National unique ID = `acheteur.id` + `id` |
| `acheteur.id` | string | Buyer SIRET (14-digit identifier) |
| `acheteur.nom` | string | Buyer official name |
| `nature` | string | Nature of market (enum, see Code Normalization below) |
| `objet` | string | Object/title of the contract |
| `codeCPV` | string | CPV code |
| `procedure` | string | Procedure type (enum, see Code Normalization below) |
| `lieuExecution.code` | string | Place of execution code (postal code, INSEE code, or NUTS code) |
| `lieuExecution.typeCode` | string | Type of execution code (`Code postal`, `Code commune`, `Code arrondissement`, `Code canton`, `Code departement`, `Code region`, `Code pays`, `Code nuts`) |
| `lieuExecution.nom` | string | Place of execution name |
| `dureeMois` | integer | Contract duration in months |
| `dateNotification` | date | Notification date (when contract was awarded) |
| `datePublicationDonnees` | date | Data publication date |
| `montant` | float | Contract amount in EUR |
| `formePrix` | string | Price form (e.g., `Ferme`, `Ferme et actualisable`, `Révisable`) |
| `titulaire.id` | string | Contractor identifier (SIRET or other) |
| `titulaire.typeIdentifiant` | string | Contractor identifier type (`SIRET`, `TVA`, `TAHITI`, `RIDET`, `FRWF`, `IREP`, `UE`, `HORS-UE`) |
| `titulaire.denominationSociale` | string | Contractor official name |
| `objetModification` | string | Description of modification (if `modification_id > 0`) |
| `source` | string | Source platform that originally published the data |
| `donneesActuelles` | boolean | Whether this row represents the current state of the contract |
| `anomalies` | string | Data quality anomalies detected |

### Field Mapping Tables

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `uid` | National unique ID. Use as-is; format is `{SIRET}{id}`. |
| `edition` | -- | `None`. DECP has no edition concept. |
| `version` | -- | Set to a constant like `"DECP-v3"` to identify the source format. |
| `reception_id` | -- | `None`. No reception ID in DECP. |
| `official_journal_ref` | -- | `None`. DECP is not an official journal. Could synthesize from `source` if desired, but per fail-loud rules, leave as `None`. |
| `publication_date` | `datePublicationDonnees` | Date the data was published on the open data platform. |
| `dispatch_date` | `dateNotification` | Date the contract was notified/awarded. Closest equivalent to TED's dispatch date. |
| `source_country` | -- | Hardcode to `"FR"`. All DECP data is French procurement. |
| `contact_point` | -- | `None`. Not available in DECP. |
| `phone` | -- | `None`. Not available in DECP. |
| `email` | -- | `None`. Not available in DECP. |
| `url_general` | -- | `None`. Not available in DECP tabular format. |
| `url_buyer` | -- | `None`. Not available in DECP tabular format. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `acheteur.nom` | Buyer official name. Required field in DECP. |
| `address` | -- | `None`. DECP does not include buyer address. |
| `town` | -- | `None`. DECP does not include buyer town. |
| `postal_code` | -- | `None`. DECP does not include buyer postal code. Could potentially be derived from SIRET via external lookup, but that violates the "no defaults, no fallbacks" rule. |
| `country_code` | -- | Hardcode to `"FR"`. All DECP buyers are French public entities. |
| `nuts_code` | -- | `None`. DECP does not include buyer NUTS code. The `lieuExecution.code` is the *contract execution* location, not the buyer location. |
| `authority_type` | -- | `None`. DECP does not classify the type of authority. |
| `main_activity_code` | -- | `None`. Not available in DECP. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `objet` | Object/title of the contract. Required in DECP. |
| `short_description` | `objet` | Same as title; DECP has no separate short description. |
| `main_cpv_code` | `codeCPV` | CPV code. DECP provides a single CPV code per contract. |
| `cpv_codes` | `codeCPV` | List with a single entry from `codeCPV`. DECP does not provide additional CPV codes. |
| `nuts_code` | `lieuExecution.code` | Only when `lieuExecution.typeCode` is `"Code nuts"`. Otherwise `None` (see Data Format Notes). |
| `contract_nature_code` | `nature` | Requires mapping to eForms codes (see Code Normalization below). |
| `procedure_type` | `procedure` | Requires mapping to eForms codes (see Code Normalization below). |
| `accelerated` | -- | `False`. DECP does not track whether a procedure was accelerated. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `objet` | Use the contract object as the award title. DECP has no separate award title. |
| `contract_number` | `id` | The market identifier (unique per buyer). |
| `tenders_received` | -- | `None`. DECP does not record number of tenders received. |
| `awarded_value` | `montant` | Contract amount in EUR. |
| `awarded_value_currency` | -- | Hardcode to `"EUR"`. All DECP amounts are in euros. |
| `contractors` | (see ContractorModel below) | Built from `titulaire.*` fields. Multiple rows with the same `uid` but different `titulaire.*` indicate multiple contractors on one contract. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `titulaire.denominationSociale` | Contractor name. Required in DECP. |
| `address` | -- | `None`. DECP does not include contractor address. |
| `town` | -- | `None`. DECP does not include contractor town. |
| `postal_code` | -- | `None`. DECP does not include contractor postal code. |
| `country_code` | -- | `None`. DECP does not include contractor country. Could infer from `titulaire.typeIdentifiant` (e.g., `SIRET` implies France) but that would be inference, not raw data. |
| `nuts_code` | -- | `None`. DECP does not include contractor NUTS code. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `codeCPV` | Single CPV code from the contract. |
| `description` | -- | `None`. DECP does not include CPV descriptions. Look up from the `cpv_codes` table if needed. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `procedure` | After mapping to eForms code (see Code Normalization below). |
| `description` | -- | Use the standard eForms description from `_PROCEDURE_TYPE_DESCRIPTIONS` after mapping. |

### Unmappable Schema Fields

The following schema fields cannot be populated from DECP data and should be `None`:

- **DocumentModel**: `edition`, `reception_id`, `official_journal_ref`, `contact_point`, `phone`, `email`, `url_general`, `url_buyer`
- **ContractingBodyModel**: `address`, `town`, `postal_code`, `nuts_code`, `authority_type`, `main_activity_code`
- **ContractModel**: `accelerated` (always `False`)
- **AwardModel**: `tenders_received`
- **ContractorModel**: `address`, `town`, `postal_code`, `country_code`, `nuts_code`

This is a significant amount of missing data compared to TED, reflecting that DECP is a minimal "essential data" schema focused on transparency (who bought what, from whom, for how much) rather than full procurement metadata.

### Extra Portal Fields

The following DECP fields are not covered by the current schema and are flagged for review:

| Portal Field | Description | Notes |
|---|---|---|
| `acheteur.id` | Buyer SIRET (14-digit French business identifier) | **Schema doesn't cover** - flagging for review. Highly valuable for entity deduplication. SIRET is a stable, official identifier far more reliable than name matching. Consider adding a `national_id` field to `ContractingBodyModel`. |
| `titulaire.id` | Contractor identifier (SIRET, TVA, etc.) | **Schema doesn't cover** - flagging for review. Same value as above for contractors. Stable identifier enabling exact dedup without fuzzy matching. |
| `titulaire.typeIdentifiant` | Type of the contractor identifier | **Schema doesn't cover** - flagging for review. Needed to interpret `titulaire.id` correctly. |
| `dureeMois` | Contract duration in months | **Schema doesn't cover** - flagging for review. Useful for analysis (value-per-month, long vs short contracts). |
| `formePrix` | Price form (fixed, revisable, etc.) | **Schema doesn't cover** - flagging for review. Indicates pricing structure. |
| `lieuExecution.nom` | Place of execution name | **Schema doesn't cover** - flagging for review. Human-readable location name. |
| `lieuExecution.typeCode` | Type of location code | **Schema doesn't cover** - flagging for review. Needed to interpret `lieuExecution.code`. |
| `source` | Source platform that published the data | **Schema doesn't cover** - flagging for review. Useful for provenance tracking. |
| `donneesActuelles` | Whether row is the current version | **Schema doesn't cover** - flagging for review. Essential for filtering: only import rows where `donneesActuelles = true` to avoid duplicate/outdated records. |
| `objetModification` | Modification description | **Schema doesn't cover** - flagging for review. Relevant if tracking contract amendments. |
| `anomalies` | Data quality flags | **Schema doesn't cover** - flagging for review. Could be used to skip or flag low-quality records. |

### Code Normalization

#### Procedure Types (DECP `procedure` to eForms codes)

DECP uses French-language procedure names. These must be mapped to eForms `procurement-procedure-type` codes (lowercase, hyphens) used in our schema.

| DECP `procedure` Value | eForms Code | Notes |
|---|---|---|
| `Procédure adaptée` | `oth-single` | Adapted procedure is a French-specific below-threshold procedure. Closest eForms match is `oth-single` ("Other single stage procedure"). **Mapping requires confirmation** -- this is a judgment call. |
| `Appel d'offres ouvert` | `open` | Open call for tenders. Direct equivalent. |
| `Appel d'offres restreint` | `restricted` | Restricted call for tenders. Direct equivalent. |
| `Procédure avec négociation` | `neg-w-call` | Negotiated procedure with prior call. Direct equivalent. |
| `Marché passé sans publicité ni mise en concurrence préalable` | `neg-wo-call` | Award without prior publication or competition. Maps to negotiated without call. |
| `Dialogue compétitif` | `comp-dial` | Competitive dialogue. Direct equivalent. |

**Implementation note**: DECP procedure values are full French strings, not codes. The mapping must be exact string matches (case-sensitive, including accented characters). Unknown values should log a warning and map to `None`, per the fail-loud principle.

#### Contract Nature Codes (DECP `nature` to eForms codes)

DECP uses French-language nature names. These must be mapped to eForms `contract-nature-type` codes used in our schema.

| DECP `nature` Value | eForms Code | Notes |
|---|---|---|
| `Marché` | -- | `None`. "Marché" is the generic term for a public contract. It does not distinguish between works, supplies, or services. DECP does not provide this classification. |
| `Accord-cadre` | -- | `None`. "Framework agreement" is a contracting mechanism, not a contract nature (works/supplies/services). No eForms equivalent in the `contract-nature-type` codelist. |
| `Marché subséquent` | -- | `None`. "Subsequent contract" (under a framework agreement). Same issue as above. |
| `Marché de partenariat` | -- | `None`. "Partnership contract" (public-private partnership). Not a works/supplies/services classification. |
| `Marché de défense ou de sécurité` | -- | `None`. "Defence or security contract". Not a works/supplies/services classification. |

**Critical finding**: The DECP `nature` field does **not** map to `contract_nature_code` (works/supplies/services). It describes the *legal form* of the contract (standard market, framework agreement, subsequent contract, etc.), not the *type of procurement*. The `contract_nature_code` field should be set to `None` for all DECP records unless a CPV-code-based heuristic is implemented in a separate analysis layer.

#### Authority Types

DECP does not include authority type information. The `authority_type` field should always be `None`.

### Parsing Considerations

1. **Row aggregation**: DECP has one row per (contract, contractor). The parser must group rows by `uid` to assemble a single `AwardDataModel` with multiple `ContractorModel` entries in the `contractors` list. All non-contractor fields (title, amount, CPV, etc.) should be identical across rows sharing the same `uid` (take from the first row; optionally validate consistency).

2. **Modification filtering**: Only import rows where the modification identifier is `0` (initial award) or where `donneesActuelles = true` (current state). Modifications can change `titulaire.*`, `montant`, and `dureeMois`. The safest approach for initial implementation: filter to `donneesActuelles = true` to get the latest state of each contract.

3. **Idempotency**: Use `uid` as the `doc_id`. Re-importing the same DECP data should be idempotent (same behavior as TED's doc_id skip).

4. **Bulk import strategy**: Parquet is the recommended format for bulk imports. Use `pyarrow` or `pandas` to read Parquet files. The full dataset is several GB but manageable. The data.gouv.fr bulk files are updated approximately daily.

5. **API pagination**: The data.economie.gouv.fr API (OpenDataSoft Explore v2.1) supports `limit` (max 100) and `offset` parameters. For full dataset retrieval, bulk Parquet download is far more efficient than paginating through the API.

6. **Character encoding**: French text with accents (e.g., `Procédure adaptée`, `Société Générale`). Ensure UTF-8 handling throughout.

7. **SIRET validation**: `acheteur.id` should be a 14-digit SIRET. Invalid SIRETs may indicate data quality issues but should not block import (store as-is per fail-loud rules).

8. **Amount validation**: `montant` can contain anomalous values (same issue as TED data). Apply the same sanity filtering used for TED (`awarded_value >= 1 AND awarded_value < 1000000000`).
