# Estonia (EE)

**Feasibility: Tier 2**

## Portal

- **Name**: Riigihangete Register (Public Procurement Register)
- **URL**: https://riigihanked.riik.ee
- **Managed by**: Ministry of Finance
- **Open data**: Available on Estonian Open Data Portal

## Data Access

- **Method**: REST API with monthly XML exports
- **API Base URL**: `https://riigihanked.riik.ee/rhr/api/public/v1/opendata/`
- **Award notices endpoint**: `notice_award/{year}/month/{month}/xml`
- **All notices endpoint**: `notice/{year}/month/{month}/xml`
- **Format**: XML (eForms UBL for 2023+, TED v2 R2.0.9 for 2018-2022, no data before 2018)
- **Auth**: Open (no authentication required)
- **OCDS**: No
- **Wrapper element**: `<OPEN-DATA>` contains multiple `<ContractAwardNotice>` elements

## Coverage

All public procurement (mandatory publication).

## Language

Estonian

## Notes

- First e-procurement system in the Baltic states
- General open data portal API available; procurement-specific API docs unclear
- OCP entry: https://data.open-contracting.org/en/publication/50
- Since 2024-01-01 administered by Riigi Tugiteenuste Keskus (RTK)
- Open data portal listing: https://andmed.eesti.ee/datasets/riigihangete-register

## Schema Mapping

### Key Finding: eForms UBL Format

The Estonian portal's `notice_award` API returns XML in **eForms UBL ContractAwardNotice format** -- the same format already parsed by `portals/ted/eforms_ubl.py`. This means the existing eForms parser can be reused with minimal adaptation rather than writing a parser from scratch.

**Two XML format eras:**

| Period | Format | Root Element | Notes |
|--------|--------|-------------|-------|
| 2018-2022 | TED v2 R2.0.9 | `<TED_ESENDERS>` containing `<F03_2014>` | Same as `ted_v2.py` handles |
| 2023+ | eForms UBL | `<ContractAwardNotice>` | Same as `eforms_ubl.py` handles |
| Pre-2018 | N/A | API returns `OPEN_DATA_XML_NOT_FOUND` | No data available |

**Structural difference from TED:** The API returns a single XML document with a `<OPEN-DATA>` wrapper element containing **multiple** `<ContractAwardNotice>` (or `<TED_ESENDERS>`) elements concatenated together, one per notice. The TED portal provides one XML file per notice. The parser must split on the wrapper element.

### DocumentModel

| Schema Field | Portal Field/Path (eForms 2023+) | Portal Field/Path (TED v2 2018-2022) | Notes |
|---|---|---|---|
| `doc_id` | `cbc:ID[@schemeName='notice-id']` | `SENDER/IDENTIFICATION/NO_DOC_EXT` | UUID in eForms (e.g. `07c5b599-39a3-437a-a690-98efa0169959`), year-prefixed ID in TED v2 (e.g. `2020-084267`). Prefix with `EE-` to avoid collisions with TED doc_ids. |
| `edition` | Derive from `cbc:IssueDate` | Derive from `cbc:IssueDate` | No OJ edition concept; synthesize from publication date as `{year}{day_of_year:03d}` |
| `version` | `cbc:CustomizationID` | `TED_ESENDERS/@VERSION` | e.g. `eforms-sdk-1.3`, `eforms-sdk-1.9`, `R2.0.9.S03` |
| `reception_id` | None | None | Not available from this portal |
| `official_journal_ref` | None | None | These are national notices, not published in the Official Journal. Set to `None`. |
| `publication_date` | `cbc:IssueDate` | Derive from `NO_DOC_EXT` or request month/year | eForms dates include timezone: `2024-06-03+03:00`. TED v2 notices lack a direct publication date; use the API request year/month as approximation. |
| `dispatch_date` | `efbc:TransmissionDate` | Not directly available | eForms has explicit transmission date in extensions |
| `source_country` | `cac:Country/cbc:IdentificationCode` | `COUNTRY/@VALUE` | **CRITICAL**: eForms uses ISO 3166-1 alpha-3 (`EST`), TED v2 uses alpha-2 (`EE`). Must normalize to alpha-2 `EE` for our database. |
| `contact_point` | None | None | Not populated in observed samples (empty `<cac:Contact>` elements) |
| `phone` | `efac:Company/cac:Contact/cbc:Telephone` | `ADDRESS_CONTRACTING_BODY/PHONE` (if present) | Empty in most observed samples |
| `email` | `efac:Company/cac:Contact/cbc:ElectronicMail` | `ADDRESS_CONTRACTING_BODY/E_MAIL` (if present) | Empty in most observed samples |
| `url_general` | `efac:Company/cbc:WebsiteURI` | `ADDRESS_CONTRACTING_BODY/URL_GENERAL` | Available when buyer provides website |
| `url_buyer` | `cac:ContractingParty/cbc:BuyerProfileURI` | `ADDRESS_CONTRACTING_BODY/URL_BUYER` (if present) | Same URL as `url_general` in many cases |

### ContractingBodyModel

| Schema Field | Portal Field/Path (eForms 2023+) | Portal Field/Path (TED v2 2018-2022) | Notes |
|---|---|---|---|
| `official_name` | `efac:Company/cac:PartyName/cbc:Name` | `CONTRACTING_BODY/ADDRESS_CONTRACTING_BODY/OFFICIALNAME` | In Estonian. Identified via `cac:ContractingParty/cac:Party/cac:PartyIdentification/cbc:ID` -> org lookup. |
| `address` | `efac:Company/cac:PostalAddress/cbc:StreetName` | `ADDRESS_CONTRACTING_BODY/ADDRESS` | |
| `town` | `efac:Company/cac:PostalAddress/cbc:CityName` | `ADDRESS_CONTRACTING_BODY/TOWN` | Note: some values have leading spaces (e.g. ` Tallinn`) -- trim needed |
| `postal_code` | `efac:Company/cac:PostalAddress/cbc:PostalZone` | `ADDRESS_CONTRACTING_BODY/POSTAL_CODE` | |
| `country_code` | `efac:Company/cac:PostalAddress/cac:Country/cbc:IdentificationCode` | `ADDRESS_CONTRACTING_BODY/COUNTRY/@VALUE` | **Alpha-3 in eForms (`EST`), alpha-2 in TED v2 (`EE`)**. Normalize to alpha-2. |
| `nuts_code` | `efac:Company/cac:PostalAddress/cbc:CountrySubentityCode` | `ADDRESS_CONTRACTING_BODY/ns2:NUTS/@CODE` | NUTS codes observed: `EE` (country level only, no region breakdown). Often absent in eForms. |
| `authority_type` | `cac:ContractingPartyType/cbc:PartyTypeCode[@listName='buyer-legal-type']` | `CONTRACTING_BODY/CA_TYPE/@VALUE` | eForms uses eForms codes directly (e.g. `body-pl`, `la`). TED v2 uses TED codes (e.g. `MINISTRY`) needing mapping. See Code Normalization below. |
| `main_activity_code` | `cac:ContractingActivity/cbc:ActivityTypeCode[@listName='authority-activity']` | `CONTRACTING_BODY/CA_ACTIVITY/@VALUE` | eForms codes: `education`, `gen-pub`, `econ-aff`. TED v2 codes: `ECONOMIC_AND_FINANCIAL_AFFAIRS` etc. |

### ContractModel

| Schema Field | Portal Field/Path (eForms 2023+) | Portal Field/Path (TED v2 2018-2022) | Notes |
|---|---|---|---|
| `title` | `cac:ProcurementProject/cbc:Name` | `OBJECT_CONTRACT/TITLE/P` | In Estonian |
| `short_description` | `cac:ProcurementProject/cbc:Description` | `OBJECT_CONTRACT/SHORT_DESCR/P` | Multi-paragraph in TED v2 (multiple `<P>` elements). In Estonian. |
| `main_cpv_code` | `cac:ProcurementProject/cac:MainCommodityClassification/cbc:ItemClassificationCode` | `OBJECT_CONTRACT/CPV_MAIN/CPV_CODE/@CODE` | Standard CPV codes (e.g. `35613000`, `73110000`) |
| `cpv_codes` | Main + `cac:AdditionalCommodityClassification/cbc:ItemClassificationCode` | Main + `OBJECT_DESCR/CPV_ADDITIONAL/CPV_CODE/@CODE` | No descriptions included in either format |
| `nuts_code` | `cac:RealizedLocation/cac:Address/cac:Country/cbc:IdentificationCode` | `OBJECT_DESCR/ns2:NUTS/@CODE` | eForms often only has country code, not NUTS. TED v2 has `EE` as NUTS. |
| `contract_nature_code` | `cac:ProcurementProject/cbc:ProcurementTypeCode[@listName='contract-nature']` | `OBJECT_CONTRACT/TYPE_CONTRACT/@CTYPE` | eForms: `supplies`, `services`, `works` (already eForms codes). TED v2: `SUPPLIES`, `SERVICES`, `WORKS` (need lowercase). |
| `procedure_type` | `cac:TenderingProcess/cbc:ProcedureCode[@listName='procurement-procedure-type']` | `PROCEDURE` element type | eForms codes directly: `open`, `neg-wo-call`, `oth-single`. TED v2 needs mapping. See Code Normalization. |
| `accelerated` | `cac:TenderingProcess/cac:ProcessJustification/cbc:ProcessReasonCode[@listName='accelerated-procedure']` | `PROCEDURE/ACCELERATED_PROC` | eForms: check for `true` value. TED v2: presence of element. |

### AwardModel

| Schema Field | Portal Field/Path (eForms 2023+) | Portal Field/Path (TED v2 2018-2022) | Notes |
|---|---|---|---|
| `award_title` | `efac:SettledContract/cbc:Title` | `AWARD_CONTRACT/TITLE/P` (if present) | eForms example: `Hankeleping (Threod Systems OU) 272794` |
| `contract_number` | `efac:SettledContract/efac:ContractReference/cbc:ID` | `AWARD_CONTRACT/CONTRACT_NO` | e.g. `4.1-11/1777-1` |
| `tenders_received` | `efac:LotResult/efac:ReceivedSubmissionsStatistics` where `efbc:StatisticsCode='tenders'` -> `efbc:StatisticsNumeric` | `AWARD_CONTRACT/AWARDED_CONTRACT/NB_TENDERS_RECEIVED` | eForms has multiple statistics types (`tenders`, `t-sme`, `t-esubm`); use the one with code `tenders`. |
| `awarded_value` | `efac:LotTender/cac:LegalMonetaryTotal/cbc:PayableAmount` | `AWARD_CONTRACT/AWARDED_CONTRACT/VAL_TOTAL` or `OBJECT_CONTRACT/VAL_TOTAL` | Float value. Currency always EUR for Estonian domestic procurement. |
| `awarded_value_currency` | `cbc:PayableAmount/@currencyID` | `VAL_TOTAL/@CURRENCY` | Always `EUR` in observed samples (Estonia uses the Euro). |
| `contractors` | See ContractorModel below | See ContractorModel below | |

### ContractorModel

| Schema Field | Portal Field/Path (eForms 2023+) | Portal Field/Path (TED v2 2018-2022) | Notes |
|---|---|---|---|
| `official_name` | `efac:Company/cac:PartyName/cbc:Name` (matched via `efac:TenderingParty/efac:Tenderer/cbc:ID`) | `AWARD_CONTRACT/AWARDED_CONTRACT/CONTRACTORS/CONTRACTOR/ADDRESS_CONTRACTOR/OFFICIALNAME` | Resolved through org ID indirection in eForms |
| `address` | `efac:Company/cac:PostalAddress/cbc:StreetName` | `ADDRESS_CONTRACTOR/ADDRESS` | |
| `town` | `efac:Company/cac:PostalAddress/cbc:CityName` | `ADDRESS_CONTRACTOR/TOWN` | Leading spaces observed (e.g. ` Viimsi vald`) -- trim needed |
| `postal_code` | `efac:Company/cac:PostalAddress/cbc:PostalZone` | `ADDRESS_CONTRACTOR/POSTAL_CODE` | |
| `country_code` | `efac:Company/cac:PostalAddress/cac:Country/cbc:IdentificationCode` | `ADDRESS_CONTRACTOR/COUNTRY/@VALUE` | Alpha-3 (`EST`) in eForms, alpha-2 (`EE`) in TED v2. Normalize to alpha-2. |
| `nuts_code` | `efac:Company/cac:PostalAddress/cbc:CountrySubentityCode` | `ADDRESS_CONTRACTOR/ns2:NUTS/@CODE` | Rarely populated |

### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `cbc:ItemClassificationCode` (eForms) / `CPV_CODE/@CODE` (TED v2) | Standard 8-digit CPV codes |
| `description` | None | Not provided in the XML. Set to `None`. |

### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `cbc:ProcedureCode` (eForms) / derived from `PROCEDURE` child elements (TED v2) | eForms codes used directly. TED v2 codes need mapping. |
| `description` | `cac:TenderingProcess/cbc:Description` (eForms) / None (TED v2) | eForms has Estonian-language descriptions (e.g. `Avatud hankemenetlus`, `Valjakuulutamiseta labirakimistega hankemenetlus`). Not useful for schema (Estonian only). |

### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `cbc:PartyTypeCode[@listName='buyer-legal-type']` (eForms) / `CA_TYPE/@VALUE` (TED v2) | eForms codes used directly. TED v2 codes need mapping. |
| `description` | None | Not provided. Set to `None`. |

### Unmappable Schema Fields

These fields will always be `None` for Estonian portal data:

| Field | Model | Reason |
|---|---|---|
| `reception_id` | DocumentModel | No reception concept in national portal |
| `official_journal_ref` | DocumentModel | National notices, not published in EU Official Journal |
| `contact_point` | DocumentModel | Observed as empty in all samples |

### Extra Portal Fields Not in Schema

The following fields are available in the Estonian data but not captured by the current schema. Flagging for review:

| Portal Field | Path | Description |
|---|---|---|
| **National ID (registry code)** | `efac:Company/cac:PartyLegalEntity/cbc:CompanyID` / `NATIONALID` | Estonian business registry code (e.g. `70004465`, `12323903`). Highly valuable for entity resolution. |
| **Procurement reference number** | `cac:ProcurementProject/cbc:ID` / `OBJECT_CONTRACT/REFERENCE_NUMBER` | National procurement number (e.g. `272794`). Useful for cross-referencing with the portal UI. |
| **Contract folder ID** | `cbc:ContractFolderID` | UUID grouping related notices |
| **Notice sub-type code** | `efac:NoticeSubType/cbc:SubTypeCode` | Numeric code (e.g. `29` = contract award notice) |
| **Regulatory domain** | `cbc:RegulatoryDomain` | Legal basis (e.g. `32014L0024` = Directive 2014/24/EU) |
| **EU funding indicator** | `cbc:FundingProgramCode[@listName='eu-funded']` | `eu-funds` or `no-eu-funds` |
| **Funding project reference** | `efac:Funding/cbc:Description` | e.g. `Projekti nr. 20.2.02.22-0079` |
| **Framework agreement indicator** | `efbc:ContractFrameworkIndicator` | `true`/`false` |
| **SME tender count** | `efac:ReceivedSubmissionsStatistics` where code=`t-sme` | Number of tenders from SMEs |
| **E-submission count** | `efac:ReceivedSubmissionsStatistics` where code=`t-esubm` | Number of electronically submitted tenders |
| **Subcontracting indicator** | `efac:SubcontractingTerm/efbc:TermCode` | `yes`/`no` |
| **Award criteria** | `cac:AwardingTerms/cac:AwardingCriterion/cac:SubordinateAwardingCriterion` | Type (`price`/`quality`) and weights |
| **Contract duration** | `cac:PlannedPeriod/cbc:DurationMeasure` | Duration with unit (e.g. `12 MONTH`) |
| **Direct award justification** | `cac:ProcessJustification/cbc:ProcessReasonCode` | Reason code + free-text reason for negotiated procedures |
| **Award date** | `cac:TenderResult/cbc:AwardDate` | Note: some observed as placeholder `2000-01-01` |
| **Contract issue date** | `efac:SettledContract/cbc:IssueDate` | Date the contract was signed |
| **Additional contracting bodies** | `ADDRESS_CONTRACTING_BODY_ADDITIONAL` (TED v2) | Joint procurement participants |
| **Accessibility justification** | `cac:ProcurementAdditionalType` where `listName='accessibility'` | |

### Code Normalization

#### Authority Types (buyer-legal-type)

eForms data (2023+) already uses eForms codes. TED v2 data (2018-2022) uses TED codes that need mapping:

| TED v2 Code | eForms Code | Description |
|---|---|---|
| `MINISTRY` | `cga` | Central government authority |
| `NATIONAL_AGENCY` | `cga` | Central government authority |
| `REGIONAL_AUTHORITY` | `ra` | Regional authority |
| `REGIONAL_AGENCY` | `ra` | Regional authority |
| `BODY_PUBLIC` | `body-pl` | Body governed by public law |
| `EU_INSTITUTION` | `eu-ins-bod-ag` | EU institution |
| `UTILITIES` | `pub-undert` | Public undertaking |
| `OTHER` | `org-sub` | Other |

Observed eForms codes in Estonian data: `body-pl`, `la` (local authority).

#### Procedure Types (procurement-procedure-type)

eForms data already uses eForms codes. TED v2 data uses TED element names that need mapping (handled by existing `_normalize_procedure_type()` in `ted_v2.py`):

| TED v2 Element | eForms Code |
|---|---|
| `PT_OPEN` | `open` |
| `PT_RESTRICTED` | `restricted` |
| `PT_COMPETITIVE_NEGOTIATION` | `neg-w-call` |
| `PT_NEGOTIATED_WITHOUT_PUBLICATION` | `neg-wo-call` |
| `PT_COMPETITIVE_DIALOGUE` | `comp-dial` |
| `PT_INNOVATION_PARTNERSHIP` | `innovation` |

Observed eForms codes in Estonian data: `open`, `neg-wo-call`, `oth-single`.

Note: `oth-single` (other single-stage procedure) appears in Estonian data for below-threshold "simplified" procedures. This is a valid eForms code.

#### Contract Nature Codes

Both formats use recognizable codes that map to eForms:

| TED v2 `@CTYPE` | eForms `contract-nature` | Description |
|---|---|---|
| `WORKS` | `works` | Works contracts |
| `SUPPLIES` | `supplies` | Supply contracts |
| `SERVICES` | `services` | Service contracts |

Normalization: lowercase the TED v2 value (handled by existing `_normalize_contract_nature_code()`).

#### Country Code Normalization

**This is the most important normalization concern.** The eForms data uses ISO 3166-1 **alpha-3** country codes (e.g. `EST`, not `EE`), while the database `countries` table uses alpha-2 codes. A mapping table or library (e.g. `pycountry`) is needed to convert alpha-3 to alpha-2. The TED v2 data already uses alpha-2 codes.

### Data Format Notes

1. **Format**: XML (not CSV as originally documented). The API serves XML directly over HTTPS.

2. **Wrapper structure**: Each monthly response is a single XML document with `<OPEN-DATA>` as the root element. Inside it, multiple `<ContractAwardNotice>` (eForms) or `<TED_ESENDERS>` (TED v2) elements are concatenated as siblings. The parser must iterate over these children.

3. **Two parsers needed**: The data has two format eras requiring different parsers, but both are already implemented in `ted_v2.py` and `eforms_ubl.py`. The Estonian portal module should:
   - Download monthly XML bundles via the API
   - Split the `<OPEN-DATA>` wrapper into individual notice elements
   - Detect format (eForms vs TED v2) per notice element
   - Delegate to the appropriate existing parser (with adaptations)

4. **Parser adaptations needed**:
   - Existing parsers expect files on disk (`Path` arguments). Adapt to accept `lxml.etree._Element` directly or write each notice to a temp file.
   - The `doc_id` extraction in `eforms_ubl.py` currently derives from the filename. For the Estonian portal, extract from `cbc:ID[@schemeName='notice-id']` instead, prefixed with `EE-`.
   - Country code alpha-3 to alpha-2 conversion for eForms data.
   - Whitespace trimming on town/city names (leading spaces observed).

5. **API pagination**: Data is organized by year and month. No pagination within a month -- the entire month's data is returned in a single response. Iterate `year` x `month` (1-12).

6. **Data volume**: Each monthly XML response appears to contain dozens to hundreds of notices. No rate limiting was observed during testing.

7. **Mixed notice types in TED v2 era**: The 2018-2022 data may include `F20_2014` (contract modification notices) alongside `F03_2014` (contract award notices). Filter by form type.

8. **Language**: All text content is in Estonian (`languageID="EST"`). No multilingual variants.

9. **Currency**: Always EUR (Estonia adopted the Euro in 2011).

10. **Date formats**: eForms dates include timezone offset (e.g. `2024-06-03+03:00` for Estonian summer time, `2023-12-30+02:00` for winter time). The existing `_parse_date_eforms()` handles this correctly.
