# Cyprus (CY)

**Feasibility: Tier 3**

## Portal

- **Name**: e-PPS (Electronic Procurement System)
- **URL**: https://www.eprocurement.gov.cy/

## Data Access

- **Method**: Web portal with registration required
- **Format**: HTML
- **Auth**: Registration required to search and access documents
- **OCDS**: No

## Coverage

All public procurement above thresholds.

## Language

Greek, English

## Notes

- Registration-gated web portal with no API
- No public API documentation found

## Schema Mapping

### Data Access Assessment

Cyprus is classified as **Tier 3** -- the e-PPS portal at `https://www.eprocurement.gov.cy/` is a registration-gated web application with no public API, no bulk data export, and no structured data feed (no OCDS, no XML, no CSV). As of the research date (2026-02-14), no public API documentation has been found. This means:

1. **No programmatic data access** has been confirmed. All data access requires manual registration and authentication through a web browser.
2. **Data format is HTML** -- procurement data is rendered as web pages, not served as structured data (JSON, XML, CSV, etc.).
3. **The field mappings below are speculative** -- they are based on typical procurement portal fields observed in similar EU e-procurement systems (particularly Malta's ePPS and Greece's ESIDIS, which share architectural similarities). The actual field names, structures, and availability must be confirmed by registering on the portal and inspecting the HTML structure of award notice pages.

**Before implementing a scraper**, the following must be done manually:
- Register for an account on `https://www.eprocurement.gov.cy/`
- Navigate to award/contract notices and inspect the HTML structure
- Document the actual fields, their labels (Greek and/or English), and their DOM structure
- Determine if any hidden API endpoints exist (check browser network traffic for XHR/fetch calls that return JSON)
- Check for any RSS/Atom feeds or sitemap that could aid discovery

### Data Format Notes

- **Format**: HTML web pages. No confirmed structured data format (JSON, XML, CSV).
- **Authentication**: Registration required. Credentials must be obtained by creating an account on the portal. Store in environment variables (e.g., `CY_EPPS_USER`, `CY_EPPS_PASSWORD`).
- **Language**: Greek and English. The portal may serve bilingual content or allow language switching. Field labels may be in Greek.
- **Currency**: Cyprus uses EUR (joined Eurozone in 2008). All monetary values should be in EUR unless otherwise indicated.
- **Character encoding**: Expect Greek text (UTF-8) in titles, descriptions, and organization names.
- **Scraping approach**: Likely requires HTML scraping (e.g., BeautifulSoup or lxml.html) or browser automation (e.g., Playwright/Selenium) if the portal relies on JavaScript rendering.
- **Rate limits**: Unknown. Implement conservative rate limiting (e.g., 1 request every 2 seconds) to avoid being blocked.
- **NUTS codes**: Cyprus uses `CY` prefix in NUTS codes (e.g., `CY000` -- Cyprus has a single NUTS-2 region).
- **Pagination**: Unknown. The portal likely paginates search results; the mechanism (query params, form submission, JavaScript-driven) must be determined by inspection.
- **IMPORTANT**: The portal may use session-based authentication, CSRF tokens, or other anti-scraping measures that complicate automated access. This must be assessed during the manual inspection phase.

### Field Mapping Tables

All mappings below are **speculative** and based on fields commonly found in EU procurement portals. The "Portal Field/Path" column describes the expected field based on EU procurement directive requirements, not confirmed portal structure. Each field marked with `[UNCONFIRMED]` must be verified against the actual portal HTML.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | Portal-specific notice ID or URL slug `[UNCONFIRMED]` | Must identify a unique notice. Could be a reference number displayed on the page, or derived from the URL. If no stable ID exists, construct one from portal name + sequential number (e.g., `CY-EPPS-12345`). |
| `edition` | `None` | No edition concept expected in a national portal. |
| `version` | `None` | No version numbering expected. |
| `reception_id` | `None` | TED-specific field. No equivalent expected. |
| `official_journal_ref` | `None` | Not an official journal. |
| `publication_date` | Publication/posting date on the notice page `[UNCONFIRMED]` | EU directives require publication dates on award notices. Look for a date field labeled "Publication Date" or similar (Greek: "Ημερομηνία Δημοσίευσης"). Parse from displayed text. |
| `dispatch_date` | `None` | Unlikely to be available on a national portal. |
| `source_country` | hardcode `"CY"` | All data is Cypriot procurement. |
| `contact_point` | Contact person/point on the notice `[UNCONFIRMED]` | EU directives require contact information on notices. Look for a "Contact" section. |
| `phone` | Phone number on the notice `[UNCONFIRMED]` | May be in the contact section of the notice. |
| `email` | Email on the notice `[UNCONFIRMED]` | May be in the contact section of the notice. |
| `url_general` | URL of the notice page itself | Construct from the portal URL + notice path. |
| `url_buyer` | `None` | Unlikely to have a separate buyer profile URL. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | Contracting authority name on the notice `[UNCONFIRMED]` | EU directives require the contracting authority name. Look for "Contracting Authority" or "Αναθέτουσα Αρχή". |
| `address` | Contracting authority address `[UNCONFIRMED]` | May be part of the contracting authority details section. |
| `town` | Contracting authority town/city `[UNCONFIRMED]` | May be part of address or separate field. |
| `postal_code` | Contracting authority postal code `[UNCONFIRMED]` | May be part of address. |
| `country_code` | hardcode `"CY"` or from notice `[UNCONFIRMED]` | Almost always `"CY"` for Cypriot procurement. Could hardcode, but if the field exists, extract it. |
| `nuts_code` | `[UNCONFIRMED]` | Cyprus has limited NUTS granularity (`CY000`). May not be displayed on the portal. If not available, could hardcode `"CY000"` but per fail-loud principle, set to `None` if not present. |
| `authority_type` | Type of contracting authority `[UNCONFIRMED]` | EU directive forms include authority type. If present, will need mapping to eForms codes. See Code Normalization. |
| `main_activity_code` | Main activity of the contracting authority `[UNCONFIRMED]` | EU directive forms include main activity. If present, will need mapping to eForms codes. See Code Normalization. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | Contract/notice title `[UNCONFIRMED]` | EU directives require a title. Look for "Title" or "Τίτλος". |
| `short_description` | Description or object of the contract `[UNCONFIRMED]` | Look for "Short description" or "Σύντομη περιγραφή". |
| `main_cpv_code` | Main CPV code `[UNCONFIRMED]` | EU directive award notices require CPV codes. Look for "CPV" label followed by codes in format `########-#`. |
| `cpv_codes` | All CPV codes listed on the notice `[UNCONFIRMED]` | May include main + additional CPV codes. |
| `nuts_code` | Place of performance NUTS code `[UNCONFIRMED]` | If present, likely `CY000`. May not be displayed. |
| `contract_nature_code` | Type of contract (works/supplies/services) `[UNCONFIRMED]` | EU directives require this. Will need mapping to eForms codes. See Code Normalization. |
| `procedure_type` | Type of procedure `[UNCONFIRMED]` | EU directives require this on award notices. Will need mapping to eForms codes. See Code Normalization. |
| `accelerated` | `False` | No accelerated procedure flag expected on a basic web portal. Set to `False`. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | Award/lot title `[UNCONFIRMED]` | May be the same as the contract title, or per-lot titles if the notice covers multiple lots. |
| `contract_number` | Contract number or reference number `[UNCONFIRMED]` | Look for "Contract number" or "Αριθμός Σύμβασης". |
| `tenders_received` | Number of tenders received `[UNCONFIRMED]` | EU directive award notices include this field. Look for "Number of tenders received" or "Αριθμός προσφορών που υποβλήθηκαν". |
| `awarded_value` | Total value of the contract/award `[UNCONFIRMED]` | EU directive award notices require the value. Look for "Total value" or "Συνολική αξία". Will need monetary parsing from displayed text (e.g., "€1,234,567.89" or "1.234.567,89 EUR"). |
| `awarded_value_currency` | Currency from value field or hardcode `"EUR"` | Cyprus uses EUR. Extract if displayed alongside value, otherwise hardcode `"EUR"`. |
| `contractors` | See ContractorModel below | |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | Name of winning contractor/supplier `[UNCONFIRMED]` | EU directive award notices require contractor identification. Look for "Contractor" / "Ανάδοχος" or "Economic operator" / "Οικονομικός φορέας". |
| `address` | Contractor address `[UNCONFIRMED]` | May be part of the contractor details section. |
| `town` | Contractor town/city `[UNCONFIRMED]` | May be part of address. |
| `postal_code` | Contractor postal code `[UNCONFIRMED]` | May be part of address. |
| `country_code` | Contractor country `[UNCONFIRMED]` | If present, extract. Do not assume `"CY"` -- contractors can be from any country. |
| `nuts_code` | `None` | Unlikely to be displayed for contractors on a basic web portal. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | CPV code(s) displayed on the notice `[UNCONFIRMED]` | Standard format `########-#`. Extract from text using regex if needed. |
| `description` | CPV description text `[UNCONFIRMED]` | May be displayed alongside the code. If not, descriptions can be looked up from the standard CPV code list. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Procedure type value (after mapping to eForms) `[UNCONFIRMED]` | Raw value will be a Greek or English procedure type label. Must be mapped to eForms codes. See Code Normalization. |
| `description` | Raw procedure type label from the portal `[UNCONFIRMED]` | Store the original label as the description. |

#### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Authority type value (after mapping to eForms) `[UNCONFIRMED]` | If present, raw value will be a Greek or English label. Must be mapped to eForms codes. See Code Normalization. |
| `description` | Raw authority type label from the portal `[UNCONFIRMED]` | Store the original label as the description. |

### Unmappable Schema Fields

The following fields are **likely** to be `None` based on what national web portals typically do not expose. This must be confirmed during the manual inspection phase.

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | No edition concept in a national portal |
| `DocumentModel.version` | No version numbering expected |
| `DocumentModel.reception_id` | TED-specific concept |
| `DocumentModel.official_journal_ref` | Not an official journal |
| `DocumentModel.dispatch_date` | TED-specific concept, unlikely on a national portal |
| `DocumentModel.url_buyer` | Unlikely to have a separate buyer profile URL |
| `ContractingBodyModel.nuts_code` | May not be displayed; Cyprus has only `CY000` at NUTS-2 level |
| `ContractModel.nuts_code` | May not be displayed |
| `ContractModel.accelerated` | No accelerated flag expected; always `False` |
| `ContractorModel.nuts_code` | Unlikely to be displayed for contractors |

### Extra Portal Fields

Without access to the portal, it is impossible to enumerate extra fields with certainty. However, based on typical EU procurement portals, the following fields are likely available but not covered by the current schema. **This list must be updated after manual inspection.**

| Expected Portal Field | Notes |
|---|---|
| Tender/Notice reference number | Internal reference number distinct from the contract number. Schema doesn't cover separate tender identifiers -- flagging for review. |
| Award date / Decision date | The date the award decision was made, distinct from publication date. Schema doesn't cover award date separately -- flagging for review. |
| Contract signing date | Date the contract was signed. Schema doesn't cover -- flagging for review. |
| Estimated value / Budget | The estimated or budgeted value before award. Schema doesn't cover -- flagging for review. |
| Lot information | If multi-lot notices are used, individual lot details. Schema doesn't cover lot structure -- flagging for review. |
| Award criteria | Lowest price, best quality-price ratio, etc. Schema doesn't cover -- flagging for review. |
| Submission deadline | Deadline for tender submissions. Schema doesn't cover -- flagging for review. |
| Status (open/closed/cancelled) | Notice or contract status. Schema doesn't cover -- flagging for review. |
| VAT number of contracting authority | Organization identifier. Schema doesn't cover structured organization identifiers -- flagging for review. |
| VAT number of contractor | Supplier identifier. Schema doesn't cover -- flagging for review. |
| Subcontracting information | Whether subcontracting is involved. Schema doesn't cover -- flagging for review. |
| Framework agreement indicator | Whether this is under a framework agreement. Schema doesn't cover -- flagging for review. |
| EU funding indicator | Whether EU funds are involved. Schema doesn't cover -- flagging for review. |

### Code Normalization

The actual code values used by the Cypriot portal are **unknown** without portal access. The mappings below document what will need to be mapped, and provide the expected eForms target codes. The actual source values (whether they are numeric codes, Greek labels, English labels, or EU directive form codes) must be discovered during the manual inspection phase.

#### Contract Nature Codes

Cyprus, as an EU member state, follows EU procurement directives which define three contract types. The portal will display these in Greek, English, or as codes.

| Expected Portal Value (Greek) | Expected Portal Value (English) | eForms Code |
|---|---|---|
| Έργα | Works | `works` |
| Προμήθειες | Supplies | `supplies` |
| Υπηρεσίες | Services | `services` |

If the portal uses numeric codes (e.g., from TED form conventions: `1` = works, `2` = supplies, `4` = services), those must be mapped too.

#### Procedure Type Codes

EU procurement directives define standard procedure types. The portal may use Greek labels, English labels, or directive codes.

| Expected Portal Value (Greek) | Expected Portal Value (English) | eForms Code |
|---|---|---|
| Ανοικτή διαδικασία | Open procedure | `open` |
| Κλειστή διαδικασία | Restricted procedure | `restricted` |
| Ανταγωνιστική διαδικασία με διαπραγμάτευση | Competitive procedure with negotiation | `neg-w-call` |
| Διαδικασία με διαπραγμάτευση χωρίς προκήρυξη | Negotiated procedure without prior publication | `neg-wo-call` |
| Ανταγωνιστικός διάλογος | Competitive dialogue | `comp-dial` |
| Σύμπραξη καινοτομίας | Innovation partnership | `innovation` |

**Note**: Below-threshold procurement in Cyprus may use simplified procedures (e.g., direct award, request for quotation) that do not have direct eForms equivalents. These must be documented when discovered.

#### Authority Type Codes

EU directive forms include authority type classifications. The portal may display these in Greek or English.

| Expected Portal Value (Greek) | Expected Portal Value (English) | eForms Code |
|---|---|---|
| Υπουργείο ή άλλη εθνική/ομοσπονδιακή αρχή | Ministry or other national/federal authority | `ra-authority` |
| Αρχή τοπικής αυτοδιοίκησης | Local authority | `la-authority` |
| Οργανισμός δημοσίου δικαίου | Body governed by public law | `body-public` |
| Ευρωπαϊκό θεσμικό όργανο | EU institution/agency | `eu-ins-bod-ag` |
| Άλλο | Other | `other` |

#### Main Activity Codes

EU directive forms include main activity classifications. Mapping depends on whether the contracting authority falls under the general directive (2014/24/EU) or the utilities directive (2014/25/EU).

**Action required**: Determine which activity codes the portal uses and map to eForms `main-activity` codelist values (e.g., `gen-pub`, `defence`, `health`, `education`, `water`, `electricity`, `gas-oil`, `transport`, etc.).

#### Country Codes

If the portal displays country names in Greek, a mapping to ISO 3166-1 alpha-2 codes will be needed. Common cases:

| Greek Name | ISO Code |
|---|---|
| Κύπρος | `CY` |
| Ελλάδα | `GR` |
| Ηνωμένο Βασίλειο | `GB` |

A broader mapping table should be prepared if international contractors are common.

### Implementation Notes

1. **Tier 3 reality**: This is the hardest category of portal to scrape. There is no API, no structured data, and registration is required. Implementation feasibility is uncertain until the manual inspection is complete.

2. **Recommended investigation steps**:
   - Register for an account on `https://www.eprocurement.gov.cy/`
   - Search for completed/awarded contract notices
   - Use browser developer tools to inspect network traffic -- some "web-only" portals actually make XHR calls to internal APIs that return JSON. If such an API is discovered, this portal could be upgraded to Tier 2.
   - Document the HTML structure of an award notice page, including all field labels and their CSS selectors or XPath expressions.
   - Check for any search/export functionality that produces CSV or PDF output.

3. **Alternative data sources**: Consider whether Cypriot award data below TED thresholds might be accessible through other channels:
   - Cyprus Open Data portal (`https://www.data.gov.cy/`) -- check for procurement datasets.
   - The Treasury of the Republic of Cyprus may publish procurement statistics.
   - DIAVGEIA-style transparency portals (Greece's model) -- check if Cyprus has adopted something similar.

4. **Scraping architecture**: If HTML scraping is the only option:
   - Use session-based authentication (login once, reuse cookies).
   - Parse HTML with lxml.html or BeautifulSoup.
   - If the portal is JavaScript-heavy (SPA), browser automation (Playwright) may be required.
   - Implement robust error handling for HTML structure changes.
   - Store raw HTML alongside parsed data for debugging.

5. **doc_id construction**: Since there is no confirmed unique identifier format, the implementer must decide on a stable `doc_id` scheme. Options:
   - Use the portal's internal reference number if one exists.
   - Construct from URL path (e.g., `CY-EPPS-{url_slug}`).
   - Use a hash of key fields (title + date + contracting authority) as a last resort, but this is fragile.
