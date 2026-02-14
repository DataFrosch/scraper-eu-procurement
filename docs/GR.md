# Greece (GR)

**Feasibility: Tier 2**

## Portal

- **Name**: ESIDIS / Promitheus (National System of Electronic Public Procurement)
- **URL**: http://www.eprocurement.gov.gr/
- **API**: https://cerpp.eprocurement.gov.gr/khmdhs-opendata/help

## Data Access

- **Method**: REST API (KHMDHS OpenData)
- **Format**: JSON
- **Auth**: Basic Authentication required
- **OCDS**: No

## Coverage

Public procurement for projects >1,000 EUR (ex VAT).

## Language

Greek

## Notes

- API help page at /khmdhs-opendata/help
- Basic Auth requirement adds friction
- Open data situation in Greece has been described as deteriorating
- Documentation is Greek-only

## Schema Mapping

### API Overview

The KHMDHS OpenData API (OpenAPI 3.0 spec at `https://cerpp.eprocurement.gov.gr/khmdhs-opendata/v3/api-docs`) exposes five main entity types, each with a paginated POST search endpoint and a GET attachment endpoint:

| # | Greek Name | Endpoint | English | Relevance |
|---|-----------|----------|---------|-----------|
| 1 | Αιτήματα | `POST /request` | Requests | Low -- internal budget requests |
| 2 | Προσκλήσεις-Προκηρύξεις-Διακηρύξεις | `POST /notice` | Notices/Tenders | Medium -- call-for-tender stage, no award data |
| 3 | **Αναθέσεις** | **`POST /auction`** | **Awards/Assignments** | **High -- this is the award decision** |
| 4 | **Συμβάσεις** | **`POST /contract`** | **Contracts** | **High -- signed contract with contractor details** |
| 5 | Εντολές Πληρωμών | `POST /payment` | Payment Orders | Low -- post-contract payments |

Additionally: `GET /adamChain/{referenceNumber}` returns linked acts in the procurement chain (request -> notice -> award -> contract -> payments).

**Primary strategy**: Use the `/auction` endpoint (awards) as the main data source. Supplement with `/contract` endpoint to get contractor details when the auction record alone does not contain them. The `adamChain` endpoint can link an award's `referenceNumber` to its corresponding contract record.

All search endpoints accept a `page` query parameter (0-indexed) and return paginated results in a `content` array. Date-range queries auto-fill: if `dateTo` is omitted, it defaults to `dateFrom + 180 days`; if `dateFrom` is omitted, it defaults to `dateTo - 180 days`.

### Auction (Award) Response Fields

Based on the OpenAPI specification, the `/auction` response objects include:

**Top-level fields**: `title`, `referenceNumber`, `submissionDate`, `lastUpdateDate`, `signedDate`, `publishedDate`, `cancelled`, `cancellationDate`, `cancellationType`, `cancellationReason`, `cancellationADA`, `protocolNumber`, `aaht` (ADAM reference number), `authorEmail`, `organizationVatNumber`, `greekOrganizationVatNumber`, `budget`, `nutsCode`, `nutsCity`, `nutsPostalCode`, `nutsCountry`, `contractType`, `additionalContractType`, `amendPreviousAuction`, `amendedAuctionADAM`, `centralizedMarkets`, `legalContext`, `classificationOfPublicLawOrganization`, `typeOfContractingAuthority`, `auctionAmount`, `procedureType`, `awardProcedure`, `numberOfSections`, `criteriaCode`, `assignedContract`, `socialContract`, `centralGovernmentAuthority`, `contractDuration`, `contractingAuthorityActivity`

**Nested objects**:
- `contractingData` -- contains `unitsOperator` and `signers`
- `contractingMembersDataList[]` -- array of objects with `vatNumber`, `greekVatNumber`, `name`, `nutsCode`, `installationCountry`
- `objectDetailsList[]` -- array of objects with `quantity`, `costWithoutVAT`, `type`, `vat`, `currency`, `shortDescription`, `cpvs`

### Auction Search Criteria (Request Body)

`title`, `cpvItems[]`, `organizations[]`, `signer`, `referenceNumber`, `contractType`, `dateFrom`, `dateTo`, `totalCostFrom`, `totalCostTo`, `cancelDateFrom`, `cancelDateTo`, `procedureType`, `vatNumber`, `contractorName`, `aaht`, `estTotalCostFrom`, `estTotalCostTo`, `isModified`

### Contract Response Fields

The `/contract` response includes: `title`, `referenceNumber`, `previousRequestReferenceNumber`, `signedDate`, `lastUpdateDate`, `submissionDate`, `procurementDeliveryDate`, `cancellationDate`, `cancelled`, `cancellationReason`, `cancellationADA`, `cancellationType`, `protocolNumber`, `approvalCommitmentCode`, `procedureType`, `approvalADA`, `authorEmail`, and contractor-related fields accessible via search by `contractorName` and `vatNumber`.

### Contract Search Criteria (Request Body)

`title`, `cpvItems[]`, `organizations[]`, `referenceNumber`, `signer`, `contractType`, `dateFrom`, `dateTo`, `totalCostFrom`, `totalCostTo`, `cancelDateFrom`, `cancelDateTo`, `procedureType`, `vatNumber`, `contractorName`, `aaht`, `estTotalCostFrom`, `estTotalCostTo`, `isModified`

### Field Mapping Tables

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `referenceNumber` (ADAM code) | The ADAM reference number (e.g., `25AWRD...`) serves as the unique document identifier. Format: `YYtypeNNNNNNNNNN`. |
| `edition` | -- | `None`. No edition concept in KHMDHS. |
| `version` | `isModified` / `amendPreviousAuction` | Boolean flags indicate if the record was modified. No explicit version number. Could store `"modified"` if `isModified` is true, but recommend `None` per fail-loud principle. |
| `reception_id` | -- | `None`. No reception ID concept. |
| `official_journal_ref` | -- | `None`. KHMDHS is not an official journal. |
| `publication_date` | `publishedDate` | Datetime string, parse date portion. May be `null`. |
| `dispatch_date` | `submissionDate` | The date the record was submitted to KHMDHS. Datetime string. |
| `source_country` | hardcode `"GR"` | All records are Greek. |
| `contact_point` | -- | `None`. Not available in API response. |
| `phone` | -- | `None`. Not available in API response. |
| `email` | `authorEmail` | Email of the person who submitted the record. Not exactly a contact point but closest available. |
| `url_general` | Construct from referenceNumber | Could construct `https://cerpp.eprocurement.gov.gr/khmdhs-opendata/auction/attachment/{referenceNumber}` for the PDF link. |
| `url_buyer` | -- | `None`. Not available in API response. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `contractingMembersDataList[0].name` | The first (or sole) member of the contracting members list. If list is empty, this is a problem -- the organization ID is in `organizations[]` (search criteria) or `organizationVatNumber` but the name must come from the members list. |
| `address` | -- | `None`. Not available in the auction response. |
| `town` | `nutsCity` | The NUTS-associated city name from the auction response. |
| `postal_code` | `nutsPostalCode` | Postal code from the auction response. |
| `country_code` | `nutsCountry` OR `contractingMembersDataList[0].installationCountry` | Country from NUTS data or member data. Will typically be `"GR"`. |
| `nuts_code` | `nutsCode` OR `contractingMembersDataList[0].nutsCode` | NUTS code from top-level or from member data. Verify format matches EU NUTS codes (e.g., `EL30` for Attica). Note: Greece uses `EL` prefix in NUTS, not `GR`. |
| `authority_type` | `typeOfContractingAuthority` | Numeric code (e.g., `"10"`, `"12"`). **Requires mapping to eForms codes** -- see Code Normalization section. |
| `main_activity_code` | `contractingAuthorityActivity` | Numeric code. **Requires mapping to eForms codes** -- see Code Normalization section. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `title` | Direct mapping. Will be in Greek. |
| `short_description` | `objectDetailsList[].shortDescription` | Concatenate or use first item's `shortDescription`. May be `null` for some items. |
| `main_cpv_code` | `objectDetailsList[0].cpvs[0]` | First CPV code from the first object detail. CPV format is `########-#` (validated by the API). |
| `cpv_codes` | `objectDetailsList[*].cpvs[*]` | Flatten all CPV codes from all object details. Deduplicate. |
| `nuts_code` | `nutsCode` | Top-level NUTS code for the contract. Same as contracting body NUTS. |
| `contract_nature_code` | `contractType` | Numeric code (e.g., `"10"`, `"12"`). **Requires mapping to eForms codes** (`services`, `supplies`, `works`) -- see Code Normalization section. |
| `procedure_type` | `procedureType` | Numeric code (e.g., `"1"`). **Requires mapping to eForms codes** -- see Code Normalization section. |
| `accelerated` | -- | `False`. No accelerated procedure flag observed in the API. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `title` | Same as contract title. The API does not distinguish award title from the overall title. |
| `contract_number` | `referenceNumber` | The ADAM reference number of the award. |
| `tenders_received` | `numberOfSections` | **Uncertain mapping**. `numberOfSections` may refer to lots, not tenders received. More likely `None` -- the API does not appear to expose tender count. |
| `awarded_value` | `auctionAmount` OR `budget` OR `objectDetailsList[].costWithoutVAT` | `auctionAmount` is the most likely field for the awarded value. `budget` may be the estimated value. If `auctionAmount` is `null`, sum `costWithoutVAT` from `objectDetailsList`. Verify which field represents the actual awarded amount vs. estimated budget. |
| `awarded_value_currency` | `objectDetailsList[].currency` OR hardcode `"EUR"` | Greece uses EUR. The `objectDetailsList` items have a `currency` field. If present, use it; otherwise default to `"EUR"`. Per fail-loud principle, prefer extracting from data. |
| `contractors` | See ContractorModel below | Contractor details may need to come from the linked `/contract` endpoint via `adamChain`. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `/contract` response or `contractorName` search field | **The auction endpoint does not appear to include contractor name in the response.** Contractor details are on the `/contract` endpoint. Must follow the `adamChain` from the auction `referenceNumber` to find the linked contract, then extract contractor data from there. Alternatively, the `contractingMembersDataList` might sometimes contain contractor info, but this seems to be about the contracting authority members, not the winning bidder. |
| `address` | -- | `None`. Not clearly available even on the contract endpoint response. |
| `town` | -- | `None`. Not clearly available. |
| `postal_code` | -- | `None`. Not clearly available. |
| `country_code` | -- | `None`. Not clearly available. May be inferred as `"GR"` for domestic contractors but should not be assumed. |
| `nuts_code` | -- | `None`. Not clearly available. |

**Critical gap**: Contractor details (name, address, VAT number) appear to be on the `/contract` endpoint but the exact response schema for contractor fields is not fully documented in the OpenAPI spec. The search criteria allow filtering by `contractorName` and `vatNumber`, suggesting these fields exist in the response. The implementer must make sample API calls to confirm the exact contractor field names and structure in the contract response.

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `objectDetailsList[*].cpvs[*]` | CPV codes from the object details list. Format `########-#`. |
| `description` | -- | `None` from the portal. CPV descriptions can be looked up from the standard CPV code list. The portal's own CPV lookup is at `https://cerpp.eprocurement.gov.gr/cpv/main/`. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `procedureType` (after mapping to eForms) | Raw value is a numeric code. Must be mapped to eForms equivalent. See Code Normalization. |
| `description` | -- | `None` from the portal. Derive from the eForms code list after mapping. |

### Unmappable Schema Fields

These fields have no equivalent in the KHMDHS API and should be set to `None`:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | No edition concept in KHMDHS |
| `DocumentModel.version` | No version numbering (only boolean `isModified`) |
| `DocumentModel.reception_id` | No reception ID concept |
| `DocumentModel.official_journal_ref` | KHMDHS is not an official journal |
| `DocumentModel.contact_point` | Not in API response |
| `DocumentModel.phone` | Not in API response |
| `DocumentModel.url_buyer` | Not in API response |
| `ContractingBodyModel.address` | Not in auction API response (only NUTS-level location data) |
| `AwardModel.tenders_received` | Not exposed by the API |
| `ContractModel.accelerated` | No accelerated procedure flag; always `False` |
| `ContractorModel.address` | Not confirmed in API response |
| `ContractorModel.town` | Not confirmed in API response |
| `ContractorModel.postal_code` | Not confirmed in API response |
| `ContractorModel.country_code` | Not confirmed in API response |
| `ContractorModel.nuts_code` | Not confirmed in API response |

### Extra Portal Fields

These fields are available in the KHMDHS API but not covered by the current schema. Flagging for review:

| Portal Field | Type | Notes |
|---|---|---|
| `organizationVatNumber` / `greekOrganizationVatNumber` | string | VAT number of the contracting authority. Useful for entity resolution. Schema doesn't cover -- flagging for review. |
| `contractingMembersDataList[].vatNumber` / `greekVatNumber` | string | VAT numbers for all contracting body members. Schema doesn't cover -- flagging for review. |
| `budget` | number | Estimated budget/value. Distinct from `auctionAmount` (awarded value). Schema doesn't cover -- flagging for review. |
| `aaht` | string | Secondary reference number (ADAM). Schema doesn't cover -- flagging for review. |
| `protocolNumber` | string | Protocol number in the contracting body's registry. Schema doesn't cover -- flagging for review. |
| `criteriaCode` | string | Award criteria code (e.g., lowest price, best value). Schema doesn't cover -- flagging for review. |
| `legalContext` | string | Legal basis for the procurement. Schema doesn't cover -- flagging for review. |
| `classificationOfPublicLawOrganization` | string | Sub-classification of the authority. Schema doesn't cover -- flagging for review. |
| `centralizedMarkets` | array | Whether centralized purchasing was used. Schema doesn't cover -- flagging for review. |
| `socialContract` | boolean | Social clause contract flag. Schema doesn't cover -- flagging for review. |
| `centralGovernmentAuthority` | boolean | Whether authority is central government. Schema doesn't cover -- flagging for review. |
| `contractDuration` | unknown | Duration of the contract. Schema doesn't cover -- flagging for review. |
| `assignedContract` | unknown | Whether a contract has been signed for this award. Schema doesn't cover -- flagging for review. |
| `objectDetailsList[].quantity` | number | Quantity per lot/object. Schema doesn't cover -- flagging for review. |
| `objectDetailsList[].vat` | number | VAT rate per object. Schema doesn't cover -- flagging for review. |
| `objectDetailsList[].type` | string | Object type classification. Schema doesn't cover -- flagging for review. |
| `cancelled` / `cancellationDate` / `cancellationType` / `cancellationReason` | various | Full cancellation metadata. Schema doesn't cover -- flagging for review. |
| `amendPreviousAuction` / `amendedAuctionADAM` | boolean/string | Amendment chain tracking. Schema doesn't cover -- flagging for review. |
| `awardProcedure` | string | Award procedure sub-type. Schema doesn't cover -- flagging for review. |
| Payment data (`/payment` endpoint) | various | Full payment tracking per contract. Schema doesn't cover -- flagging for review. |

### Code Normalization

The KHMDHS API uses numeric codes for several fields that must be mapped to eForms equivalents. The exact code-to-meaning mappings are **not documented in the OpenAPI spec** -- they must be discovered by either:
1. Making sample API calls and inspecting values
2. Consulting the KHMDHS web UI's dropdown menus
3. Contacting the portal administrators

#### contractType (Contract Nature)

Maps to `contract_nature_code` in the schema. Expected eForms target values: `services`, `supplies`, `works`.

| KHMDHS Code | Suspected Meaning | eForms Code |
|---|---|---|
| `10` | Unknown -- needs verification | `services` / `supplies` / `works` |
| `12` | Unknown -- needs verification | `services` / `supplies` / `works` |
| Others | Unknown -- full code list not documented | TBD |

**Action required**: Make sample API calls across different `contractType` values, or inspect the KHMDHS web UI at `https://cerpp.eprocurement.gov.gr/kimds2/` to find the dropdown options and their numeric codes.

#### procedureType (Procedure Type)

Maps to `procedure_type` in the schema. Expected eForms target values: `open`, `restricted`, `neg-w-call`, `neg-wo-call`, `comp-dial`, `innovation`, etc.

| KHMDHS Code | Suspected Meaning | eForms Code |
|---|---|---|
| `1` | Unknown -- possibly Open | `open` (?) |
| Others | Unknown -- full code list not documented | TBD |

**Action required**: Same approach as contractType. Greek procurement law (N.4412/2016) defines procedure types that should map to EU directives.

#### typeOfContractingAuthority (Authority Type)

Maps to `authority_type` in the schema. Expected eForms target values: `ra-authority`, `body-public`, `eu-ins-bod-ag`, `grp-p-aut`, etc.

| KHMDHS Code | Suspected Meaning | eForms Code |
|---|---|---|
| `10` | Unknown | TBD |
| `12` | Possibly "Central Administration" (Κεντρική Διοίκηση) | `ra-authority` (?) |
| Others | Unknown -- full code list not documented | TBD |

**Action required**: Same discovery approach. The `classificationOfPublicLawOrganization` and `centralGovernmentAuthority` fields may help disambiguate.

#### contractingAuthorityActivity (Main Activity)

Maps to `main_activity_code` in the schema. Expected eForms target values: `gen-pub`, `defence`, `health`, `housing`, `education`, etc.

**Action required**: No code values observed yet. Discover via sample API calls.

#### criteriaCode (Award Criteria)

Not mapped to the current schema, but if added: expected eForms target values: `price`, `quality`, `cost`.

### Data Format Notes

- **Format**: JSON responses from REST API (POST requests with JSON body, paginated responses)
- **Authentication**: HTTP Basic Authentication required for all endpoints. Credentials must be obtained by registration.
- **Pagination**: Zero-indexed `page` query parameter. Page size is server-controlled (not documented; likely 10 or 20 items per page). Must iterate through all pages.
- **Date handling**: Dates are ISO 8601 datetime strings (e.g., `"2025-01-21T11:21:09.222823"`). Parse date portion only for `publication_date` and `dispatch_date`.
- **Date range constraints**: Queries enforce a maximum 180-day window. For yearly scraping, iterate in ~6-month windows (e.g., Jan-Jun, Jul-Dec per year).
- **Currency**: Greece uses EUR. The `objectDetailsList[].currency` field may confirm this per record.
- **Character encoding**: Expect Greek text (UTF-8) in titles, descriptions, and organization names.
- **NUTS codes**: Greece uses `EL` prefix (not `GR`) in NUTS codes (e.g., `EL30` for Attica). This is standard EU practice.
- **CPV codes**: Standard EU CPV format `########-#`. The API validates this format.
- **Cancelled records**: The `cancelled` boolean and related fields indicate cancelled awards. These should be filtered out during import (or flagged).
- **Amendments**: `amendPreviousAuction` and `isModified` flags indicate amended records. The `amendedAuctionADAM` field points to the original. Decide whether to import only the latest version.
- **Rate limits**: Not documented in the API spec. Implement conservative rate limiting (e.g., 1 request/second) until limits are known.
- **Error handling**: API returns `ErrorResponse` objects with HTTP 400/404/500 status codes.

### Implementation Notes

1. **Two-endpoint strategy**: The award data is split across `/auction` (award decision) and `/contract` (signed contract with contractor). The implementer must decide whether to:
   - (a) Use `/auction` as primary and follow `adamChain` to get contractor details from the linked `/contract` -- more complete but slower (3 API calls per award).
   - (b) Use `/contract` as primary (since it has both award and contractor info) -- but may miss awards that haven't resulted in a signed contract yet.
   - (c) Use both endpoints independently and merge by `referenceNumber` chain.

   **Recommended**: Start with option (b) -- the `/contract` endpoint -- since it likely contains the most complete data for signed contracts, and our schema is centered on awarded contracts.

2. **Iterating by date**: Use 180-day windows with `dateFrom`/`dateTo`, paginating through all results. For a full year, two windows (Jan 1 - Jun 30, Jul 1 - Dec 31) should suffice.

3. **Credentials management**: Store Basic Auth credentials in environment variables (e.g., `GR_KHMDHS_USER`, `GR_KHMDHS_PASSWORD`). Do not hardcode.

4. **Field discovery**: Before full implementation, make exploratory API calls to:
   - Confirm contractor field names in `/contract` response
   - Document all valid values for `contractType`, `procedureType`, `typeOfContractingAuthority`, `contractingAuthorityActivity`
   - Determine page size and total result counts
   - Test `adamChain` linking behavior
