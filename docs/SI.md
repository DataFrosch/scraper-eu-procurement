# Slovenia (SI)

**Feasibility: Tier 2**

## Portal

- **Name**: enarocanje.si
- **URL**: http://www.enarocanje.si/
- **Open data**: OPSI portal (https://nio.gov.si/)
- **OCP Registry**: https://data.open-contracting.org/en/publication/82

## Data Access

- **Method**: Open data in OCDS format via OPSI and "They Buy For You" platform
- **Format**: JSON (OCDS)
- **Auth**: Open
- **OCDS**: Yes

## Coverage

All procurements above statutory thresholds.

## Language

Slovenian

## Notes

- OECD ranks Slovenia as one of the most transparent procurement systems
- Access may require navigating multiple platforms (enarocanje.si, OPSI, They Buy For You)

## Schema Mapping

### Data Format Notes

- **Format**: JSON (OCDS 1.1 release packages)
- **Source URL**: `http://tbfy.ijs.si/public/ocds/mju/` — directory listing of JSON files, one per data dump (filename pattern: `YYYYMMDD-ocds-si-public-tenders.json`)
- **Reference implementation**: Kingfisher Collect spider `slovenia` ([source](https://github.com/open-contracting/kingfisher-collect/blob/main/kingfisher_scrapy/spiders/slovenia.py)) scrapes the directory listing and downloads each `.json` file
- **Structure**: Each file is an OCDS release package containing a `releases[]` array. Each release represents one contracting process (identified by `ocid`). A release contains top-level sections: `parties[]`, `buyer`, `tender`, `awards[]`, `contracts[]`
- **Parsing considerations**:
  - OCDS separates organizations into a `parties[]` array with role-based cross-referencing. The buyer/procuringEntity and suppliers are referenced by `id` from other sections. The parser must resolve these references to extract contracting body and contractor details.
  - A single release may contain multiple awards (one per lot/contract). Each award has its own `suppliers[]` array.
  - Currency is always EUR for Slovenian procurement (but should be read from `value.currency` to be safe).
  - The data is in Slovenian; field names follow the English OCDS schema, but free-text values (titles, descriptions, organization names) are in Slovenian.
  - The TBFY endpoint serves data converted from enarocanje.si's internal format to OCDS. Field completeness depends on the conversion quality; some fields may be absent or sparse.

### Field Mapping: DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `releases[].ocid` | OCDS contracting process identifier. Globally unique. Use as document ID. |
| `edition` | None | OCDS has no edition concept. Set to `None`. |
| `version` | `releases[].id` | The release ID within the contracting process. Could serve as version identifier. |
| `reception_id` | None | TED-specific field. Not available in OCDS. Set to `None`. |
| `official_journal_ref` | None | TED-specific field. Not available in national portal data. Set to `None`. |
| `publication_date` | `releases[].date` | ISO 8601 datetime of the release. Parse date portion. |
| `dispatch_date` | None | TED-specific field. Not available in OCDS. Set to `None`. |
| `source_country` | Hard-coded `"SI"` | All data from this portal is Slovenian. |
| `contact_point` | `parties[buyer].contactPoint.name` | Contact point name from the buyer party entry. |
| `phone` | `parties[buyer].contactPoint.telephone` | Telephone from the buyer party's contact point. |
| `email` | `parties[buyer].contactPoint.email` | Email from the buyer party's contact point. |
| `url_general` | `parties[buyer].contactPoint.url` | URL from the buyer party's contact point. |
| `url_buyer` | `buyer.id` cross-ref to `parties[].details.buyerProfile` | Buyer profile URL, if the OCDS extension is used. Likely `None` in this dataset. |

### Field Mapping: ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[buyer].name` | Resolve `buyer.id` to the matching entry in `parties[]`. Required field. |
| `address` | `parties[buyer].address.streetAddress` | Street address of the buyer party. |
| `town` | `parties[buyer].address.locality` | Town/city of the buyer party. |
| `postal_code` | `parties[buyer].address.postalCode` | Postal code of the buyer party. |
| `country_code` | `parties[buyer].address.countryName` | OCDS uses country name strings, not ISO codes. Will need mapping to 2-letter ISO code, or hard-code `"SI"` if always domestic. |
| `nuts_code` | `parties[buyer].address.region` | OCDS `region` field. Unlikely to contain a proper NUTS code; may need mapping or set to `None`. The SI doc does not confirm NUTS availability. |
| `authority_type` | Not directly available | OCDS has no standard field for authority/buyer legal type. Some publishers use `parties[].details.classifications[]` with scheme `"TED_CA_TYPE"` or similar, but this is not guaranteed. Likely `None` unless the Slovenian data includes this extension. Needs empirical verification. |
| `main_activity_code` | Not directly available | OCDS has no standard field for main activity. Some publishers use `parties[].details.classifications[]`. Likely `None`. Needs empirical verification. |

### Field Mapping: ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `tender.title` | Title of the tender/contracting process. Required field. |
| `short_description` | `tender.description` | Description of the tender. |
| `main_cpv_code` | `tender.items[0].classification.id` where `classification.scheme == "CPV"` | Main CPV code from item classification. Take the first item's classification, or look for `tender.classification.id` if the tenderClassification extension is used. |
| `cpv_codes` | `tender.items[].classification` where `scheme == "CPV"`, plus `tender.items[].additionalClassifications[]` where `scheme == "CPV"` | Collect all CPV codes from item classifications and additional classifications. Each entry has `id` (code) and `description`. |
| `nuts_code` | `tender.items[].deliveryAddress.region` | OCDS uses `deliveryAddress.region` for performance location. May or may not contain valid NUTS codes. Needs empirical verification. |
| `contract_nature_code` | `tender.mainProcurementCategory` | OCDS values: `"goods"`, `"works"`, `"services"`. These map directly to eForms codes (see Code Normalization below). |
| `procedure_type` | `tender.procurementMethod` + `tender.procurementMethodDetails` | OCDS codelist: `"open"`, `"selective"`, `"limited"`, `"direct"`. Needs mapping to eForms procedure type codes (see Code Normalization below). `procurementMethodDetails` provides the free-text description. |
| `accelerated` | `tender.procurementMethodDetails` (text inspection) | OCDS has no dedicated accelerated field. If the Slovenian data uses the `procurementMethodDetails` string to indicate acceleration (e.g., "pospesen"), this would need text-based detection. Likely set to `False` by default. |

### Field Mapping: AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `awards[].title` | Title of the award. May be absent in some releases. |
| `contract_number` | `contracts[].id` or `awards[].id` | OCDS links contracts to awards via `contracts[].awardID`. The contract ID or award ID can serve as contract number. |
| `tenders_received` | `tender.numberOfTenderers` | Number of unique tenderers who participated. This is at the tender level, not per-award. If there are multiple awards (lots), this value applies to all. OCDS does not have a per-award tender count in the base schema. |
| `awarded_value` | `awards[].value.amount` | Monetary value of the award. |
| `awarded_value_currency` | `awards[].value.currency` | ISO 4217 currency code (expected: `"EUR"` for Slovenia). |
| `contractors` | `awards[].suppliers[]` | Array of supplier organization references. Each supplier `id` must be resolved against `parties[]` to get full details. |

### Field Mapping: ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[supplier].name` | Resolve the supplier reference `id` against the `parties[]` array. Required field. |
| `address` | `parties[supplier].address.streetAddress` | Street address of the supplier party. |
| `town` | `parties[supplier].address.locality` | Town/city of the supplier party. |
| `postal_code` | `parties[supplier].address.postalCode` | Postal code of the supplier party. |
| `country_code` | `parties[supplier].address.countryName` | Country name string. Needs mapping to ISO 2-letter code. |
| `nuts_code` | `parties[supplier].address.region` | Unlikely to contain proper NUTS codes. Likely `None`. |

### Field Mapping: CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `tender.items[].classification.id` (where `scheme == "CPV"`) | CPV code string (e.g., `"45000000"`). |
| `description` | `tender.items[].classification.description` | Human-readable CPV description. May be in Slovenian. |

### Field Mapping: ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Derived from `tender.procurementMethod` | Needs mapping from OCDS codelist to eForms codes (see Code Normalization). |
| `description` | `tender.procurementMethodDetails` | Free-text procedure description (likely in Slovenian). |

### Unmappable Schema Fields

These schema fields cannot be populated from the Slovenian OCDS data and should be set to `None`:

| Field | Model | Reason |
|---|---|---|
| `edition` | DocumentModel | TED-specific concept, no OCDS equivalent |
| `reception_id` | DocumentModel | TED-specific identifier |
| `official_journal_ref` | DocumentModel | TED Official Journal reference, not applicable to national portal data |
| `dispatch_date` | DocumentModel | TED-specific dispatch date |
| `url_buyer` | DocumentModel | Buyer profile URL; not a standard OCDS field, unlikely present |
| `authority_type` | ContractingBodyModel | No standard OCDS field for buyer legal type; may be absent unless a custom extension is used |
| `main_activity_code` | ContractingBodyModel | No standard OCDS field for main activity; may be absent |
| `nuts_code` | ContractingBodyModel | OCDS `region` field is free-text, unlikely to contain valid NUTS codes |
| `nuts_code` | ContractModel | OCDS `deliveryAddress.region` is free-text, unlikely NUTS |
| `nuts_code` | ContractorModel | Same issue as above |
| `accelerated` | ContractModel | No dedicated OCDS field; default to `False` |

### Extra Portal Fields

These fields are available in OCDS but not covered by the current schema. Flagged for review:

| OCDS Field | Description | Notes |
|---|---|---|
| `parties[].identifier.id` | Organization tax/registration number | schema doesn't cover - flagging for review. Valuable for entity matching and deduplication. |
| `parties[].identifier.scheme` | Identifier scheme (e.g., `"SI-TIN"`) | schema doesn't cover - flagging for review. Pairs with identifier.id. |
| `parties[].identifier.legalName` | Registered legal name | schema doesn't cover - flagging for review. May differ from `name`. |
| `tender.status` | Tender status (e.g., `"complete"`, `"active"`) | schema doesn't cover - flagging for review. Useful for filtering. |
| `awards[].status` | Award status (e.g., `"active"`, `"unsuccessful"`) | schema doesn't cover - flagging for review. Important for identifying cancelled awards. |
| `awards[].date` | Date the award was made | schema doesn't cover - flagging for review. Useful for time-series analysis. |
| `contracts[].value.amount` | Final contract value (may differ from award value) | schema doesn't cover - flagging for review. |
| `contracts[].period.startDate` / `endDate` | Contract performance period | schema doesn't cover - flagging for review. |
| `tender.tenderPeriod.endDate` | Submission deadline | schema doesn't cover - flagging for review. |
| `tender.value.amount` / `currency` | Estimated total tender value | schema doesn't cover - flagging for review. |
| `tender.items[].quantity` / `unit` | Item quantities and units | schema doesn't cover - flagging for review. |
| `parties[].address.region` | Region string (potential NUTS source if structured) | schema doesn't cover - flagging for review. |

### Code Normalization

#### Procedure Type: OCDS `procurementMethod` to eForms codes

The OCDS `tender.procurementMethod` codelist uses four values that must be mapped to eForms `procurement-procedure-type` codes:

| OCDS `procurementMethod` | eForms Code | Notes |
|---|---|---|
| `"open"` | `"open"` | Direct match. |
| `"selective"` | `"restricted"` | OCDS "selective" corresponds to eForms "restricted" (pre-qualified bidder list). |
| `"limited"` | `"neg-w-call"` | Best approximation. OCDS "limited" covers negotiated procedures with some competition. May need `procurementMethodDetails` inspection to distinguish `"neg-w-call"` from `"comp-dial"` or `"innovation"`. |
| `"direct"` | `"neg-wo-call"` | Direct award without competition maps to negotiated without prior call. |

**Important**: OCDS `procurementMethod` is coarser than eForms procedure types. The four OCDS codes collapse multiple eForms codes (`restricted`, `neg-w-call`, `comp-dial`, `innovation`, `neg-wo-call`, `oth-single`, `oth-mult`, `comp-tend`) into just four buckets. The `procurementMethodDetails` free-text field may contain additional detail (in Slovenian) that could help disambiguate, but this requires empirical analysis of the actual data. When disambiguation is not possible, use the mapping above as the default.

#### Contract Nature: OCDS `mainProcurementCategory` to eForms codes

| OCDS `mainProcurementCategory` | eForms Code | Notes |
|---|---|---|
| `"goods"` | `"supplies"` | OCDS uses "goods", eForms uses "supplies". |
| `"works"` | `"works"` | Direct match. |
| `"services"` | `"services"` | Direct match. |

#### Authority Type

OCDS has no standard codelist for authority/buyer legal type. The Slovenian data may or may not include this via extensions (e.g., `parties[].details.classifications[]`). If present, the classification values would need to be mapped to eForms `buyer-legal-type` codes (`"cga"`, `"ra"`, `"la"`, `"body-pl"`, etc.). **Empirical verification of the actual data is required** to determine whether this field is populated and what values appear.

#### Country Codes

OCDS `address.countryName` uses full country name strings (e.g., `"Slovenia"`, `"Slovenija"`), not ISO 2-letter codes. The parser must either:
1. Hard-code `"SI"` for the contracting body (since all data is from the Slovenian portal)
2. Build a country name-to-code mapping for contractor country codes (suppliers may be from other countries)

The [pycountry](https://pypi.org/project/pycountry/) library or a static lookup table could handle this conversion.
