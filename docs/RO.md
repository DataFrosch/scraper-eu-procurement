# Romania (RO)

**Feasibility: Tier 2**

## Portal

- **Name**: SEAP / SICAP
- **URL**: https://www.e-licitatie.ro/pub
- **Open data**: https://data.gov.ro/dataset?q=achizitii+publice
- **Community tool**: https://sicap.ai/

## Data Access

- **Method**: OCDS API (webservice with JSON following OCDS standard)
- **Format**: JSON (OCDS)
- **Auth**: Open
- **OCDS**: Yes (partial — implementation has had technical issues)

## Coverage

All public procurement (above and below EU thresholds).

## Language

Romanian

## Notes

- SICAP replaced SEAP but has had implementation problems
- Bulk data export to national portal was interrupted for months in 2018
- Community-built SICAP.ai provides alternative search
- OGP commitment: https://www.opengovpartnership.org/members/romania/commitments/RO0046/
- OCDS data exists but implementation quality is a concern
- OCP Data Registry entry: https://data.open-contracting.org/en/publication/38
- Kingfisher Collect has a Romania spider (`romania`) that can serve as a reference implementation

## Schema Mapping

### Data Format Notes

- **Format**: JSON (OCDS 1.1). Romania's SICAP/SEAP publishes data following the Open Contracting Data Standard.
- **API Base**: The OCDS API is served from `https://e-licitatie.ro` (exact endpoint paths need discovery -- see below).
- **OCDS prefix**: Not confirmed from available documentation. Likely follows the pattern `ocds-XXXXXX-` assigned by OCP. **Must be confirmed by inspecting actual API responses.**
- **Access method**: The Kingfisher Collect project's Romania spider (`kingfisher_scrapy/spiders/romania.py`) is the best reference for the exact API endpoint URLs, pagination strategy, and data retrieval approach. **The implementing agent should consult this spider before starting work.**
- **Currency**: Romanian Leu (RON). Romania is not in the Eurozone. Awards will predominantly be in `"RON"`, but some EU-funded procurements may use `"EUR"`. Always read `awards[].value.currency` rather than assuming RON.
- **Language**: All free-text fields (titles, descriptions, organization names, procedure details) are in Romanian.
- **Coverage**: All public procurement above and below EU thresholds. Historical data coverage extent is unclear -- the portal has had interruptions (notably in 2018).
- **Quality concerns**: The OCDS implementation is described as "partial" with "technical issues". Expect:
  - Missing or incomplete fields compared to a full OCDS implementation
  - Possible schema validation errors in a portion of records
  - Potential gaps in historical data (2018 bulk export interruption)
  - The parser must be defensive: treat all optional fields as potentially absent and handle malformed data gracefully

**CRITICAL UNKNOWNS**: The existing documentation for Romania is sparse. The following must be determined by inspecting the actual API and/or the Kingfisher Collect Romania spider before implementation:

1. **Exact API endpoint URLs** (release packages, record packages, or bulk download)
2. **Pagination mechanism** (cursor-based, page-based, date-range-based)
3. **Query parameters** for filtering by award stage or date range
4. **Whether data is served as release packages or record packages** (compiledRelease vs. individual releases)
5. **Rate limits** (if any)
6. **OCDS identifier prefix**
7. **Which OCDS extensions are used** (EU extension, bids extension, etc.)
8. **Actual field population rates** -- which OCDS fields are actually populated vs. always null
9. **Whether data.gov.ro offers bulk downloads** as an alternative to the API

### Field Mapping Tables

Romania publishes OCDS data, so the mapping follows standard OCDS structure. Organization details (buyer, supplier) are stored in a top-level `parties` array with `OrganizationReference` objects elsewhere. The parser must cross-reference party IDs to resolve full details.

OCDS path notation below uses dot-separated paths within the release (or `compiledRelease` if record packages are used).

**Important**: Because Romania's OCDS implementation is "partial", many fields marked as mappable below may in practice be empty or absent. The implementing parser should log warnings for missing fields but not fail.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `ocid` (or composite `{ocid}/{release.id}`) | The OCDS contracting process identifier. If multiple releases per ocid exist, use a composite key for uniqueness. Prefix with `RO-` if needed to avoid collision with TED doc_ids. |
| `edition` | `None` | No equivalent in OCDS. Set to `None`. |
| `version` | `None` | Could set to `"OCDS-1.1"` as a format identifier, or `None`. |
| `reception_id` | `None` | TED-specific field. No OCDS equivalent. |
| `official_journal_ref` | `None` | TED-specific OJ reference. Not applicable to national portals. |
| `publication_date` | `date` (release-level) or `compiledRelease.date` | The release date (ISO 8601). Parse date portion only. |
| `dispatch_date` | `None` | TED-specific concept. No clean OCDS equivalent. |
| `source_country` | (hardcoded `"RO"`) | All data is Romanian procurement. Hardcode `"RO"`. |
| `contact_point` | `parties[role=buyer].contactPoint.name` | Contact point from the buyer party. **May not be populated** given partial OCDS implementation. |
| `phone` | `parties[role=buyer].contactPoint.telephone` | Buyer's telephone. **May not be populated.** |
| `email` | `parties[role=buyer].contactPoint.email` | Buyer's email. **May not be populated.** |
| `url_general` | `parties[role=buyer].contactPoint.url` | Buyer's contact URL. **May not be populated.** |
| `url_buyer` | `None` | No separate buyer profile URL in standard OCDS. |

#### ContractingBodyModel

The buyer is identified in the `parties` array where `roles` contains `"buyer"`. The `buyer` object at the release root provides an `OrganizationReference` (`id` + `name`) linking to the full `parties` entry.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[role=buyer].name` | Buyer organization name. In Romanian. |
| `address` | `parties[role=buyer].address.streetAddress` | Street address. |
| `town` | `parties[role=buyer].address.locality` | City/town name (Romanian names, e.g., "Bucuresti", "Cluj-Napoca"). |
| `postal_code` | `parties[role=buyer].address.postalCode` | Romanian postal code. |
| `country_code` | `parties[role=buyer].address.countryName` | OCDS uses full country name (e.g., `"Romania"` or `"Romania"`), not ISO code. Hardcode `"RO"` for buyer entities since all SICAP data is Romanian, or map from `countryName`. |
| `nuts_code` | `None` | OCDS does not have a standard NUTS code field. `address.region` may exist as free text but is not a NUTS code. Set to `None`. **Check actual data** -- if SICAP populates `address.region` with NUTS codes (Romania uses `RO1xx` format), this could be extracted. |
| `authority_type` | `None` | Not part of standard OCDS. If Romania uses the OCDS EU extension, `parties[].details.classifications[]` with `scheme == "eu-buyer-legal-type"` might carry this. **Unconfirmed -- check actual data.** |
| `main_activity_code` | `None` | Not part of standard OCDS. Same EU extension caveat as `authority_type`. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `tender.title` | Tender/procurement title. In Romanian. |
| `short_description` | `tender.description` | Tender description text. In Romanian. |
| `main_cpv_code` | `tender.items[0].classification.id` | CPV code from the first item classification where `scheme == "CPV"`. CPV codes are universal (not language-dependent). |
| `cpv_codes` | `tender.items[].classification` + `tender.items[].additionalClassifications[]` | Collect all classifications where `scheme == "CPV"`. Use `id` for code and `description` for description. Descriptions will be in Romanian. |
| `nuts_code` | `None` | OCDS `tender.items[].deliveryLocation` may have location data but is not guaranteed to contain NUTS codes. Set to `None` unless actual data confirms NUTS code presence. |
| `contract_nature_code` | `tender.mainProcurementCategory` | OCDS values: `"goods"`, `"works"`, `"services"`. Requires mapping to eForms codes (see Code Normalization). |
| `procedure_type` | `tender.procurementMethod` + `tender.procurementMethodDetails` | OCDS `procurementMethod`: `"open"`, `"selective"`, `"limited"`, `"direct"`. `procurementMethodDetails` contains the Romanian-language free-text description. See Code Normalization. |
| `accelerated` | `False` | OCDS has no dedicated accelerated procedure flag. Always `False`. If `procurementMethodDetails` contains "accelerat" (Romanian for accelerated), this could be detected, but this needs data inspection to confirm. |

#### AwardModel

OCDS `awards` is an array; each entry maps to one `AwardModel`. A single tender can have multiple awards (one per lot).

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `awards[].title` | Award title. May be `None` if not populated. In Romanian. |
| `contract_number` | `contracts[].id` or `awards[].id` | OCDS links contracts to awards via `contracts[].awardID`. Use `awards[].id` as fallback. |
| `tenders_received` | `tender.numberOfTenderers` | Tender-level field (not per-award). **May not be populated** in Romania's partial implementation. Also check `bids.statistics[]` if the bids extension is used. |
| `awarded_value` | `awards[].value.amount` | Monetary value. |
| `awarded_value_currency` | `awards[].value.currency` | ISO 4217 currency code. Predominantly `"RON"`, possibly `"EUR"` for some EU-funded contracts. |
| `contractors` | `awards[].suppliers[]` | Array of `OrganizationReference` objects. Cross-reference `parties` array for full details. |

#### ContractorModel

Each entry in `awards[].suppliers[]` is an `OrganizationReference` pointing to a full organization in `parties`. Look up the supplier by matching `parties[].id == suppliers[].id`.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[supplier_id].name` | Supplier organization name. In Romanian. |
| `address` | `parties[supplier_id].address.streetAddress` | Street address. |
| `town` | `parties[supplier_id].address.locality` | City/town. |
| `postal_code` | `parties[supplier_id].address.postalCode` | Postal code. |
| `country_code` | `parties[supplier_id].address.countryName` | Country name string. Needs ISO 3166-1 alpha-2 mapping. For Romanian suppliers will typically be `"RO"`. For foreign suppliers, map from Romanian-language country name (e.g., `"Romania"` -> `"RO"`, `"Ungaria"` -> `"HU"`, `"Germania"` -> `"DE"`). |
| `nuts_code` | `None` | Not available in standard OCDS. Set to `None`. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `tender.items[].classification.id` (where `scheme == "CPV"`) | CPV code string (e.g., `"45000000"`). Also check `additionalClassifications`. |
| `description` | `tender.items[].classification.description` | CPV description. Will be in Romanian. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Derived from `tender.procurementMethod` | After mapping to eForms codes (see Code Normalization). |
| `description` | `tender.procurementMethodDetails` | Free-text Romanian description of the procedure. |

#### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `None` | Not available in standard OCDS. **Check actual data** for EU extension fields. |
| `description` | `None` | Not available. |

### Unmappable Schema Fields

The following schema fields have no equivalent in the Romanian OCDS data and should be set to `None`:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | TED-specific OJ edition number. No OCDS equivalent. |
| `DocumentModel.version` | No clean equivalent. Could use a format identifier constant but not semantically the same. |
| `DocumentModel.reception_id` | TED-specific reception identifier. No OCDS equivalent. |
| `DocumentModel.official_journal_ref` | TED-specific OJ reference. Not applicable to national portals. |
| `DocumentModel.dispatch_date` | TED-specific concept (date sent to OJ). No OCDS equivalent. |
| `DocumentModel.url_buyer` | No separate buyer profile URL in standard OCDS. |
| `ContractingBodyModel.nuts_code` | OCDS does not include NUTS codes as a standard field. `address.region` is free text. **Might be available if Romania uses NUTS in region field -- needs data inspection.** |
| `ContractingBodyModel.authority_type` | Not part of standard OCDS. Only available if EU extension is used, which is unconfirmed for Romania. |
| `ContractingBodyModel.main_activity_code` | Not part of standard OCDS. Same EU extension caveat. |
| `ContractModel.nuts_code` | OCDS delivery location does not reliably provide NUTS codes. |
| `ContractModel.accelerated` | OCDS has no concept of accelerated procedures. Always `False`. |
| `ContractorModel.nuts_code` | Not available in standard OCDS. |

### Extra Portal Fields

The following fields are potentially available in Romania's OCDS data but are not covered by the current schema. Flagged for review:

| OCDS Field | Description | Notes |
|---|---|---|
| `parties[].identifier.id` | Legal entity identifier (CUI/CIF -- Romanian fiscal code) | **High value** -- schema does not cover entity identifiers. Would enable cross-referencing entities across portals and against Romanian business registries. |
| `parties[].identifier.scheme` | Identifier scheme (e.g., `"RO-CUI"`) | Accompanies the identifier. |
| `parties[].identifier.legalName` | Registered legal name | May differ from `name` (trading name). |
| `awards[].date` | Award decision date | Schema does not cover -- flagging for review. Distinct from publication date. |
| `awards[].status` | Award status (`"active"`, `"cancelled"`, etc.) | Schema does not cover -- flagging for review. Useful for filtering out cancelled awards. |
| `tender.status` | Tender status | Schema does not cover -- flagging for review. |
| `tender.value` | Estimated tender value | Schema does not cover -- flagging for review. |
| `tender.tenderPeriod` | Submission period (start/end dates) | Schema does not cover -- flagging for review. |
| `contracts[].period` | Contract execution period (start/end dates) | Schema does not cover -- flagging for review. |
| `contracts[].value` | Contract value (may differ from award value) | Schema does not cover -- flagging for review. |
| `tender.lots[]` | Lot-level breakdown | Schema does not cover lot structure -- flagging for review. |
| `tender.documents[]` | Tender documents with URLs | Schema does not cover -- flagging for review. |
| `planning.budget` | Budget allocation information | Schema does not cover -- flagging for review. May not be populated given partial implementation. |

**Note**: Given Romania's "partial" OCDS implementation, many of these extra fields may not actually be populated. The implementing parser should log which fields are present in practice during initial data inspection.

### Code Normalization

Our schema uses exact eForms codes (lowercase, hyphens) for all coded values. OCDS uses its own codelists. The following mappings are needed:

#### Contract Nature Code (`tender.mainProcurementCategory` to eForms)

OCDS `tender.mainProcurementCategory` values must be mapped to eForms `contract-nature-types` codes:

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"goods"` | `"supplies"` | OCDS "goods" = eForms "supplies" |
| `"works"` | `"works"` | Direct match |
| `"services"` | `"services"` | Direct match |
| (missing/other) | `None` | Log warning |

Note: OCDS does not have an equivalent to eForms `"combined"`.

#### Procedure Type Code (`tender.procurementMethod` to eForms)

OCDS `tender.procurementMethod` values must be mapped to eForms `procurement-procedure-type` codes. OCDS has only 4 broad categories vs. eForms' fine-grained types:

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"open"` | `"open"` | Direct match |
| `"selective"` | `"restricted"` | OCDS "selective" corresponds to eForms "restricted" (pre-qualified bidders) |
| `"limited"` | `"neg-w-call"` | Best approximation. OCDS "limited" covers negotiated procedures with a limited pool. |
| `"direct"` | `"neg-wo-call"` | Direct award without competition = negotiated without prior call |
| (missing/other) | `None` | Log warning |

**Romanian procedure type disambiguation**: The `tender.procurementMethodDetails` field contains the original Romanian procedure name. These free-text values could enable more precise mapping but would require a Romanian-to-eForms lookup table. Common Romanian procedure type strings (from Romanian procurement law):

- "Licitatie deschisa" = `"open"` (open procedure)
- "Licitatie restransa" = `"restricted"` (restricted procedure)
- "Negociere cu publicare prealabila" / "Negociere competitiva" = `"neg-w-call"` (negotiated with prior publication)
- "Negociere fara publicare prealabila" = `"neg-wo-call"` (negotiated without prior publication)
- "Dialog competitiv" = `"comp-dial"` (competitive dialogue)
- "Achizitie directa" = `"neg-wo-call"` (direct award)
- "Procedura simplificata" = `"open"` or `None` (simplified procedure for below-threshold -- no direct eForms equivalent; needs decision on mapping)
- "Concurs de solutii" = `"oth-single"` or `None` (design contest -- may not map cleanly to eForms procedure types)
- "Parteneriat pentru inovare" = `"innovation"` (innovation partnership)
- "Cerere de oferte" = `"open"` (request for quotation -- simplified open procedure)

**Recommended approach**: Start with the coarse `procurementMethod` mapping above. Store `procurementMethodDetails` in `ProcedureTypeEntry.description`. Optionally parse `procurementMethodDetails` to refine the mapping. Log a warning when the detailed string suggests a different mapping than the baseline.

**Important**: These Romanian procedure name strings are educated guesses based on Romanian procurement legislation terminology. **They must be verified against actual data** before implementation.

#### Authority Type Code

Not available in standard OCDS. Always `None` unless Romania uses the OCDS EU extension (`parties[].details.classifications[]` with `scheme == "eu-buyer-legal-type"`). **Must be checked against actual data.**

#### Country Code Normalization

OCDS `address.countryName` is free text. For Romanian portal data:
- Hardcode `"RO"` for buyer entities (all SICAP data is Romanian procurement)
- For suppliers, map from Romanian-language country names to ISO 3166-1 alpha-2 codes
- Common Romanian country names and their ISO codes:
  - "Romania" -> `"RO"`
  - "Ungaria" -> `"HU"`
  - "Bulgaria" -> `"BG"`
  - "Germania" -> `"DE"`
  - "Franta" -> `"FR"`
  - "Italia" -> `"IT"`
  - "Austria" -> `"AT"`
  - "Republica Moldova" -> `"MD"`
- Build a lookup table for EU member states + common trading partners in Romanian, with a warning for unmapped values
- Alternatively, check if Romania's OCDS uses ISO codes directly in `address.country` (non-standard but some publishers do this)

### Implementation Notes

1. **Discover the API first**: The exact API endpoint URLs, pagination mechanism, and query parameters are not documented in this file. The implementing agent must:
   - Inspect the Kingfisher Collect Romania spider (`kingfisher_scrapy/spiders/romania.py`) for endpoint URLs and pagination logic
   - Alternatively, probe `https://e-licitatie.ro` for OCDS API endpoints (common patterns: `/api/ocds/`, `/ocds/releases/`, `/api/v1/`)
   - Check `https://data.gov.ro/dataset?q=achizitii+publice` for bulk download alternatives

2. **Party resolution is central**: OCDS stores organization details in the `parties` array and references them by ID elsewhere. The parser must build an `{id: party}` lookup dict first, then resolve buyer and supplier references. Handle missing cross-references gracefully (party ID in award but no matching entry in `parties` array).

3. **Multiple awards per release**: A single OCDS release can contain multiple awards (one per lot). Each maps to a separate `AwardModel`. All share the same `DocumentModel`, `ContractingBodyModel`, and `ContractModel`.

4. **doc_id strategy**: Use the OCDS `ocid` as the base `doc_id`. If multiple releases exist per `ocid`, use a composite like `"{ocid}/{release.id}"` for global uniqueness. Consider prefixing with `RO-` to avoid any collision with TED doc_ids (though OCDS `ocid` prefixes are already globally unique).

5. **Currency handling**: Romania uses RON. The `ExchangeRate` table in the database already supports multi-currency conversion. Always read `awards[].value.currency` from the data. The `update-rates` command fetches ECB rates including RON/EUR.

6. **Data quality defensive coding**: Given the "partial" OCDS implementation with known technical issues:
   - Wrap all field extractions in try/except or null checks
   - Log warnings for missing required fields (e.g., buyer party not found in `parties`)
   - Log statistics on field population rates during import to identify systematically empty fields
   - Handle malformed JSON records (skip and log, don't crash the entire import)

7. **Alternative data source**: If the OCDS API proves too unreliable, `https://data.gov.ro/dataset?q=achizitii+publice` may offer bulk CSV or JSON exports. The community tool `https://sicap.ai/` may also provide structured data access. These are fallback options -- try the OCDS API first.

8. **sicap.ai as reference**: The community-built SICAP.ai tool successfully parses Romanian procurement data. Its source code (if available) could provide insight into the actual data structure and field availability.
