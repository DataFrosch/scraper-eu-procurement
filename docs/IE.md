# Ireland (IE)

**Feasibility: Tier 2**

## Portal

- **Name**: eTenders
- **URL**: https://www.etenders.gov.ie/
- **Platform provider**: EU-Supply
- **Open data**: https://www.gov.ie/en/office-of-government-procurement/collections/opendata/
- **data.gov.ie**: https://data.gov.ie/dataset/?tags=Procurement

## Data Access

- **Method**: API available + open data portal
- **Format**: JSON, CSV
- **Auth**: Open
- **OCDS**: No

## Coverage

All award details >25,000 EUR (ex VAT). Below-EU-threshold contracts.

## Language

English

## Notes

- API exists but specifics need verification
- OCP entry: https://data.open-contracting.org/en/publication/58

## Schema Mapping

### Data Sources

Ireland has two distinct open data exports from eTenders, both CSV:

1. **Public Procurement Open Data Dataset** (primary, recommended):
   - URL: `https://assets.gov.ie/static/documents/7ba65f1b/Public_Procurement_Opendata_Dataset.csv`
   - Published at: https://data.gov.ie/dataset/contract-notices-published-on-etenders
   - ~100,000 rows, single file covering all years (both notices and awards)
   - 30 columns with rich structured data (CPV codes, procedure types, award values, bid counts, supplier names)
   - Contains both awarded and not-yet-awarded tenders; filter on `Award Published != NULL` for awards only

2. **Quarterly Award Summaries** (secondary, less useful):
   - Published at: https://www.gov.ie/en/office-of-government-procurement/collections/contract-awards-for-standalone-and-mini-competitions/
   - Quarterly CSV files, only 8 columns (no award value, no procedure type, no bid count)
   - Only covers mini-competitions and standalone awards, not all awards
   - Columns: `Name of Contracting Authority`, `Name of Client Contracting Authority`, `Title of Contract`, `Suppliers`, `ContractAwardConfirmedDate`, `Contract Start Date`, `Contract End Date`, `Common Procurement Vocabulary (CPV) codes`

**Recommendation**: Use source (1) exclusively. Source (2) is a strict subset with far fewer fields.

No real API exists. The "API available" note in the Data Access section is inaccurate -- the data is a single downloadable CSV file, not a queryable API endpoint. The data.gov.ie portal uses CKAN which exposes a metadata API, but the actual data is a static CSV download.

### Primary Dataset Columns

The Public Procurement Open Data Dataset has these 30 columns:

| # | Column Name | Example Value |
|---|-------------|---------------|
| 1 | Tender ID | `7084262` |
| 2 | Parent Agreement ID | `NULL` or framework ID |
| 3 | Contracting Authority | `Roscommon County Council` |
| 4 | Name of Client Contracting Authority | `NULL` or delegated body name |
| 5 | Agreement Owner | `NULL` |
| 6 | Tender/Contract Name | `Supply of 60no. Self Contained Breathing Apparatus Sets` |
| 7 | Notice Published Date/Contract Created Date | `28/11/2025` (DD/MM/YYYY) |
| 8 | Directive | `Classic`, `Utilities`, or `Defence` |
| 9 | Competition Type | `Bespoke` or `Framework` |
| 10 | Main Cpv Code | `35111100` |
| 11 | Main Cpv Code Description | `Breathing apparatus for firefighting.` |
| 12 | Additional CPV Codes on CFT | `35111100;44611200` (semicolon-separated) |
| 13 | Spend Category | `Defence`, `Professional Services`, etc. |
| 14 | Contract Type | `Services`, `Supplies`, `Works`, `Work Related Services`, `Concession` |
| 15 | Threshold Level | `National` or `OJEU` |
| 16 | Procedure | `Open Procedure`, `Restricted Procedure`, etc. |
| 17 | Tender Submission Deadline | `19/12/2025` (DD/MM/YYYY) |
| 18 | Evaluation Type | `MEAT` or `Lowest Price` |
| 19 | Notice Estimated Value (EUR) | `160000` (numeric, euros, no currency symbol) |
| 20 | Contract Duration (Months) | `6` |
| 21 | Cancelled Date | `NULL` or `DD/MM/YYYY` |
| 22 | Award Published | `NULL` or `DD/MM/YYYY` |
| 23 | Awarded Value (EUR) | `159600` (numeric, euros) |
| 24 | No of Bids Received | `1` |
| 25 | No of SMEs Bids Received | `1` |
| 26 | Awarded Suppliers | `\| Respro Ltd` or `\| BWG Foods \| Sysco Ireland` (pipe-delimited, leading pipe) |
| 27 | No of Awarded SMEs | `1` |
| 28 | TED Notice Link | `NULL` or `https://ted.europa.eu/en/notice/-/detail/...` |
| 29 | TED CAN Link | `NULL` or TED contract award notice URL |
| 30 | Platform | `ED Platform` or `EUS Platform` |

### Field Mapping: DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `Tender ID` | Numeric ID from eTenders. Prefix with `IE-` to avoid collision with TED doc_ids (e.g., `IE-7084262`). |
| `edition` | -- | `None`. Not available in the portal data. |
| `version` | -- | `None`. Not available in the portal data. |
| `reception_id` | -- | `None`. Not available in the portal data. |
| `official_journal_ref` | -- | `None`. Not an OJ publication. Could optionally store the `TED Notice Link` or `TED CAN Link` here if present, but these are TED references, not OJ references. |
| `publication_date` | `Notice Published Date/Contract Created Date` | Parse from DD/MM/YYYY format. This is the notice publication date, not the award date. For awarded contracts, `Award Published` is the award publication date. Use `Award Published` as the publication_date since we are importing award notices. |
| `dispatch_date` | -- | `None`. Not available in the portal data. |
| `source_country` | -- | Hardcode to `"IE"`. All records are Irish procurement. |
| `contact_point` | -- | `None`. Not available in the portal data. |
| `phone` | -- | `None`. Not available in the portal data. |
| `email` | -- | `None`. Not available in the portal data. |
| `url_general` | `TED Notice Link` | Use if present, otherwise `None`. |
| `url_buyer` | -- | `None`. Not available in the portal data. |

### Field Mapping: ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `Contracting Authority` | Always populated. If `Name of Client Contracting Authority` is non-NULL, the actual buyer is the client; `Contracting Authority` is the framework owner (e.g., "The Office of Government Procurement"). Use `Name of Client Contracting Authority` when available, falling back to `Contracting Authority`. |
| `address` | -- | `None`. Not available in the portal data. |
| `town` | -- | `None`. Not available in the portal data. |
| `postal_code` | -- | `None`. Not available in the portal data. |
| `country_code` | -- | Hardcode to `"IE"`. |
| `nuts_code` | -- | `None`. Not available in the portal data. |
| `authority_type` | -- | `None`. Not available in the portal data. The `Directive` field (`Classic`/`Utilities`/`Defence`) is related but does not map to eForms authority type codes. |
| `main_activity_code` | -- | `None`. Not available in the portal data. |

### Field Mapping: ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `Tender/Contract Name` | Always populated. |
| `short_description` | -- | `None`. Not available in the portal data. |
| `main_cpv_code` | `Main Cpv Code` | Numeric CPV code (e.g., `35111100`). Always populated for the primary dataset. |
| `cpv_codes` | `Main Cpv Code` + `Additional CPV Codes on CFT` | Parse `Additional CPV Codes on CFT` by splitting on `;`. Includes the main code. The `Main Cpv Code Description` column provides the description for the main CPV code; additional CPV codes have no descriptions in the data. |
| `nuts_code` | -- | `None`. Not available in the portal data. |
| `contract_nature_code` | `Contract Type` | Needs mapping to eForms codes. See Code Normalization section below. |
| `procedure_type` | `Procedure` | Needs mapping to eForms codes. See Code Normalization section below. Often `NULL` in the data (most rows use the old EUS Platform which did not capture this). |
| `accelerated` | -- | `False`. Not available in the portal data. |

### Field Mapping: AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | -- | `None`. Not available separately from contract title. Could reuse `Tender/Contract Name` but that duplicates the contract title. |
| `contract_number` | `Tender ID` | Use the eTenders Tender ID as the contract number. |
| `tenders_received` | `No of Bids Received` | Integer. May be `NULL`. |
| `awarded_value` | `Awarded Value (€)` | Float, in euros. May be `0` for framework agreements (where individual call-off values are not recorded). May be `NULL` for unaward records. |
| `awarded_value_currency` | -- | Hardcode to `"EUR"`. All values are in euros. |
| `contractors` | `Awarded Suppliers` | See contractor mapping below. |

### Field Mapping: ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `Awarded Suppliers` | Pipe-delimited list with leading pipe: `\| Name1 \| Name2`. Split on `\|`, strip whitespace, skip empty strings. Each name becomes a separate ContractorModel. |
| `address` | -- | `None`. Not available in the portal data. |
| `town` | -- | `None`. Not available in the portal data. |
| `postal_code` | -- | `None`. Not available in the portal data. |
| `country_code` | -- | `None`. Not available in the portal data. Could default to `"IE"` but per project rules ("no defaults, no fallbacks"), leave as `None`. |
| `nuts_code` | -- | `None`. Not available in the portal data. |

### Field Mapping: CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `Main Cpv Code` and values from `Additional CPV Codes on CFT` | Numeric string (e.g., `"35111100"`). Split additional codes on `;`. |
| `description` | `Main Cpv Code Description` | Only available for the main CPV code. Additional codes will have `None` for description. |

### Field Mapping: ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `Procedure` | Needs mapping to eForms codes. See Code Normalization section. |
| `description` | `Procedure` | Use the raw portal value as the description. |

### Unmappable Schema Fields

The following schema fields cannot be populated from the Irish portal data and will always be `None`:

**DocumentModel**: `edition`, `version`, `reception_id`, `official_journal_ref`, `dispatch_date`, `contact_point`, `phone`, `email`, `url_buyer`

**ContractingBodyModel**: `address`, `town`, `postal_code`, `nuts_code`, `authority_type`, `main_activity_code`

**ContractModel**: `short_description`, `nuts_code`

**AwardModel**: `award_title`

**ContractorModel**: `address`, `town`, `postal_code`, `country_code`, `nuts_code`

This is a significant number of unmappable fields. The Irish data is notably sparse compared to TED -- it is essentially a flat table of contract awards with no structured address data for either buyers or suppliers.

### Extra Portal Fields

The following portal fields are not covered by the current schema. Flagging for review:

| Portal Field | Description | Notes |
|---|---|---|
| `Parent Agreement ID` | Links mini-competition awards back to framework agreements | Schema doesn't cover framework linkage -- flagging for review. |
| `Name of Client Contracting Authority` | The actual buyer when OGP or another central body runs the procurement | Schema has a single `contracting_body`; this second authority name is not captured -- flagging for review. |
| `Agreement Owner` | Owner of the framework agreement | Schema doesn't cover -- flagging for review. |
| `Directive` | EU directive type: `Classic`, `Utilities`, `Defence` | Schema doesn't cover -- flagging for review. |
| `Competition Type` | `Bespoke` (one-off) vs `Framework` (call-off) | Schema doesn't cover -- flagging for review. |
| `Spend Category` | OGP classification (e.g., "Professional Services", "Defence") | Schema doesn't cover -- flagging for review. |
| `Threshold Level` | `National` (below EU threshold) vs `OJEU` (above) | Schema doesn't cover -- flagging for review. Useful for filtering since TED already covers OJEU-level tenders. |
| `Tender Submission Deadline` | Deadline for bid submissions | Schema doesn't cover -- flagging for review. |
| `Evaluation Type` | `MEAT` (Most Economically Advantageous Tender) or `Lowest Price` | Schema doesn't cover -- flagging for review. |
| `Notice Estimated Value (€)` | Estimated contract value at notice stage | Schema only has `awarded_value`, not estimated value -- flagging for review. |
| `Contract Duration (Months)` | Duration of the contract | Schema doesn't cover -- flagging for review. |
| `Cancelled Date` | Date the tender was cancelled (if applicable) | Schema doesn't cover cancellation -- flagging for review. |
| `No of SMEs Bids Received` | SME-specific bid count | Schema has `tenders_received` but not SME breakdown -- flagging for review. |
| `No of Awarded SMEs` | Number of awarded suppliers that are SMEs | Schema doesn't cover -- flagging for review. |
| `TED CAN Link` | Link to the TED Contract Award Notice | Schema doesn't cover; could be used to cross-reference with TED data already in DB -- flagging for review. |
| `Platform` | `ED Platform` (new European Dynamics) or `EUS Platform` (old EU-Supply) | Schema doesn't cover -- flagging for review. |

### Code Normalization

#### Contract Nature Codes (Contract Type -> eForms)

| Portal Value | eForms Code | Notes |
|---|---|---|
| `Services` | `services` | Direct mapping. |
| `Supplies` | `supplies` | Direct mapping. |
| `Works` | `works` | Direct mapping. |
| `Work Related Services` | `services` | No direct eForms equivalent. Map to `services` as it covers services related to works. |
| `Concession` | `services` or `works` | Ambiguous -- concessions can be for services or works. The portal does not distinguish. Map to `services` as a fallback, or leave as `None` and log a warning. |

#### Procedure Type Codes (Procedure -> eForms)

| Portal Value | eForms Code | Notes |
|---|---|---|
| `Open Procedure` | `open` | Direct mapping. ~76,000 rows. |
| `Restricted Procedure` | `restricted` | Direct mapping. ~4,800 rows. |
| `Competitive Dialogue` | `comp-dialogue` | Direct mapping. ~740 rows. |
| `Negotiated Procedure Without Prior Publication` | `neg-wo-call` | Direct mapping. ~370 rows. |
| `Innovation Partnership` | `innovation` | Direct mapping. ~9 rows. |
| `Competitive Procedure with Negotiation` | `comp-w-neg` | Direct mapping. ~3 rows. |
| `NULL` | `None` | Most rows (~62% of all data). Procedure is not recorded for many records, especially on the older EUS Platform. |
| Free-text variants | -- | Rare (< 5 rows total). Values like "Direct Award Contract" or "Negotiated Procedure for..." appear as free-text in the Procedure column due to data entry errors. Log a warning and set to `None`. |

#### Authority Type Codes

Not available in the portal data. Always `None`.

### Data Format Notes

- **Format**: Single CSV file, UTF-8 with BOM (`\xef\xbb\xbf`). Use `utf-8-sig` encoding when reading.
- **Size**: ~100,000 rows (as of February 2026), single file covering all years from ~2012 onwards.
- **Date format**: `DD/MM/YYYY` (European format). Parse with `strptime("%d/%m/%Y")`.
- **NULL representation**: Literal string `NULL` (not empty string, not Python None). Must explicitly check for `"NULL"` when parsing.
- **Currency**: All monetary values are in EUR. No currency column exists; this is implicit.
- **Supplier delimiter**: Pipe character (`|`) with leading pipe. E.g., `| Supplier1 | Supplier2`. Split on `|`, strip whitespace, filter out empty strings.
- **CPV code delimiter**: Semicolon (`;`) in the `Additional CPV Codes on CFT` column.
- **Quoting**: Standard CSV quoting for fields containing commas (e.g., contract titles with commas).
- **Incremental updates**: The CSV appears to be a full snapshot updated periodically. No incremental API. Re-download and diff against existing `doc_id` values to find new records. Existing records should be skipped (idempotent import).
- **Filtering for awards only**: Only import rows where `Award Published` is not `NULL`. Rows with `Award Published = NULL` are open/pending tenders, not completed awards.
- **Deduplication with TED**: Records with `Threshold Level = OJEU` are likely already in the database via TED. The `TED Notice Link` and `TED CAN Link` columns can be used to cross-reference. Consider either: (a) skipping OJEU-level records entirely, or (b) importing them with the `IE-` prefix and accepting duplicates. Decision needed.
- **Platform migration**: The portal migrated from EU-Supply (`EUS Platform`) to European Dynamics (`ED Platform`). Older records (EUS Platform) have fewer populated fields (procedure type, evaluation type, etc. are often NULL). Both platforms use the same CSV structure.
