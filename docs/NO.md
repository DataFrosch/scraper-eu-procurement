# Norway (NO)

**Feasibility: Tier 1**

## Portal

- **Name**: Doffin
- **URL**: https://doffin.no/
- **API (dev)**: https://dof-notices-dev-api.developer.azure-api.net/
- **API (prod)**: https://dof-notices-prod-api.developer.azure-api.net/
- **Open data**: https://data.norge.no/en/datasets/a77b0408-85f9-3e12-8a66-8d500b492e9d/kunngjoringer-av-offentlig-anskaffelser
- **eForms SDK Norway**: https://github.com/anskaffelser/eforms-sdk-nor
- **Managed by**: Norwegian Digitalisation Agency (DFO)

## Data Access

- **Method**: REST API (Notices API + Public API)
- **Format**: JSON, XML
- **Auth**: Free API key (register on Azure APIM portal for each environment)
- **OCDS**: No

## Coverage

All public procurement tenders, bids, and awards.

## Language

Norwegian

## Notes

- Two independent environments (dev/prod); each requires separate registration
- Doffin is implementing eForms via Norwegian SDK
- API mimics TED API structure
- Well-structured API on Azure APIM, eForms-compatible

## Schema Mapping

### Data Access Strategy

Doffin provides two distinct APIs:

1. **Notices API** (`dof-notices-prod-api`): Used to submit, validate, and translate notices. Mimics the TED API. Requires subscription approval (contact `ingunn.ostrem@dfo.no`). Includes:
   - `GET doffin/notices/download/{when}` — returns all notices published on a given date as a **zip archive** containing eForms XML files
   - `GET doffin/notices/monthly/{when}` — monthly zip archive (**restricted to DFO internal use**)
2. **Public API v2** (`betaapi.doffin.no/public/v2`): Search and retrieve individual notices. Returns JSON metadata and full notice XML. No subscription approval needed (free API key only).

**Recommended approach**: Use the Notices API `download/{when}` endpoint to fetch daily zip archives of eForms XML, analogous to the TED daily package download. This aligns with the existing TED portal pattern (year-based iteration, archive extraction, per-file XML parsing).

**Alternative approach**: Use the Public API v2 to search for notices by type and date range, then fetch individual notice XML. Better for selective retrieval but slower for bulk import.

### Data Format

- **Primary format**: eForms UBL XML (`ContractAwardNotice` root element for award notices)
- **Doffin is "native" eForms** — the new Doffin (launched October 2023, replacing `classic.doffin.no`) stores and serves notices in eForms format natively
- **Norwegian eForms SDK** (`eforms-sdk-nor`) adds Norwegian translations and national validation rules on top of the standard EU eForms SDK
- **Key implication**: The existing `eforms_ubl.py` parser should handle Doffin XML with minimal or no modifications, since Doffin produces standard eForms UBL XML. Norwegian national extensions (via `eforms-sdk-nor`) add validation rules and translations but do not change the XML structure itself.

### Parsing Considerations

- The zip archives from `download/{when}` contain individual XML files, one per notice (same pattern as TED `.tar.gz` archives)
- Filter for `<ContractAwardNotice` root element to select award notices only, exactly as `try_parse_award()` already does
- Norwegian notices will use Norwegian-language text for titles, descriptions, and organization names
- The `{when}` parameter format for the download endpoint is not documented publicly; likely a date string (YYYY-MM-DD or similar) — **must be verified by calling the API or checking the Azure APIM portal swagger definition**
- Currency will typically be `NOK` (Norwegian Krone) rather than EUR
- NUTS codes will use the `NO` prefix (e.g., `NO081` for Telemark)
- `source_country` will always be `NO`

### Field Mapping: DocumentModel

| Schema Field | Portal Field/Path (eForms UBL XPath) | Notes |
|---|---|---|
| `doc_id` | Filename stem (e.g., `00654321_2024.xml` -> `00654321-2024`) | Same convention as TED eForms; normalize `_` to `-` |
| `edition` | Derived from `publication_date` as `{year}{day_of_year:03d}` | Synthetic, same as TED eForms parser |
| `version` | Hardcode `"eForms-UBL"` | Or use a Doffin-specific marker like `"Doffin-eForms"` to distinguish from TED-sourced eForms |
| `reception_id` | None | Doffin does not use TED reception IDs |
| `official_journal_ref` | Synthetic from `publication_date` + `doc_id` | Doffin notices are not published in OJ S; could use `"DOFFIN-{doc_id}"` or leave `None` |
| `publication_date` | `//efac:Publication/efbc:PublicationDate` or `//cbc:IssueDate` | Standard eForms path; format `YYYY-MM-DD+HH:MM` or `YYYY-MM-DDZ` |
| `dispatch_date` | `//cbc:IssueDate` | Same as publication_date in practice for eForms |
| `source_country` | `//cac:Country/cbc:IdentificationCode` | Will be `NO` for all Doffin notices |
| `contact_point` | `//efac:Company//cac:Contact/cbc:Name` | May not be populated in Norwegian notices |
| `phone` | `//efac:Company//cac:Contact/cbc:Telephone` | Standard eForms path |
| `email` | `//efac:Company//cac:Contact/cbc:ElectronicMail` | Standard eForms path |
| `url_general` | `//efac:Company//cbc:WebsiteURI` | Standard eForms path |
| `url_buyer` | None | Not a standard eForms field; likely `None` |

### Field Mapping: ContractingBodyModel

| Schema Field | Portal Field/Path (eForms UBL XPath) | Notes |
|---|---|---|
| `official_name` | `//efac:Company//cac:PartyName/cbc:Name` | Matched via `cac:ContractingParty` org ID lookup; Norwegian-language names |
| `address` | `//efac:Company//cac:PostalAddress/cbc:StreetName` | Standard eForms path |
| `town` | `//efac:Company//cac:PostalAddress/cbc:CityName` | Standard eForms path |
| `postal_code` | `//efac:Company//cac:PostalAddress/cbc:PostalZone` | Norwegian postal codes (4 digits) |
| `country_code` | `//efac:Company//cac:PostalAddress/cac:Country/cbc:IdentificationCode` | Will be `NO` |
| `nuts_code` | `//efac:Company//cac:PostalAddress/cbc:CountrySubentityCode` | Norwegian NUTS codes (e.g., `NO081`) |
| `authority_type` | `//cac:ContractingParty/cbc:ContractingPartyTypeCode` or organization-level BT-11 | See code normalization section below |
| `main_activity_code` | `//cac:ContractingActivity/cbc:ActivityTypeCode` | Standard eForms BT-10; may use eForms codelist values directly |

### Field Mapping: ContractModel

| Schema Field | Portal Field/Path (eForms UBL XPath) | Notes |
|---|---|---|
| `title` | `//efac:SettledContract/cbc:Title` | Norwegian language |
| `short_description` | `//efac:SettledContract/cbc:Title` | Same as title in eForms (no separate short description) |
| `main_cpv_code` | `./cac:ProcurementProject/cac:MainCommodityClassification/cbc:ItemClassificationCode` | Direct child of root to avoid lot-level duplicates |
| `cpv_codes` | Main + `./cac:ProcurementProject/cac:AdditionalCommodityClassification/cbc:ItemClassificationCode` | Standard eForms paths |
| `nuts_code` | `//cac:ProcurementProjectLot//cac:RealizedLocation//cbc:CountrySubentityCode` | Falls back to project-level NUTS |
| `contract_nature_code` | `//cac:ProcurementProject/cbc:ProcurementTypeCode` | Already normalized in `_normalize_contract_nature_code()`; eForms uses standard codes: `works`, `supplies`, `services` |
| `procedure_type` | `//cac:TenderingProcess/cbc:ProcedureCode` | Already normalized in `_normalize_procedure_type()`; see code normalization below |
| `accelerated` | `//cac:TenderingProcess/cac:ProcessJustification/cbc:ProcessReasonCode[@listName='accelerated-procedure']` | eForms BT-106; value `"true"` if accelerated |

### Field Mapping: AwardModel

| Schema Field | Portal Field/Path (eForms UBL XPath) | Notes |
|---|---|---|
| `award_title` | `//efac:SettledContract/cbc:Title` | Same as contract title in eForms |
| `contract_number` | `//efac:SettledContract/efac:ContractReference/cbc:ID` | Standard eForms path |
| `tenders_received` | `//efac:LotResult/efbc:TenderReceivedNumber` or `//efac:LotResult//cbc:StatisticsNumericValue` | **Not extracted by current `eforms_ubl.py`** — would need to add this extraction. The current TED eForms parser does not populate `tenders_received`; this is a gap in the existing parser too. |
| `awarded_value` | `//efac:LotTender/cac:LegalMonetaryTotal/cbc:PayableAmount` | Standard eForms path; value as float |
| `awarded_value_currency` | `//efac:LotTender/cac:LegalMonetaryTotal/cbc:PayableAmount/@currencyID` | Typically `NOK` for Norwegian notices |
| `contractors` | See ContractorModel mapping below | Resolved via org ID cross-reference |

### Field Mapping: ContractorModel

| Schema Field | Portal Field/Path (eForms UBL XPath) | Notes |
|---|---|---|
| `official_name` | `//efac:Company//cac:PartyName/cbc:Name` | Matched via winning tenderer org ID (`//efac:TenderingParty//efac:Tenderer/cbc:ID`) |
| `address` | `//efac:Company//cac:PostalAddress/cbc:StreetName` | Standard eForms path |
| `town` | `//efac:Company//cac:PostalAddress/cbc:CityName` | Standard eForms path |
| `postal_code` | `//efac:Company//cac:PostalAddress/cbc:PostalZone` | Norwegian postal codes (4 digits) |
| `country_code` | `//efac:Company//cac:PostalAddress/cac:Country/cbc:IdentificationCode` | May be `NO` or foreign country code |
| `nuts_code` | `//efac:Company//cac:PostalAddress/cbc:CountrySubentityCode` | Norwegian NUTS codes |

### Field Mapping: CpvCodeEntry

| Schema Field | Portal Field/Path (eForms UBL XPath) | Notes |
|---|---|---|
| `code` | `//cac:MainCommodityClassification/cbc:ItemClassificationCode` and `//cac:AdditionalCommodityClassification/cbc:ItemClassificationCode` | CPV codes are EU-standard; identical in Doffin |
| `description` | None | eForms does not include CPV descriptions in the XML; looked up from CPV reference table |

### Field Mapping: ProcedureTypeEntry

| Schema Field | Portal Field/Path (eForms UBL XPath) | Notes |
|---|---|---|
| `code` | `//cac:TenderingProcess/cbc:ProcedureCode` | Already uses eForms codelist values; see code normalization below |
| `description` | None | Not in XML; can be looked up from eForms codelist |

### Unmappable Schema Fields

These fields have no direct equivalent in Doffin eForms data and will be `None`:

| Schema Field | Model | Reason |
|---|---|---|
| `reception_id` | DocumentModel | TED-specific concept; Doffin has its own internal notice IDs |
| `url_buyer` | DocumentModel | Not a standard eForms field |
| `contact_point` | DocumentModel | Rarely populated in eForms notices generally |
| `tenders_received` | AwardModel | **Available in eForms** (`efbc:TenderReceivedNumber`) but **not currently extracted** by the existing `eforms_ubl.py` parser. Should be added during implementation. |

Note: `tenders_received` is technically available in the eForms XML but is listed here because the current parser does not extract it. Implementing the Doffin portal would be a good opportunity to add this extraction to the shared eForms parser.

### Extra Portal Fields (Not in Current Schema)

The following fields are available in Doffin/eForms data but not covered by the current schema. Flagging for review:

| Portal Field | eForms BT | Description | Notes |
|---|---|---|---|
| Organization ID (org number) | BT-501 | Norwegian organization number (e.g., `971526920`) | Schema doesn't cover — flagging for review. Very useful for entity deduplication (more reliable than name matching). |
| Lot information | BT-137 etc. | Individual lot details, values, and results | Schema doesn't cover — flagging for review. Current schema treats the entire notice as one contract; eForms has detailed per-lot data. |
| Framework agreement indicator | BT-768 | Whether the contract is a framework agreement | Schema doesn't cover — flagging for review. |
| Electronic auction used | BT-767 | Whether an electronic auction was used | Schema doesn't cover — flagging for review. |
| GPA (WTO agreement) coverage | BT-115 | Whether covered by WTO Government Procurement Agreement | Schema doesn't cover — flagging for review. |
| Award criteria | BT-539, BT-540, BT-541 | Criteria type, description, and weight | Schema doesn't cover — flagging for review. |
| Contract conclusion date | BT-145 | Date the contract was concluded | Schema doesn't cover — flagging for review. |
| Estimated contract value | BT-27 | Estimated value before award | Schema doesn't cover — flagging for review. |
| Subcontracting information | BT-773, BT-730 | Subcontracting value and description | Schema doesn't cover — flagging for review. |
| EU funding indicator | BT-60 | Whether EU funds are used | Schema doesn't cover — flagging for review. |
| National below-threshold notices | N/A | Notices below EU thresholds (Doffin-only, never appear in TED) | Schema doesn't cover — flagging for review. This is the primary value-add of the Doffin portal. |

### Code Normalization

#### Procedure Types

Doffin uses native eForms, so procedure type codes should already be in eForms format. The existing `_normalize_procedure_type()` function in `ted_v2.py` (re-exported and used by `eforms_ubl.py`) handles eForms codes. Expected codes from Doffin:

| eForms Code | Description |
|---|---|
| `open` | Open procedure |
| `restricted` | Restricted procedure |
| `neg-w-call` | Negotiated procedure with prior call for competition |
| `neg-wo-call` | Negotiated procedure without prior call for competition |
| `comp-dial` | Competitive dialogue |
| `innovation` | Innovation partnership |
| `comp-neg` | Competitive procedure with negotiation |

Norway may also use national procedure types for below-threshold notices. The `eforms-sdk-nor` may define additional codes — **must be verified against the SDK's codelists**. If national codes are encountered, they will need mapping to the nearest eForms equivalent, or the codelist will need to be extended.

#### Authority Types

eForms authority type codes (BT-11, `buyer-legal-type` codelist) are used directly. Expected codes:

| eForms Code | Description |
|---|---|
| `cga` | Central government authority |
| `ra` | Regional authority |
| `la` | Local authority |
| `body-pl` | Body governed by public law |
| `eu-ins-bod-ag` | EU institution, body or agency |
| `org-sub` | Organisation sub-type |
| `pub-undert` | Public undertaking |
| `grp-p-aut` | Group of public authorities |
| `int-org` | International organisation |

Since Doffin uses native eForms, no mapping should be needed — codes should arrive in eForms format already. **Verify against `eforms-sdk-nor` codelists** for any Norwegian national extensions.

#### Contract Nature Codes

eForms uses standard `ProcurementTypeCode` values. The existing `_normalize_contract_nature_code()` function handles these. Expected values:

| eForms Code | Description |
|---|---|
| `works` | Works |
| `supplies` | Supplies |
| `services` | Services |

No Norwegian-specific mapping expected for these.

### Implementation Notes

1. **Reuse `eforms_ubl.py`**: Since Doffin produces standard eForms UBL XML, the existing parser in `awards/portals/ted/eforms_ubl.py` should work with little to no modification. Consider extracting the eForms parsing logic into a shared module (e.g., `awards/parsers/eforms.py`) that both the TED and Doffin portals can use.

2. **Portal structure**: Follow the `TEDPortal` pattern:
   - `awards/portals/doffin/__init__.py` — entry point, re-exports
   - `awards/portals/doffin/portal.py` — `DoffinPortal` class implementing `download()` and `import_data()`
   - Register in `awards/portals/__init__.py` as `"doffin": DoffinPortal()`

3. **Download strategy**: Iterate dates (not OJ issue numbers) since Doffin uses calendar dates for the `download/{when}` endpoint. Skip dates with no data (weekends/holidays will return empty or 404).

4. **Authentication**: API key via `Ocp-Apim-Subscription-Key` header (standard Azure APIM pattern). Store in environment variable (e.g., `DOFFIN_API_KEY`).

5. **doc_id namespacing**: Doffin notice IDs may overlap with TED notice IDs. Use a prefix like `DOFFIN-{id}` or `NO-{id}` to avoid primary key collisions in the `documents` table.

6. **API documentation gap**: The exact Swagger/OpenAPI specification for the Doffin API is behind the Azure APIM portal login. The implementer should register for a free API key at https://dof-notices-dev-api.developer.azure-api.net/, then inspect the full API specification in the portal before coding. Key things to verify:
   - Exact format of the `{when}` parameter in `download/{when}`
   - Response format of the zip archive (flat XML files or nested directories)
   - Rate limits and pagination parameters
   - Whether `ContractAwardNotice` subtypes need filtering or all notice types are in one archive
