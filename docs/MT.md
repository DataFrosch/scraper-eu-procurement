# Malta (MT)

**Feasibility: Tier 3**

## Portal

- **Name**: ePPS (Electronic Public Procurement System)
- **URL**: https://www.etenders.gov.mt/
- **Department of Contracts**: https://contracts.gov.mt/

## Data Access

- **Method**: Web portal with registration
- **Format**: HTML
- **Auth**: Registration required
- **OCDS**: No

## Coverage

All government procurement above thresholds.

## Language

English, Maltese

## Notes

- Small country
- Department of Contracts handles administration and ex ante control
- Working on APIs and data strategy but not yet publicly available
- No public API documentation found

## Schema Mapping

### Data Format Notes

- **Format**: HTML only. The ePPS portal at etenders.gov.mt serves procurement data as rendered HTML pages behind an authenticated web application. There is no structured data export (no JSON API, no XML feed, no CSV download, no OCDS endpoint).
- **Authentication**: User registration is required to access the portal. It is unclear whether registration is open to anyone or restricted to Maltese entities. The portal may use session-based authentication with CSRF tokens, making automated scraping fragile.
- **Scraping approach**: Any implementation would require either (a) HTML scraping with a session-authenticated HTTP client (requests + BeautifulSoup or similar), or (b) browser automation (Playwright/Selenium) if the portal relies heavily on JavaScript rendering. **The exact HTML structure, URL patterns, pagination behavior, and field availability cannot be determined without authenticated access to the portal.**
- **Language**: Content is available in English and Maltese. English is the more practical choice for scraping.
- **Currency**: Malta uses EUR (Eurozone member since 2008).
- **Identifiers**: The portal likely uses internal tender/contract reference numbers. The exact format is unknown.
- **Coverage**: All government procurement above national thresholds. The Department of Contracts (contracts.gov.mt) handles administration and ex ante control, and may publish summary data separately.

**CRITICAL CAVEAT**: Because Malta's ePPS portal has no public API and no documented data structure, **all field mappings below are speculative**. They are based on what a typical EU procurement portal would expose for contract award notices. The actual field availability, naming, and structure must be verified by logging into the portal and inspecting the HTML/DOM of a contract award notice page. An implementing agent should treat this as a research-first task: gain portal access, document the actual page structure, then revise these mappings.

### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | Unknown -- likely a portal-internal tender/notice ID visible in the URL or page header | Must be verified after portal access. Could be a numeric ID or alphanumeric reference. Prefix with `"MT-"` to namespace. |
| `edition` | `None` | No OJ edition concept in a national portal. |
| `version` | Hardcode `"MT-ePPS"` | To identify the source format. |
| `reception_id` | `None` | TED-specific field. No equivalent in a national portal. |
| `official_journal_ref` | `None` | TED-specific field. No equivalent. |
| `publication_date` | Unknown -- likely a "Published Date" or "Publication Date" field on the notice page | Must be verified. Parse from whatever date format the portal uses (likely DD/MM/YYYY given EU conventions). |
| `dispatch_date` | `None` | TED-specific field. Unlikely to have an equivalent. |
| `source_country` | Hardcode `"MT"` | All data is Maltese procurement. |
| `contact_point` | Unknown -- likely a contact name on the notice page | Must be verified. May appear under a "Contact" or "Contracting Authority" section. |
| `phone` | Unknown -- likely a phone number on the notice page | Must be verified. |
| `email` | Unknown -- likely an email address on the notice page | Must be verified. |
| `url_general` | Unknown -- possibly a contracting authority website link | Must be verified. May not be present. |
| `url_buyer` | `None` | Unlikely to have a separate buyer profile URL. |

### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | Unknown -- likely "Contracting Authority" or "Organisation" field | Must be verified. This is almost certainly present on award notices. |
| `address` | Unknown -- likely part of the contracting authority details | Must be verified. May or may not be displayed. |
| `town` | Unknown -- likely part of the contracting authority address | Must be verified. Malta is small (few towns: Valletta, Floriana, etc.). |
| `postal_code` | Unknown -- likely part of the address | Must be verified. Maltese postal codes follow the format "ABC 1234". |
| `country_code` | Hardcode `"MT"` | All contracting bodies are Maltese. |
| `nuts_code` | Unknown -- unlikely to be displayed | Malta has only two NUTS 2 regions: `MT001` (Malta island) and `MT002` (Gozo and Comino). The portal probably does not show NUTS codes, but the town/address could theoretically be mapped to a NUTS code. Set to `None` unless discovered. |
| `authority_type` | Unknown -- the portal may classify contracting authorities by type | Must be verified. If present, will need mapping to eForms codes (see Code Normalization). |
| `main_activity_code` | Unknown -- unlikely to be displayed | Set to `None` unless discovered. |

### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | Unknown -- likely "Title" or "Subject" field on the notice | Must be verified. Almost certainly present. |
| `short_description` | Unknown -- likely a "Description" field | Must be verified. May be a long HTML text block requiring cleanup. |
| `main_cpv_code` | Unknown -- CPV codes may or may not be displayed | Must be verified. EU procurement portals typically include CPV codes, but not all national below-threshold portals do. |
| `cpv_codes` | Unknown -- additional CPV codes may or may not be listed | Must be verified. If CPV codes are shown, there may be a main code and additional codes. |
| `nuts_code` | Unknown -- place of performance NUTS code | Must be verified. Likely `None` -- same reasoning as contracting body NUTS code. |
| `contract_nature_code` | Unknown -- likely a "Type of Contract" field (works/supplies/services) | Must be verified. If present, will need mapping to eForms codes (see Code Normalization). |
| `procedure_type` | Unknown -- likely a "Procedure Type" field | Must be verified. EU portals typically show procedure type for above-threshold procurement. May use English labels like "Open Procedure", "Restricted Procedure", etc. Needs mapping to eForms codes. |
| `accelerated` | `None` / `False` | Unlikely to be explicitly flagged in a web portal. Default to `False`. |

### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | Unknown -- may or may not have a separate award/lot title | Must be verified. Could be the same as the contract title or a lot-specific title. |
| `contract_number` | Unknown -- likely a "Contract Number" or "Reference Number" field | Must be verified. |
| `tenders_received` | Unknown -- may be displayed as "Number of Tenders Received" | Must be verified. This is commonly shown on EU award notices but may be omitted on national portals. |
| `awarded_value` | Unknown -- likely "Contract Value" or "Award Value" | Must be verified. Almost certainly present on award notices. Parse as a numeric value; handle comma vs. period decimal separators. |
| `awarded_value_currency` | Hardcode `"EUR"` | Malta uses EUR. If the portal shows a currency symbol/code, verify it is EUR. |
| `contractors` | Unknown -- likely "Successful Tenderer" or "Contractor" section | Must be verified. Award notices should identify the winning bidder. |

### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | Unknown -- likely the contractor/supplier name | Must be verified. Almost certainly present. |
| `address` | Unknown -- may or may not show contractor address | Must be verified. |
| `town` | Unknown -- may or may not show contractor town | Must be verified. |
| `postal_code` | Unknown -- may or may not show contractor postal code | Must be verified. |
| `country_code` | Unknown -- may show contractor country | Must be verified. If shown, parse to ISO 3166-1 alpha-2. Likely `"MT"` for most contractors. |
| `nuts_code` | `None` | Unlikely to be shown for contractors. |

### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Unknown -- CPV code if displayed | Must be verified. Standard CPV format is `XXXXXXXX-X` (8 digits + check digit). |
| `description` | Unknown -- CPV description if displayed alongside the code | Must be verified. |

### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Unknown -- procedure type if displayed | Must be verified. Needs mapping to eForms codes (see Code Normalization). |
| `description` | Unknown -- procedure type label text | Must be verified. Could serve as the raw description before code mapping. |

### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Unknown -- authority type if displayed | Must be verified. Needs mapping to eForms codes (see Code Normalization). |
| `description` | Unknown -- authority type label text | Must be verified. |

### Unmappable Schema Fields

The following schema fields are almost certainly not available from the Malta ePPS portal and should be set to `None`:

- **DocumentModel.edition** -- TED OJ edition number. No equivalent in a national portal.
- **DocumentModel.reception_id** -- TED-specific reception identifier.
- **DocumentModel.official_journal_ref** -- TED Official Journal reference.
- **DocumentModel.dispatch_date** -- TED dispatch date.
- **DocumentModel.url_buyer** -- Unlikely to have a separate buyer profile URL.
- **ContractingBodyModel.nuts_code** -- NUTS codes are an EU statistical concept unlikely to appear on a national portal. Could potentially be derived from town/address.
- **ContractingBodyModel.main_activity_code** -- Unlikely to be displayed.
- **ContractModel.nuts_code** -- Same reasoning as above.
- **ContractModel.accelerated** -- Unlikely to be explicitly flagged. Default to `False`.
- **ContractorModel.nuts_code** -- Unlikely to be shown.

Fields that **might** be unavailable but need verification:

- **ContractingBodyModel.authority_type** -- May or may not classify authorities by type.
- **ContractModel.main_cpv_code** / **cpv_codes** -- CPV codes are standard in EU procurement but may not be shown on below-threshold national notices.
- **AwardModel.tenders_received** -- Commonly shown on award notices in the EU but may be omitted.
- **ContractorModel.address/town/postal_code/country_code** -- Contractor address details may or may not be displayed.

### Extra Portal Fields

Without portal access, it is impossible to enumerate extra fields definitively. However, based on typical EU national procurement portals, the following fields are commonly available and not covered by the current schema (flagging for review):

- **Tender reference number / Call for Tenders ID** -- National reference number for the procurement procedure. Schema doesn't cover a separate national identifier -- flagging for review.
- **Lot information** -- If the portal breaks down awards by lot, the lot structure is lost in the current schema. Schema doesn't cover lot-level grouping -- flagging for review.
- **Award date** -- The date the award decision was made (distinct from publication date). Schema doesn't cover award date -- flagging for review.
- **Submission deadline** -- The deadline for submitting tenders. Schema doesn't cover -- flagging for review.
- **Estimated value** -- The estimated contract value before award. Schema doesn't cover -- flagging for review.
- **Contract duration / period** -- Start and end dates of the contract. Schema doesn't cover -- flagging for review.
- **Contractor registration/VAT number** -- If displayed, useful for entity resolution. Schema doesn't cover structured organization identifiers -- flagging for review.
- **Department/ministry** -- The specific government department handling the procurement. May provide more granular classification than the contracting body name alone.

### Code Normalization

**All code mappings below are speculative and must be verified against the actual values displayed on the portal.**

#### Contract Nature Codes

If the portal displays contract types, they likely use English labels (Malta's procurement is conducted in English). Expected mapping to eForms `contract-nature` codes:

| Likely Portal Value | eForms Code | Notes |
|---|---|---|
| "Works" / "Public Works" | `"works"` | Direct match |
| "Supplies" / "Supply" / "Goods" | `"supplies"` | "Goods" maps to "supplies" per eForms convention |
| "Services" | `"services"` | Direct match |

#### Procedure Type Codes

If the portal displays procedure types, they likely use standard EU terminology in English. Expected mapping to eForms `procurement-procedure-type` codes:

| Likely Portal Value | eForms Code | Notes |
|---|---|---|
| "Open Procedure" | `"open"` | Direct match |
| "Restricted Procedure" | `"restricted"` | Direct match |
| "Competitive Procedure with Negotiation" | `"neg-w-call"` | |
| "Negotiated Procedure without Prior Publication" | `"neg-wo-call"` | |
| "Competitive Dialogue" | `"comp-dial"` | |
| "Innovation Partnership" | `"innovation"` | |
| "Direct Award" / "Direct Order" | `"neg-wo-call"` | Below-threshold direct awards map to negotiated without call |

Maltese procurement law follows EU directives closely. Below-threshold procedures may use simplified labels (e.g., "Direct Order" for small-value contracts, "Departmental Tender" for mid-value). These national-specific labels will need investigation and mapping.

#### Authority Type Codes

If the portal classifies contracting authorities, the mapping to eForms `buyer-legal-type` codes would likely follow:

| Likely Portal Value | eForms Code | Notes |
|---|---|---|
| "Ministry" / "Government Ministry" | `"cent-gov"` | Central government |
| "Local Council" | `"ra-aut"` | Regional/local authority |
| "Public Entity" / "Government Agency" | `"body-public"` | Body governed by public law |
| "Public Corporation" | `"pub-undert"` | Public undertaking |

Malta's government structure is relatively simple: central government ministries, a few statutory authorities/agencies, and 68 local councils. The Department of Contracts is the central procurement authority.

#### Country Codes

If the portal shows country names, they will likely be in English. A simple mapping from common country names to ISO 3166-1 alpha-2 codes is needed. The vast majority of contractors will be Maltese (`"MT"`).

### Implementation Considerations

1. **Tier 3 feasibility**: This is rated Tier 3 (most difficult). Before investing in implementation, attempt to gain portal access and document the actual page structure. If the portal is JavaScript-heavy or uses anti-scraping measures, the effort may not be justified given Malta's small procurement volume.

2. **Alternative data sources**: Check whether the Department of Contracts (contracts.gov.mt) publishes any structured data, annual reports with tabular data, or open data on Malta's national open data portal (data.gov.mt). These may provide a more tractable data source than scraping the ePPS portal.

3. **Small data volume**: Malta is the smallest EU member state. Total annual procurement volume is low (likely hundreds to low thousands of award notices per year). This means scraping feasibility is less about scale and more about access.

4. **TED overlap**: Above-threshold Maltese procurement is already published on TED and captured by the existing TED scraper. The value-add from a national portal scraper is only the below-threshold procurement data. Assess whether the volume of below-threshold data justifies the scraping complexity.

5. **Research-first approach**: The implementing agent should:
   - Register on the ePPS portal and document the registration process.
   - Navigate to a sample contract award notice and document the HTML structure, URL pattern, and available fields.
   - Check for any hidden API calls (inspect browser network tab) that the portal's frontend makes to fetch data.
   - Revise all "Unknown" mappings in this document based on actual findings.
   - Only then proceed to implementation.
