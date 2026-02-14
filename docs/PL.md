# Poland (PL)

**Feasibility: Tier 1**

## Portal

- **Name**: e-Zamowienia / BZP (Biuletyn Zamowien Publicznych)
- **URL**: https://ezamowienia.gov.pl/en/ (platform) / https://bzp.uzp.gov.pl/ (bulletin)
- **API**: http://ezamowienia.gov.pl/mo-board/api/v1/notice
- **WebService**: https://bzp.uzp.gov.pl/WebService.aspx
- **Search**: https://searchbzp.uzp.gov.pl/
- **Integration docs**: https://ezamowienia.gov.pl/pl/integracja/

## Data Access

- **Method**: REST API for reading notices and statistics (no auth for read-only)
- **Format**: JSON
- **Auth**: Open for reading; integration tests required for write APIs
- **OCDS**: No

## Coverage

All domestic procurement notices published in BZP (below EU thresholds). Since Jan 2022, BZP is integrated into e-Zamowienia.

## Language

Polish

## Notes

- Public API, no auth for reading, well-structured
- Documentation in Polish but API is straightforward
- WebService also available at bzp.uzp.gov.pl
- Legacy SOAP WebService also at http://websrv.bzp.uzp.gov.pl/BZP_PublicWebService.asmx (pre-2022 notices)
- Uses OCDS identifiers internally (prefix `ocds-148610`) despite not publishing full OCDS packages
- Notice types relevant to us: **Ogłoszenie o wyniku postępowania** (Result of Procedure Notice) — equivalent to contract award notice

## API Details

### Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /mo-board/api/v1/notice` | Search/list notices (requires `NoticeType`, `PublicationDateFrom`, `PublicationDateTo`) |
| `GET /mo-board/api/v1/Board/GetNoticePdfById?noticeId={uuid}` | Get notice as PDF |
| `GET /mo-client-board/api/notices/` | WebService endpoint (OAuth 2.0 required) |

### Query Parameters (mo-board/api/v1/notice)

Confirmed by API error messages (400 response lists required fields):

- `NoticeType` (required) — notice type filter
- `PublicationDateFrom` (required) — start date for publication range
- `PublicationDateTo` (required) — end date for publication range
- `PageSize` — pagination size
- `PageNumber` — pagination offset (0-based)

### Notice Types

The relevant notice type for award data is the **Ogłoszenie o wyniku postępowania** (Result of Procedure Notice). The exact `NoticeType` enum value needs to be discovered by querying the API. Likely candidates: `ContractAward`, `ResultNotice`, or a Polish-language equivalent. **The implementing agent must call the API and inspect error messages or try common values to determine the correct enum.**

### Rate Limits

Not documented. The API is described as free and open for reading. Standard politeness (1-2 req/sec) should be applied until limits are discovered empirically.

## Regulatory Context

Notice content is defined by Rozporządzenie Ministra Rozwoju, Pracy i Technologii z dnia 23 grudnia 2020 r. (Dz.U. 2020 poz. 2439). Attachment No. 3 specifies the fields for "ogłoszenie o wyniku postępowania" (result of procedure notice). This regulation guarantees that the following categories of data exist in every result notice:

- Contracting authority identification (name, address, NIP/REGON, contact)
- Procedure type and legal basis
- Subject of procurement (title, description, CPV codes)
- Whether the contract was divided into lots
- Contract value (estimated and awarded)
- Winning contractor(s) (name, address, NIP/REGON)
- Number of tenders received
- Whether the procedure was cancelled (per lot)

## Schema Mapping

### Important Caveats

**The exact JSON field names returned by the BZP API are not publicly documented.** The API documentation is contained in internal attachments to the API Usage Regulation (Załącznik nr 3) and the Developer Portal (Portal Deweloperski), which are not indexed by search engines. The field names below are **best-effort guesses** based on:
1. The legally mandated notice fields (Dz.U. 2020 poz. 2439, Attachment 3)
2. Common .NET API naming conventions (the backend is ASP.NET Core based on error response format)
3. Observed URL patterns and query parameter names

**The implementing agent MUST perform API exploration as the first step**: call the search endpoint with valid parameters for a small date range, inspect the response JSON, and update this mapping with actual field names before writing any parser code.

### DocumentModel

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `doc_id` | Notice UUID (e.g. `08d96208-4f81-5055-2212-d80001663ad1`) or BZP number (e.g. `2025/BZP 00004819/01`) | The portal uses GUIDs as `noticeId` in URLs. BZP numbers follow the format `YYYY/BZP NNNNNNN/VV`. Use BZP number as `doc_id` for human readability, prefixed with `PL-BZP-`. |
| `edition` | Derive from `PublicationDate` | No direct equivalent; set to `None` or derive from publication date. |
| `version` | Notice version number (visible in URL as `/01`, `/02`, etc.) | BZP notices can have versions. Use the version from the BZP number. |
| `reception_id` | `None` | No equivalent in BZP. |
| `official_journal_ref` | BZP number (e.g. `2025/BZP 00004819/01`) | This is the canonical reference for BZP notices. |
| `publication_date` | Publication date field | Required query parameter; will be in the response. |
| `dispatch_date` | `None` | BZP is the publisher, so there is no separate dispatch date. Set to same as `publication_date` or `None`. |
| `source_country` | Hardcode `"PL"` | All BZP notices are Polish domestic procurement. |
| `contact_point` | Contracting authority contact person name | Legally required in the notice. |
| `phone` | Contracting authority phone number | Legally required in the notice. |
| `email` | Contracting authority email | Legally required in the notice. |
| `url_general` | Contracting authority website URL | Legally required in the notice. |
| `url_buyer` | `None` | No buyer profile URL concept in BZP. |

### ContractingBodyModel

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `official_name` | Contracting authority name | Legally required. Likely a top-level field or under a section object. |
| `address` | Contracting authority street address | Legally required. |
| `town` | Contracting authority city/town | Legally required. |
| `postal_code` | Contracting authority postal code | Legally required. |
| `country_code` | Hardcode `"PL"` | All BZP contracting authorities are in Poland. |
| `nuts_code` | `None` | **BZP does not use NUTS codes.** Polish domestic notices use voivodeship (województwo) instead. See "Extra portal fields" below. |
| `authority_type` | Authority type field | Legally required in BZP notices. See "Code normalization" section below for mapping. |
| `main_activity_code` | `None` | **Not a standard BZP field.** This is a TED/eForms concept. BZP may have a field for "sector" but it does not map cleanly. Set to `None`. |

### ContractModel

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `title` | Subject of procurement / order name | Legally required. The main title of the procurement. |
| `short_description` | Short description of the subject | Legally required. |
| `main_cpv_code` | Main CPV code | Legally required. BZP uses standard EU CPV codes. |
| `cpv_codes` | List of CPV codes (main + additional) | Legally required. Both main and supplementary CPV codes are present. |
| `nuts_code` | `None` | **BZP does not use NUTS codes for performance location.** See "Extra portal fields" for the Polish location equivalent. |
| `contract_nature_code` | Type of order (Rodzaj zamówienia) | Legally required. Values are: Roboty budowlane (works), Dostawy (supplies), Usługi (services). See "Code normalization" below. |
| `procedure_type` | Procedure type (Tryb udzielenia zamówienia) | Legally required. See "Code normalization" below. |
| `accelerated` | `False` | **BZP below-threshold procedures do not have an accelerated variant.** Hardcode `False`. |

### AwardModel

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `award_title` | Lot title (Nazwa części) | If the contract is divided into lots (części), each lot has a title. For undivided contracts, use the main contract title. |
| `contract_number` | Lot number (Numer części) or contract/order number | May be the lot number if divided, or a contract reference number. |
| `tenders_received` | Number of tenders received (Liczba otrzymanych ofert) | Legally required per lot/contract. |
| `awarded_value` | Awarded contract value (Cena wybranej oferty / wartość umowy) | Legally required. The notice includes both the estimated value and the actual awarded value. Use the awarded/contract value, not the estimate. |
| `awarded_value_currency` | Hardcode `"PLN"` | BZP below-threshold contracts are overwhelmingly in PLN. However, check if the notice includes a currency field — some contracts may use EUR. If no explicit currency field exists, default to `"PLN"`. |
| `contractors` | List of winning contractors (Wykonawcy) | See ContractorModel below. |

### ContractorModel

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `official_name` | Contractor name (Nazwa wykonawcy) | Legally required. |
| `address` | Contractor street address (Ulica) | Legally required. |
| `town` | Contractor city (Miejscowość) | Legally required. |
| `postal_code` | Contractor postal code (Kod pocztowy) | Legally required. |
| `country_code` | Contractor country or hardcode `"PL"` | Most contractors are Polish. There may be a country field for foreign contractors. |
| `nuts_code` | `None` | **BZP does not use NUTS codes.** |

### CpvCodeEntry

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `code` | CPV code string (e.g. `45000000-7`) | Standard EU CPV codes; directly usable. |
| `description` | CPV description (Polish) | May be included in the notice or can be derived from a CPV lookup table. |

### ProcedureTypeEntry

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `code` | Mapped eForms code (see Code normalization) | Must be mapped from BZP procedure type values. |
| `description` | Mapped description | Use the standard eForms descriptions from `_PROCEDURE_TYPE_DESCRIPTIONS`. |

### AuthorityTypeEntry

| Schema Field | Portal Field/Path (estimated) | Notes |
|---|---|---|
| `code` | Mapped eForms code (see Code normalization) | Must be mapped from BZP authority type values. |
| `description` | Mapped description | Use the standard eForms descriptions from `_AUTHORITY_TYPE_DESCRIPTIONS`. |

### Unmappable Schema Fields

The following schema fields have no equivalent in BZP and should be set to `None`:

| Schema Field | Reason |
|---|---|
| `document.edition` | No OJ edition concept in BZP. |
| `document.reception_id` | No reception ID concept. |
| `document.url_buyer` | No buyer profile URL in BZP. |
| `contracting_body.nuts_code` | BZP uses Polish administrative divisions (województwo), not NUTS codes. Could be derived via a mapping table (województwo -> NUTS PL code) but this is not direct. |
| `contracting_body.main_activity_code` | Not a standard BZP field. |
| `contract.nuts_code` | Same as above — no NUTS codes in BZP. |
| `contract.accelerated` | Below-threshold procedures have no accelerated variant. Hardcode `False`. |
| `contractor.nuts_code` | Same as above. |

### Extra Portal Fields

The following BZP fields are potentially interesting but not covered by the current schema. Flagged for review:

| Portal Field | Description | Notes |
|---|---|---|
| NIP / REGON | National tax ID (NIP) and statistical ID (REGON) of contracting authority and contractors | **Schema doesn't cover** — flagging for review. Unique entity identifiers far more reliable than name-matching for deduplication. |
| Województwo (Voivodeship) | Polish administrative region of contracting authority and place of performance | Schema doesn't cover — flagging for review. Could be mapped to NUTS-2 codes (e.g. Mazowieckie -> PL9). |
| Estimated contract value (Wartość zamówienia) | The pre-award estimated value, separate from the awarded value | Schema doesn't cover — flagging for review. Useful for price analysis. |
| Whether procedure was cancelled (Unieważnienie) | Per-lot cancellation status and reason | Schema doesn't cover — flagging for review. Important for data completeness. |
| Number of lots (Podział na części) | Whether and how the contract is divided into lots | Schema doesn't cover — flagging for review. Affects how awards map to the contract. |
| Date of contract conclusion (Data zawarcia umowy) | When the contract was actually signed | Schema doesn't cover — flagging for review. |
| Subcontracting information | Whether subcontracting is involved | Schema doesn't cover — flagging for review. |
| Legal basis (Podstawa prawna) | Specific article of the Public Procurement Law | Schema doesn't cover — flagging for review. |
| OCDS identifier | e-Zamówienia assigns OCDS IDs (prefix `ocds-148610`) | Schema doesn't cover — flagging for review. Could link to TED publications of the same procedure. |
| VAT information | Whether values include/exclude VAT | Schema doesn't cover — flagging for review. Critical for value comparisons (TED values are typically net). |
| Joint procurement | Whether the procurement is conducted jointly by multiple contracting authorities | Schema doesn't cover — flagging for review. |

### Code Normalization

#### Contract Nature Codes (Rodzaj zamówienia)

BZP uses Polish-language labels for contract nature. Map to eForms codes:

| BZP Value | eForms Code | Notes |
|---|---|---|
| `Roboty budowlane` | `works` | Construction works |
| `Dostawy` | `supplies` | Supply contracts |
| `Usługi` | `services` | Service contracts |

**Note:** The exact string values may differ in the API response (could be enum codes rather than Polish text). The implementing agent must inspect actual API responses to determine the format.

#### Procedure Types (Tryb udzielenia zamówienia)

BZP below-threshold procedure types per the Polish Public Procurement Law (Prawo zamówień publicznych, 2019):

| BZP Procedure Type (Polish) | eForms Code | Notes |
|---|---|---|
| Tryb podstawowy (wariant 1 — bez negocjacji) | `open` | Basic mode without negotiation — closest to open procedure |
| Tryb podstawowy (wariant 2 — z możliwością negocjacji) | `open` | Basic mode with optional negotiation — still closest to open |
| Tryb podstawowy (wariant 3 — z negocjacjami) | `neg-w-call` | Basic mode with mandatory negotiation |
| Zamówienie z wolnej ręki | `neg-wo-call` | Single-source / negotiated without competition |
| Partnerstwo innowacyjne | `innovation` | Innovation partnership |
| Negocjacje bez ogłoszenia | `neg-wo-call` | Negotiated procedure without prior publication |
| Przetarg nieograniczony | `open` | Unlimited (open) tender — used above threshold but may appear |
| Przetarg ograniczony | `restricted` | Restricted tender |
| Dialog konkurencyjny | `comp-dial` | Competitive dialogue |
| Negocjacje z ogłoszeniem | `neg-w-call` | Negotiated procedure with prior publication |

**Note:** "Tryb podstawowy" (basic mode) is the most common below-threshold procedure in Poland since 2021. It has three variants depending on whether negotiation is allowed. The exact representation in the API (enum code vs. Polish text vs. numeric code) must be determined by inspecting actual responses. The mappings above are best-effort — the implementing agent should validate these against real data.

#### Authority Types (Rodzaj zamawiającego)

BZP authority types per Polish law:

| BZP Authority Type (Polish) | eForms Code | Notes |
|---|---|---|
| Jednostka sektora finansów publicznych — organ władzy publicznej (w tym administracja rządowa, organy kontroli państwowej i ochrony prawa oraz sądy i trybunały) | `cga` | Central government authority |
| Jednostka sektora finansów publicznych — jednostka samorządu terytorialnego | `ra` or `la` | Regional/local authority — need to check if BZP distinguishes regional vs. local |
| Jednostka sektora finansów publicznych — związek jednostek samorządu terytorialnego | `ra` | Association of local authorities |
| Jednostka sektora finansów publicznych — jednostka budżetowa | `body-pl` | Budgetary unit — body governed by public law |
| Jednostka sektora finansów publicznych — uczelnia publiczna | `body-pl` | Public university |
| Zamawiający publiczny — inna państwowa jednostka organizacyjna nieposiadająca osobowości prawnej | `body-pl` | Other state organizational unit |
| Zamawiający publiczny — osoba prawna utworzona w celu zaspokajania potrzeb o charakterze powszechnym | `body-pl` | Entity created to meet public-interest needs |
| Inny zamawiający | `None` | Other — no clear eForms mapping |

**Note:** The Polish authority type classification is more granular than the eForms system. The mappings above are approximate. The exact BZP values (whether text, codes, or enums) must be discovered from actual API responses. Some categories may not map cleanly — these should log a warning and return `None` per the project's fail-loud principle.

### Data Format Notes

- **Format**: JSON (REST API responses)
- **Encoding**: UTF-8
- **Language**: All text content is in Polish
- **Dates**: Expected ISO 8601 format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`) based on the .NET backend
- **Monetary values**: Expected as numeric values (float/decimal). Currency is almost always PLN for below-threshold contracts. Check if values include or exclude VAT — Polish notices typically report gross (with VAT) values, whereas TED values are typically net
- **Pagination**: Page-based (`PageNumber` + `PageSize` query parameters). 0-indexed
- **Notice IDs**: GUIDs (e.g. `08d96208-4f81-5055-2212-d80001663ad1`); BZP numbers (e.g. `2025/BZP 00004819/01`)
- **Multi-lot contracts**: A single notice may contain multiple lots (części), each with its own award/cancellation outcome. The parser must iterate over lots and produce one `AwardModel` per awarded lot
- **Cancelled lots**: Lots can be individually cancelled within a notice. The parser should skip cancelled lots (no contractor, no award value) rather than creating empty AwardModel entries
- **Error responses**: ASP.NET Core validation errors return JSON with `errors`, `type`, `title`, `status`, `traceId` fields — useful for discovering required parameters

### Implementation Strategy

1. **API exploration (first step)**: Call `GET https://ezamowienia.gov.pl/mo-board/api/v1/notice` with valid required parameters for a 1-day range. Inspect the full response JSON and update this mapping with actual field names.
2. **Discover notice type enum**: Try common values for `NoticeType` parameter or inspect validation error messages to learn valid values.
3. **Paginated scraping by date range**: Iterate day-by-day (or week-by-week) through the date range, paginating through results. BZP publishes ~250 working days/year with potentially hundreds of result notices per day.
4. **Detail fetching**: Determine whether the search endpoint returns full notice details or just summaries. If summaries only, a second API call per notice may be needed to fetch the full record.
5. **Deduplication**: Use the BZP number as the canonical `doc_id` (format: `PL-BZP-YYYY-NNNNNNN-VV`). Higher version numbers supersede lower ones for the same base number.
6. **Województwo to NUTS mapping**: If contracting body location is important, build a static mapping table from Polish voivodeships to NUTS-2 codes (16 entries).
