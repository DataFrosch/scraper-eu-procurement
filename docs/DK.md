# Denmark (DK)

**Feasibility: Tier 3**

## Portal

- **Name**: udbud.dk
- **URL**: https://udbud.dk/
- **Operated by**: Danish Competition and Consumer Authority (KFST)

## Data Access

- **Method**: Web search portal
- **Format**: HTML
- **Auth**: Open browse
- **OCDS**: No

## Coverage

All procurements including below EU thresholds with cross-border interest.

## Language

Danish

## Notes

- No API documentation found
- Web-only portal with no known structured data export
- URL structure uses UUID-based `noticeId` parameters, e.g. `https://udbud.dk/detaljevisning?noticeId={uuid}&noticeVersion=01&noticePublicationNumber=00189934-2025`
- An `api.udbud.dk` subdomain exists and is used at least for document attachments (`api.udbud.dk/udbud/vedhaeftning/...`), but no public API documentation has been found
- The `noticePublicationNumber` values (e.g. `00189934-2025`, `00432323-2025`) follow a TED-like numbering pattern, suggesting EU-threshold notices are cross-published to TED
- Denmark has been required to use eForms for EU-threshold notices since October 2023
- Multiple eSender platforms operate in Denmark (Mercell, EU-Supply/CTM), handling TED integration for contracting authorities

## Schema Mapping

### Feasibility Assessment

**Denmark is Tier 3** -- the most difficult tier for scraping. udbud.dk is a web-only search portal with:

- **No documented public API** (though an `api.udbud.dk` subdomain exists for document attachments)
- **No structured data export** (no JSON, XML, CSV, or OCDS bulk download)
- **No open data portal** for procurement data (Denmark's open data efforts via opendata.dk and datavejviser.dk do not include procurement data from udbud.dk)
- **HTML-only** notice rendering through a JavaScript-based single-page application

This means implementing a DK portal scraper would require either:

1. **Reverse-engineering the frontend API**: The SPA at udbud.dk almost certainly makes XHR/fetch calls to a backend API (likely the `api.udbud.dk` subdomain) to retrieve notice data as JSON. Intercepting these calls via browser developer tools would reveal the actual API endpoints, request/response formats, and available fields. This is the most promising path but requires manual investigation.
2. **HTML scraping**: Rendering pages with a headless browser (Selenium/Playwright) and extracting data from the DOM. Fragile and slow.
3. **Bypassing udbud.dk entirely**: For EU-threshold notices, the same data is available via TED (already covered by our TED portal). The unique value-add of udbud.dk is below-threshold national notices, which are only available through this portal.

**Recommendation**: Before implementing, an engineer should manually inspect the udbud.dk frontend with browser developer tools (Network tab) to:
- Identify the backend API base URL (likely `api.udbud.dk` or a path under `udbud.dk`)
- Document the search/list endpoint (used by the archive/search page)
- Document the detail endpoint (used by the `detaljevisning` page)
- Capture sample JSON responses for awarded contract notices
- Determine if any authentication/session tokens are required beyond cookies

If a usable JSON API is discovered behind the frontend, this portal could potentially be upgraded to Tier 2 or even Tier 1.

### Data Format Notes

- **Current known format**: HTML pages rendered by a JavaScript SPA. The underlying data format served to the frontend is unknown but likely JSON.
- **URL structure**: `https://udbud.dk/detaljevisning?noticeId={uuid}&noticeVersion={version}&noticePublicationNumber={number}` -- the UUID-based `noticeId` and versioned `noticeVersion` suggest a well-structured backend data model.
- **Likely backend format**: JSON responses from `api.udbud.dk` or an internal API. The `noticePublicationNumber` parameter (e.g. `00189934-2025`) follows TED publication number conventions, suggesting the backend may store notices in an eForms-like or TED-compatible structure.
- **eForms connection**: Since Denmark uses eForms for EU-threshold notices (mandatory since Oct 2023), the backend may store eForms data natively. If the backend API returns eForms-structured JSON or XML, our existing `eforms_ubl.py` parser could potentially be adapted.
- **Archive page**: `https://udbud.dk/arkiv` provides a search interface. The query parameters and filtering capabilities are unknown and must be reverse-engineered.
- **Parsing considerations**: If the backend API is discovered, the primary parsing challenge will be mapping the API's JSON field names (likely in Danish or eForms-style) to our schema. If only HTML scraping is possible, the parser will need to handle dynamic content loading, pagination, and DOM structure changes.

### Field Mapping

The tables below document the **best-effort mapping** based on what is known about udbud.dk's data model. Since no API documentation exists, these mappings are based on:
- Standard fields required by Danish procurement law (Udbudsloven)
- eForms fields that Denmark is required to publish for EU-threshold notices
- Common fields visible on similar Nordic procurement portals (Hilma/Finland, Doffin/Norway)

**All field paths marked with `[UNKNOWN]` require verification against actual API responses or HTML page structure once the backend is reverse-engineered.**

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `noticeId` (UUID from URL) | The UUID used in the `noticeId` URL parameter. Prefix with `DK-` to avoid collisions with TED doc_ids, e.g. `DK-cc0b31a1-2763-437b-a41d-ec678d5914d5`. |
| `edition` | `[UNKNOWN]` | No known equivalent. Could derive from `publication_date` as `{year}{day_of_year:03d}` if available, or set to `None`. |
| `version` | `noticeVersion` from URL (e.g. `"01"`) | The version parameter is present in the URL structure. Could store as-is or use a format identifier like `"udbud.dk"`. |
| `reception_id` | `None` | TED-specific concept. No equivalent expected. |
| `official_journal_ref` | `noticePublicationNumber` from URL | For EU-threshold notices, this may match the TED publication number (e.g. `00189934-2025`). For national-only notices, this will likely be empty. |
| `publication_date` | `[UNKNOWN]` -- likely present in notice detail | Danish law requires publication dates. Likely available in the notice detail page/API response. |
| `dispatch_date` | `[UNKNOWN]` | May be available for EU-threshold notices that were sent to TED. Likely `None` for national notices. |
| `source_country` | Hardcode `"DK"` | All udbud.dk notices are Danish procurement. |
| `contact_point` | `[UNKNOWN]` -- likely present in contracting body section | Danish procurement law requires contracting authorities to provide contact information. |
| `phone` | `[UNKNOWN]` -- likely present in contracting body section | Likely available but field path unknown. |
| `email` | `[UNKNOWN]` -- likely present in contracting body section | Likely available; Danish procurement notices typically include email contacts. |
| `url_general` | `[UNKNOWN]` | May be available as the contracting authority's website. |
| `url_buyer` | `[UNKNOWN]` | May or may not be available. Likely `None` for national notices. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `[UNKNOWN]` -- "Ordregiver" section in Danish | Danish term is "ordregiver" (contracting authority). Mandatory field in all procurement notices. Will be present. |
| `address` | `[UNKNOWN]` | Likely present for EU-threshold notices (eForms BT-510). May be omitted in below-threshold national notices. |
| `town` | `[UNKNOWN]` | Likely present. Danish procurement notices typically include city. |
| `postal_code` | `[UNKNOWN]` | Likely present. Danish postal codes are 4 digits. |
| `country_code` | `[UNKNOWN]` or hardcode `"DK"` | Will almost always be `"DK"` for contracting authorities on udbud.dk. |
| `nuts_code` | `[UNKNOWN]` | Denmark has NUTS codes (`DK0xx`). Mandatory for EU-threshold eForms notices (BT-507). May not be present in below-threshold national notices. |
| `authority_type` | `[UNKNOWN]` | Mandatory in eForms (BT-11 buyer-legal-type). Unknown whether udbud.dk exposes this for national notices. See Code Normalization below. |
| `main_activity_code` | `[UNKNOWN]` | Mandatory in eForms (BT-10). Unknown whether exposed for national notices. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `[UNKNOWN]` -- likely the notice/contract title visible on detail page | Mandatory in all procurement notices. Will be in Danish. |
| `short_description` | `[UNKNOWN]` | Likely available for EU-threshold notices. May be absent for simpler national notices. |
| `main_cpv_code` | `[UNKNOWN]` | CPV codes are mandatory for EU-threshold notices. For below-threshold national notices, CPV usage depends on Danish national rules and may not always be present. |
| `cpv_codes` | `[UNKNOWN]` | Same as above. If present, CPV codes are EU-standard and need no conversion. |
| `nuts_code` | `[UNKNOWN]` | NUTS code for place of performance. Mandatory for EU-threshold eForms (BT-5071). May not be present for national notices. |
| `contract_nature_code` | `[UNKNOWN]` | Whether the contract is for works, supplies, or services. Likely present in some form. See Code Normalization below. |
| `procedure_type` | `[UNKNOWN]` | The procurement procedure used. Likely present; Danish law (Udbudsloven) defines specific procedure types. See Code Normalization below. |
| `accelerated` | `[UNKNOWN]` | eForms BT-106. May be present for EU-threshold notices. Likely not tracked for national below-threshold notices. Default to `False` if absent. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `[UNKNOWN]` | May or may not be separate from the contract title. In eForms this is BT-721 (settled contract title). |
| `contract_number` | `[UNKNOWN]` | Contract reference number. Likely available. |
| `tenders_received` | `[UNKNOWN]` | Number of tenders received. Present in eForms (BT-759) for EU-threshold notices. Unknown availability for national notices. |
| `awarded_value` | `[UNKNOWN]` | The awarded contract value. Danish law requires publication of contract values for awarded contracts above certain thresholds. Likely present. |
| `awarded_value_currency` | `[UNKNOWN]` or hardcode `"DKK"` | Danish Krone for national notices. EU-threshold notices may use EUR. Need to check actual data. |
| `contractors` | `[UNKNOWN]` -- "Leverandør"/"Tilbudsgiver" in Danish | The winning contractor/supplier. Danish term is "leverandør" (supplier) or "tilbudsgiver" (tenderer). Mandatory to publish for awarded contracts. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `[UNKNOWN]` | Contractor/supplier name. Mandatory in award notices. |
| `address` | `[UNKNOWN]` | Likely present for EU-threshold notices. May be absent for national notices. |
| `town` | `[UNKNOWN]` | Likely present. |
| `postal_code` | `[UNKNOWN]` | Likely present. Danish postal codes are 4 digits. |
| `country_code` | `[UNKNOWN]` | May be `"DK"` or a foreign country code. |
| `nuts_code` | `[UNKNOWN]` | May not be present, especially for national below-threshold notices. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `[UNKNOWN]` | CPV codes are EU-standard. If present in the data, they need no conversion. Mandatory for EU-threshold notices; uncertain for national notices. |
| `description` | `[UNKNOWN]` | May be present in Danish alongside the code. If not, can be looked up from a CPV reference table. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `[UNKNOWN]` | See Code Normalization below. Will need mapping from Danish procedure names or codes to eForms equivalents. |
| `description` | `[UNKNOWN]` | May be present in Danish. |

#### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `[UNKNOWN]` | See Code Normalization below. |
| `description` | `[UNKNOWN]` | May be present in Danish. |

### Unmappable Schema Fields

These fields will likely be `None` for udbud.dk-sourced notices:

| Schema Field | Reason |
|---|---|
| `DocumentModel.reception_id` | TED-specific concept. No equivalent in udbud.dk. |
| `DocumentModel.official_journal_ref` | Only applicable for EU-threshold notices cross-published to TED. National-only notices will have no OJ reference. The `noticePublicationNumber` URL parameter may serve as a partial substitute for EU-threshold notices. |
| `DocumentModel.dispatch_date` | TED-specific (date sent to OJ). Likely not tracked by udbud.dk for national notices. |
| `DocumentModel.url_buyer` | Buyer profile URL is not a common field in national portals. Likely `None`. |
| `ContractingBodyModel.nuts_code` | NUTS codes are an EU eForms requirement. Below-threshold national notices may not include them. |
| `ContractingBodyModel.authority_type` | May not be exposed for national below-threshold notices. |
| `ContractingBodyModel.main_activity_code` | May not be exposed for national below-threshold notices. |
| `ContractModel.nuts_code` | Place-of-performance NUTS code likely absent for national notices. |
| `ContractModel.accelerated` | eForms BT-106 concept. Not applicable to most national below-threshold notices. Default to `False`. |
| `ContractorModel.nuts_code` | Supplier NUTS code likely absent for national notices. |
| `CpvCodeEntry.description` | May or may not be present. Not critical -- can be looked up from CPV reference data. |
| `ProcedureTypeEntry.description` | May or may not be present. Can be populated from a static lookup. |
| `AuthorityTypeEntry.description` | May or may not be present. Can be populated from a static lookup. |

### Extra Portal Fields

The following fields are potentially available on udbud.dk but not covered by the current schema. Flagged for review.

| Portal Field | Description | Notes |
|---|---|---|
| `noticeId` (UUID) | Unique notice identifier in udbud.dk | Schema doesn't cover portal-specific identifiers separately from `doc_id` -- flagging for review. Useful for deduplication and back-references. |
| `noticeVersion` | Version number of the notice | Schema doesn't cover notice versioning -- flagging for review. Indicates whether a notice has been corrected/updated. |
| `noticePublicationNumber` | TED-style publication number | Schema doesn't cover this as a separate field -- flagging for review. Useful for cross-referencing with TED data and deduplication. |
| CVR number (Danish business register) | Danish company registration number | Schema doesn't cover organization identifiers -- flagging for review. Very useful for entity resolution. Danish companies are identified by CVR numbers (8 digits), queryable at cvr.dk. Equivalent to BT-501 in eForms. |
| Lot-level data | Individual lot details within multi-lot notices | Schema doesn't cover lot structure -- flagging for review. Danish procurement often involves multi-lot tenders. |
| Contract conclusion date | Date the contract was signed | Schema doesn't cover -- flagging for review. |
| Estimated value | Pre-award estimated contract value | Schema doesn't cover -- flagging for review. |
| Framework agreement indicator | Whether this is a framework agreement | Schema doesn't cover -- flagging for review. Framework agreements (rammeaftaler) are very common in Danish public procurement. |
| Below-threshold notice type | Specific Danish national notice categories | Schema doesn't cover notice type granularity -- flagging for review. These below-threshold notices are the primary value-add over TED data. |
| Complaint deadline (klagefrist) | Deadline for filing procurement complaints at Klagenaevnet for Udbud | Schema doesn't cover -- flagging for review. Denmark-specific; could indicate legal dispute risk. |

### Code Normalization

Since the actual field values from udbud.dk are unknown (no API documentation), the mappings below are based on Danish procurement law (Udbudsloven) and the assumption that udbud.dk follows either eForms conventions (for EU-threshold notices) or Danish-language equivalents (for national notices).

#### Procedure Type Codes

For EU-threshold notices stored in eForms format, codes should already be eForms-compliant. For national notices, Danish-language procedure names from Udbudsloven will need mapping:

| Danish Term (Udbudsloven) | eForms Code | Notes |
|---|---|---|
| Offentligt udbud | `open` | Open procedure (Udbudsloven Part II, ch. 5) |
| Begrænset udbud | `restricted` | Restricted procedure (Udbudsloven Part II, ch. 6) |
| Udbud med forhandling | `neg-w-call` | Negotiated procedure with prior publication (Udbudsloven Part II, ch. 7) |
| Konkurrencepræget dialog | `comp-dial` | Competitive dialogue (Udbudsloven Part II, ch. 8) |
| Innovationspartnerskab | `innovation` | Innovation partnership (Udbudsloven Part II, ch. 9) |
| Udbud uden forudgående offentliggørelse | `neg-wo-call` | Negotiated without prior publication (Udbudsloven Part II, ch. 10) |
| Light-regimet / Udbud af sociale og andre specifikke tjenesteydelser | `oth-single` | Light regime for social/health services (Udbudsloven Part III). Best-effort mapping; no exact eForms equivalent. |
| Tilbudsloven procedure | `[UNKNOWN]` | Below-threshold procedures under the Danish Tender Act (Tilbudsloven) may use different categories. Mapping needed once actual values are observed. |

**Important**: Below-threshold national notices may use simplified procedure descriptions that do not map cleanly to eForms codes. The implementing parser should log warnings for unmapped values and store the original Danish text in the `description` field.

#### Authority Type Codes

For EU-threshold eForms notices, standard eForms `buyer-legal-type` codes apply. For national notices, Danish-language equivalents may appear:

| Danish Term | eForms Code | Notes |
|---|---|---|
| Statslig myndighed | `cga` | Central government authority |
| Regional myndighed | `ra-aut` | Regional authority |
| Kommunal myndighed | `la` | Local authority (municipality) |
| Offentligretligt organ | `body-public` | Body governed by public law |
| Offentlig virksomhed | `pub-undert` | Public undertaking |
| Forsyningsvirksomhed | `spec-rights-entity` | Utilities / entity with special rights |

**Note**: The exact code values used by udbud.dk are unknown. The table above assumes Danish-language labels; the actual backend may use numeric codes, eForms codes directly, or a different coding scheme entirely. Verification against real data is required.

#### Contract Nature Codes

| Likely Portal Value | eForms Code | Notes |
|---|---|---|
| Bygge- og anlægsarbejder / Bygge- og anlæg | `works` | Works |
| Varer / Varekøb | `supplies` | Supplies |
| Tjenesteydelser | `services` | Services |

These are straightforward. If the portal uses eForms codes natively (for EU-threshold notices), no mapping is needed. For national notices, the Danish terms above are the standard vocabulary.

### Implementation Recommendations

1. **Reverse-engineer the frontend API first**: Open `https://udbud.dk/arkiv` in a browser with DevTools Network tab open. Search for awarded contract notices ("Bekendtgørelse om indgåede kontrakter" or filter by notice type). Document:
   - The API base URL (likely `api.udbud.dk` or an internal path)
   - The search/list endpoint URL, request method, and parameters (pagination, date filters, notice type filters)
   - The detail endpoint URL and response format
   - Authentication requirements (cookies, tokens, API keys)
   - Rate limits (observe response headers)
   - Sample JSON response structure for awarded contract notices

2. **Check if eForms XML is accessible**: Since EU-threshold notices must be in eForms format, the backend may store the original eForms XML. Check whether the detail API returns or links to the underlying XML document. If so, the existing `eforms_ubl.py` parser can be reused for EU-threshold notices.

3. **Prioritize EU-threshold notices with national extras**: Start by scraping EU-threshold awarded contract notices (which will have the richest data due to eForms requirements). Add national below-threshold notices as a second phase, accepting that these will have more `None` fields.

4. **Deduplication with TED**: EU-threshold notices from udbud.dk will overlap with TED data. The `noticePublicationNumber` URL parameter appears to contain TED publication numbers -- use this for deduplication. Skip any notice that already exists in the database via the TED portal import.

5. **doc_id namespacing**: Use a `DK-` prefix for udbud.dk-sourced `doc_id` values to prevent primary key collisions with TED-sourced documents, e.g. `DK-{noticeId_uuid}`.

6. **Fragility warning**: Since there is no documented API contract, any scraping approach is inherently fragile. The frontend SPA and its backend API can change without notice. The implementing parser should include robust error handling, detailed logging of unexpected response formats, and version/format detection to fail loudly when the portal changes.

7. **Consider contacting KFST**: The Danish Competition and Consumer Authority (KFST) operates udbud.dk. Before investing in reverse-engineering, consider contacting them to ask about:
   - Whether a public API is planned or already exists (undocumented)
   - Whether bulk data exports are available on request
   - Whether they publish to data.gov.dk or another open data portal
   - Contact: https://en.kfst.dk/public-procurement
