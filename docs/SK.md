# Slovakia (SK)

**Feasibility: Tier 2**

## Portal

- **Name**: UVO (Public Procurement Office)
- **URL**: https://www.uvo.gov.sk/
- **Open data**: Available via data.gov.sk and slovensko.digital

## Data Access

- **Method**: Open data portal; SQL dumps available from slovensko.digital
- **Format**: CSV, SQL dump
- **Auth**: Open
- **OCDS**: No

## Coverage

Over 2 million contracts published online. All public procurement.

## Language

Slovak

## Notes

- ~10% of published contracts have at least one key piece of information missing
- Data quality is a concern
- Community resources: https://ekosystem.slovensko.digital/otvorene-data (structured data with REST/SQL API)

## Schema Mapping

### Data Source Assessment

Slovakia does **not** have a single well-documented public API with a published schema for procurement data. The situation is fragmented across multiple sources, none of which provide a clean, documented, machine-readable feed equivalent to what Tier 1 countries offer. The viable options, in order of recommendation, are:

1. **UVOstat.sk API** (https://www.uvostat.sk/api) -- Third-party structured API built on top of UVO data. Requires an API token (request via their site). Returns JSON. Covers completed procurements (`/api/ukoncene_obstaravania`). Pagination via `limit` param (max 100). Documentation: https://github.com/MiroBabic/uvostat_api. **This is the recommended primary data source** because it provides structured JSON with procurement-specific fields.

2. **OpenTender/OCDS bulk download** (https://data.open-contracting.org/en/publication/88) -- DIGIWHIST project converts UVO data to OCDS JSONL. Available by year. Includes below-threshold contracts. However, this is a **derived** dataset maintained by a third party (Government Transparency Institute), with unknown update frequency and potential lag. It mixes national data with TED data.

3. **UVO Vestnik (official bulletin)** (https://www.uvo.gov.sk/vestnik-590.html) -- The primary source of truth. Since ~2024, Slovakia's vestnik uses **eForms** format for new notices. Older notices use a proprietary HTML format. No documented bulk download API -- would require HTML scraping of individual notice pages or reverse-engineering the vestnik search interface.

4. **slovensko.digital SQL dumps** (https://ekosystem.slovensko.digital/otvorene-data) -- Weekly PostgreSQL dumps of harvested data. REST and SQL API available. Structured but documentation on the procurement-specific schema (table names, column definitions) is sparse.

**Recommendation**: Start with the **UVOstat API** as the primary source for structured data. Fall back to **OpenTender OCDS** bulk downloads if the UVOstat API proves too rate-limited or if API token access is difficult to obtain. The UVO Vestnik eForms path is a future option once eForms coverage matures.

### Data Format Notes

- **UVOstat API**: JSON responses. Paginated (max 100 records per request). Requires `ApiToken` header for authentication. Filter by date range (`datum_zverejnenia_od`/`datum_zverejnenia_do`), CPV codes, and procurer ID. Example endpoint: `GET https://www.uvostat.sk/api/ukoncene_obstaravania?limit=100&datum_zverejnenia_od=2024-01-01`.
- **OpenTender OCDS**: Gzipped JSONL files (`.jsonl.gz`). One JSON object per line, each representing a contracting process. OCDS 1.1 format with lots/bids extensions.
- **Currency**: Slovakia uses EUR (Eurozone member since 2009). All values should be in EUR.
- **Language**: All data is in Slovak. Field values (titles, descriptions, organization names) are Slovak-language strings.
- **Data quality**: ~10% of records have at least one key field missing according to portal documentation. Expect `None` values frequently.

### Field Mapping: UVOstat API (Primary Path)

The UVOstat API documentation (https://github.com/MiroBabic/uvostat_api) lists the following response fields for the `/api/ukoncene_obstaravania` endpoint. **Important caveat**: The full response schema is not exhaustively documented in public sources. The field names below are reconstructed from partial documentation, search result excerpts, and the UVOstat web UI. **An implementer must fetch a sample API response to verify exact field names and nesting before coding the parser.**

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `id` or `order_id` | UVOstat internal ID. Use as the document identifier, prefixed with `"SK-UVO-"` to avoid collisions with TED doc_ids. Exact field name needs verification. |
| `edition` | `None` | No equivalent concept in UVOstat. Set to `None`. |
| `version` | (hardcoded) | Set to `"UVOstat-JSON"` to identify the source format. |
| `reception_id` | `None` | TED-specific concept. Not available. Set to `None`. |
| `official_journal_ref` | `None` | National notices have no OJ reference. Set to `None`. |
| `publication_date` | `datum_zverejnenia` | Publication date. Exact date format needs verification (likely `YYYY-MM-DD` or ISO 8601). |
| `dispatch_date` | `None` | Not available in UVOstat. Set to `None`. |
| `source_country` | (hardcoded `"SK"`) | All UVO notices are Slovak. Hardcode `"SK"`. |
| `contact_point` | Not documented | **Needs verification against sample response.** May not be available. Likely `None`. |
| `phone` | Not documented | **Needs verification.** Likely `None`. |
| `email` | Not documented | **Needs verification.** Likely `None`. |
| `url_general` | `order_url` | URL to the original UVO notice. Exact field name needs verification. |
| `url_buyer` | `None` | Not available. Set to `None`. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `obstaravatel_meno` | Procurer name. Slovak-language string. |
| `address` | Not documented | **Needs verification.** The API may not include full address details for the procurer. Likely `None` from this endpoint; may need a separate `/api/obstaravatelia/{id}` call. |
| `town` | Not documented | Same as above. Likely `None` from the main endpoint. |
| `postal_code` | Not documented | Same as above. Likely `None`. |
| `country_code` | (hardcoded `"SK"`) | Slovak procurers. Hardcode `"SK"` or `None` if non-SK procurers exist. |
| `nuts_code` | Not documented | **Needs verification.** Likely `None`. |
| `authority_type` | Not documented | UVOstat does not appear to expose the authority type classification. Set to `None`. |
| `main_activity_code` | Not documented | Not available. Set to `None`. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `nazov` | Procurement title/name. Slovak-language string. |
| `short_description` | `popis` | Description of the procurement. Slovak-language. May be `None`. |
| `main_cpv_code` | `cpv` | CPV code. UVOstat supports CPV filtering and returns CPV codes. Exact format needs verification (may be a single code string like `"45000000-7"` or a list). |
| `cpv_codes` | `cpv` | If the API returns multiple CPV codes, extract all. Otherwise, use the single `cpv` value as both main and only entry. **Needs verification of whether additional CPV codes are included.** |
| `nuts_code` | Not documented | **Needs verification.** Likely `None`. |
| `contract_nature_code` | `typ` | Type of contract. **Needs mapping** -- the UVOstat `typ` field likely uses Slovak-language labels or UVO-internal codes (e.g., `"Tovary"` = supplies, `"Stavebne prace"` = works, `"Sluzby"` = services). See Code Normalization below. |
| `procedure_type` | Not directly documented | **Needs verification.** May be available as a field in the response or may need to be scraped from the linked UVO notice. The `formular` field indicates form type but not procedure type. |
| `accelerated` | Not available | UVOstat does not expose this field. Always set to `False`. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `nazov` | Same as contract title. UVOstat may not distinguish award-level titles. |
| `contract_number` | `znacka` | Reference/mark number. **Needs verification.** May also be `order_id`. |
| `tenders_received` | Not directly documented | **Needs verification against sample response.** The UVOstat web UI shows "pocet ponuk" (number of offers) which is calculated. Check if the API response includes this. |
| `awarded_value` | `rozsah` or `rozsah_do` | Value range or final value. The API appears to return `rozsah` (range), `rozsah_od` (range from), and `rozsah_do` (range to). **Needs verification** -- for award value, `rozsah_do` (upper bound) or a separate final value field may be appropriate. The `zmluvy` (contracts) sub-object may contain the actual awarded value. |
| `awarded_value_currency` | `mena` | Currency code. Should always be `"EUR"` for Slovakia. |
| `contractors` | `zmluvy` (contracts sub-object) | The `zmluvy` field contains contract details including supplier information. **Structure needs verification.** Likely contains `dodavatel_meno` (supplier name) and possibly `dodavatel_ico` (supplier registration number). |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `zmluvy[].dodavatel_meno` or similar | Supplier name from the contracts sub-object. **Exact path needs verification.** |
| `address` | Not documented | **Needs verification.** Likely `None` from this endpoint. |
| `town` | Not documented | **Needs verification.** Likely `None`. |
| `postal_code` | Not documented | **Needs verification.** Likely `None`. |
| `country_code` | Not documented | **Needs verification.** Default to `None`. |
| `nuts_code` | Not documented | **Needs verification.** Likely `None`. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `cpv` | CPV code string. |
| `description` | Not available from API | `None`. CPV descriptions would need a local lookup table. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Unknown | **Needs verification.** If the API returns a procedure type field, it will need mapping to eForms codes. See Code Normalization. |
| `description` | Unknown | **Needs verification.** May contain Slovak-language procedure description. |

#### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Not available | UVOstat does not appear to expose authority type. Set to `None`. |
| `description` | Not available | Set to `None`. |

### Field Mapping: OpenTender OCDS (Fallback Path)

If the UVOstat API proves unworkable, the OpenTender OCDS data follows the same OCDS 1.1 format as the Italy (IT) mapping. The mapping below highlights Slovakia-specific considerations. Refer to the IT.md OCDS mapping for the general pattern.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `ocid` | OpenTender OCDS identifier. Prefix varies. |
| `edition` | `None` | No OCDS equivalent. |
| `version` | (hardcoded `"OCDS-1.1"`) | |
| `reception_id` | `None` | Not in OCDS. |
| `official_journal_ref` | `None` | Not in OCDS for national notices. |
| `publication_date` | `date` | Release date. |
| `dispatch_date` | `None` | Not in OCDS. |
| `source_country` | (hardcoded `"SK"`) | Filter out non-SK releases if the dataset mixes TED data. |
| `contact_point` | `parties[role=buyer].contactPoint.name` | If present. |
| `phone` | `parties[role=buyer].contactPoint.telephone` | If present. |
| `email` | `parties[role=buyer].contactPoint.email` | If present. |
| `url_general` | `parties[role=buyer].contactPoint.url` | If present. |
| `url_buyer` | `None` | Not in OCDS. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[role=buyer].name` | Organization name in Slovak. |
| `address` | `parties[role=buyer].address.streetAddress` | |
| `town` | `parties[role=buyer].address.locality` | |
| `postal_code` | `parties[role=buyer].address.postalCode` | |
| `country_code` | `parties[role=buyer].address.countryName` | Free-text country name. Needs mapping to ISO 3166-1 alpha-2. Usually `"Slovensko"` or `"Slovakia"` -> `"SK"`. |
| `nuts_code` | `None` | Not in standard OCDS. |
| `authority_type` | `None` | Not in standard OCDS. |
| `main_activity_code` | `None` | Not in standard OCDS. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `tender.title` | Slovak-language title. |
| `short_description` | `tender.description` | Slovak-language description. |
| `main_cpv_code` | `tender.items[0].classification.id` | Where `scheme == "CPV"`. |
| `cpv_codes` | `tender.items[*].classification` + `additionalClassifications` | Collect all CPV codes. |
| `nuts_code` | `None` | Not in standard OCDS. |
| `contract_nature_code` | `tender.mainProcurementCategory` | OCDS values: `"goods"`, `"works"`, `"services"`. Needs mapping (see Code Normalization). |
| `procedure_type` | `tender.procurementMethod` | OCDS values: `"open"`, `"selective"`, `"limited"`, `"direct"`. Needs mapping (see Code Normalization). |
| `accelerated` | `False` | No OCDS equivalent. Always `False`. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `awards[i].title` | May not be populated. |
| `contract_number` | `awards[i].id` | Award identifier. |
| `tenders_received` | `tender.numberOfTenderers` | Tender-level, not per-award. |
| `awarded_value` | `awards[i].value.amount` | |
| `awarded_value_currency` | `awards[i].value.currency` | Should be `"EUR"`. |
| `contractors` | `awards[i].suppliers` | Array of organization references. Look up in `parties` by ID. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[supplier_id].name` | |
| `address` | `parties[supplier_id].address.streetAddress` | |
| `town` | `parties[supplier_id].address.locality` | |
| `postal_code` | `parties[supplier_id].address.postalCode` | |
| `country_code` | `parties[supplier_id].address.countryName` | Needs ISO mapping. |
| `nuts_code` | `None` | Not in OCDS. |

### Unmappable Schema Fields

The following schema fields cannot be populated from either data source and should be set to `None`:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | TED OJ edition concept. No equivalent in UVOstat or OCDS. |
| `DocumentModel.reception_id` | TED-specific reception identifier. Not available. |
| `DocumentModel.official_journal_ref` | National notices have no OJ reference. |
| `DocumentModel.dispatch_date` | TED-specific dispatch date. Not available. |
| `DocumentModel.url_buyer` | No buyer profile URL in either source. |
| `DocumentModel.contact_point` | **Likely `None`** from UVOstat (not documented). May be available in OCDS path. |
| `DocumentModel.phone` | **Likely `None`** from UVOstat. May be available in OCDS path. |
| `DocumentModel.email` | **Likely `None`** from UVOstat. May be available in OCDS path. |
| `ContractingBodyModel.nuts_code` | Not documented in UVOstat. Not in standard OCDS. |
| `ContractingBodyModel.authority_type` | Not available in UVOstat. Not in standard OCDS. |
| `ContractingBodyModel.main_activity_code` | Not available in either source. |
| `ContractModel.nuts_code` | Not documented in UVOstat. Not in standard OCDS. |
| `ContractModel.accelerated` | Not available. Always `False`. |
| `ContractorModel.address` | **Likely `None`** from UVOstat. May be available in OCDS path. |
| `ContractorModel.town` | Same as above. |
| `ContractorModel.postal_code` | Same as above. |
| `ContractorModel.country_code` | Same as above. |
| `ContractorModel.nuts_code` | Not available in either source. |
| `CpvCodeEntry.description` | Not available from UVOstat API. OCDS may include it. |
| `ProcedureTypeEntry.description` | Not documented in UVOstat. |
| `AuthorityTypeEntry.code` | Not available from either source. |
| `AuthorityTypeEntry.description` | Not available. |

### Extra Portal Fields

The following fields are available in the portal data but not covered by the current schema. Flagging for review.

#### UVOstat API

| Portal Field | Description | Notes |
|---|---|---|
| `obstaravatel_id` | Internal UVOstat procurer ID | Schema doesn't cover -- flagging for review. Useful for linking multiple procurements by the same entity. |
| `obstaravatel_ico` / `dodavatel_ico` | Slovak ICO (company registration number) | Schema doesn't cover -- flagging for review. **Very valuable** for entity deduplication. ICO is an 8-digit national identifier unique to each legal entity. |
| `eaukcia` | Whether an electronic auction was used | Schema doesn't cover -- flagging for review. |
| `eufondy` | Whether EU funds were used | Schema doesn't cover -- flagging for review. Useful for EU fund analysis. |
| `uspesne` | Whether the procurement was successful | Schema doesn't cover -- flagging for review. Could be used to filter out cancelled/unsuccessful procurements. |
| `rozdelenie_na_casti` | Whether the procurement was divided into lots | Schema doesn't cover lot structure -- flagging for review. |
| `phz` | Estimated value (predpokladana hodnota zakazky) | Schema doesn't cover estimated value -- flagging for review. |
| `opcie` | Options included | Schema doesn't cover -- flagging for review. |
| `ramcova_dohoda` | Framework agreement indicator | Schema doesn't cover -- flagging for review. |
| `kriteria` / `kriteria_list` | Award criteria details | Schema doesn't cover -- flagging for review. |
| `formular` | Form type identifier | Schema doesn't cover -- flagging for review. Useful for identifying notice types. |
| `eks_id` | Electronic marketplace (EKS) identifier | Schema doesn't cover -- flagging for review. |
| `zaznam_vytvoreny` / `zaznam_aktualizovany` | Record creation/update timestamps | Schema doesn't cover -- flagging for review. Useful for incremental imports. |

#### OpenTender OCDS (same extras as IT.md)

| Portal Field | Description | Notes |
|---|---|---|
| `tender.id` | National tender identifier | Schema doesn't cover -- flagging for review. |
| `parties[].identifier.id` / `.scheme` | Organization identifiers (Slovak ICO) | Schema doesn't cover structured organization identifiers -- flagging for review. |
| `awards[].status` | Award status (active, cancelled, etc.) | Schema doesn't cover -- flagging for review. |
| `awards[].date` | Award decision date | Schema doesn't cover -- flagging for review. |
| `contracts[].period` | Contract execution period | Schema doesn't cover -- flagging for review. |
| `tender.value` | Estimated tender value | Schema doesn't cover -- flagging for review. |

### Code Normalization

#### Contract Nature Codes (to eForms `contract-nature-types`)

**UVOstat API path**: The `typ` field likely uses Slovak-language labels or UVO-internal codes. Mapping:

| UVOstat Value (expected) | eForms Code | Notes |
|---|---|---|
| `"Tovary"` or `"Dodanie tovaru"` | `"supplies"` | Goods/supplies |
| `"Stavebne prace"` or `"Stavebné práce"` | `"works"` | Construction works |
| `"Sluzby"` or `"Služby"` | `"services"` | Services |

**Important**: The exact values in the `typ` field need verification against a sample API response. The values may be abbreviations, codes, or full Slovak labels with diacritics.

**OCDS path**: Same mapping as IT.md:

| OCDS Value | eForms Code |
|---|---|
| `"goods"` | `"supplies"` |
| `"works"` | `"works"` |
| `"services"` | `"services"` |

#### Procedure Type Codes (to eForms `procurement-procedure-type`)

**UVOstat API path**: The API may not directly expose procedure type. If it does, expect Slovak-language values from UVO form types:

| UVO/Slovak Value (expected) | eForms Code | Notes |
|---|---|---|
| `"Verejná súťaž"` | `"open"` | Open procedure |
| `"Užšia súťaž"` | `"restricted"` | Restricted procedure |
| `"Rokovacie konanie so zverejnením"` | `"neg-w-call"` | Negotiated with prior publication |
| `"Priame rokovacie konanie"` | `"neg-wo-call"` | Negotiated without prior publication |
| `"Súťažný dialóg"` | `"comp-dial"` | Competitive dialogue |
| `"Inovatívne partnerstvo"` | `"innovation"` | Innovation partnership |

**Important**: These Slovak procedure type labels need verification. The API may use abbreviations or internal codes instead of full labels.

**OCDS path**: Same lossy mapping as IT.md:

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"open"` | `"open"` | Direct match |
| `"selective"` | `"restricted"` | Best approximation |
| `"limited"` | `"neg-wo-call"` | Covers negotiated without publication |
| `"direct"` | `"neg-wo-call"` | Direct award |

#### Authority Type Codes

Not available from either data source. No mapping needed.

#### Country Codes

**OCDS path**: The `address.countryName` field contains free-text country names in Slovak. A lookup table is needed:

| Slovak Name | ISO Code |
|---|---|
| `"Slovensko"` / `"Slovenská republika"` | `"SK"` |
| `"Česko"` / `"Česká republika"` | `"CZ"` |
| `"Maďarsko"` | `"HU"` |
| `"Poľsko"` | `"PL"` |
| `"Rakúsko"` | `"AT"` |
| `"Nemecko"` | `"DE"` |

Additional entries for other EU member states should be added as encountered. Log warnings for unmapped values.

### Implementation Notes

1. **Start with a sample**: Before implementing the parser, obtain a UVOstat API token and fetch a sample response from `/api/ukoncene_obstaravania` with `limit=5`. Document the complete JSON response structure including all field names and nesting. Many field paths in this mapping are based on partial documentation and need verification.

2. **Doc ID namespacing**: Prefix all document IDs with `"SK-UVO-"` to avoid collisions with TED document IDs. E.g., `"SK-UVO-12345"`.

3. **Deduplication with TED**: Above-threshold Slovak notices are cross-published to TED. There is no documented field linking UVOstat records to TED document IDs. Deduplication may need to be done by matching on title + procurer + date, or accepted as unavoidable overlap.

4. **Pagination**: UVOstat API returns max 100 records per request. To scrape by year, use `datum_zverejnenia_od` and `datum_zverejnenia_do` date filters and paginate through results. The API may not support offset-based pagination -- if not, narrow the date window until each window returns fewer than 100 results.

5. **Rate limits**: Not documented for UVOstat. Start conservatively (1 request/second) and adjust.

6. **Data quality**: Expect ~10% of records to have missing key fields. The parser must handle `None`/missing values gracefully throughout.

7. **ICO identifiers**: The `obstaravatel_ico` and `dodavatel_ico` fields (company registration numbers) are extremely valuable for entity deduplication even though the schema does not currently have a field for them. Consider storing them in a future schema extension or logging them for later use.
