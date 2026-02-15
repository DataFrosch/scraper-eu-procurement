# Finland (FI)

**Feasibility: Tier 1**

## Portal

- **Name**: Hilma
- **URL**: https://www.hankintailmoitukset.fi/en/
- **API Portal**: https://hns-hilma-prod-apim.developer.azure-api.net/
- **GitHub**: https://github.com/Hankintailmoitukset/hilma-api

## Data Access

- **Method**: REST API (Read API + Read API (EForms) + Search)
- **Base URL**: `https://api.hankintailmoitukset.fi/`
- **Format**: JSON (search, notice metadata), base64-encoded eForms UBL XML (notice content)
- **Auth**: `Ocp-Apim-Subscription-Key` header required. Self-service subscriptions are **disabled** on the developer portal — email `yllapito@hankintailmoitukset.fi` (Hansel Oy) to request access.
- **Swagger**: `https://api.hankintailmoitukset.fi/swagger/swagger/external-read-v1/swagger.json` (publicly accessible)
- **OCDS**: No

## Coverage

All public procurement notices (above and below EU thresholds).

## Language

Finnish, English (portal and API)

## Notes

- Owner: Ministry of Finance, maintained by Hansel Oy
- Azure APIM developer portal at https://hns-hilma-prod-apim.developer.azure-api.net/ (account creation works, but subscription creation is disabled)
- GitHub repo has API meeting memos and old AVP examples (marked OBSOLETE)
- Community R package: https://rdrr.io/github/hansel-oy/hilma/

## Schema Mapping

### Data Flow Overview

Hilma exposes two separate layers through the AVP (read) API:

1. **Search index** (`POST /notices/docs/search`) -- Azure Cognitive Search over a shared index of all notices (both eForms and legacy non-eForms). Returns summary metadata only. Used to discover notice IDs and filter by type, date, etc.
2. **Full notice retrieval** -- Separate endpoints for eForms and non-eForms notices. eForms notices are returned as **base64-encoded eForms UBL XML** documents. Non-eForms (legacy) notices are returned as JSON matching the old Hilma data model.

**Recommended strategy**: Use the search index to find contract award notice IDs (filtering by notice type), then fetch the full eForms XML for each. Since Hilma uses **eForms SDK 1.13.0**, the XML follows the same eForms UBL schema that our existing `eforms_ubl.py` parser already handles. The parser can be reused with minimal adaptation (primarily around document ID generation and `source_country` defaulting to `"FI"`).

For legacy (pre-eForms) notices, Hilma returns JSON based on their proprietary data model (see the `README-old.md` in the GitHub repo). A separate JSON parser would be needed for those.

### Data Format Notes

- **eForms notices (current)**: Base64-encoded eForms UBL XML. Decode base64, then parse as standard eForms XML. Our existing `eforms_ubl.py` parser handles this format directly.
- **Non-eForms notices (legacy)**: Hilma-proprietary JSON. The `objectDescriptions[n].awardContract.awardedContract` (single) or `objectDescriptions[n].awardContract.awardedContracts` (array) pattern is used for award data. A dedicated JSON parser would be needed.
- **Search index**: JSON responses following Azure Cognitive Search conventions. The index schema can be fetched via `GET /notices` to discover all filterable/searchable fields.
- **Rate limits**: All read endpoints are rate-limited. The exact limits are not documented; the API docs say "use in moderation."
- **Auth**: Requires `Ocp-Apim-Subscription-Key` header. Self-service subscriptions disabled — email `yllapito@hankintailmoitukset.fi` for access.
- **Batch retrieval**: Up to 50 eForms notices per batch request.

### Notice Type Filtering

Contract award notices in Hilma correspond to these notice type codes (from `NoticeType.cs`):

| Hilma NoticeType | Code | Description |
|---|---|---|
| ContractAward | (F03_2014) | Standard contract award |
| ContractAwardUtilities | (F06) | Utilities contract award |
| SocialContractAward | | Social/health services award |
| DefenceContractAward | | Defence contract award |
| ConcessionAward | | Concession award |
| SocialUtilitiesContractAward | | Social utilities award |
| DpsAward | (F03 or F06) | Dynamic purchasing system award |
| DesignContestResults | | Design contest results |
| SocialConcessionAward | | Social concession award |
| NationalDirectAward | | National direct award (below threshold) |

For eForms notices, the notice subtypes 29-37 correspond to contract award notices. The search index likely provides a type/subtype field to filter on.

### Field Mapping: eForms Notices (Primary Path)

Since Hilma returns standard eForms UBL XML for current notices, the field mappings are identical to our existing `eforms_ubl.py` parser. The table below documents the XML paths.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | Filename stem or `cbc:ID` in the XML | Hilma may use its own ID scheme (e.g. ETS identifier). Needs investigation of actual returned filenames/IDs. |
| `edition` | Derived from publication date | Same logic as eforms_ubl.py: `{year}{day_of_year:03d}` |
| `version` | Hardcode `"eForms-UBL"` | Or include Hilma SDK version if useful |
| `reception_id` | Not available in eForms XML | `None` |
| `official_journal_ref` | Not applicable for national notices | National (below-threshold) notices have no OJ reference. For above-threshold notices cross-published to TED, the TED doc_id is the canonical reference. Set to `None` or synthesize a Hilma-specific reference. |
| `publication_date` | `efac:Publication/efbc:PublicationDate` or `cbc:IssueDate` | Standard eForms date parsing (YYYY-MM-DD+HH:MM or YYYY-MM-DDZ) |
| `dispatch_date` | `cbc:IssueDate` | Same as publication date in eForms |
| `source_country` | `cac:Country/cbc:IdentificationCode` or hardcode `"FI"` | All Hilma notices are Finnish; can default to `"FI"` if not present in XML |
| `contact_point` | `efac:Company/cac:Contact/cbc:Name` | Not commonly populated in eForms |
| `phone` | `efac:Company/cac:Contact/cbc:Telephone` | From contracting party organization |
| `email` | `efac:Company/cac:Contact/cbc:ElectronicMail` | From contracting party organization. BT-506 is mandatory in Hilma national tailoring. |
| `url_general` | `efac:Company/cbc:WebsiteURI` | From contracting party organization |
| `url_buyer` | Not available in eForms standard path | `None`. BT-508 (buyer profile URL) is marked as PROHIBITED in Hilma's national tailoring for E3/E4 forms. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `efac:Company/cac:PartyName/cbc:Name` | BT-500. Mandatory. |
| `address` | `efac:Company/cac:PostalAddress/cbc:StreetName` | BT-510 |
| `town` | `efac:Company/cac:PostalAddress/cbc:CityName` | BT-513. Mandatory in Hilma national tailoring. |
| `postal_code` | `efac:Company/cac:PostalAddress/cbc:PostalZone` | BT-512 |
| `country_code` | `efac:Company/cac:PostalAddress/cac:Country/cbc:IdentificationCode` | BT-514 |
| `nuts_code` | `efac:Company/cac:PostalAddress/cbc:CountrySubentityCode` | BT-507. Mandatory when country has NUTS codes (Finland does: FI1xx). |
| `authority_type` | `cac:ContractingParty/cac:ContractingPartyType/cbc:PartyTypeCode` | BT-11 (buyer-legal-type). Mandatory in Hilma. Values are eForms codes -- see code normalization below. |
| `main_activity_code` | `cac:ContractingParty/cac:ContractingActivity/cbc:ActivityTypeCode` | BT-10. eForms activity codes. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `efac:SettledContract/cbc:Title` or `cac:ProcurementProject/cbc:Name` | BT-721 (contract title) or BT-21 (procedure title) |
| `short_description` | `cac:ProcurementProject/cbc:Description` or lot-level description | BT-24 |
| `main_cpv_code` | `cac:ProcurementProject/cac:MainCommodityClassification/cbc:ItemClassificationCode` | BT-262 |
| `cpv_codes` | Main + `cac:AdditionalCommodityClassification/cbc:ItemClassificationCode` | BT-263. eForms does not include CPV descriptions in the XML. |
| `nuts_code` | `cac:RealizedLocation/cbc:CountrySubentityCode` | BT-5071. Lot-level or project-level. |
| `contract_nature_code` | `cac:ProcurementProject/cbc:ProcurementTypeCode` | BT-23 (contract-nature). Mandatory in Hilma. Already eForms codes: `works`, `supplies`, `services`. |
| `procedure_type` | `cac:TenderingProcess/cbc:ProcedureCode` | BT-105. eForms codes (e.g. `open`, `restricted`, `neg-w-call`, `neg-wo-call`). |
| `accelerated` | `cac:TenderingProcess/cac:ProcessJustification/cbc:ProcessReasonCode[@listName='accelerated-procedure']` | BT-106. Note: marked as PROHIBITED in Hilma E3 forms per national tailoring. For E4 (award notices) it may still appear if the original procedure was accelerated. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `efac:SettledContract/cbc:Title` | BT-721 |
| `contract_number` | `efac:SettledContract/efac:ContractReference/cbc:ID` | BT-150 |
| `tenders_received` | `efac:LotResult/efac:ReceivedSubmissionsStatistics/efbc:StatisticsNumeric` where `efbc:StatisticsCode='tenders'` | BT-759. Needs filtering by statistics code. |
| `awarded_value` | `efac:LotTender/cac:LegalMonetaryTotal/cbc:PayableAmount` | BT-720. The `@currencyID` attribute provides the currency. |
| `awarded_value_currency` | `cbc:PayableAmount/@currencyID` | From the same element as awarded_value. Typically `EUR` for Finland. |
| `contractors` | Via `efac:TenderingParty/efac:Tenderer` cross-referenced with `efac:Organizations/efac:Organization/efac:Company` | Same resolution pattern as eforms_ubl.py: find winning tenderer org IDs, then look up organization details. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `efac:Company/cac:PartyName/cbc:Name` | BT-500 |
| `address` | `efac:Company/cac:PostalAddress/cbc:StreetName` | BT-510 |
| `town` | `efac:Company/cac:PostalAddress/cbc:CityName` | BT-513 |
| `postal_code` | `efac:Company/cac:PostalAddress/cbc:PostalZone` | BT-512 |
| `country_code` | `efac:Company/cac:PostalAddress/cac:Country/cbc:IdentificationCode` | BT-514 |
| `nuts_code` | `efac:Company/cac:PostalAddress/cbc:CountrySubentityCode` | BT-507 |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `cbc:ItemClassificationCode` text content | BT-262 (main) / BT-263 (additional) |
| `description` | Not available in eForms XML | `None`. CPV descriptions must come from a local lookup table if needed. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `cbc:ProcedureCode` text content | BT-105. Already eForms codes. |
| `description` | Not in XML | `None`. Can be populated from a static lookup of eForms procedure type codes. |

### Field Mapping: Legacy (Non-eForms) JSON Notices

For pre-eForms notices, Hilma returns a proprietary JSON structure. The exact field paths below are based on the legacy API documentation (`README-old.md`) and the C# data model. **The exact JSON field names need verification against a real API response** since the GitHub repo does not publish a complete JSON schema.

#### DocumentModel

| Schema Field | Portal Field/Path (JSON) | Notes |
|---|---|---|
| `doc_id` | `etsIdentifier` or `hilmaNoticeId` | The ETS identifier is the primary key in Hilma. |
| `edition` | Not directly available | Derive from publication date if needed. |
| `version` | Hardcode based on form type (e.g. `"F03_2014"`) | |
| `reception_id` | Not available | `None` |
| `official_journal_ref` | `tedPublicationInfo.tedOjsNumber` or similar | If the notice was published to TED. |
| `publication_date` | `datePublished` or `publicationDate` | Exact field name needs verification. |
| `dispatch_date` | `dateSentToTed` | If applicable. |
| `source_country` | Hardcode `"FI"` | All Hilma notices are Finnish. |
| `contact_point` | `organisationInformation.contactPerson` | Exact path needs verification. |
| `phone` | `organisationInformation.telephone` | Exact path needs verification. |
| `email` | `organisationInformation.email` | Exact path needs verification. |
| `url_general` | `organisationInformation.mainUrl` | Exact path needs verification. |
| `url_buyer` | `organisationInformation.buyerProfileUrl` | Exact path needs verification. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path (JSON) | Notes |
|---|---|---|
| `official_name` | `organisationInformation.officialName` | Exact path needs verification. |
| `address` | `organisationInformation.postalAddress.streetAddress` | Exact path needs verification. |
| `town` | `organisationInformation.postalAddress.town` | Exact path needs verification. |
| `postal_code` | `organisationInformation.postalAddress.postalCode` | Exact path needs verification. |
| `country_code` | `organisationInformation.postalAddress.country` | Exact path needs verification. |
| `nuts_code` | `organisationInformation.nutsCodes[0]` | Exact path needs verification. |
| `authority_type` | `organisationInformation.contractingAuthorityType` | Needs mapping from Hilma codes to eForms codes. |
| `main_activity_code` | `organisationInformation.mainActivity` | Needs mapping from Hilma codes to eForms codes. |

#### ContractModel

| Schema Field | Portal Field/Path (JSON) | Notes |
|---|---|---|
| `title` | `objectDescriptions[0].title` | Or `project.title`. Exact path needs verification. |
| `short_description` | `objectDescriptions[0].shortDescription` | Exact path needs verification. |
| `main_cpv_code` | `objectDescriptions[0].mainCpvCode.code` | Exact path needs verification. |
| `cpv_codes` | `objectDescriptions[0].additionalCpvCodes` | Array of CPV code objects. |
| `nuts_code` | `objectDescriptions[0].nutsCodes[0]` | Exact path needs verification. |
| `contract_nature_code` | `project.contractType` | Values likely `0`=supplies, `1`=works, `2`=services or similar. Needs mapping. |
| `procedure_type` | `procedureInformation.procedureType` | Values like `"ProTypeOpen"`, `"ProTypeRestricted"`. Needs mapping to eForms codes. |
| `accelerated` | `procedureInformation.acceleratedProcedure` | Boolean. Exact path needs verification. |

#### AwardModel

| Schema Field | Portal Field/Path (JSON) | Notes |
|---|---|---|
| `award_title` | `objectDescriptions[n].awardContract.awardedContract.title` | Or from `awardedContracts[]` array. |
| `contract_number` | `objectDescriptions[n].awardContract.contractNumber` | Exact path needs verification. |
| `tenders_received` | `objectDescriptions[n].awardContract.numberOfTendersReceived` | Exact path needs verification. |
| `awarded_value` | `objectDescriptions[n].awardContract.awardedContract.finalTotalValue.value` | Or `.totalValue.value`. |
| `awarded_value_currency` | `objectDescriptions[n].awardContract.awardedContract.finalTotalValue.currency` | Typically `EUR`. |
| `contractors` | `objectDescriptions[n].awardContract.awardedContract.contractors` | Array of contractor objects. |

#### ContractorModel (Legacy JSON)

| Schema Field | Portal Field/Path (JSON) | Notes |
|---|---|---|
| `official_name` | `contractors[n].officialName` | Exact path needs verification. |
| `address` | `contractors[n].postalAddress.streetAddress` | Exact path needs verification. |
| `town` | `contractors[n].postalAddress.town` | Exact path needs verification. |
| `postal_code` | `contractors[n].postalAddress.postalCode` | Exact path needs verification. |
| `country_code` | `contractors[n].postalAddress.country` | Exact path needs verification. |
| `nuts_code` | `contractors[n].nutsCodes[0]` | Exact path needs verification. |

### Unmappable Schema Fields

These fields will likely be `None` for Hilma-sourced notices:

| Schema Field | Reason |
|---|---|
| `DocumentModel.reception_id` | TED-specific concept. No equivalent in Hilma. |
| `DocumentModel.official_journal_ref` | Only applicable for notices cross-published to TED/OJ S. National-only notices have no OJ reference. |
| `DocumentModel.url_buyer` | BT-508 is PROHIBITED in Hilma's eForms national tailoring for E3/E4 forms. |
| `CpvCodeEntry.description` | eForms XML does not include CPV descriptions. Legacy JSON may include them (needs verification). |
| `ProcedureTypeEntry.description` | Not present in eForms XML. Can be populated from a static lookup table. |
| `AuthorityTypeEntry.description` | Not present in eForms XML. Can be populated from a static lookup table. |

### Extra Portal Fields

These fields are available in Hilma but not covered by the current schema. Flagged for review.

| Portal Field | Description | Notes |
|---|---|---|
| `BT-501` (Company ID / Business Register Number) | Organization registration ID (e.g. Finnish Y-tunnus) | Schema doesn't cover -- flagging for review. Very useful for entity resolution/deduplication. Mandatory in Hilma. |
| `HilmaStatistics` (green/social/innovation criteria) | Boolean fields for energy efficiency, circular economy, biodiversity, fair working conditions, innovation, SME participation | Schema doesn't cover -- flagging for review. Finland-specific statistical questions, mandatory since Jan 2022. |
| `BT-727` (Place of Performance) | Full place-of-performance description text | Schema only captures NUTS code, not free-text location descriptions. |
| `BT-539/BT-540` (Duration) | Contract duration (start/end dates or duration period) | Schema doesn't cover -- flagging for review. |
| `BT-36` (Duration period) | Contract duration in months/days | Schema doesn't cover -- flagging for review. |
| Vehicle purchase data | Per-lot vehicle category counts for clean vehicle directive | Schema doesn't cover -- flagging for review. Applicable when CPV codes match transport services. |
| `isPlan` flag | Distinguishes procurement plans from notices in search index | Not relevant for award notices, but important for search filtering. |
| `TedPublishState` | Whether the notice was cross-published to TED and its status | Schema doesn't cover -- flagging for review. Useful for deduplication against TED data. |
| National notice types (9902, etc.) | Below-threshold national procurement types | Schema doesn't cover notice type granularity -- flagging for review. These are the primary value-add over TED. |
| `endUserInvolved` | Whether end users were involved in procurement preparation | Schema doesn't cover -- flagging for review. Part of HilmaStatistics. |
| Multiple contracts per lot | `awardedContracts[]` array allows multiple awards per lot | Current schema supports multiple awards via the `awards` list, but the lot-level grouping is lost. |

### Code Normalization

#### Authority Type Codes (BT-11 buyer-legal-type)

eForms notices from Hilma already use eForms codelist values. No mapping needed for eForms path. These are the standard eForms `buyer-legal-type` codes:

| eForms Code | Description |
|---|---|
| `body-public` | Body governed by public law |
| `cent-gov` | Central government authority |
| `def-cont` | Defence contractor |
| `eu-ins-bod-ag` | EU institution, body or agency |
| `grp-p-aut` | Group of public authorities |
| `int-org` | International organization |
| `org-sub` | Organisation awarding a subsidised contract |
| `pub-undert` | Public undertaking |
| `ra-aut` | Regional or local authority |
| `rl-aut` | Regional or local authority |
| `spec-rights-entity` | Entity with special or exclusive rights |

For **legacy JSON notices**, the `contractingAuthorityType` field likely uses Hilma-internal or TED F-form codes (e.g. numeric codes 1-8 or uppercase string codes like `"MINISTRY"`, `"REGIONAL_AUTHORITY"`). These will need mapping to the eForms equivalents above. **The exact legacy code values need verification against real API responses.**

#### Contract Nature Codes (BT-23 contract-nature)

eForms notices use standard codes. No mapping needed for eForms path:

| eForms Code | Description |
|---|---|
| `works` | Works |
| `supplies` | Supplies |
| `services` | Services |

For **legacy JSON notices**, the `contractType` field may use numeric codes (e.g. `1`=supplies, `2`=services, `4`=works following TED conventions) or string codes. Mapping needed. Our existing `_normalize_contract_nature_code()` in `ted_v2.py` already handles TED numeric-to-eForms mapping and can be reused.

#### Procedure Type Codes (BT-105 procurement-procedure-type)

eForms notices use standard codes. No mapping needed for eForms path:

| eForms Code | Description |
|---|---|
| `open` | Open procedure |
| `restricted` | Restricted procedure |
| `neg-w-call` | Negotiated with prior call for competition |
| `neg-wo-call` | Negotiated without prior publication |
| `comp-dial` | Competitive dialogue |
| `innovation` | Innovation partnership |
| `oth-single` | Other single-stage procedure |
| `oth-multi` | Other multi-stage procedure |

For **legacy JSON notices**, the `procedureType` field uses Hilma-internal codes (likely matching TED F-form codes such as `"PT_OPEN"`, `"PT_RESTRICTED"`, `"PT_NEGOTIATED_WITH_PUBLICATION"`, etc.). Our existing `_normalize_procedure_type()` in `ted_v2.py` handles TED-to-eForms mapping and can be reused.

### Implementation Recommendations

1. **Start with eForms path only**: Since Hilma has been on eForms SDK since the transition, focus on eForms XML parsing first. The existing `eforms_ubl.py` parser can be reused almost directly -- the main changes are: (a) base64-decoding the API response before parsing, (b) generating `doc_id` from the Hilma identifier rather than filename, (c) defaulting `source_country` to `"FI"`.

2. **Search index discovery**: Before implementing, call `GET /notices` to fetch the current search index schema. This will reveal the exact field names available for filtering contract award notices by type and date. Document the actual index field names.

3. **Deduplication with TED**: Above-threshold Finnish notices are cross-published to TED. The `TedPublishState` field or the presence of a TED publication reference can be used to skip notices already imported via the TED portal. Alternatively, use `doc_id` collision (if Hilma's eForms XML uses the same document ID as TED).

4. **Legacy JSON parser**: Only needed if historical (pre-eForms) below-threshold notices are valuable. The JSON field paths documented above are best-effort based on the GitHub README and need verification against actual API responses. Recommend fetching a sample response first.

5. **API key management**: Store the `Ocp-Apim-Subscription-Key` as an environment variable (e.g. `HILMA_API_KEY`). Self-service subscriptions are disabled — email `yllapito@hankintailmoitukset.fi` for access.

6. **Verified eForms endpoint**: `GET https://api.hankintailmoitukset.fi/avp-eforms/external-read/v1/notice/{noticeId}` — returns JSON with `id` (int), `procedureId` (int), `eForm` (base64-encoded XML), `hilmaStatistics` (object), `dateCreated`, `dateModified`. The `noticeId` parameter is an integer (Hilma-generated).
