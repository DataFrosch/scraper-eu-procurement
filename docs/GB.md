# United Kingdom (GB)

**Feasibility: Tier 1**

## Portals

1. **Find a Tender**: https://www.find-tender.service.gov.uk/ (above and below threshold since Feb 2025)
2. **Contracts Finder**: https://www.contractsfinder.service.gov.uk/ (legacy, still operational)

## Data Access

### Find a Tender API
- **Docs**: https://www.find-tender.service.gov.uk/Developer/Documentation
- **REST API spec**: https://www.find-tender.service.gov.uk/apidocumentation
- **OCDS releases**: https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages
- **OCDS records**: https://www.find-tender.service.gov.uk/api/1.0/ocdsRecordPackages
- **Bulk download**: Daily ZIP files with XML per notice; also on data.gov.uk

### Contracts Finder API
- **Docs**: https://www.contractsfinder.service.gov.uk/apidocumentation

### OCP Registry
- Find a Tender: https://data.open-contracting.org/en/publication/41
- Contracts Finder: https://data.open-contracting.org/en/publication/128

## Data Access Summary

- **Format**: JSON (OCDS 1.1.5 with extensions)
- **Auth**: Open, no authentication
- **OCDS**: Yes — full compliance

## Coverage

Since Feb 2025, both above and below threshold notices (except Scotland below threshold). Historical data on Contracts Finder.

## Language

English

## Notes

- Best-documented procurement API in Europe
- Open, OCDS-native, comprehensive
- Two portals with overlapping coverage — Find a Tender is the primary going forward

## Schema Mapping

Target portal: **Find a Tender** (primary, OCDS-native).

### Data Format Notes

- **Format**: JSON, OCDS 1.1.5 release packages
- **Endpoint**: `GET /api/1.0/ocdsReleasePackages`
- **Query parameters**: `stages` (filter by `award` to get award releases only), `limit`, `cursor` (cursor-based pagination), `updatedFrom`, `updatedTo` (ISO 8601 datetime strings)
- **Filtering for awards**: Use `?stages=award` to retrieve only award-stage releases
- **Extensions used**: EU extension, document details, suitability, contract completion, links, budget breakdown, pagination, amendment rationale classifications
- **OCDS identifier prefix**: `ocds-h6vhtk`
- **Pagination**: Cursor-based (`cursor` parameter). Follow `links.next` in the response to iterate through pages.
- **Rate limits**: Not explicitly documented; treat conservatively
- **Reference implementation**: [Kingfisher Collect uk_fts spider](https://github.com/open-contracting/kingfisher-collect/blob/main/kingfisher_scrapy/spiders/uk_fts.py) uses `from_date`/`until_date` parameters (default start: `2021-01-01T00:00:00`)

### OCDS Structure Overview

OCDS releases have a top-level `parties` array containing all organizations (buyers, suppliers) with full details. Other sections (`tender`, `awards`, `contracts`) reference parties by ID. The parser must resolve organization references by looking up party IDs in the `parties` array.

A single release may contain multiple awards (one per lot). Each award references its suppliers in `awards[].suppliers[]` (organization references with `id` and `name`), with full address details in the `parties` array.

### Field Mapping: DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `releases[].id` | OCDS release ID, unique within an `ocid`. Use `{ocid}-{release.id}` as a composite doc_id to ensure global uniqueness. |
| `edition` | `None` | No direct equivalent. Could synthesize from `releases[].date` (e.g., date-based edition). Set to `None`. |
| `version` | (hardcoded) | Set to `"OCDS-1.1.5"` or similar portal version identifier. |
| `reception_id` | `None` | TED-specific concept. Not present in OCDS. Set to `None`. |
| `official_journal_ref` | `None` | TED OJ reference. Not applicable to UK national portal. Set to `None`. |
| `publication_date` | `releases[].date` | ISO 8601 datetime string. Parse date portion. |
| `dispatch_date` | `releases[].date` | No separate dispatch date in OCDS. Use same as `publication_date` or set to `None`. |
| `source_country` | (hardcoded) | Always `"GB"` for this portal. |
| `contact_point` | `parties[buyer].contactPoint.name` | From the buyer party's `contactPoint.name`. Requires resolving buyer party from `parties` array. |
| `phone` | `parties[buyer].contactPoint.telephone` | From the buyer party's `contactPoint.telephone`. |
| `email` | `parties[buyer].contactPoint.email` | From the buyer party's `contactPoint.email`. |
| `url_general` | `parties[buyer].contactPoint.url` | From the buyer party's `contactPoint.url`. |
| `url_buyer` | `parties[buyer].details.buyerProfile` | EU extension field. May or may not be populated. |

### Field Mapping: ContractingBodyModel

Buyer/procuring entity details come from the `parties` array entry with `"buyer"` (or `"procuringEntity"`) in its `roles` array. Identify the buyer via `buyer.id` at the release level, then look up that ID in `parties[]`.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[buyer].name` | Organization name. |
| `address` | `parties[buyer].address.streetAddress` | Street address. |
| `town` | `parties[buyer].address.locality` | City/town. |
| `postal_code` | `parties[buyer].address.postalCode` | Postal code. |
| `country_code` | `parties[buyer].address.countryName` | OCDS uses full country name (e.g., `"United Kingdom"`), not ISO code. Must map to ISO 3166-1 alpha-2 code (`"GB"`). Alternatively, check if `parties[buyer].address.country` (2-letter code) is available via EU extension. |
| `nuts_code` | `parties[buyer].address.region` | OCDS `region` may contain a NUTS code or a region name. Needs inspection of actual data to confirm format. May require normalization. |
| `authority_type` | `parties[buyer].details.classifications[]` | EU extension. Look for classification where `scheme` is `"eu-buyer-legal-type"` or `"TED_CA_TYPE"`. The `id` field contains the authority type code. Requires mapping to eForms codes (see Code Normalization below). |
| `main_activity_code` | `parties[buyer].details.classifications[]` | EU extension. Look for classification where `scheme` is `"eu-main-activity"`. The `id` field contains the activity code. |

### Field Mapping: ContractModel

Contract-level information comes from the `tender` section (procurement-level info) and potentially `contracts[]` (post-award).

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `tender.title` | Tender/procurement title. |
| `short_description` | `tender.description` | Tender description text. |
| `main_cpv_code` | `tender.classification.id` | Main CPV code from the tender classification where `scheme` is `"CPV"`. |
| `cpv_codes` | `tender.classification` + `tender.additionalClassifications[]` + `tender.items[].classification` | Combine: main classification + additional classifications + item-level classifications, all where `scheme` is `"CPV"`. The `id` is the CPV code and `description` is available. Deduplicate by code. |
| `nuts_code` | `tender.items[].deliveryAddress.region` | Performance location from item delivery addresses. May also appear at `tender.deliveryAddresses[].region` (EU extension). Needs data inspection to confirm presence and format. |
| `contract_nature_code` | `tender.mainProcurementCategory` | OCDS values: `"goods"`, `"works"`, `"services"`. Map to eForms codes: `"goods"` -> `"supplies"`, `"works"` -> `"works"`, `"services"` -> `"services"`. See Code Normalization below. |
| `procedure_type` | `tender.procurementMethod` + `tender.procurementMethodDetails` | OCDS `procurementMethod` is a high-level codelist (`"open"`, `"selective"`, `"limited"`, `"direct"`). `procurementMethodDetails` contains the more specific procedure name (e.g., `"Open procedure"`, `"Restricted procedure"`, `"Competitive procedure with negotiation"`). Requires mapping to eForms codes. See Code Normalization below. |
| `accelerated` | `tender.procurementMethodDetails` | OCDS has no dedicated accelerated boolean. If `procurementMethodDetails` contains `"Accelerated"` (e.g., `"Accelerated restricted procedure"`), set `accelerated = True` and map the base procedure type. Otherwise `False`. Needs data inspection to confirm exact string values used. |

### Field Mapping: AwardModel

Each entry in the `awards[]` array maps to one AwardModel.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `awards[].title` | Award title. May be `null`. |
| `contract_number` | `awards[].id` or `contracts[].id` | OCDS `awards[].id` is a local identifier. Could also use `contracts[].awardID` to link. Use `awards[].id` as a fallback contract number, or check `contracts[]` for a contract number. |
| `tenders_received` | `bids.statistics[]` where `measure` is `"tenderers"` or `"bids"` | From the OCDS bids extension. Look for `bids.statistics[].measure == "validBids"` or `"bids"`, then use `bids.statistics[].value`. May also appear at lot level in `bids.statistics[].relatedLot`. If the bids extension is not populated, this field will be `None`. Also check `tender.numberOfTenderers` as a fallback. |
| `awarded_value` | `awards[].value.amount` | Monetary amount as a number. |
| `awarded_value_currency` | `awards[].value.currency` | ISO 4217 currency code (e.g., `"GBP"`). |
| `contractors` | `awards[].suppliers[]` | Array of organization references. Each supplier has `id` and `name`. Resolve full details from the `parties` array using the supplier `id`. |

### Field Mapping: ContractorModel

Contractor details come from the `parties` array, resolved via `awards[].suppliers[].id`.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[supplier].name` | Supplier organization name. |
| `address` | `parties[supplier].address.streetAddress` | Street address. |
| `town` | `parties[supplier].address.locality` | City/town. |
| `postal_code` | `parties[supplier].address.postalCode` | Postal code. |
| `country_code` | `parties[supplier].address.countryName` | Full country name in OCDS. Must map to ISO 3166-1 alpha-2. |
| `nuts_code` | `parties[supplier].address.region` | May contain NUTS code or region name. Needs data inspection. |

### Field Mapping: CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `tender.classification.id`, `tender.additionalClassifications[].id`, `tender.items[].classification.id` | CPV code string (e.g., `"45000000"`). Filter by `scheme == "CPV"`. |
| `description` | `tender.classification.description`, etc. | Human-readable CPV description. Available in OCDS classification objects. |

### Field Mapping: ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Derived from `tender.procurementMethod` + `tender.procurementMethodDetails` | Must be mapped to eForms codes. See Code Normalization below. |
| `description` | `tender.procurementMethodDetails` | Free-text procedure description as published. |

### Unmappable Schema Fields

These schema fields have no equivalent in the UK portal's OCDS data and will always be `None`:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | TED-specific OJ edition number. No OCDS equivalent. |
| `DocumentModel.reception_id` | TED-specific reception tracking. No OCDS equivalent. |
| `DocumentModel.official_journal_ref` | TED Official Journal reference. Not applicable to national portals. |
| `DocumentModel.dispatch_date` | TED-specific concept (date notice sent to OJ). Could reuse `releases[].date` but semantically different. Recommend `None`. |

### Extra Portal Fields (schema does not cover -- flagging for review)

The OCDS data from Find a Tender contains many fields not captured by the current schema:

| Portal Field | Description | Notes |
|---|---|---|
| `releases[].ocid` | OCDS procurement process identifier | Globally unique procurement ID (`ocds-h6vhtk-xxxxxx`). Useful for linking releases across the lifecycle. |
| `releases[].tag` | Release type tag | e.g., `"award"`, `"tender"`, `"planning"`. Useful for filtering. |
| `awards[].date` | Award decision date | Date the award was made, separate from publication date. |
| `awards[].status` | Award status | e.g., `"active"`, `"cancelled"`, `"unsuccessful"`. |
| `awards[].description` | Award description | Free-text description of the award. |
| `contracts[].period` | Contract period | Start date, end date, max extent date. |
| `contracts[].value` | Contract value | May differ from award value (e.g., after modifications). |
| `tender.status` | Tender status | e.g., `"complete"`, `"active"`, `"cancelled"`. |
| `tender.tenderPeriod` | Submission period | Deadline for bid submissions. |
| `parties[].identifier` | Organization identifier | Structured ID with `scheme` (e.g., `"GB-COH"` for Companies House) and `id`. Useful for entity resolution. |
| `parties[].additionalIdentifiers[]` | Additional org identifiers | e.g., charity numbers, DUNS numbers. |
| `parties[].roles` | Organization roles | Array of roles (e.g., `["buyer"]`, `["supplier"]`, `["tenderer"]`). |
| `bids.statistics[]` | Bid statistics | Number of bids, tenderers, SME bids, etc. Rich competition data. |
| `bids.details[]` | Individual bid details | Per-bidder information where available. |
| `tender.lots[]` | Lot-level breakdown | Individual lot titles, descriptions, values, CPV codes. |
| `tender.value` | Estimated tender value | Pre-award estimated total value. |
| `planning.budget` | Budget information | Source of funding, budget allocation. |
| `relatedProcesses[]` | Linked procurement processes | Framework agreements, prior information notices, etc. |

### Code Normalization

#### Contract Nature Code (`tender.mainProcurementCategory` -> eForms)

OCDS uses a slightly different vocabulary than eForms for procurement categories:

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"goods"` | `"supplies"` | OCDS says "goods", eForms says "supplies" |
| `"works"` | `"works"` | Direct match |
| `"services"` | `"services"` | Direct match |

Implementation: map `"goods"` to `"supplies"`, pass through `"works"` and `"services"` as-is.

#### Procedure Type (`tender.procurementMethod` + `tender.procurementMethodDetails` -> eForms)

OCDS `procurementMethod` is a coarse 4-value codelist. The detailed procedure type is in `procurementMethodDetails` (free text). The mapping requires parsing `procurementMethodDetails` to determine the eForms code:

| OCDS `procurementMethod` | Expected `procurementMethodDetails` values | eForms Code | `accelerated` |
|---|---|---|---|
| `"open"` | `"Open procedure"` | `"open"` | `False` |
| `"selective"` | `"Restricted procedure"` | `"restricted"` | `False` |
| `"selective"` | `"Accelerated restricted procedure"` | `"restricted"` | `True` |
| `"selective"` | `"Competitive procedure with negotiation"` | `"neg-w-call"` | `False` |
| `"selective"` | `"Accelerated competitive procedure with negotiation"` | `"neg-w-call"` | `True` |
| `"selective"` | `"Competitive dialogue"` | `"comp-dial"` | `False` |
| `"selective"` | `"Innovation partnership"` | `"innovation"` | `False` |
| `"limited"` | `"Negotiated procedure without prior publication"` | `"neg-wo-call"` | `False` |
| `"direct"` | Various | `"neg-wo-call"` | `False` |

**IMPORTANT**: The exact string values used in `procurementMethodDetails` by Find a Tender need to be confirmed by inspecting actual API responses. The values above are educated guesses based on EU directive terminology. The parser should use case-insensitive substring matching or a lookup dict. Unknown values should log a warning and return `None`, consistent with the project's fail-loud philosophy.

**Fallback strategy**: If `procurementMethodDetails` is absent, map from `procurementMethod` alone: `"open"` -> `"open"`, `"selective"` -> `None` (ambiguous), `"limited"` -> `"neg-wo-call"`, `"direct"` -> `"neg-wo-call"`.

#### Authority Type (`parties[buyer].details.classifications[]` -> eForms)

The EU extension stores authority type as a classification with `scheme` = `"eu-buyer-legal-type"` (or possibly `"TED_CA_TYPE"`). The `id` values may already be eForms codes (e.g., `"cga"`, `"ra"`, `"body-pl"`) or may use EU/TED codes that need mapping. **Requires data inspection** to determine exact scheme and code values used by Find a Tender.

If the values match the existing `_AUTHORITY_TYPE_DESCRIPTIONS` dict in `ted_v2.py`, they can be passed through. If they use TED-style codes, use the existing `_make_authority_type_entry()` normalization function.

#### Country Code Normalization

OCDS `address.countryName` uses full English country names (e.g., `"United Kingdom"`, `"France"`). The schema requires ISO 3166-1 alpha-2 codes. The parser must maintain or use a country name -> code mapping. The `pycountry` library (already a project dependency) can handle this conversion.

### Implementation Notes

1. **Party resolution is central**: OCDS stores organization details in the `parties` array and references them by ID elsewhere. The parser must build an `{id: party}` lookup dict first, then resolve buyer and supplier references.

2. **Multiple awards per release**: A single OCDS release can contain multiple awards (one per lot). Each maps to a separate `AwardModel`. All share the same `DocumentModel`, `ContractingBodyModel`, and `ContractModel`.

3. **Release vs. Record**: Use releases (`ocdsReleasePackages`), not records. Releases are point-in-time snapshots (like notices). Filter with `stages=award` to get only award-stage releases.

4. **doc_id uniqueness**: OCDS release IDs are only unique within an `ocid`. Construct `doc_id` as `"{ocid}/{release_id}"` or similar composite to ensure global uniqueness across all procurement processes.

5. **Currency**: UK awards are predominantly in GBP, but the data may contain other currencies for international suppliers or EU-related procurements. Always read `awards[].value.currency` rather than assuming GBP.

6. **Data coverage start**: Find a Tender has been operational since January 2021. The Kingfisher Collect spider defaults to `2021-01-01` as start date. Pre-2021 UK data would require scraping Contracts Finder instead (different API, different format).
