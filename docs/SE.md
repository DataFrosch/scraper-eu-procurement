# Sweden (SE)

**Feasibility: Tier 3**

## Portal

- **Name**: Upphandlingsmyndigheten (National Agency for Public Procurement)
- **URL**: https://www.upphandlingsmyndigheten.se/en/
- **Data portal**: https://www.dataportal.se/
- **Community project**: https://github.com/okfse/oppna-upphandlingsdata

## Data Access

- **Method**: Statistics database on data portal; community-driven open data efforts
- **Format**: CSV
- **Auth**: Open
- **OCDS**: No

## Coverage

Statistics on procurement tenders, values, winning companies.

## Language

Swedish

## Notes

- No centralized procurement notice portal with API
- Data available primarily as statistics rather than individual notices
- Community initiative "Oppen Upphandling" pushing for better data access
- Article: https://medium.com/civictechsweden/disrupting-public-procurement-with-open-data-in-sweden-f8d774b0e5e5

## Schema Mapping

### Critical Data Access Limitation

Sweden is a **Tier 3** country because there is no public API or data source that provides **individual notice-level** contract award data. The data landscape is as follows:

1. **Statistikdatabasen** (https://www.upphandlingsmyndigheten.se/statistik/statistikdatabasen/) -- The official open data from Upphandlingsmyndigheten. Available as CSV/Excel download. This contains **aggregate statistics** about announced procurements (counts by year, CPV category, procedure type, region, etc.), NOT individual notice-level records with contractor names, award values, or contracting body details. Five datasets are published, all under the statistics product "Advertised Procurements in Sweden" (Annonserade upphandlingar i Sverige).

2. **UBL Reporting API** (UFS 2023:1 / UFS 2023:2) -- Upphandlingsmyndigheten operates a **write-only collection API** that registered procurement databases (annonsdatabaser) use to **submit** notice data for statistical purposes. The format is UBL 2.3-based XML (with Annex 3 defining the ContractAwardNotice schema). This API is NOT publicly readable -- it is a submission endpoint for registered platform operators, not a retrieval API.

3. **Registered Procurement Databases (Annonsdatabaser)** -- Procurement notices are published across multiple private/commercial platforms registered with Konkurrensverket (Swedish Competition Authority): e-Avrop, Mercell TendSign, Mercell Opic, and others. These are the actual sources of individual notices, but they are commercial platforms without public read APIs. There is no centralized national procurement portal aggregating them.

4. **Community project** (okfse/oppna-upphandlingsdata) -- Scrapes the Statistikdatabasen and provides cleaned CSV/Excel files. Same aggregate statistics limitation applies.

**Bottom line**: There is currently no viable path to obtain individual award-level data (contracting body, contractor names, award values, CPV codes per notice) from any Swedish open data source. The data that *would* populate our schema exists inside the registered annonsdatabaser and in Upphandlingsmyndigheten's internal collection database, but neither exposes a public read API. Upphandlingsmyndigheten has stated that a public retrieval API is planned for the future, but as of February 2026, it does not exist.

### Data Format Notes

- **Statistics data**: CSV and Excel files downloadable from Statistikdatabasen. Aggregate counts and breakdowns, not individual records.
- **Reporting format** (write-only API): UBL 2.3 XML, following eForms business terms with Swedish national extensions. Annex 3 (ContractAwardNotice) is the relevant document type. The specification follows eForms codes where possible, with additional codes for below-threshold national procurement types.
- **Language**: All data is in Swedish. Field names, descriptions, and values are in Swedish.
- **No OCDS support**: Sweden does not publish procurement data in OCDS format.

### Field Mapping Table (Theoretical)

The tables below document what a mapping **would** look like if individual notice-level data becomes available. The "Portal Field/Path" column references the UBL Reporting Format (Annex 3: ContractAwardNotice) since that is the closest thing to a structured data specification Sweden has. These paths describe the XML structure that registered databases submit to Upphandlingsmyndigheten -- they are documented here for future use when/if a public read API is launched.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `cbc:ID` (UBL document ID) or `ext:SwedishProcurementID` | Each procurement has a unique "upphandlings-ID". The UBL schema also includes `ext:RegisteredDatabaseID` identifying the source platform. **No public access to retrieve by ID.** |
| `edition` | Not available | No OJ S edition equivalent. `None`. |
| `version` | Not available | Could hardcode `"SE-UBL-1.1"` if data becomes accessible. |
| `reception_id` | Not available | TED-specific concept. `None`. |
| `official_journal_ref` | Not available | National notices have no OJ reference. Above-threshold notices are published on TED and already captured there. `None`. |
| `publication_date` | `cbc:IssueDate` | Date the notice was published in the registered database. |
| `dispatch_date` | `cbc:IssueDate` | Same as publication date for national notices. |
| `source_country` | Hardcode `"SE"` | All notices from this portal are Swedish. |
| `contact_point` | `cac:ContractingParty/cac:Party/cac:Contact/cbc:Name` | Standard UBL contact path. Availability in Swedish data is uncertain. |
| `phone` | `cac:ContractingParty/cac:Party/cac:Contact/cbc:Telephone` | Standard UBL path. |
| `email` | `cac:ContractingParty/cac:Party/cac:Contact/cbc:ElectronicMail` | BT-506. Likely mandatory per Swedish reporting rules. |
| `url_general` | `cac:ContractingParty/cac:Party/cbc:WebsiteURI` | BT-505. |
| `url_buyer` | `cac:ContractingParty/cac:Party/cbc:BuyerProfileURI` | BT-508. May or may not be populated. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `cac:ContractingParty/cac:Party/cac:PartyName/cbc:Name` | BT-500. Mandatory. |
| `address` | `cac:ContractingParty/cac:Party/cac:PostalAddress/cbc:StreetName` | BT-510. |
| `town` | `cac:ContractingParty/cac:Party/cac:PostalAddress/cbc:CityName` | BT-513. |
| `postal_code` | `cac:ContractingParty/cac:Party/cac:PostalAddress/cbc:PostalZone` | BT-512. |
| `country_code` | `cac:ContractingParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode` | BT-514. Typically `"SE"`. |
| `nuts_code` | `cac:ContractingParty/cac:Party/cac:PostalAddress/cbc:CountrySubentityCode` | BT-507. Sweden has NUTS codes SE1xx-SE3xx. |
| `authority_type` | `cac:ContractingParty/cac:ContractingPartyType/cbc:PartyTypeCode` | BT-11 (buyer-legal-type). See code normalization below. |
| `main_activity_code` | `cac:ContractingParty/cac:ContractingActivity/cbc:ActivityTypeCode` | BT-10. eForms activity codes. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `cac:ProcurementProject/cbc:Name` | BT-21 (procedure title). Swedish language. |
| `short_description` | `cac:ProcurementProject/cbc:Description` | BT-24. Swedish language. |
| `main_cpv_code` | `cac:ProcurementProject/cac:MainCommodityClassification/cbc:ItemClassificationCode` | BT-262. |
| `cpv_codes` | Main + `cac:AdditionalCommodityClassification/cbc:ItemClassificationCode` at lot level | BT-263. Standard CPV codes. |
| `nuts_code` | `cac:ProcurementProjectLot/cac:ProcurementProject/cac:RealizedLocation/cbc:CountrySubentityCode` | BT-5071. Place of performance NUTS code. |
| `contract_nature_code` | `cac:ProcurementProject/cbc:ProcurementTypeCode` | BT-23. eForms codes: `works`, `supplies`, `services`. |
| `procedure_type` | `cac:TenderingProcess/cbc:ProcedureCode` | BT-105. eForms codes. See code normalization below. |
| `accelerated` | `cac:TenderingProcess/cac:ProcessJustification/cbc:ProcessReasonCode[@listName='accelerated-procedure']` | BT-106. Boolean derived from presence of code. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `cac:TenderResult/cbc:Description` or settled contract title | UBL TenderResult or eForms `efac:SettledContract/cbc:Title` (BT-721). |
| `contract_number` | `cac:TenderResult/cac:Contract/cbc:ID` or `efac:SettledContract/efac:ContractReference/cbc:ID` | BT-150. |
| `tenders_received` | `cac:TenderingProcess/ext:UBLExtensions/.../cbc:ReceivedTenderQuantity` | Per Annex 3 schema, this is in a UBL extension within TenderingProcess. |
| `awarded_value` | `cac:TenderResult/cac:AwardedTenderedProject/cbc:TotalAmount` or lot tender `cac:LegalMonetaryTotal/cbc:PayableAmount` | BT-720. The `@currencyID` attribute provides currency. |
| `awarded_value_currency` | `@currencyID` attribute on the amount element | Typically `SEK` for national procurements. |
| `contractors` | `cac:TenderResult/cac:WinningParty/cac:Party` or via eForms `efac:TenderingParty/efac:Tenderer` cross-reference | Winner party details. Multiple contractors possible for joint bids. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `cac:WinningParty/cac:Party/cac:PartyName/cbc:Name` | BT-500. |
| `address` | `cac:WinningParty/cac:Party/cac:PostalAddress/cbc:StreetName` | BT-510. |
| `town` | `cac:WinningParty/cac:Party/cac:PostalAddress/cbc:CityName` | BT-513. |
| `postal_code` | `cac:WinningParty/cac:Party/cac:PostalAddress/cbc:PostalZone` | BT-512. |
| `country_code` | `cac:WinningParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode` | BT-514. |
| `nuts_code` | `cac:WinningParty/cac:Party/cac:PostalAddress/cbc:CountrySubentityCode` | BT-507. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `cbc:ItemClassificationCode` text content | BT-262 (main) / BT-263 (additional). Standard CPV codes. |
| `description` | Not available in UBL XML | `None`. CPV descriptions would need a local lookup table. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `cbc:ProcedureCode` text content | BT-105. Uses eForms codes per the reporting specification. |
| `description` | Not in XML | `None`. Can be populated from a static eForms code lookup. |

### Unmappable Schema Fields

These fields will be `None` for any Swedish portal data:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | No OJ S edition concept for national notices. |
| `DocumentModel.version` | No standard version field available. |
| `DocumentModel.reception_id` | TED-specific concept. No equivalent in Swedish system. |
| `DocumentModel.official_journal_ref` | National-only notices have no OJ reference. Above-threshold notices are already on TED. |
| `CpvCodeEntry.description` | UBL XML does not include CPV descriptions. |
| `ProcedureTypeEntry.description` | Not present in UBL XML. Could be populated from a static lookup. |
| `AuthorityTypeEntry.description` | Not present in UBL XML. Could be populated from a static lookup. |

Additionally, the following fields have **uncertain availability** even if notice-level data becomes accessible:

| Schema Field | Uncertainty |
|---|---|
| `DocumentModel.contact_point` | May or may not be populated in Swedish reporting. |
| `DocumentModel.url_buyer` | BT-508 may not be commonly used in Sweden. |
| `ContractorModel.nuts_code` | Contractor NUTS codes may not be reported for Swedish suppliers. |

### Extra Portal Fields

These fields exist in the Swedish UBL reporting format (Annex 3) or in the Statistikdatabasen but are not covered by our schema. Flagged for review.

| Portal Field | Description | Notes |
|---|---|---|
| `ext:SwedishProcurementID` (Upphandlings-ID) | Unique national procurement identifier | Schema doesn't cover -- flagging for review. Essential for deduplication and tracking procurements across their lifecycle. |
| `ext:RegisteredDatabaseID` | Identifies which annonsdatabas published the notice | Schema doesn't cover -- flagging for review. Useful for provenance tracking. |
| `cbc:ReceivedTenderQuantity` (lowest/highest tender values) | `LowerTenderAmount` and `HigherTenderAmount` -- range of admissible tender values | Schema only captures the awarded value, not the bid range. Flagging for review. |
| Organization registration number | Swedish organizational number (organisationsnummer) | Schema doesn't cover -- flagging for review. Very useful for entity resolution/deduplication. |
| Below-threshold procurement type | National procedure types not in eForms standard (e.g. direct award / direktupphandling) | Schema doesn't cover notice-type granularity -- flagging for review. These below-threshold procurements are the primary value-add over TED. |
| Framework agreement indicators | Whether the procurement is under a framework agreement | Schema doesn't cover -- flagging for review. |
| Sustainability/innovation criteria | Whether the procurement includes environmental, social, or innovation requirements | Schema doesn't cover -- flagging for review. Upphandlingsmyndigheten tracks these as statistical indicators. |
| Contract duration | Start/end dates or duration period for the contract | Schema doesn't cover -- flagging for review. |
| Statistikdatabasen aggregates | Pre-computed statistics by year, CPV group, procedure type, region, organization type | Not individual notice data. Only useful as a supplementary/validation dataset, not as a primary data source. |

### Code Normalization

The Swedish UBL reporting format (UFS 2023:1 / UFS 2023:2) follows eForms business terms and codelists. Since the specification explicitly states that it follows the eForms Schemas Usage Specification with national extensions, most code values should already be in eForms format. However, the following normalization considerations apply:

#### Authority Type Codes (BT-11 buyer-legal-type)

The reporting format uses eForms `buyer-legal-type` codes. No mapping needed if data comes from the UBL reporting format. Expected codes:

| eForms Code | Description |
|---|---|
| `body-public` | Body governed by public law |
| `cent-gov` | Central government authority |
| `ra-aut` | Regional authority |
| `rl-aut` | Regional or local authority |
| `pub-undert` | Public undertaking |
| `grp-p-aut` | Group of public authorities |
| `org-sub` | Organisation awarding a subsidised contract |

Swedish-specific codes may exist for below-threshold national procurement types. The exact additional codes are not documented in publicly available sources and would need verification against the full UFS 2023:1/2023:2 Annex A (available by request from statistik@uhmynd.se).

#### Contract Nature Codes (BT-23 contract-nature)

Standard eForms codes. No mapping needed:

| eForms Code | Description |
|---|---|
| `works` | Works |
| `supplies` | Supplies |
| `services` | Services |

#### Procedure Type Codes (BT-105 procurement-procedure-type)

Standard eForms codes for directive-governed procurements. No mapping needed for these:

| eForms Code | Description |
|---|---|
| `open` | Open procedure |
| `restricted` | Restricted procedure |
| `neg-w-call` | Negotiated with prior call for competition |
| `neg-wo-call` | Negotiated without prior publication |
| `comp-dial` | Competitive dialogue |
| `innovation` | Innovation partnership |

For **below-threshold national procurements**, the Swedish reporting format adds additional procedure type codes not in the standard eForms codelist. These national codes are defined in UFS 2023:1/2023:2 but the exact values are not available in public documentation. They would need mapping to our schema's procedure type codes (or stored as-is with a description). Verification against the technical specification is required.

### Implementation Recommendations

1. **Do NOT implement now.** There is no viable data source for individual notice-level award data. The Statistikdatabasen provides only aggregate statistics, and the UBL reporting API is write-only (submission by registered platforms to Upphandlingsmyndigheten). Implementing a scraper would yield no usable data.

2. **Monitor for API launch.** Upphandlingsmyndigheten has stated that a public retrieval API is planned. When launched, it will likely expose data in the same UBL 2.3 format as the reporting specification (Annex 3). The field mappings above would then apply directly. Check https://www.upphandlingsmyndigheten.se/om-oss/upphandlingsmyndighetens-forfattningssamling/api/ periodically.

3. **Alternative: scrape registered annonsdatabaser.** Individual notice data exists on commercial platforms (e-Avrop, Mercell TendSign, etc.). These would require reverse-engineering web interfaces and likely violate terms of service. Not recommended.

4. **Alternative: request data directly.** Contact Upphandlingsmyndigheten (statistik@uhmynd.se or oppnadata@uhmynd.se) to request access to the underlying notice-level data from their collection database. They may provide bulk exports or early API access.

5. **If data becomes available**, the parser should be straightforward since the reporting format is UBL 2.3 with eForms business terms. Our existing `eforms_ubl.py` parser handles eForms UBL XML and could potentially be adapted, though the Swedish national extensions (UBL Extensions for `SwedishProcurementID`, `RegisteredDatabaseID`, tender statistics) would need custom handling. Currency will typically be `SEK` rather than `EUR`.
