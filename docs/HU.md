# Hungary (HU)

**Feasibility: Tier 3**

## Portal

- **Name**: EKR (Electronic Public Procurement System)
- **URL**: https://english.kozbeszerzes.hu/ (Public Procurement Authority)
- **Operated by**: NEKSZT Kft

## Data Access

- **Method**: Machine-readable search and bulk export of contract award notice data
- **Format**: CSV
- **Auth**: Open for browsing the bulletin
- **OCDS**: No

## Coverage

All public procurement since April 2018 (mandatory via EKR).

## Language

Hungarian (English version of authority site available)

## Notes

- Limited machine-readable exports, no well-documented API
- OECD recommends improving data governance
- Not all data is in machine-readable format
- OCP entry: https://data.open-contracting.org/en/publication/56

## Schema Mapping

### Data Sources Overview

Hungary has four potential data sources for contract award notices:

1. **Official CSV export** from the Public Procurement Authority (kozbeszerzes.hu) — "Eredmenytajekoztatok adatai" (Result Notifications Data). A single CSV file downloadable from `https://kozbeszerzes.hu/media/documents/Eredménytájékoztatók_adatai.csv`. Covers result notifications published between **April 15, 2018 and June 30, 2022**. Last updated September 30, 2022. **This file appears to be a static historical export, not a regularly updated feed.**

2. **CRCB (Corruption Research Center Budapest) dataset** — Research dataset covering 2005-2021, available in CSV and Stata DTA format from `https://www.crcb.eu/?p=3173`. Contains main indicators: publication date, name of issuer, name of winner, contract value, number of bidders, and links to notices. This is a third-party research dataset, not an official source, and stops at 2021.

3. **EKR public API** — The EKR system at `ekr.gov.hu` exposes undocumented API endpoints (e.g. `ekr.gov.hu/api/publikus/kozbeszerzesi-eljaras-nyilvantartas/{id}/dokumentum-letoltes/{docId}` and `ekr.gov.hu/api/publikus/kozbeszerzesi-hirdetmenyek/{id}/dokumentum-letoltes`). No public API documentation, Swagger, or developer portal exists. These endpoints appear to serve individual document downloads, not bulk search or listing. **Not viable for systematic scraping without reverse-engineering the web interface.**

4. **kozbeszerzes.hu notice search** — Web search interface at `https://www.kozbeszerzes.hu/adatbazis/keres/hirdetmeny/` allows filtering by notice type, procedure type, CPV codes, contracting authority, and date ranges. No documented programmatic access. Could potentially be scraped by reverse-engineering HTTP requests, but this would be fragile.

**Recommended primary source**: The official CSV export (source 1), supplemented by scraping the notice search interface (source 4) if ongoing data beyond June 2022 is needed. The CSV is the only confirmed machine-readable bulk data source from the official portal.

### Data Format Notes

- **Format**: CSV (semicolon-delimited based on Hungarian CSV conventions; delimiter needs verification from the actual file).
- **Encoding**: Likely UTF-8 or Windows-1252 (Hungarian characters present). Needs verification.
- **Language**: All field names and values are in Hungarian. No English version of the data exists.
- **Column names**: **Not publicly documented.** The CSV column headers must be inspected by downloading the file. Based on the standard Hungarian result notification form (eredmenytajekoztato), which follows the EU F03 (Contract Award Notice) form structure, the expected fields are listed below. **All field paths below are best-effort estimates based on the standard form structure and need verification against the actual CSV file.**
- **Coverage gap**: The CSV covers April 2018 to June 2022 only. For data after June 2022, a different approach (web scraping or EKR API reverse-engineering) would be required.
- **One row = one what?**: Unknown. Could be one row per notice, per lot, or per award. Needs verification from the actual file. If one row per notice, multi-lot awards would need special handling.

### Expected CSV Fields

Based on the standard Hungarian result notification (eredmenytajekoztato) form, which mirrors the EU F03 form, the CSV likely contains columns corresponding to these data areas. **The actual Hungarian column names must be verified by downloading the file.**

Expected data areas:
- Contracting authority name, address, NUTS code, authority type, main activity
- Contract title, short description, CPV code(s), contract nature (supplies/works/services)
- Procedure type
- Number of tenders received
- Winning tenderer (contractor) name, address, country
- Contract/award value (with or without VAT), currency
- Date of contract award decision, date of publication
- Whether the contract is related to an EU-funded project
- Lot number (if multi-lot procedure)

### Field Mapping: Official CSV (Estimated)

**IMPORTANT**: All "Portal Field/Path" entries below are estimated Hungarian field names based on the standard F03 form. The actual column names in the CSV must be verified by downloading and inspecting the file. An implementing agent should download the CSV first and update this mapping with actual column names before writing parser code.

#### DocumentModel

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `doc_id` | Notice number or EKR reference number (e.g. `EKR azonosító` or `Hirdetmény szám`) | The notice identifier in the Public Procurement Bulletin. Exact column name unknown. |
| `edition` | Derive from publication date | Not a direct field. Derive as `{year}{day_of_year:03d}` if needed, or set to `None`. |
| `version` | Hardcode `"HU-CSV"` | To identify the source format. |
| `reception_id` | `None` | TED-specific concept. Not available in Hungarian portal data. |
| `official_journal_ref` | `None` | National notices have no OJ reference. Above-threshold notices cross-published to TED will have a TED reference, but this is unlikely to be in the CSV. |
| `publication_date` | Publication date column (e.g. `Közzététel dátuma` or `Feladás dátuma`) | Date format needs verification (likely `YYYY-MM-DD` or `YYYY.MM.DD`). |
| `dispatch_date` | Dispatch/sending date column (e.g. `Feladás dátuma`) | May or may not be present as a separate column. |
| `source_country` | Hardcode `"HU"` | All notices are Hungarian procurement. |
| `contact_point` | Contact person column (if present) | May not be included in the CSV export. Likely `None`. |
| `phone` | Phone column (if present) | May not be included in the CSV export. Likely `None`. |
| `email` | Email column (if present) | May not be included in the CSV export. Likely `None`. |
| `url_general` | URL column (if present) or link to notice on kozbeszerzes.hu | The CRCB dataset includes links to notices. The official CSV may or may not. |
| `url_buyer` | `None` | Not expected in CSV export. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `official_name` | Contracting authority name (e.g. `Ajánlatkérő neve`) | This is a standard field in Hungarian result notices. |
| `address` | Address column (e.g. `Ajánlatkérő címe`) | May be a single combined address string or separate street/city/postal fields. |
| `town` | Town/city column (e.g. `Város` or `Település`) | May be embedded in the address field. |
| `postal_code` | Postal code column (e.g. `Irányítószám`) | May be embedded in the address field. |
| `country_code` | Hardcode `"HU"` or from a country column | Almost all contracting authorities will be Hungarian. Hardcode `"HU"` unless a column exists. |
| `nuts_code` | NUTS code column (e.g. `NUTS kód`) | Hungarian F03 forms include NUTS codes. Whether the CSV includes them is unknown. |
| `authority_type` | Authority type column (e.g. `Ajánlatkérő típusa`) | See Code Normalization below. Values will be in Hungarian. |
| `main_activity_code` | Main activity column (e.g. `Fő tevékenység`) | See Code Normalization below. Values will be in Hungarian. |

#### ContractModel

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `title` | Contract/procedure title (e.g. `A szerződés megnevezése` or `Tárgy`) | Standard field in result notices. |
| `short_description` | Description column (e.g. `Rövid leírás`) | May be truncated in CSV export. |
| `main_cpv_code` | Main CPV code column (e.g. `Fő CPV kód`) | CPV codes are standardized EU-wide (numeric format like `45000000`). |
| `cpv_codes` | Main + additional CPV columns (e.g. `Kiegészítő CPV kód(ok)`) | Additional CPV codes may be in a separate column, comma-separated, or absent. |
| `nuts_code` | NUTS code for place of performance (e.g. `Teljesítés helye NUTS kód`) | Separate from the contracting authority NUTS code. |
| `contract_nature_code` | Contract type column (e.g. `Szerződés típusa` or `Beszerzés tárgya`) | Hungarian values: `Építési beruházás` (works), `Árubeszerzés` (supplies), `Szolgáltatásmegrendelés` (services). Needs mapping to eForms codes. |
| `procedure_type` | Procedure type column (e.g. `Eljárás fajtája`) | Hungarian values need mapping. See Code Normalization below. |
| `accelerated` | Accelerated procedure indicator (if present) | Unlikely to be a separate column in the CSV. Default to `False`. |

#### AwardModel

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `award_title` | Award/lot title (e.g. `Rész megnevezése`) | May be the same as the contract title for single-lot procedures. |
| `contract_number` | Contract number (e.g. `Szerződés száma`) | May not be present in CSV. |
| `tenders_received` | Number of tenders column (e.g. `Beérkezett ajánlatok száma`) | Standard field in result notices. |
| `awarded_value` | Contract value column (e.g. `Szerződés értéke` or `A szerződés végleges összértéke`) | **Critical**: Verify whether values include VAT or not. The form distinguishes `ÁFA nélkül` (without VAT) vs `ÁFA-val` (with VAT). Parse as float. |
| `awarded_value_currency` | Currency column (e.g. `Pénznem`) | Typically `HUF` (Hungarian Forint). May also be `EUR` for some contracts. |
| `contractors` | See ContractorModel below | |

#### ContractorModel

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `official_name` | Winning tenderer name (e.g. `Nyertes ajánlattevő neve`) | Standard field. |
| `address` | Winner address (e.g. `Nyertes ajánlattevő címe`) | May be combined or separate fields. |
| `town` | Winner town (e.g. `Nyertes város`) | May be embedded in address. |
| `postal_code` | Winner postal code | May be embedded in address. |
| `country_code` | Winner country (e.g. `Nyertes ország`) | May need mapping from Hungarian country names to ISO codes. Mostly `"HU"`. |
| `nuts_code` | Winner NUTS code | Unlikely to be in CSV. Set to `None`. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `code` | CPV code numeric value (e.g. `45000000-7`) | Standard EU format. Parse the numeric portion. |
| `description` | CPV description (if present) | May be included in Hungarian. If not in CSV, set to `None`. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `code` | Procedure type column value, after mapping to eForms code | See Code Normalization below. |
| `description` | Hungarian procedure type text (raw value from CSV) | Useful for debugging. |

#### AuthorityTypeEntry

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `code` | Authority type column value, after mapping to eForms code | See Code Normalization below. |
| `description` | Hungarian authority type text (raw value from CSV) | Useful for debugging. |

### Unmappable Schema Fields

These fields will likely be `None` for Hungarian portal data:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | TED OJ edition number. No equivalent in national portal data. |
| `DocumentModel.reception_id` | TED-specific reception identifier. No equivalent. |
| `DocumentModel.official_journal_ref` | National notices have no OJ S reference. |
| `DocumentModel.dispatch_date` | May not be present as a separate field in the CSV. |
| `DocumentModel.contact_point` | Contact details are unlikely to be in the CSV summary export. |
| `DocumentModel.phone` | Same as above. |
| `DocumentModel.email` | Same as above. |
| `DocumentModel.url_buyer` | Not expected in CSV data. |
| `ContractingBodyModel.nuts_code` | May or may not be in the CSV. Needs verification. Likely `None`. |
| `ContractModel.nuts_code` | May or may not be in the CSV. Needs verification. Likely `None`. |
| `ContractModel.accelerated` | Unlikely to be present as a separate field. Default to `False`. |
| `ContractorModel.nuts_code` | Very unlikely to be in CSV. |
| `CpvCodeEntry.description` | May not be in CSV. Can be populated from a static CPV lookup table. |
| `ProcedureTypeEntry.description` | Populate from the raw Hungarian text or a static lookup. |
| `AuthorityTypeEntry.description` | Populate from the raw Hungarian text or a static lookup. |

### Extra Portal Fields

These fields may be available in the Hungarian portal data but are not covered by the current schema. Flagged for review.

| Portal Field (estimated) | Description | Notes |
|---|---|---|
| EU funding indicator | Whether the contract is part of an EU-funded project | Schema doesn't cover -- flagging for review. Important for cross-referencing with EU structural fund data. |
| Estimated value (`Becsült érték`) | Estimated contract value before award | Schema doesn't cover -- flagging for review. Useful for comparing estimated vs awarded value. |
| VAT indicator | Whether the awarded value includes or excludes VAT | Schema doesn't cover -- flagging for review. Critical for value comparability. |
| Lot number (`Rész sorszáma`) | Lot identifier within a multi-lot procedure | Schema doesn't cover lot-level granularity -- flagging for review. |
| Date of award decision (`Döntés dátuma`) | Date when the award decision was made | Schema doesn't cover -- flagging for review. Different from publication date. |
| Contract conclusion date | Date the contract was signed | Schema doesn't cover -- flagging for review. |
| Subcontracting information | Whether subcontracting is involved and its extent | Schema doesn't cover -- flagging for review. |
| SME status of winner | Whether the winning tenderer is an SME | Schema doesn't cover -- flagging for review. Required by Hungarian law for statistical reporting. |
| Tax number (`Adószám`) | Tax identification number of contracting authority or winner | Schema doesn't cover structured organization identifiers -- flagging for review. Very useful for entity deduplication. |
| Framework agreement indicator | Whether the award is under a framework agreement | Schema doesn't cover -- flagging for review. |
| Joint procurement indicator | Whether multiple contracting authorities procured jointly | Schema doesn't cover -- flagging for review. |

### Code Normalization

#### Contract Nature Codes (to eForms `contract-nature-types`)

Hungarian result notices use Hungarian-language descriptions for contract type. Mapping to eForms codes:

| Hungarian Value | eForms Code | Notes |
|---|---|---|
| `Építési beruházás` | `works` | Construction works |
| `Árubeszerzés` | `supplies` | Goods/supplies procurement |
| `Szolgáltatásmegrendelés` or `Szolgáltatás megrendelés` | `services` | Service procurement |

**Note**: The exact string values in the CSV may differ (e.g. abbreviations, capitalization variants). The implementing parser should normalize by lowercasing and checking for substring matches (e.g. `építési` -> `works`, `áru` -> `supplies`, `szolgáltatás` -> `services`). Unknown values should log a warning and return `None` per the project's fail-loud policy.

#### Procedure Type Codes (to eForms `procurement-procedure-type`)

Hungarian procurement law (Kbt. 2015 CXLIII) defines these procedure types. The CSV likely uses Hungarian names:

| Hungarian Value | eForms Code | Notes |
|---|---|---|
| `Nyílt eljárás` | `open` | Open procedure |
| `Meghívásos eljárás` | `restricted` | Restricted procedure |
| `Tárgyalásos eljárás` (with prior publication) | `neg-w-call` | Negotiated with prior call for competition |
| `Tárgyalásos eljárás közzététel nélkül` or `Hirdetmény nélküli tárgyalásos eljárás` | `neg-wo-call` | Negotiated without prior publication |
| `Versenypárbeszéd` | `comp-dial` | Competitive dialogue |
| `Innovációs partnerség` | `innovation` | Innovation partnership |
| `Közvetlen beszerzés` or `Hirdetmény közzététele nélküli eljárás` | `neg-wo-call` | Direct award / procedure without publication |
| `Gyorsított eljárás` variants | Base type + `accelerated=True` | Accelerated variants (e.g. `Gyorsított meghívásos eljárás` = restricted + accelerated) |

**Note**: The exact Hungarian strings in the CSV need verification. The implementing parser should use substring/keyword matching:
- `nyílt` -> `open`
- `meghívásos` -> `restricted`
- `tárgyalásos` -> `neg-w-call` (default) or `neg-wo-call` (if `nélkül`/`közzététel nélkül` is present)
- `versenypárbeszéd` -> `comp-dial`
- `innovációs` -> `innovation`
- `gyorsított` -> set `accelerated=True` and extract the base type

Unknown values should log a warning and return `None`.

#### Authority Type Codes (to eForms `buyer-legal-type`)

Hungarian result notices categorize contracting authorities. Expected Hungarian values and their eForms mappings:

| Hungarian Value | eForms Code | Notes |
|---|---|---|
| `Minisztérium vagy egyéb országos szerv` | `cga` | Ministry or other national body (central government authority) |
| `Regionális vagy helyi hatóság` or `Regionális/Helyi szintű` | `ra` | Regional or local authority |
| `Közjogi intézmény` or `Közjogi szervezet` | `body-pl` | Body governed by public law |
| `Európai intézmény/ügynökség` | `eu-ins-bod-ag` | EU institution/body/agency |
| `Nemzetközi szervezet` | `int-org` | International organisation |
| `Közszolgáltató szervezet` | `pub-undert` | Public undertaking |
| `Egyéb` | `None` | "Other" -- no eForms equivalent (consistent with TED v2 mapping) |

**Note**: The exact Hungarian strings need verification from the actual CSV data. This mapping is derived from the standard EU authority type categories and their Hungarian translations on TED forms. The implementing parser should use keyword-based matching with normalization (lowercase, strip whitespace).

#### Main Activity Codes

If present, these would be Hungarian translations of EU main activity categories (e.g. `Általános közszolgáltatások` = "General public services"). A full mapping table should be built after inspecting the actual CSV values. The eForms `main-activity` codelist values are: `defence`, `econ-aff`, `education`, `env-pro`, `gen-pub`, `hc-am`, `health`, `housing`, `pub-os`, `rec-am`, `social-am`, `gas-oil`, `port-rel`, `post`, `rail`, `urb-rlw`, `water`, `airport`, `electricity`, `exploration`.

### Implementation Recommendations

1. **Download and inspect the CSV first**: Before writing any parser code, download `https://kozbeszerzes.hu/media/documents/Eredménytájékoztatók_adatai.csv` and inspect: (a) the delimiter (semicolon vs comma), (b) encoding, (c) exact column names, (d) row granularity (per notice, per lot, or per award), (e) date formats, (f) value formats (decimal separator, thousand separator). Update this mapping document with the actual column names.

2. **Coverage limitation**: The CSV only covers April 2018 to June 2022. For ongoing data ingestion, the implementing agent must investigate whether the CSV is periodically updated (it appears to have stopped in September 2022) or whether an alternative approach is needed (e.g. scraping the web search interface at `kozbeszerzes.hu/adatbazis/keres/hirdetmeny/`).

3. **Deduplication with TED**: Above-threshold Hungarian notices are cross-published to TED. The implementing parser should either: (a) filter out above-threshold notices from the Hungarian data, or (b) use `doc_id` collision to skip duplicates. The CSV may contain a column indicating whether the notice was also published in the EU Official Journal.

4. **Address parsing**: Hungarian addresses in the CSV may be in a single concatenated field or split across multiple columns. The parser may need to extract town, postal code, and street from a combined string. Hungarian addresses typically follow the format: `{postal_code} {town}, {street} {number}`.

5. **Currency and value parsing**: Hungarian CSV files typically use comma as decimal separator and space or period as thousand separator (e.g. `1 234 567,89`). The `parsers/monetary.py` module may need a new Hungarian-locale parser. Currency will predominantly be `HUF` but `EUR` is also possible.

6. **Character encoding**: Hungarian uses accented characters (a, e, i, o, o, u, u and their uppercase equivalents). Ensure the CSV reader handles the correct encoding (likely UTF-8 or Windows-1252).

7. **Multi-lot handling**: If the CSV has one row per lot/award rather than per notice, the parser must group rows by notice identifier to construct a single `AwardDataModel` with multiple `AwardModel` entries.

8. **CRCB as fallback for historical data**: For data before April 2018, the CRCB dataset (2005-2021) could serve as a supplementary source, though it is a third-party research dataset with potentially different field granularity.
