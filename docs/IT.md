# Italy (IT)

**Feasibility: Tier 1**

## Portal

- **Name**: ANAC (Autorita Nazionale Anticorruzione) Open Data Portal
- **URL**: https://dati.anticorruzione.it/opendata/
- **Swagger UI**: https://dati.anticorruzione.it/opendata/ocds/api/ui
- **OCDS Info**: https://dati.anticorruzione.it/opendata/ocds_en
- **GitHub**: https://github.com/anticorruzione/npa
- **OCP Registry**: https://data.open-contracting.org/en/publication/117

## Data Access

- **Method**: REST API with Swagger documentation
- **Format**: JSON (OCDS format)
- **Auth**: Open, no authentication required
- **OCDS**: Yes — full compliance for contracts >40k EUR

## Coverage

All public procurement contracts >40,000 EUR. Monthly bulk datasets (2nd of month); real-time via API. Historical datasets available by year.

## Language

Italian (English info page available)

## Notes

- One of the best procurement APIs in Europe
- Swagger-documented OCDS API, open access, real-time data
- Monthly bulk datasets plus real-time API access

## Schema Mapping

ANAC publishes data in [OCDS 1.1](https://standard.open-contracting.org/latest/en/schema/reference/) format. Each contracting process is a JSON release object. The mapping below uses OCDS JSON paths (dot notation) from the release object.

### Data Format Notes

- **Format**: JSON Lines (`.jsonl`) for bulk downloads; JSON objects via REST API.
- **Standard**: OCDS 1.1 — well-defined schema with codelists. No custom XML to parse.
- **Identifier**: Each release has an `ocid` (Open Contracting ID). ANAC uses the prefix `ocds-b1ewdt-`. The national identifier is the CIG (Codice Identificativo Gara).
- **Single release per process**: ANAC publishes one compiled release per contracting process (no change history).
- **Bulk download**: Yearly `.jsonl` files available at `https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-{year}`. The API provides real-time access per-release.
- **Currency**: Always EUR (Italy is in the Eurozone).
- **Quality caveat**: OCP Data Registry notes that a minority of releases have inconsistent dates or erroneous organization names (blank or punctuation-only), due to errors from contracting authorities.

### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `ocid` | OCDS open contracting identifier, e.g. `ocds-b1ewdt-S00001234`. Unique per contracting process. Alternatively, use `id` (release ID) if multiple releases per ocid exist. |
| `edition` | `None` | No equivalent in OCDS. Set to `None`. |
| `version` | (hardcoded) | Set to `"OCDS-1.1"` or similar constant to identify the source format. |
| `reception_id` | `None` | TED-specific field. No OCDS equivalent. Set to `None`. |
| `official_journal_ref` | `None` | TED-specific field. No OCDS equivalent. Set to `None`. |
| `publication_date` | `date` | Release date (ISO 8601 string, e.g. `"2024-03-15T00:00:00Z"`). Parse date portion. |
| `dispatch_date` | `None` | TED-specific field. No OCDS equivalent. Set to `None`. |
| `source_country` | (hardcoded `"IT"`) | All data is Italian procurement. Hardcode `"IT"`. |
| `contact_point` | `parties[role=buyer].contactPoint.name` | Contact point name from the buyer organization's `contactPoint` object. |
| `phone` | `parties[role=buyer].contactPoint.telephone` | Buyer's telephone number. |
| `email` | `parties[role=buyer].contactPoint.email` | Buyer's email address. |
| `url_general` | `parties[role=buyer].contactPoint.url` | Buyer's contact URL. May not always be populated. |
| `url_buyer` | `None` | No separate buyer profile URL in OCDS. Set to `None`. |

### ContractingBodyModel

The buyer organization is identified in the `parties` array where `roles` contains `"buyer"`. The `buyer` object at the release root provides an `OrganizationReference` (`id` + `name`) that links to the full entry in `parties`.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[role=buyer].name` | Organization name. OCP notes some entries may be blank or punctuation-only due to upstream errors. |
| `address` | `parties[role=buyer].address.streetAddress` | Street address. |
| `town` | `parties[role=buyer].address.locality` | City/town name. |
| `postal_code` | `parties[role=buyer].address.postalCode` | Postal code. |
| `country_code` | `parties[role=buyer].address.countryName` | OCDS uses country name string, not ISO code. Needs mapping to ISO 3166-1 alpha-2. For Italian portal data this will almost always be `"IT"` — hardcode or map from `countryName`. |
| `nuts_code` | `None` | OCDS does not have a standard NUTS code field. Not available. Set to `None`. |
| `authority_type` | `None` | OCDS does not have a standard authority type field equivalent to eForms buyer-legal-type. The `parties[].details` object may contain classification info if the OCDS for EU extension is used, but this is **not confirmed** for ANAC. Set to `None` unless sample data reveals otherwise. |
| `main_activity_code` | `None` | Same as above — no standard OCDS field. Set to `None`. |

### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `tender.title` | Tender title. |
| `short_description` | `tender.description` | Tender description text. |
| `main_cpv_code` | `tender.items[0].classification.id` | CPV code from the first item classification where `classification.scheme == "CPV"`. OCDS uses item-level classification; pick the first/primary item's CPV. |
| `cpv_codes` | `tender.items[*].classification` | Iterate all items, collect `classification.id` where `classification.scheme == "CPV"`. Description available in `classification.description`. Also check `additionalClassifications` arrays on each item for additional CPV codes. |
| `nuts_code` | `None` | OCDS does not have a standard NUTS code field for delivery location. The `tender.items[*].deliveryLocation` or `tender.items[*].deliveryAddress.region` may exist but are not standard OCDS and unlikely to contain NUTS codes. Set to `None`. |
| `contract_nature_code` | `tender.mainProcurementCategory` | OCDS codelist: `"goods"`, `"works"`, `"services"`. Needs mapping to eForms codes (see Code Normalization below). |
| `procedure_type` | `tender.procurementMethod` | OCDS codelist: `"open"`, `"selective"`, `"limited"`, `"direct"`. Needs mapping to eForms codes (see Code Normalization below). `tender.procurementMethodDetails` contains the Italian-language free-text description which may help disambiguate. |
| `accelerated` | `None` | No OCDS equivalent for eForms BT-106. Always set to `False`. |

### AwardModel

OCDS `awards` is an array; each entry maps to one `AwardModel`. A single tender can have multiple awards (one per lot).

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `awards[i].title` | Award title. May or may not be populated. |
| `contract_number` | `contracts[i].id` or `awards[i].id` | OCDS separates awards and contracts. `awards[i].id` is the award identifier; `contracts[i].id` is the contract identifier. Use `awards[i].id` as the contract_number, or cross-reference via `contracts[i].awardID`. |
| `tenders_received` | `tender.numberOfTenderers` | Number of tenderers at tender level (not per-award). Alternatively, check `bids.statistics` if the bid extension is used. This is a tender-level field in OCDS, not per-award, so it will be the same across all awards in a multi-lot process. |
| `awarded_value` | `awards[i].value.amount` | Monetary value of the award. |
| `awarded_value_currency` | `awards[i].value.currency` | ISO 4217 currency code (will be `"EUR"` for Italy). |
| `contractors` | `awards[i].suppliers` | Array of `OrganizationReference` objects. Each has `id` and `name`; full details in `parties` array (look up by `id`). |

### ContractorModel

Each entry in `awards[i].suppliers` is an `OrganizationReference` pointing to a full organization in `parties`. Look up the supplier by matching `parties[].id == suppliers[j].id`.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[supplier_id].name` | Supplier organization name. |
| `address` | `parties[supplier_id].address.streetAddress` | Street address. |
| `town` | `parties[supplier_id].address.locality` | City/town. |
| `postal_code` | `parties[supplier_id].address.postalCode` | Postal code. |
| `country_code` | `parties[supplier_id].address.countryName` | Country name string. Needs ISO 3166-1 alpha-2 mapping. For Italian suppliers will typically be `"IT"`. |
| `nuts_code` | `None` | No NUTS code in standard OCDS. Set to `None`. |

### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `tender.items[*].classification.id` | Where `classification.scheme == "CPV"`. Also check `additionalClassifications`. |
| `description` | `tender.items[*].classification.description` | CPV description text in Italian. |

### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `tender.procurementMethod` | After mapping to eForms codes (see below). |
| `description` | `tender.procurementMethodDetails` | Free-text Italian description of the procedure. Useful for logging/debugging but not for the normalized code. |

### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `None` | Not available in standard OCDS. |
| `description` | `None` | Not available. |

### Unmappable Schema Fields

The following schema fields have no equivalent in the ANAC OCDS data and should be set to `None`:

- **DocumentModel.edition** — TED OJ edition number, no OCDS equivalent.
- **DocumentModel.reception_id** — TED-specific reception identifier.
- **DocumentModel.official_journal_ref** — TED Official Journal reference.
- **DocumentModel.dispatch_date** — TED dispatch date.
- **DocumentModel.url_buyer** — No separate buyer profile URL.
- **ContractingBodyModel.nuts_code** — NUTS codes not part of standard OCDS.
- **ContractingBodyModel.authority_type** — No eForms buyer-legal-type equivalent in OCDS.
- **ContractingBodyModel.main_activity_code** — No eForms main-activity equivalent in OCDS.
- **ContractModel.nuts_code** — NUTS codes for performance location not in OCDS.
- **ContractModel.accelerated** — eForms BT-106 has no OCDS equivalent; always `False`.
- **ContractorModel.nuts_code** — NUTS codes not part of standard OCDS.

### Extra Portal Fields

The following ANAC OCDS fields are potentially useful but not covered by the current schema (flagging for review):

- **`ocid`** — Open Contracting ID; globally unique identifier. Currently used as `doc_id` but carries extra semantic meaning. Schema doesn't cover - flagging for review.
- **`tender.id`** — National tender identifier (CIG code). Schema doesn't cover a separate national identifier - flagging for review.
- **`parties[].identifier.id`** and **`parties[].identifier.scheme`** — Organization identifiers (e.g. Italian fiscal code / VAT number with scheme `"IT-CF"` or `"IT-IVA"`). Schema doesn't cover structured organization identifiers - flagging for review.
- **`parties[].roles`** — Full role list (buyer, procuringEntity, supplier, tenderer, etc.). Schema doesn't cover multi-role tracking - flagging for review.
- **`tender.status`** — Tender status (active, complete, cancelled, etc.). Schema doesn't cover - flagging for review.
- **`awards[].status`** — Award status (pending, active, cancelled, unsuccessful). Schema doesn't cover - flagging for review.
- **`awards[].date`** — Award date. Schema doesn't cover award date separately - flagging for review.
- **`contracts[].period`** — Contract execution period (startDate, endDate). Schema doesn't cover - flagging for review.
- **`contracts[].value`** — Contract value (may differ from award value). Schema doesn't cover - flagging for review.
- **`tender.value`** — Estimated tender value. Schema doesn't cover - flagging for review.
- **`tender.tenderPeriod`** — Submission period (startDate, endDate). Schema doesn't cover - flagging for review.
- **`planning.budget`** — Budget allocation information. Schema doesn't cover - flagging for review.
- **`tender.lots`** — Lot-level breakdown (if the OCDS lots extension is used). Schema doesn't cover lot structure - flagging for review.

### Code Normalization

#### Contract Nature Codes (`tender.mainProcurementCategory` to eForms)

OCDS uses a closed codelist for `mainProcurementCategory`. Mapping to eForms `contract-nature-types`:

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"goods"` | `"supplies"` | OCDS "goods" = eForms "supplies" |
| `"works"` | `"works"` | Direct match |
| `"services"` | `"services"` | Direct match |

Note: OCDS does not have an equivalent to eForms `"combined"`.

#### Procedure Type Codes (`tender.procurementMethod` to eForms)

OCDS uses a closed codelist with only 4 values. The mapping to eForms `procurement-procedure-type` is lossy because OCDS is less granular:

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"open"` | `"open"` | Direct match |
| `"selective"` | `"restricted"` | OCDS "selective" corresponds to eForms "restricted" |
| `"limited"` | `"neg-wo-call"` | Best approximation. OCDS "limited" covers negotiated procedures without prior publication. |
| `"direct"` | `"neg-wo-call"` | Direct award without competition. Maps to negotiated without call. |

**Important**: The `tender.procurementMethodDetails` field contains Italian free-text that may allow more precise mapping. For example, it might specify "Procedura negoziata senza previa pubblicazione" (negotiated without prior publication) vs "Procedura negoziata con previa pubblicazione" (negotiated with prior publication / `neg-w-call`). The implementing parser should:
1. Use the coarse `procurementMethod` mapping above as a baseline.
2. Optionally parse `procurementMethodDetails` to distinguish `neg-w-call` from `neg-wo-call` when OCDS reports `"limited"`.
3. Log a warning when `procurementMethodDetails` suggests a different mapping than the baseline.

Common Italian procedure type strings in `procurementMethodDetails` (to aid future parsing):
- "Procedura aperta" = `open`
- "Procedura ristretta" = `restricted`
- "Procedura competitiva con negoziazione" = `neg-w-call`
- "Procedura negoziata senza previa pubblicazione" = `neg-wo-call`
- "Procedura negoziata con previa pubblicazione" = `neg-w-call`
- "Dialogo competitivo" = `comp-dial`
- "Affidamento diretto" = `neg-wo-call` (direct award)
- "Partenariato per l'innovazione" = `innovation`

#### Authority Type Codes

Not available in standard OCDS. No mapping needed. The `parties[].details` object could theoretically carry this in an OCDS extension, but ANAC's usage of such extensions is **unconfirmed** from available documentation. The implementing parser should check a sample release and log if `parties[].details.classifications` or similar fields are present.

#### Country Codes

OCDS `address.countryName` is a free-text country name, not an ISO code. The parser needs a mapping from Italian country names to ISO 3166-1 alpha-2 codes. For Italian portal data, the vast majority will be "Italia" or "Italy" mapping to `"IT"`. A small lookup table for common trading partners (EU member states) should suffice, with a warning for unmapped values.
