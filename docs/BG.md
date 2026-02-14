# Bulgaria (BG)

**Feasibility: Tier 2**

## Portal

- **Name**: Electronic Public Procurement (CAIS EOP)
- **URL**: https://app.eop.bg/today (register) / https://www2.aop.bg/ (agency portal)
- **Open data**: https://data.egov.bg/

## Data Access

- **Method**: Public register searchable online; open data portal
- **Format**: XML, CSV (on open data portal)
- **Auth**: Open for browsing
- **OCDS**: No

## Coverage

All public procurement covered by the Public Procurement Act.

## Language

Bulgarian (English version available on agency site)

## Notes

- Limited English documentation
- Open data portal has general API
- May require parsing Bulgarian-language exports

## Schema Mapping

### Data Flow Overview

Bulgaria has two data access paths, neither with a well-documented public API:

1. **Open Data Portal CSV exports** (`data.egov.bg`) -- The Public Procurement Agency (AOP) publishes yearly CSV datasets on the national open data portal at `https://data.egov.bg/organisation/e9a95e08-7759-497a-a478-55f331d59447/datasets`. Two dataset types are published per year:
   - **Contracts dataset** (e.g. `contracts2022.csv`) -- concluded contracts from public procurement procedures.
   - **Annexes/amendments dataset** (e.g. `annexes2022.csv`) -- modifications to contracts or framework agreements during execution.

   Data comes from both the CAIS EOP system and the older Register of Public Procurements (ROP) for procedures opened before mandatory CAIS EOP use. The portal is powered by CKAN (or a CKAN-like system), but direct API access via `data.egov.bg/api/` returns 403 Forbidden for automated requests -- a browser user-agent may be required, or downloads may need to go through the web UI.

2. **CAIS EOP public register** (`app.eop.bg`) -- The live register at `https://app.eop.bg/today/reporting/search` allows searching procurement notices. No public API documentation has been found. The system appears to expose search results via HTTP but the endpoints, request/response formats, and field structures are undocumented. Reverse-engineering the web interface would be needed.

**Recommended strategy**: Use the open data portal CSV exports as the primary data source. These are published yearly (data available from at least 2020 onward). The contracts CSV is the relevant dataset for award data. The portal blocks simple `curl` requests (403), so the downloader will need to either (a) use browser-like headers, (b) use the CKAN API with proper authentication/cookies, or (c) download files manually and import locally. **The exact CSV column names and structure must be verified by downloading a sample file** -- the column names documented below are inferred from the Bulgarian Public Procurement Act field requirements, the AOP announcement about the 2022 data publication, and the GPPD data processing methodology, but have NOT been confirmed against an actual CSV header row.

### Data Format Notes

- **Format**: CSV files, likely UTF-8 encoded with comma or semicolon delimiters. Column headers are in Bulgarian.
- **Language**: All field values (names, descriptions, addresses) are in Bulgarian. No English translations are provided.
- **Multi-value delimiter**: When multiple contractors exist for a single contract, their names are combined in a single field using `|||` as a separator. The same `|||` delimiter is applied to contractor identification codes (EIK numbers).
- **Yearly publication**: Data is published retrospectively. The 2022 data was published in June 2023. Publication cadence is approximately annual.
- **Dual sources**: Each year may have two CSV variants: one from CAIS EOP and one from the older ROP register. The column structures may differ between the two sources.
- **No OCDS**: The data does not follow the Open Contracting Data Standard. It uses a proprietary flat CSV structure.
- **Portal technology**: data.egov.bg appears to run on a CKAN-based platform. Standard CKAN API endpoints (`/api/3/action/package_show`, `/api/3/action/datastore_search`) may work if access restrictions can be bypassed.
- **Rate limits**: Unknown. The portal blocks direct programmatic access (403 Forbidden), suggesting anti-scraping measures are in place.

### Field Mapping: Contracts CSV (Inferred)

**IMPORTANT**: The column names below are best-effort inferences based on Bulgarian procurement law requirements, the AOP's public announcements, and the structure used by third-party data processors (GPPD/GTI). They have NOT been verified against an actual CSV file. The implementing agent MUST download a sample CSV file first and adjust these mappings to match the actual column headers.

The Bulgarian names below follow the standard terminology from the Public Procurement Act (ZOP) and the CAIS EOP system.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | Unique procurement number (e.g. `Уникален номер на поръчката` or similar identifier column) | **Column name unverified.** Each contract in CAIS EOP has a unique reference number. Use this as the document ID, prefixed with `BG-` to avoid collision with TED doc IDs. |
| `edition` | Not available | `None`. CSV exports are yearly snapshots, not OJ editions. |
| `version` | Hardcode `"BG-CSV"` | To distinguish from TED-sourced documents. |
| `reception_id` | Not available | `None`. TED-specific concept. |
| `official_journal_ref` | Not available | `None`. National below-threshold notices have no OJ reference. |
| `publication_date` | Contract publication date column (e.g. `Дата на публикуване`) | **Column name unverified.** Parse from Bulgarian date format (likely `DD.MM.YYYY` or ISO `YYYY-MM-DD`). |
| `dispatch_date` | Not available | `None`. Not applicable for national CSV data. |
| `source_country` | Hardcode `"BG"` | All records are Bulgarian procurement. |
| `contact_point` | Not likely available in CSV | `None`. Contact details are typically in the full notice, not the CSV summary. |
| `phone` | Not likely available in CSV | `None`. |
| `email` | Not likely available in CSV | `None`. |
| `url_general` | Not likely available in CSV | `None`. |
| `url_buyer` | Not likely available in CSV | `None`. The CAIS EOP system has buyer profiles, but the CSV export likely does not include URLs. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | Contracting authority name column (e.g. `Наименование на възложителя`) | **Column name unverified.** Mandatory field per ZOP. Will be in Bulgarian. |
| `address` | Possibly available (e.g. `Адрес на възложителя`) | **Column name unverified.** May not be in the CSV summary export. |
| `town` | Possibly available (e.g. `Населено място` or `Град`) | **Column name unverified.** |
| `postal_code` | Possibly available | **Column name unverified.** May not be in CSV. |
| `country_code` | Hardcode `"BG"` | All contracting authorities in this dataset are Bulgarian. |
| `nuts_code` | Possibly available (e.g. `NUTS код`) | **Column name unverified.** Bulgaria uses NUTS codes (BG3xx, BG4xx series). May or may not be in the CSV export. |
| `authority_type` | Possibly available (e.g. `Вид на възложителя`) | **Column name unverified.** If present, values will be in Bulgarian and will need mapping to eForms codes. See code normalization section below. |
| `main_activity_code` | Possibly available (e.g. `Основна дейност`) | **Column name unverified.** If present, needs mapping to eForms activity codes. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | Contract subject/title column (e.g. `Предмет на договора` or `Предмет на поръчката`) | **Column name unverified.** Mandatory field per ZOP. In Bulgarian. |
| `short_description` | Same as title, or a separate description column | **Column name unverified.** The CSV may not have a separate description field. Use the title if no description column exists. |
| `main_cpv_code` | CPV code column (e.g. `CPV код` or `Основен CPV код`) | **Column name unverified.** CPV codes are mandatory per ZOP. Format is standard CPV (e.g. `45000000`). |
| `cpv_codes` | Same CPV column; possibly additional CPV columns | **Column name unverified.** The CSV may only include the main CPV code. If multiple CPV codes are present, they may be in separate columns or `|||`-delimited. |
| `nuts_code` | Performance location NUTS code (e.g. `NUTS код на мястото на изпълнение`) | **Column name unverified.** May not be in the CSV. |
| `contract_nature_code` | Contract type/nature column (e.g. `Обект на поръчката`) | **Column name unverified.** Values will be in Bulgarian: `Строителство` (works), `Доставки` (supplies), `Услуги` (services). Needs mapping to eForms codes. |
| `procedure_type` | Procedure type column (e.g. `Вид процедура` or `Вид на процедурата`) | **Column name unverified.** Values will be in Bulgarian. Needs mapping to eForms codes. See code normalization section. |
| `accelerated` | Not likely available | `False` (default). The CSV export is unlikely to include an accelerated-procedure flag. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | Same as contract title | Use the contract subject/title. The CSV likely does not have a separate award title. |
| `contract_number` | Contract number column (e.g. `Номер на договора`) | **Column name unverified.** |
| `tenders_received` | Number of tenders column (e.g. `Брой получени оферти`) | **Column name unverified.** May not be in the contracts CSV. More likely in a separate tenders dataset. |
| `awarded_value` | Contract value column (e.g. `Стойност на договора` or `Стойност`) | **Column name unverified.** Currency is likely BGN (Bulgarian Lev). Parse as float. Beware of Bulgarian number formatting (comma as decimal separator, space or period as thousands separator). |
| `awarded_value_currency` | Currency column or hardcode `"BGN"` | **Column name unverified.** If no currency column exists, default to `"BGN"`. Some EU-funded contracts may use EUR. |
| `contractors` | Contractor name column (e.g. `Наименование на изпълнителя` or `Изпълнител`) | **Column name unverified.** Multiple contractors are `|||`-delimited in a single field. Split on `|||` to create multiple ContractorModel entries. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | Contractor name from the `|||`-delimited field | **Column name unverified.** In Bulgarian. When multiple contractors exist, split on `|||`. |
| `address` | Not likely available in CSV | `None`. Contractor addresses are typically not in the summary CSV. |
| `town` | Possibly available (e.g. `Населено място на изпълнителя`) | **Column name unverified.** |
| `postal_code` | Not likely available | `None`. |
| `country_code` | Possibly available; default to `"BG"` | Most contractors will be Bulgarian. If no country column, default to `"BG"`. |
| `nuts_code` | Not likely available | `None`. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | CPV code from the contracts CSV | Standard CPV format (e.g. `45000000`). No parsing needed beyond trimming whitespace. |
| `description` | Not available in CSV | `None`. CPV descriptions must come from a local lookup table if needed. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Procedure type after normalization to eForms codes | See code normalization section. |
| `description` | Not available in CSV | `None`. Can be populated from a static lookup of eForms procedure type codes. |

### Unmappable Schema Fields

These fields will be `None` for BG open data CSV sources:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | Not applicable for yearly CSV exports. |
| `DocumentModel.reception_id` | TED-specific concept. |
| `DocumentModel.official_journal_ref` | National-only notices have no OJ reference. |
| `DocumentModel.dispatch_date` | Not in CSV export. |
| `DocumentModel.contact_point` | Not in summary CSV. |
| `DocumentModel.phone` | Not in summary CSV. |
| `DocumentModel.email` | Not in summary CSV. |
| `DocumentModel.url_general` | Not in summary CSV. |
| `DocumentModel.url_buyer` | Not in summary CSV. |
| `ContractingBodyModel.postal_code` | Likely not in CSV. |
| `ContractingBodyModel.nuts_code` | May not be in CSV. Needs verification. |
| `ContractingBodyModel.main_activity_code` | May not be in CSV. Needs verification. |
| `ContractModel.nuts_code` | May not be in CSV. Needs verification. |
| `ContractModel.accelerated` | Not available in CSV. Defaults to `False`. |
| `AwardModel.tenders_received` | May not be in contracts CSV. Needs verification. |
| `ContractorModel.address` | Not in summary CSV. |
| `ContractorModel.postal_code` | Not in summary CSV. |
| `ContractorModel.nuts_code` | Not in summary CSV. |
| `CpvCodeEntry.description` | Not in CSV. |
| `ProcedureTypeEntry.description` | Not in CSV. |
| `AuthorityTypeEntry.description` | Not in CSV (if authority type is present at all). |

### Extra Portal Fields

These fields may be available in the Bulgarian open data CSV but are not covered by the current schema. Flagged for review.

| Portal Field (Inferred) | Description | Notes |
|---|---|---|
| EIK/BULSTAT number (`ЕИК на изпълнителя`) | Contractor tax/registration ID | Schema doesn't cover -- flagging for review. Very useful for entity resolution. Multiple contractor EIKs are `|||`-delimited, mirroring the contractor names field. |
| EIK of contracting authority (`ЕИК на възложителя`) | Contracting body tax/registration ID | Schema doesn't cover -- flagging for review. Very useful for entity resolution and deduplication. |
| Contract date (`Дата на сключване на договора`) | Date the contract was signed | Schema doesn't cover -- flagging for review. Distinct from publication date. |
| Contract end date / duration | Duration or expected end date | Schema doesn't cover -- flagging for review. |
| EU funding indicator | Whether the contract is funded by EU programs | Schema doesn't cover -- flagging for review. |
| Framework agreement indicator | Whether the contract is under a framework agreement | Schema doesn't cover -- flagging for review. |
| Subcontracting information | Whether subcontracting is involved | Schema doesn't cover -- flagging for review. |
| Amendment/annex data (from `annexes` CSV) | Modifications to contracts during execution | Schema doesn't cover -- flagging for review. Separate CSV dataset available. |
| Estimated value (`Прогнозна стойност`) | Estimated value before award | Schema doesn't cover -- flagging for review. Useful for analysis of cost overruns. |

### Code Normalization

#### Contract Nature Codes (Обект на поръчката)

Bulgarian CSV values will be in Bulgarian text. Map to eForms codes:

| Bulgarian Value | eForms Code | Notes |
|---|---|---|
| `Строителство` | `works` | |
| `Доставки` | `supplies` | |
| `Услуги` | `services` | |

**Unknown values**: If the CSV uses numeric codes, abbreviations, or other variants, the exact mapping must be determined from a sample file. The existing `_normalize_contract_nature_code()` in `ted_v2.py` handles TED numeric codes (1=works, 2=supplies, 4=services) and can be extended.

#### Procedure Type Codes (Вид на процедурата)

Bulgarian CSV values will be in Bulgarian. The Public Procurement Act (ZOP) defines these procedure types, which need mapping to eForms equivalents:

| Bulgarian Value (Expected) | eForms Code | Notes |
|---|---|---|
| `Открита процедура` | `open` | Open procedure |
| `Ограничена процедура` | `restricted` | Restricted procedure |
| `Състезателна процедура с договаряне` | `neg-w-call` | Competitive procedure with negotiation |
| `Състезателен диалог` | `comp-dial` | Competitive dialogue |
| `Договаряне с предварителна покана за участие` | `neg-w-call` | Negotiated with prior call |
| `Договаряне с публикуване на обявление за поръчка` | `neg-w-call` | Negotiated with publication of notice |
| `Договаряне без предварителна покана за участие` | `neg-wo-call` | Negotiated without prior call |
| `Договаряне без предварително обявление` | `neg-wo-call` | Negotiated without prior publication |
| `Пряко договаряне` | `neg-wo-call` | Direct negotiation (below-threshold variant) |
| `Партньорство за иновации` | `innovation` | Innovation partnership |
| `Публично състезание` | `open` | Public competition (national below-threshold procedure, closest to open) |
| `Събиране на оферти с обява` | `oth-single` | Collection of offers with announcement (simplified below-threshold) |
| `Покана до определени лица` | `neg-wo-call` | Invitation to specific persons (below-threshold negotiated) |
| `Конкурс за проект` | `oth-single` | Design contest |

**IMPORTANT**: The exact Bulgarian text values in the CSV are unverified. The values above are the standard ZOP terminology, but the CSV may use abbreviations, numeric codes, or slightly different phrasing. A sample file must be examined to confirm the exact values and complete the mapping. Any unmapped values should raise an error per the project's fail-loud policy.

#### Authority Type Codes (Вид на възложителя)

If the CSV includes an authority type field, the values will be in Bulgarian. Expected mapping to eForms codes:

| Bulgarian Value (Expected) | eForms Code | Notes |
|---|---|---|
| `Министерство или друг държавен орган` | `cga` | Ministry or other state body |
| `Национална агенция` | `cga` | National agency |
| `Регионален или местен орган` | `ra` | Regional or local authority |
| `Публичноправна организация` | `body-pl` | Body governed by public law |
| `Публично предприятие` | `pub-undert` | Public undertaking |
| `Друг` | `None` | Other (no eForms equivalent) |

**IMPORTANT**: These values are inferred from the ZOP and may not match the CSV exactly. Verification against a sample file is required.

### Implementation Recommendations

1. **First step: obtain a sample CSV file.** The entire mapping above is based on inference. Before writing any parser code, manually download a contracts CSV file from `https://data.egov.bg/organisation/e9a95e08-7759-497a-a478-55f331d59447/datasets` and inspect the actual column headers, data types, and value formats. Update this document with the verified column names.

2. **Handle the 403 access restriction.** The open data portal blocks automated requests. Options to investigate: (a) use a session with proper cookies obtained from the portal's web UI, (b) check if the CKAN API (`/api/3/action/...`) is accessible with specific headers or authentication, (c) add browser-like request headers (`User-Agent`, `Accept`, `Referer`), or (d) implement a manual download step where the user downloads the CSV files to a local directory and the importer reads from there.

3. **CSV parsing considerations**: (a) Determine the delimiter (comma vs semicolon -- Bulgarian CSVs often use semicolons). (b) Handle Bulgarian number formatting for monetary values (comma as decimal separator). (c) Parse dates from `DD.MM.YYYY` or ISO format. (d) Split `|||`-delimited multi-value fields for contractors and their EIK numbers. (e) Handle encoding (likely UTF-8, but verify).

4. **Prefix doc_id with `BG-`**: To avoid collisions with TED-sourced documents, prefix all document IDs from this portal with `BG-` (e.g. `BG-00123456`).

5. **Deduplication with TED**: Above-threshold Bulgarian procurements are cross-published to TED. The CSV may include a TED reference number or OJ reference that can be used to skip records already imported via the TED portal. If no such field exists, deduplication must be done post-import by matching on contracting body name + contract value + date.

6. **Yearly import pattern**: Since data is published as yearly CSV snapshots, the importer should download one CSV per year and process all rows. This differs from the TED pattern of daily packages.

7. **Two data sources per year**: The portal may publish separate CSVs for CAIS EOP data and older ROP data. Both should be imported, but their column structures may differ. Check if the ROP CSVs use a different schema.

8. **Fail-loud on unknown code values**: Per project policy, any procedure type, contract nature, or authority type value not in the mapping tables above must raise an error with the actual bad value in the message. Do not silently skip or default.
