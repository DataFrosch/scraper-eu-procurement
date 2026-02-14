# Croatia (HR)

**Feasibility: Tier 2**

## Portal

- **Name**: EOJN RH (Electronic Public Procurement Portal)
- **URL**: https://eojn.hr/
- **OCP Registry**: https://data.open-contracting.org/en/publication/80

## Data Access

- **Method**: Monthly open data exports from contract register
- **Format**: JSON (OCDS)
- **Auth**: Open
- **OCDS**: Yes (partial — ~11% of JSON files reported as invalid)

## Coverage

All public procurement procedures and concessions.

## Language

Croatian

## Notes

- Data quality issues — about 11% of JSON files are invalid and excluded from OCP data registry
- OCDS data exists but reliability is a concern

## Schema Mapping

### Data Format Notes

Croatia publishes OCDS (Open Contracting Data Standard) data as **JSON release packages** via monthly ZIP file exports. The download page is at `https://eojn.nn.hr/SPIN/application/ipn/Oglasnik/PreuzimanjeUgovoraOCD.aspx`. This is an ASP.NET WebForms page — individual monthly ZIP files are downloaded by posting form data with the file ID to the page (not direct URLs). The Kingfisher Collect [Croatia spider](https://github.com/open-contracting/kingfisher-collect/blob/main/kingfisher_scrapy/spiders/croatia.py) serves as the reference implementation.

**Download mechanism**: The page lists download links as `<td><a id="...">` elements. Each file is downloaded by submitting an ASP.NET `__doPostBack` form with `__EVENTTARGET` set to the link ID (replacing `_` with `$`). A browser-like User-Agent header is required. The response is a ZIP file containing one or more JSON files, each being an OCDS release package.

**OCDS version**: Standard OCDS 1.1 without extensions. No custom fields or additional schemas are used.

**Key parsing considerations**:
- Each ZIP contains JSON files that are OCDS release packages (`data_type = "release_package"`)
- Each release package has a `releases` array containing individual OCDS releases
- About 11% of JSON files are invalid (malformed JSON or schema violations) — the parser must handle `json.JSONDecodeError` gracefully and skip invalid files with a warning
- The `validate_json = True` setting in the Kingfisher spider confirms JSON validity is a known issue
- Only releases with `tag` containing `"award"` or `"contract"` should be processed (to match our award-only focus)
- Source country is always `HR`
- Currency is HRK (Croatian Kuna) for historical data and EUR from 1 January 2023 onwards (Croatia adopted the euro). Always read `awards[].value.currency` rather than assuming.
- No organizational identifier schemes are provided (no `parties[].identifier.scheme`) — entity deduplication relies on exact name matching only
- Language is Croatian — all text fields (titles, descriptions, names) will be in Croatian

**Recommended approach**: Iterate over all monthly ZIP files from the download page. For each ZIP, extract JSON files, parse as OCDS release packages, and process each release that contains award data. Skip invalid JSON files with a warning.

### Field Mapping Tables

In OCDS, organization details (buyer, supplier) are stored in a top-level `parties` array, with `OrganizationReference` objects (containing `id` and `name`) in `tender.procuringEntity`, `awards[].suppliers[]`, etc. To get full address details, the parser must cross-reference the `id` in the reference to the matching entry in the `parties` array.

OCDS path notation below uses dot-separated paths within each release object.

#### DocumentModel

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `doc_id` | `ocid` | The OCDS contracting process identifier. Format: `ocds-xxxxxx-NNNNNN`. Use as-is for doc_id — globally unique across OCDS publishers. |
| `edition` | (none) | Set to `None`. OCDS has no edition concept. |
| `version` | (none) | Set to `None`. Could use `releases[].id` but no clear semantic equivalent. |
| `reception_id` | (none) | Set to `None`. TED-specific concept, no OCDS equivalent. |
| `official_journal_ref` | (none) | Set to `None`. EOJN is not an official journal in the OJ sense. |
| `publication_date` | `releases[].date` | ISO 8601 datetime string. Parse the date portion only. |
| `dispatch_date` | (none) | Set to `None`. TED-specific concept (date sent to OJ). No clean OCDS equivalent. |
| `source_country` | (hardcoded) | Always `"HR"`. |
| `contact_point` | `parties[buyer].contactPoint.name` | Cross-reference the buyer party from `parties` array using `buyer.id` or by finding the party with `"buyer"` in `roles`. |
| `phone` | `parties[buyer].contactPoint.telephone` | Cross-reference via buyer party. |
| `email` | `parties[buyer].contactPoint.email` | Cross-reference via buyer party. |
| `url_general` | `parties[buyer].contactPoint.url` | Cross-reference via buyer party. |
| `url_buyer` | (none) | Standard OCDS has no separate buyer profile URL. Set to `None`. |

#### ContractingBodyModel

Identify the buyer/procuring entity by finding the party with `"buyer"` or `"procuringEntity"` in its `roles` array, or via the `buyer.id` reference at the release level.

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `official_name` | `parties[buyer].name` | Organization name, in Croatian. |
| `address` | `parties[buyer].address.streetAddress` | Street address. |
| `town` | `parties[buyer].address.locality` | City/town name, in Croatian. |
| `postal_code` | `parties[buyer].address.postalCode` | Postal code. |
| `country_code` | `parties[buyer].address.countryName` | **Needs normalization**: OCDS uses full country name (likely in Croatian, e.g., `"Hrvatska"`), not ISO code. Hardcode `"HR"` for buyer entities since all EOJN data is Croatian. For non-Croatian entities (unlikely but possible), build a lookup table from Croatian country names to ISO codes. |
| `nuts_code` | (none) | OCDS does not have a standard NUTS code field. `address.region` is free text (if present at all). Set to `None`. |
| `authority_type` | (none) | Not part of standard OCDS. No extensions are used in the Croatian data. Set to `None`. |
| `main_activity_code` | (none) | Not part of standard OCDS. Set to `None`. |

#### ContractModel

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `title` | `tender.title` | Contract/tender title, in Croatian. |
| `short_description` | `tender.description` | Tender description text, in Croatian. |
| `main_cpv_code` | `tender.items[0].classification.id` | Take the first item's classification where `scheme == "CPV"`. If `tender.classification` exists (non-standard but sometimes present), prefer it. |
| `cpv_codes` | `tender.items[].classification` + `tender.items[].additionalClassifications[]` | Collect all classifications where `scheme == "CPV"`. Use `id` for code and `description` for description. Deduplicate by code. |
| `nuts_code` | (none) | OCDS `tender.items[].deliveryLocation` or `tender.items[].deliveryAddress` may exist but are not guaranteed to contain NUTS codes. Set to `None` unless data inspection reveals NUTS codes are populated. |
| `contract_nature_code` | `tender.mainProcurementCategory` | OCDS values: `"goods"`, `"works"`, `"services"`. Requires mapping — see Code Normalization section. |
| `procedure_type` | `tender.procurementMethod` + `tender.procurementMethodDetails` | OCDS `procurementMethod` is a 4-value codelist (`"open"`, `"selective"`, `"limited"`, `"direct"`). `procurementMethodDetails` contains the more specific procedure name in Croatian. Requires mapping — see Code Normalization section. |
| `accelerated` | `tender.procurementMethodDetails` | OCDS has no dedicated accelerated flag. If `procurementMethodDetails` contains an accelerated procedure indicator (Croatian: "ubrzani"), set `True`. Otherwise `False`. Needs data inspection to confirm exact strings. |

#### AwardModel

Each entry in the `awards[]` array maps to one AwardModel.

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `award_title` | `awards[].title` | Award title. May be `None` if not populated. |
| `contract_number` | `awards[].id` or `contracts[].id` | OCDS links contracts to awards via `contracts[].awardID`. Use `contracts[].id` if available, else fall back to `awards[].id`. |
| `tenders_received` | `tender.numberOfTenderers` | This is at the tender level, not per-award. The Croatian data does not use the bids extension (no extensions are used). May not be populated — needs data inspection. |
| `awarded_value` | `awards[].value.amount` | Monetary amount as a number. |
| `awarded_value_currency` | `awards[].value.currency` | ISO 4217 currency code. Will be `"HRK"` for pre-2023 data and `"EUR"` from 2023 onwards. |
| `contractors` | `awards[].suppliers[]` | Array of `OrganizationReference` objects. Must cross-reference the `parties` array for full details using supplier `id`. |

#### ContractorModel

Contractor details come from the `parties` array, resolved via `awards[].suppliers[].id`.

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `official_name` | `parties[supplier].name` | Supplier organization name, in Croatian. |
| `address` | `parties[supplier].address.streetAddress` | Street address. |
| `town` | `parties[supplier].address.locality` | City/town. |
| `postal_code` | `parties[supplier].address.postalCode` | Postal code. |
| `country_code` | `parties[supplier].address.countryName` | **Needs normalization**: OCDS uses full country name (likely Croatian-language), not ISO code. Must map from country name to ISO 3166-1 alpha-2 code. Build a Croatian-to-ISO lookup or use `pycountry` with Croatian locale. |
| `nuts_code` | (none) | Not available in standard OCDS. Set to `None`. |

#### CpvCodeEntry

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `code` | `tender.items[].classification.id` (where `scheme == "CPV"`) | CPV code string (e.g., `"45000000"`). |
| `description` | `tender.items[].classification.description` | May be in Croatian. |

#### ProcedureTypeEntry

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `code` | Derived from `tender.procurementMethod` | Requires mapping from OCDS values to eForms codes. See Code Normalization section. |
| `description` | `tender.procurementMethodDetails` | Free-text field, in Croatian. |

#### AuthorityTypeEntry

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `code` | (none) | Not available in standard OCDS and no extensions are used. Always `None`. |
| `description` | (none) | Always `None`. |

### Unmappable Schema Fields

The following schema fields have no equivalent in the Croatian OCDS data and should be set to `None`:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | TED-specific concept (OJ edition). Not present in OCDS. |
| `DocumentModel.version` | No semantic equivalent in OCDS. |
| `DocumentModel.reception_id` | TED-specific internal identifier. Not present in OCDS. |
| `DocumentModel.official_journal_ref` | TED-specific OJ reference. Not present in OCDS. |
| `DocumentModel.dispatch_date` | TED-specific concept (date sent to OJ). No OCDS equivalent. |
| `DocumentModel.url_buyer` | Standard OCDS has no separate buyer profile URL field. |
| `ContractingBodyModel.nuts_code` | OCDS does not include NUTS codes. `address.region` is free text if present. |
| `ContractingBodyModel.authority_type` | Not part of standard OCDS. No extensions used in Croatian data. |
| `ContractingBodyModel.main_activity_code` | Not part of standard OCDS. |
| `ContractModel.nuts_code` | OCDS delivery location does not reliably provide NUTS codes. |
| `ContractorModel.nuts_code` | Not available in standard OCDS. |

### Extra Portal Fields

The following fields are available in OCDS releases but not covered by the current schema. Flagged for review:

| OCDS Field | Description | Notes |
|---|---|---|
| `parties[].identifier.id` | Legal entity identifier (OIB — Croatian Personal Identification Number for legal entities) | **High value** — schema does not cover entity identifiers. Would enable cross-referencing entities across portals. However, OCP notes that no identifier schemes are provided in Croatian data, so this field may be empty or inconsistently populated. Needs data inspection. |
| `parties[].identifier.legalName` | Registered legal name | May differ from `name` (trading name). schema does not cover -- flagging for review. |
| `awards[].date` | Award decision date | schema does not cover -- flagging for review. Distinct from publication date. Useful for timeline analysis. |
| `awards[].status` | Award status (`"active"`, `"cancelled"`, etc.) | schema does not cover -- flagging for review. Useful for filtering out cancelled awards. |
| `contracts[].period` | Contract execution period (start/end dates) | schema does not cover -- flagging for review. |
| `contracts[].value` | Contract value (may differ from award value) | schema does not cover -- flagging for review. |
| `tender.status` | Tender status | schema does not cover -- flagging for review. |
| `tender.tenderPeriod` | Tender submission period (start/end dates) | schema does not cover -- flagging for review. |
| `tender.value` | Estimated tender value | schema does not cover -- flagging for review. Pre-award estimated total value. |
| `tender.documents[]` | Tender documents with URLs | schema does not cover -- flagging for review. |
| `implementation` | Implementation stage data (transactions, milestones) | schema does not cover -- flagging for review. Unlikely to be populated given partial OCDS compliance. |

### Code Normalization

Our schema uses exact eForms codes (lowercase, hyphens) for all coded values. OCDS uses its own codelists. The following mappings are needed:

#### Contract Nature Code (`tender.mainProcurementCategory` -> eForms)

OCDS `tender.mainProcurementCategory` values must be mapped to eForms `contract-nature-types` codes:

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"goods"` | `"supplies"` | OCDS uses "goods", eForms uses "supplies" |
| `"works"` | `"works"` | Direct match |
| `"services"` | `"services"` | Direct match |
| (missing/other) | `None` | Log warning |

#### Procedure Type Code (`tender.procurementMethod` -> eForms)

OCDS `tender.procurementMethod` is a coarse 4-value codelist. Croatia does not use OCDS extensions, so `procurementMethodDetails` (free text in Croatian) is the only source of additional granularity. The mapping from OCDS to eForms:

| OCDS `procurementMethod` | eForms Code | Notes |
|---|---|---|
| `"open"` | `"open"` | Direct match |
| `"selective"` | `"restricted"` | OCDS "selective" = eForms "restricted" (pre-qualified bidders). If `procurementMethodDetails` indicates competitive dialogue or innovation partnership, refine further — but this requires Croatian-language text parsing. |
| `"limited"` | `"neg-w-call"` | Best approximation. OCDS "limited" covers negotiated procedures with a limited pool. |
| `"direct"` | `"neg-wo-call"` | Direct award without competition = negotiated without prior call for competition |
| (missing/other) | `None` | Log warning |

**Croatian procedure type terms** (for potential `procurementMethodDetails` parsing):
- "Otvoreni postupak" = Open procedure
- "Ograniceni postupak" = Restricted procedure
- "Natjecateljski postupak uz pregovore" = Competitive procedure with negotiation
- "Natjecateljski dijalog" = Competitive dialogue
- "Partnerstvo za inovacije" = Innovation partnership
- "Pregovarecki postupak bez prethodne objave" = Negotiated without prior publication
- "Pregovarecki postupak s prethodnom objavom" = Negotiated with prior publication

**Recommended approach**: Start with the coarse OCDS `procurementMethod` mapping above. Store `procurementMethodDetails` in `ProcedureTypeEntry.description`. A future refinement pass could parse the Croatian text to disambiguate `"selective"` into `"restricted"`, `"neg-w-call"`, `"comp-dial"`, or `"innovation"`.

#### Authority Type Code

Not available in Croatian OCDS data. Always `None`.

#### Country Code Normalization

OCDS `address.countryName` is free text, likely in Croatian (e.g., `"Hrvatska"` for Croatia, `"Slovenija"` for Slovenia). Must be mapped to ISO 3166-1 alpha-2 codes. Options:
- Hardcode `"HR"` for buyer entities (all EOJN data is Croatian)
- For supplier country names, build a Croatian-to-ISO lookup table covering common trading partners (HR, SI, BA, RS, DE, AT, IT, HU, etc.)
- Consider using `pycountry` with Croatian translations if available
- **Needs data inspection**: Confirm whether `countryName` is actually populated and what language/format is used

### Data Quality Warnings

Based on OCP Data Registry assessment and the Kingfisher Collect spider:

- **Invalid JSON**: About 11% of JSON files are invalid. Parser must wrap JSON parsing in try/except and skip invalid files with a warning.
- **No identifier schemes**: `parties[].identifier.scheme` is not provided. Entity deduplication can only rely on exact name matching.
- **ASP.NET download mechanism**: The download page uses ASP.NET WebForms postback — requires form scraping and `__VIEWSTATE`/`__EVENTVALIDATION` handling. The Kingfisher spider uses `scrapy.FormRequest.from_response()` for this.
- **Monthly granularity**: Data is published in monthly batches. There is no real-time API or date-range query parameter — each file covers one month.
- **Coverage gaps**: The HR.md notes indicate "partial" OCDS compliance. Field coverage may be uneven — some releases may be missing tender, award, or party data. The parser should handle missing sections gracefully (treat as `None` rather than failing).
- **Currency transition**: Croatia switched from HRK to EUR on 2023-01-01. The parser must handle both currencies correctly and always read the `currency` field from the data.

### Implementation Notes

1. **Party resolution is central**: OCDS stores organization details in the `parties` array and references them by ID elsewhere. The parser must build an `{id: party}` lookup dict first, then resolve buyer and supplier references. Handle missing cross-references gracefully (supplier ID in award but no matching party).

2. **Multiple awards per release**: A single OCDS release can contain multiple awards. Each maps to a separate `AwardModel`. All share the same `DocumentModel`, `ContractingBodyModel`, and `ContractModel`.

3. **doc_id construction**: Use the `ocid` as `doc_id`. OCDS `ocid` values are globally unique. If multiple releases exist for the same `ocid` (e.g., tender then award), only process the award release. If reimporting, the existing document with the same `doc_id` will be skipped (idempotent per project convention).

4. **Download implementation**: Unlike TED (sequential URL pattern), Croatia requires scraping an ASP.NET page. The spider must: (a) GET the download page, (b) extract link IDs and `__VIEWSTATE`/`__EVENTVALIDATION` tokens, (c) POST to download each ZIP file. Consider using `requests` with session handling, or adapt the Kingfisher Collect approach.

5. **Year-based filtering**: The project CLI uses `--start-year` and `--end-year`. Monthly files likely have date-based names or can be associated with year/month from the download page. The spider should map files to years for selective download/import.
