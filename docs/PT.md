# Portugal (PT)

**Feasibility: Tier 1**

## Portal

- **Name**: Portal BASE
- **URL**: https://www.base.gov.pt/Base4/en/
- **Open data (OCDS)**: https://dados.gov.pt/en/datasets/ocds-portal-base-www-base-gov-pt/
- **Contracts**: https://dados.gov.pt/en/datasets/contratos-publicos-portal-base-impic-contratos-de-2012-a-2026/
- **Announcements**: https://dados.gov.pt/en/datasets/contratos-publicos-portal-base-impic-anuncios-de-2012-a-2026/
- **dados.gov API**: https://dados.gov.pt/en/docapi/

## Data Access

- **Method**: Bulk download from dados.gov.pt
- **Format**: JSON (OCDS), CSV
- **Auth**: Open
- **OCDS**: Yes — four procurement stages: tender, award, contract, implementation

## Coverage

All public contracts 2012 onwards (mainland + autonomous regions). Managed by IMPIC.

## Language

Portuguese

## Notes

- Called the "EU's e-procurement champion" by OCP
- OCP article: https://www.open-contracting.org/2020/04/16/portugal-what-you-need-to-know-about-the-eus-e-procurement-champion/
- Plans to add payment data and dedicated API
- Good historical coverage from 2012

## Schema Mapping

### Data Format Notes

Portugal publishes OCDS (Open Contracting Data Standard) data as **JSON record packages** via dados.gov.pt. The Kingfisher Collect project's Portugal spider confirms these are `record_package` type, with `iso-8859-1` encoding and `json_lines` compressed format. Each record package contains a `records` array, where each record has a `compiledRelease` object representing the latest state of a contracting process.

The OCDS data is accessed via the CKAN API at `https://dados.gov.pt/api/1/datasets/?q=ocds&organization=5ae97fa2c8d8c915d5faa3bf&page_size=20`, which returns dataset metadata including resource download URLs. Resources are compressed files (likely ZIP or GZ) containing JSON lines.

**Recommended approach**: Use the OCDS JSON data (not CSV) as the primary source because it is structured, standardized, and maps cleanly to our schema. The separate CSV contracts/announcements datasets on dados.gov.pt are an alternative but use a non-standard Portuguese-specific schema without formal documentation of field names. The OCDS data covers four stages (tender, award, contract, implementation), and each record contains party information (buyer/supplier), tender details, and award details.

**Key parsing considerations**:
- Encoding is ISO-8859-1 (Latin-1), not UTF-8
- Data is JSON lines format within compressed archives
- Each line is a full OCDS record package
- Records use `compiledRelease` which gives the latest state of each field
- Only records with `tag` containing `"award"` or `"contract"` should be processed (to match our award-only focus)
- Portugal is always the source country (`PT`)
- Currency is always EUR for Portuguese contracts

### Field Mapping Tables

In OCDS, organization details (buyer, supplier) are stored in a top-level `parties` array, with `OrganizationReference` objects (containing `id` and `name`) in `tender.procuringEntity`, `awards[].suppliers[]`, etc. To get full address details, the parser must cross-reference the `id` in the reference to the matching entry in the `parties` array.

OCDS path notation below uses dot-separated paths within the `compiledRelease` object of each record.

#### DocumentModel

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `doc_id` | `ocid` | The OCDS contracting process identifier. Prefix with `PT-` if needed to avoid collision with TED doc_ids. Format: `ocds-xxxxxx-NNNNNNNN` |
| `edition` | (none) | Set to `None`. OCDS has no edition concept. |
| `version` | (none) | Could use `compiledRelease.id` (release ID) or set to `None`. |
| `reception_id` | (none) | Set to `None`. No equivalent in OCDS. |
| `official_journal_ref` | (none) | Set to `None`. BASE is not a journal in the OJ sense. Could optionally store the `ocid` here. |
| `publication_date` | `compiledRelease.date` | The release date (ISO 8601). Use the date portion only. |
| `dispatch_date` | `compiledRelease.tender.tenderPeriod.startDate` | Approximate equivalent. Could also be `None` if concept does not cleanly map. |
| `source_country` | (hardcoded) | Always `"PT"`. |
| `contact_point` | `parties[buyer].contactPoint.name` | Cross-reference the buyer party from `parties` array using `buyer.id`. |
| `phone` | `parties[buyer].contactPoint.telephone` | Cross-reference via buyer party. |
| `email` | `parties[buyer].contactPoint.email` | Cross-reference via buyer party. |
| `url_general` | `parties[buyer].contactPoint.url` | Cross-reference via buyer party. |
| `url_buyer` | `parties[buyer].details.url` or `parties[buyer].contactPoint.url` | May not be populated separately from `url_general`. |

#### ContractingBodyModel

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `official_name` | `parties[buyer].name` | The buyer/procuringEntity party. Identify buyer via `parties` entry with `"buyer"` in `roles`. |
| `address` | `parties[buyer].address.streetAddress` | |
| `town` | `parties[buyer].address.locality` | |
| `postal_code` | `parties[buyer].address.postalCode` | |
| `country_code` | `parties[buyer].address.countryName` | **Needs normalization**: OCDS uses country name (e.g., `"Portugal"`), not ISO code. Hardcode `"PT"` or map from name. |
| `nuts_code` | (none) | OCDS does not have a standard NUTS code field. Set to `None`. Some publishers use `parties[].address.region` but this is free text, not NUTS. |
| `authority_type` | (none) | OCDS does not have a standard authority type codelist. The `parties[].details` extension may contain classification info, but this is not standard OCDS. Set to `None`. See Code Normalization section. |
| `main_activity_code` | (none) | Not part of standard OCDS. Set to `None`. |

#### ContractModel

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `title` | `compiledRelease.tender.title` | |
| `short_description` | `compiledRelease.tender.description` | |
| `main_cpv_code` | `compiledRelease.tender.items[0].classification.id` | OCDS uses `items[].classification` with scheme `"CPV"`. Take the first item's classification where `scheme == "CPV"`. |
| `cpv_codes` | `compiledRelease.tender.items[].classification` + `compiledRelease.tender.items[].additionalClassifications[]` | Collect all classifications where `scheme == "CPV"`. Use `id` for code and `description` for description. |
| `nuts_code` | (none) | OCDS `tender.items[].deliveryLocation` may have an `id` field but it is not guaranteed to be a NUTS code. Set to `None` unless the Portuguese data specifically uses NUTS codes here. |
| `contract_nature_code` | `compiledRelease.tender.mainProcurementCategory` | OCDS values: `"goods"`, `"works"`, `"services"`. See Code Normalization section. |
| `procedure_type` | `compiledRelease.tender.procurementMethod` + `compiledRelease.tender.procurementMethodDetails` | OCDS values: `"open"`, `"selective"`, `"limited"`, `"direct"`. See Code Normalization section. |
| `accelerated` | (none) | OCDS does not have an accelerated procedure flag. Always `False`. |

#### AwardModel

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `award_title` | `compiledRelease.awards[].title` | May be `None` if not populated. |
| `contract_number` | `compiledRelease.contracts[].id` or `compiledRelease.awards[].id` | OCDS links contracts to awards via `contracts[].awardID`. Use the contract `id` if available. |
| `tenders_received` | `compiledRelease.tender.numberOfTenderers` | This is at the tender level, not per-award. OCP data quality report notes this field may not be populated by Portugal. |
| `awarded_value` | `compiledRelease.awards[].value.amount` | |
| `awarded_value_currency` | `compiledRelease.awards[].value.currency` | Should always be `"EUR"` for Portuguese contracts. |
| `contractors` | `compiledRelease.awards[].suppliers[]` | Array of `OrganizationReference` objects. Must cross-reference `parties` array for full details. |

#### ContractorModel

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `official_name` | `parties[supplier].name` | Cross-reference the supplier `id` from `awards[].suppliers[].id` to the `parties` array entry with `"supplier"` in `roles`. |
| `address` | `parties[supplier].address.streetAddress` | |
| `town` | `parties[supplier].address.locality` | |
| `postal_code` | `parties[supplier].address.postalCode` | |
| `country_code` | `parties[supplier].address.countryName` | **Needs normalization**: OCDS uses country name, not ISO code. Must map (e.g., `"Portugal"` -> `"PT"`). |
| `nuts_code` | (none) | Not available in standard OCDS. Set to `None`. |

#### CpvCodeEntry

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `code` | `tender.items[].classification.id` (where `scheme == "CPV"`) | |
| `description` | `tender.items[].classification.description` | May be in Portuguese. |

#### ProcedureTypeEntry

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `code` | Derived from `tender.procurementMethod` | Requires mapping from OCDS values to eForms codes. See Code Normalization section. |
| `description` | `tender.procurementMethodDetails` | Free-text field, likely in Portuguese. |

#### AuthorityTypeEntry

| Schema Field | OCDS Path | Notes |
|---|---|---|
| `code` | (none) | Not available in standard OCDS. Set to `None`. |
| `description` | (none) | Not available. Set to `None`. |

### Unmappable Schema Fields

The following schema fields have no equivalent in the Portuguese OCDS data and should be set to `None`:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | TED-specific concept (OJ edition). Not present in OCDS. |
| `DocumentModel.reception_id` | TED-specific internal identifier. Not present in OCDS. |
| `DocumentModel.official_journal_ref` | TED-specific OJ reference. Not present in OCDS. |
| `DocumentModel.dispatch_date` | TED-specific concept (date sent to OJ). No clean OCDS equivalent. |
| `DocumentModel.url_buyer` | May overlap with `url_general`. Likely not separately available. |
| `ContractingBodyModel.nuts_code` | OCDS does not include NUTS codes. The `address.region` field is free text. |
| `ContractingBodyModel.authority_type` | Not part of standard OCDS. No codelist equivalent. |
| `ContractingBodyModel.main_activity_code` | Not part of standard OCDS. |
| `ContractModel.nuts_code` | OCDS `deliveryLocation` does not reliably provide NUTS codes. |
| `ContractModel.accelerated` | OCDS has no concept of accelerated procedures. Always `False`. |
| `ContractorModel.nuts_code` | Not available in standard OCDS. |

### Extra Portal Fields

The following fields are available in the Portuguese OCDS data but are not covered by the current schema. Flagged for review:

| OCDS Field | Description | Notes |
|---|---|---|
| `parties[].identifier.id` | Legal entity identifier (NIF/NIPC tax number) | **High value** -- schema does not cover entity identifiers. Would enable cross-referencing entities across portals. |
| `parties[].identifier.scheme` | Identifier scheme (e.g., `"PT-NIF"`) | Accompanies the identifier. |
| `parties[].identifier.legalName` | Registered legal name | May differ from `name` (trading name). |
| `compiledRelease.contracts[].period` | Contract execution period (start/end dates) | schema does not cover -- flagging for review. |
| `compiledRelease.contracts[].value` | Contract value (may differ from award value) | schema does not cover -- flagging for review. The award value and contract value can differ. |
| `compiledRelease.awards[].date` | Award decision date | schema does not cover -- flagging for review. Distinct from publication date. |
| `compiledRelease.awards[].status` | Award status (`"active"`, `"cancelled"`, etc.) | schema does not cover -- flagging for review. Useful for filtering out cancelled awards. |
| `compiledRelease.tender.status` | Tender status | schema does not cover -- flagging for review. |
| `compiledRelease.tender.tenderPeriod` | Tender submission period (start/end dates) | schema does not cover -- flagging for review. |
| `compiledRelease.tender.numberOfTenderers` | Number of tenderers (at tender level) | Maps to `AwardModel.tenders_received` but is tender-level, not per-award. |
| `compiledRelease.implementation` | Implementation stage data (transactions, milestones) | schema does not cover -- flagging for review. Portugal is one of few countries publishing implementation data. |
| `compiledRelease.tender.documents[]` | Tender documents with URLs | schema does not cover -- flagging for review. OCP notes some URLs may be invalid. |

### Code Normalization

Our schema uses exact eForms codes (lowercase, hyphens) for all coded values. OCDS uses its own codelists. The following mappings are needed:

#### Contract Nature Code (`contract_nature_code`)

OCDS `tender.mainProcurementCategory` values must be mapped to eForms `contract-nature-types` codes:

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"goods"` | `"supplies"` | OCDS uses "goods", eForms uses "supplies" |
| `"works"` | `"works"` | Direct match |
| `"services"` | `"services"` | Direct match |
| (missing/other) | `None` | Log warning |

#### Procedure Type Code (`procedure_type`)

OCDS `tender.procurementMethod` values must be mapped to eForms `procurement-procedure-type` codes. OCDS has only 4 broad categories vs eForms' fine-grained types:

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"open"` | `"open"` | Direct match |
| `"selective"` | `"restricted"` | OCDS "selective" = eForms "restricted" (pre-qualified bidders) |
| `"limited"` | `"neg-w-call"` | Best approximation. OCDS "limited" covers negotiated procedures with a limited pool. `tender.procurementMethodDetails` (free text, in Portuguese) may allow further disambiguation but would require text parsing. |
| `"direct"` | `"neg-wo-call"` | Direct award without competition = negotiated without prior call |
| (missing/other) | `None` | Log warning |

**Important**: The OCDS `tender.procurementMethodDetails` field contains the original Portuguese procedure name (e.g., "Ajuste Direto", "Concurso Publico", "Concurso Limitado por Previa Qualificacao"). This free-text field could enable more precise mapping but would require a Portuguese-to-eForms lookup table. Recommended approach: start with the coarse OCDS method mapping above, and store `procurementMethodDetails` in the `ProcedureTypeEntry.description` field for potential later refinement.

#### Authority Type Code

Not available in standard OCDS. Always `None`. If the Portuguese data includes a `parties[].details.classifications` extension, it might carry authority type info, but this is non-standard and would need to be verified against actual data.

#### Country Code Normalization

OCDS `address.countryName` is free text (e.g., `"Portugal"`, `"Espanha"`). Must be mapped to ISO 3166-1 alpha-2 codes. Options:
- Hardcode `"PT"` for buyer entities (since all BASE data is Portuguese)
- Build a lookup table for supplier country names (Portuguese language) to ISO codes
- Use `pycountry` or similar library for fuzzy matching

### Data Quality Warnings

Based on OCP Data Registry assessment of Portugal's OCDS data:

- **Party identifiers**: Some `parties[].identifier.id` values are placeholders (e.g., `"0"`). Non-unique party IDs reported.
- **Organization references**: Some `OrganizationReference` objects in awards/tender lack matching entries in the `parties` array. The parser must handle missing cross-references gracefully.
- **Blank fields**: A number of fields are blank/empty across the dataset.
- **Document URLs**: Some `tender/documents` URLs are invalid.
- **Inconsistent roles**: Party roles may be inconsistent between `OrganizationReference` usage and the `parties[].roles` array.
- **Contract section**: The poorest data coverage is around the `contracts` section. Award data and party data are more complete.
