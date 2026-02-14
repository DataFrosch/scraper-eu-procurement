# Luxembourg (LU)

**Feasibility: Tier 3**

## Portal

- **Name**: Portail des marches publics
- **URL**: https://pmp.b2g.etat.lu/ (main portal) / https://marches.public.lu/ (info site)
- **Open data**: https://data.public.lu/
- **API**: https://data.public.lu/en/docapi/ (general udata API)

## Data Access

- **Method**: Limited procurement data on open data portal
- **Format**: CSV
- **Auth**: Open
- **OCDS**: No

## Coverage

All public procurement notices (federal, municipal, public institutions).

## Language

French

## Notes

- Small country, relatively few procurement notices
- Open data portal exists but procurement dataset is limited
- No dedicated procurement API

## Schema Mapping

### Data Source Assessment

Luxembourg is rated **Tier 3** (most difficult). The procurement portal at `pmp.b2g.etat.lu` is a web application with no documented API. The only structured open data identified is on `data.public.lu`, specifically the "PCH: Marches publics" dataset published by the Administration des Ponts et Chaussees (roads/bridges administration). This dataset is:

1. **Limited to a single contracting authority** (PCH), not all of Luxembourg's public procurement.
2. **CSV format** with unknown column structure -- the exact fields have not been documented here and must be determined by downloading the dataset from `https://data.public.lu/en/datasets/pch-marches-publics/`.
3. **Not OCDS-compliant**, meaning there is no standardized field mapping.

The `data.public.lu` portal runs the udata platform and exposes a general-purpose API (`https://data.public.lu/api/1/`) that can be used to discover and download dataset resources programmatically. However, this is a metadata API for the data catalog, not a procurement-specific API.

**Before implementing a scraper, the implementer MUST:**
- Download the actual CSV resource(s) from the PCH dataset to determine available columns.
- Investigate whether the main portal (`pmp.b2g.etat.lu`) exposes any undocumented API endpoints (e.g., XHR requests on search pages at `/entreprise/consultation/`).
- Determine whether other contracting authorities publish procurement data on `data.public.lu` beyond PCH.

### Field Mapping Tables

The tables below are **best-effort mappings based on what a typical Luxembourg procurement CSV might contain**. Because the exact CSV column structure is undocumented in this spec, portal field names are marked as `UNKNOWN - VERIFY` where the mapping is speculative. Fields marked `N/A` are confirmed absent based on available information.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | UNKNOWN - VERIFY | Generate a synthetic ID (e.g., `LU-PCH-{row_number}` or hash of key fields) since national portals typically lack TED-style doc IDs. Must be unique and stable across re-imports. |
| `edition` | N/A | TED-specific concept (OJ S edition number). Will be `None`. |
| `version` | Hardcode `"lu-csv"` | Use to identify the parser variant, following the pattern in TED (`R2.0.7`, `R2.0.8`, `R2.0.9`, `eforms`). |
| `reception_id` | N/A | TED-specific. Will be `None`. |
| `official_journal_ref` | N/A | TED-specific (OJ reference). Will be `None`. |
| `publication_date` | UNKNOWN - VERIFY | Look for a date column (e.g., `date_publication`, `date_avis`). |
| `dispatch_date` | N/A | TED-specific. Will be `None`. |
| `source_country` | Hardcode `"LU"` | All records originate from Luxembourg. |
| `contact_point` | UNKNOWN - VERIFY | May appear as a contact name column. |
| `phone` | UNKNOWN - VERIFY | May appear as a phone column. |
| `email` | UNKNOWN - VERIFY | May appear as an email column. |
| `url_general` | UNKNOWN - VERIFY | May contain a link to the notice on `pmp.b2g.etat.lu`. |
| `url_buyer` | N/A | Unlikely to be in a CSV export. Will be `None`. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | UNKNOWN - VERIFY | Look for `organisme`, `pouvoir_adjudicateur`, `autorite_contractante`, or similar. For the PCH dataset this may be hardcoded as the PCH itself. |
| `address` | UNKNOWN - VERIFY | May appear as `adresse` or combined address field. |
| `town` | UNKNOWN - VERIFY | May appear as `ville`, `localite`. |
| `postal_code` | UNKNOWN - VERIFY | May appear as `code_postal`. |
| `country_code` | Hardcode `"LU"` | All contracting bodies are in Luxembourg. |
| `nuts_code` | UNKNOWN - VERIFY | Luxembourg NUTS codes are `LU000` (single NUTS-3 region) or `LU00` (NUTS-2) or `LU0` (NUTS-1). May not be present in CSV; could be hardcoded to `LU000` if absent. |
| `authority_type` | UNKNOWN - VERIFY | Unlikely to be in CSV. If present, will need mapping to eForms codes (see Code Normalization below). Will likely be `None`. |
| `main_activity_code` | N/A | Not expected in a basic CSV. Will be `None`. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | UNKNOWN - VERIFY | Look for `objet`, `intitule`, `titre`, `description_marche`. This is a required field -- if not present, the record cannot be imported. |
| `short_description` | UNKNOWN - VERIFY | May be a separate description column or may need to be left `None` if the title column serves as the only text field. |
| `main_cpv_code` | UNKNOWN - VERIFY | Look for `cpv`, `code_cpv`. CPV codes are widely used in EU procurement; may be present. |
| `cpv_codes` | UNKNOWN - VERIFY | If only one CPV column exists, use it as both `main_cpv_code` and the single entry in `cpv_codes`. Multiple CPV codes may be semicolon-delimited in a single column. |
| `nuts_code` | UNKNOWN - VERIFY | Performance location NUTS code. May not be present. |
| `contract_nature_code` | UNKNOWN - VERIFY | Look for `type_marche`, `nature`. Values will need mapping to eForms codes (`works`, `supplies`, `services`). See Code Normalization below. |
| `procedure_type` | UNKNOWN - VERIFY | Look for `type_procedure`, `procedure`. Values will need mapping to eForms codes. See Code Normalization below. |
| `accelerated` | N/A | Not expected in a basic CSV. Default `False`. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | UNKNOWN - VERIFY | May reuse the contract title or lot title. Often `None` for national portals. |
| `contract_number` | UNKNOWN - VERIFY | Look for `numero_marche`, `reference`, `numero_avis`. |
| `tenders_received` | UNKNOWN - VERIFY | Look for `nombre_offres`, `nb_offres_recues`. Often not available in basic CSV exports. |
| `awarded_value` | UNKNOWN - VERIFY | Look for `montant`, `valeur`, `montant_ttc`, `montant_ht`. This is the most critical data field. Monetary parsing must handle French locale (comma as decimal separator, period or space as thousands separator). |
| `awarded_value_currency` | Hardcode `"EUR"` or UNKNOWN - VERIFY | Luxembourg uses EUR. Verify whether a currency column exists; if not, hardcode `"EUR"`. |
| `contractors` | See ContractorModel below | May be one or more columns for awardee information. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | UNKNOWN - VERIFY | Look for `attributaire`, `titulaire`, `nom_entreprise`, `adjudicataire`. This is a required field for each contractor. |
| `address` | UNKNOWN - VERIFY | May appear as `adresse_attributaire`. |
| `town` | UNKNOWN - VERIFY | May appear as `ville_attributaire`, `localite_attributaire`. |
| `postal_code` | UNKNOWN - VERIFY | May appear as `code_postal_attributaire`. |
| `country_code` | UNKNOWN - VERIFY | May appear as `pays_attributaire`. Will need ISO 3166-1 alpha-2 normalization. |
| `nuts_code` | N/A | Not expected for contractors in a basic CSV. Will be `None`. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | UNKNOWN - VERIFY | See `main_cpv_code` above. Format should be `NNNNNNNN-N` (8 digits, dash, check digit). Verify whether the CSV stores codes with or without the check digit. |
| `description` | UNKNOWN - VERIFY | May be included alongside the CPV code or may need to be omitted (`None`) and let the database's existing CPV lookup table provide descriptions. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | UNKNOWN - VERIFY | Must be normalized to eForms codes. See Code Normalization below. |
| `description` | Derive from code | Use the `_PROCEDURE_TYPE_DESCRIPTIONS` lookup from the existing codebase once the code is normalized. |

#### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | UNKNOWN - VERIFY | Must be normalized to eForms codes. See Code Normalization below. |
| `description` | Derive from code | Use the `_AUTHORITY_TYPE_DESCRIPTIONS` lookup from the existing codebase once the code is normalized. |

### Unmappable Schema Fields

The following schema fields **cannot be populated** from a Luxembourg CSV dataset and should be set to `None` (or their default value):

| Field | Reason |
|---|---|
| `DocumentModel.edition` | TED-specific (OJ S edition). |
| `DocumentModel.reception_id` | TED-specific. |
| `DocumentModel.official_journal_ref` | TED-specific (OJ reference number). |
| `DocumentModel.dispatch_date` | TED-specific (date sent to OJ). |
| `DocumentModel.url_buyer` | Not expected in CSV. |
| `ContractingBodyModel.main_activity_code` | Not expected in CSV. |
| `ContractModel.accelerated` | Not expected; default `False`. |
| `ContractorModel.nuts_code` | Not expected for contractors. |

### Extra Portal Fields

Without access to the actual CSV column headers, this section is speculative. Common fields found in French-language procurement CSV exports that our schema does not cover include:

| Potential Portal Field | Description | Status |
|---|---|---|
| `lot_number` / `numero_lot` | Lot number within a multi-lot procurement | Schema doesn't cover -- flagging for review. Our schema handles lots implicitly via multiple awards per contract, but does not store lot numbers. |
| `date_attribution` | Date the contract was awarded | Schema doesn't cover -- flagging for review. We store `publication_date` but not `award_date`. |
| `date_notification` | Date the award decision was notified | Schema doesn't cover -- flagging for review. |
| `duree_marche` / `duration` | Contract duration (months/days) | Schema doesn't cover -- flagging for review. |
| `lieu_execution` | Place of performance (free text) | Schema doesn't cover as free text -- we only store NUTS codes. Flagging for review. |
| `forme_prix` | Price form (fixed, revisable, etc.) | Schema doesn't cover -- flagging for review. |
| `id_national` / `SIRET` equivalent | National business identifier for contractors | Schema doesn't cover -- flagging for review. Luxembourg uses `numero RCS` (Registre de Commerce et des Societes). |
| `groupement` / `co_traitance` | Whether award is to a joint venture / consortium | Schema doesn't cover explicitly -- flagging for review. Multiple contractors per award partially captures this. |
| `sous_traitance` | Subcontracting information | Schema doesn't cover -- flagging for review. |
| `montant_estime` / `valeur_estimee` | Estimated contract value (pre-award) | Schema doesn't cover -- we only store awarded value. Flagging for review. |

### Code Normalization

All coded values must be normalized to eForms equivalents (lowercase, hyphens) per project convention. The CSV likely uses French-language labels rather than codes, requiring text-to-code mapping.

#### Contract Nature Codes

| Likely CSV Value (French) | eForms Code | Notes |
|---|---|---|
| `Travaux` | `works` | Construction/engineering works |
| `Fournitures` | `supplies` | Supply of goods |
| `Services` | `services` | Service contracts |
| `Mixte` / `Combine` | `combined` | Mixed contract types (rare) |

#### Procedure Type Codes

| Likely CSV Value (French) | eForms Code | Notes |
|---|---|---|
| `Procedure ouverte` | `open` | Open procedure |
| `Procedure restreinte` | `restricted` | Restricted procedure |
| `Procedure negociee avec publication` / `Procedure negociee avec mise en concurrence` | `neg-w-call` | Negotiated with prior call |
| `Procedure negociee sans publication` / `Procedure negociee sans mise en concurrence` | `neg-wo-call` | Negotiated without prior call |
| `Dialogue competitif` | `comp-dial` | Competitive dialogue |
| `Partenariat d'innovation` | `innovation` | Innovation partnership |
| `Procedure adaptee` | UNKNOWN | French-specific concept for below-threshold; no direct eForms equivalent. May map to `oth-single` or require a new mapping. **Needs investigation.** |

#### Authority Type Codes

| Likely CSV Value (French) | eForms Code | Notes |
|---|---|---|
| `Autorite gouvernementale centrale` / `Ministere` | `cga` | Central government authority |
| `Autorite regionale` | `ra` | Regional authority |
| `Autorite locale` / `Commune` / `Administration communale` | `la` | Local authority |
| `Organisme de droit public` | `body-pl` | Body governed by public law |
| `Etablissement public` | `body-pl` | Public institution (maps to body governed by public law) |
| `Institution europeenne` | `eu-ins-bod-ag` | EU institution (unlikely for national portal) |

**Important**: Luxembourg, being a small unitary state, has no regional level in the usual EU sense. Most contracting authorities will be either central government (`cga`), local/municipal (`la`), or public-law bodies (`body-pl`). The mapping table above may need adjustment once actual CSV values are inspected.

### Data Format Notes

- **Format**: CSV (comma-separated or semicolon-separated -- French-locale CSVs often use semicolons as delimiters).
- **Encoding**: Likely UTF-8, but verify. Older French-language datasets sometimes use ISO-8859-1 / Latin-1.
- **Decimal separator**: French locale uses comma (`,`) as decimal separator. Monetary values like `1.234.567,89` or `1 234 567,89` must be handled. The existing `parsers/monetary.py` module has locale-specific parsers that may cover this (verify against its 11 format-specific parsers).
- **Date format**: Likely `DD/MM/YYYY` (French convention) or ISO 8601 (`YYYY-MM-DD`). Must be verified from actual data.
- **Multi-value fields**: CPV codes or other list fields may be semicolon-delimited within a single CSV column.
- **Text encoding of special characters**: French text will contain accented characters (e.g., `e` with accent, `c` with cedilla). Ensure UTF-8 handling throughout.
- **Download mechanism**: Use the `data.public.lu` udata API (`GET /api/1/datasets/pch-marches-publics/`) to discover resource URLs, then download CSV files directly. The API returns JSON metadata including `resources[].url` for each downloadable file.
- **Idempotency**: Since there is no stable document ID from the portal, the `doc_id` generation strategy must produce deterministic, stable IDs so that re-imports skip already-imported records. Consider using a hash of (contracting body name + contract title + award date + awarded value) or similar composite key.

### Implementation Risks

1. **Data coverage is severely limited**: The only confirmed open dataset (PCH) covers a single agency. This may yield very few records compared to other country portals.
2. **CSV structure is undocumented**: The exact columns are unknown. The implementer must download the data first, inspect the columns, and then update this mapping.
3. **No award-specific filtering**: Unlike TED (which has document type 7 for contract awards), national CSV exports may mix notices, awards, and cancellations in a single file. Filtering logic will be needed.
4. **The main portal (`pmp.b2g.etat.lu`) may have undocumented APIs**: Browser developer tools should be used to inspect XHR requests on the search and consultation pages. If an internal API is found, it would provide far richer data than the CSV export.
5. **Web scraping as fallback**: If no usable API or CSV is found, HTML scraping of `pmp.b2g.etat.lu` consultation pages would be required, which is fragile and rate-limited. This is consistent with the Tier 3 classification.
