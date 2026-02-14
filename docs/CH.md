# Switzerland (CH)

**Feasibility: Tier 2**

## Portal

- **Name**: SIMAP
- **URL**: https://www.simap.ch/
- **API docs**: https://www.it-beschaffung.ch/de/p/api/documentation (needs verification)
- **Project info**: https://kissimap.ch/

## Data Access

- **Method**: API (launched with new platform July 2024)
- **Format**: JSON, XML
- **Auth**: Registration required
- **OCDS**: No

## Coverage

Planned and awarded contracts above WTO threshold (230,000 CHF).

## Language

German, French, Italian

## Notes

- New platform launched July 2024 with API as key feature
- Registration required; documentation needs further investigation
- API connects to all platform functions

## Schema Mapping

### Data Flow Overview

SIMAP (simap.ch) is Switzerland's official procurement gazette. The new platform (July 2024) exposes a REST API documented via Swagger UI at https://www.simap.ch/api-doc. There are two relevant API layers:

1. **SIMAP native REST API** (`/api/publications/v1/project/project-search`): Returns `ProjectsSearchEntry` JSON objects covering projects and their publications (tenders, awards, corrections, cancellations). The `ProjectsSearchEntry` model was recently consolidated to include lot-level detail and project-search-detail data, eliminating the need for separate detail calls. Filter by publication type to find award notices ("Zuschlag"). The API can be used **without authentication** for public data (read-only search and publication access), though authenticated access provides additional features (tender documentation, question forums).

2. **it-beschaffung.ch wrapper API** (third-party): A simpler wrapper at `https://www.it-beschaffung.ch/api/publications/it/` that returns SIMAP data with flattened fields. Requires its own API key. Useful as a reference for understanding SIMAP's data model, but the native SIMAP API should be used for the scraper.

**Recommended strategy**: Use the native SIMAP REST API to search for award publications ("Zuschlag" type), paginate through results, and extract award data from the JSON responses. Authentication uses OAuth 2.0 Authorization Code Flow with PKCE (see https://simap-public.s3-ch-bern-1.obj.begasoft.ch/api-assets/Quick_Guide_OAuthFlow.pdf), but unauthenticated access may suffice for public publication search.

### Data Format Notes

- **Format**: JSON. The API returns structured JSON objects, not XML or OCDS.
- **Language**: Publication data appears in the original language of the contracting authority (German, French, or Italian). There is no language filtering -- each publication exists in a single language.
- **Currency**: Almost always CHF (Swiss Franc). Switzerland is not in the eurozone.
- **Publication types**: Ausschreibung (tender), Zuschlag (award), Berichtigung (correction), Abbruch (cancellation), Vorinformation (prior information), Teilnehmerauswahl (participant selection), Wettbewerb (competition), Wettbewerbsergebnis (competition result). We want **Zuschlag** only.
- **Project structure**: SIMAP organizes data by "project", where each project has one or more publications (tender, award, etc.) and one or more lots. An award ("Zuschlag") publication references back to the original tender project.
- **API access without auth**: The FAQ states the API can be used without a user account for public data. For Machine-to-Machine access, registration via a form is required. The exact scope of unauthenticated access needs verification.
- **Rate limits**: Not documented. The FAQ does not mention rate limits but "use in moderation" should be assumed.
- **Historical data**: The old platform (pre-July 2024) used a SOAP/XML interface. Historical data from before July 2024 may only be available through the archive at https://archiv.simap.ch/ or the legacy SOAP API. The new REST API's historical coverage needs verification.
- **Pagination**: The project-search endpoint likely supports pagination (page/size parameters). Exact pagination model needs verification against the Swagger spec.

### CRITICAL: API Documentation Gap

The SIMAP Swagger UI at https://www.simap.ch/api-doc requires cookie acceptance and could not be fully inspected during this research. The field mappings below are based on:
1. The it-beschaffung.ch third-party API documentation (which exposes SIMAP fields)
2. The SIMAP API changelog at https://www.simap.ch/api/specifications/changelog.html
3. The SIMAP online help and KISSimap forum discussions
4. The old platform's SOAP interface documentation

**Before implementing, the developer MUST**: Access the Swagger UI, export the OpenAPI spec, and verify all field names, types, and paths documented below. Many field paths are best-effort approximations.

### Field Mapping Tables

The tables below map schema fields to SIMAP API JSON paths. Field names marked with **(UNVERIFIED)** are inferred from the it-beschaffung.ch wrapper or changelog references and need confirmation against the actual Swagger spec.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `id` or `id_simap` **(UNVERIFIED)** | The SIMAP publication ID. Prefix with `CH-` to avoid collision with TED doc_ids (e.g. `CH-{simap_id}`). The changelog mentions `projectId` for the project level, but individual publications have their own IDs. |
| `edition` | `None` | SIMAP has no concept of OJ editions. Set to `None`. |
| `version` | Hardcode `"SIMAP"` | To identify the source format. |
| `reception_id` | `None` | TED-specific concept. Not applicable. |
| `official_journal_ref` | `None` | Swiss national publications do not appear in the EU Official Journal. For WTO-threshold notices cross-published to TED, the TED reference may exist but is not exposed via the SIMAP API. |
| `publication_date` | `publicationDate` or `date` **(UNVERIFIED)** | The changelog mentions `publicationDate` was added to models. The it-beschaffung.ch wrapper uses `date`. Format likely ISO 8601 (YYYY-MM-DD) but needs verification. |
| `dispatch_date` | `None` | SIMAP does not track dispatch dates. |
| `source_country` | Hardcode `"CH"` | All SIMAP publications are Swiss. |
| `contact_point` | Not clearly available **(UNVERIFIED)** | The contracting authority's contact person. May be part of the `orderAddress` model mentioned in the changelog. Needs Swagger verification. |
| `phone` | Not clearly available **(UNVERIFIED)** | May be part of `orderAddress` or a contact sub-object. Needs Swagger verification. |
| `email` | Not clearly available **(UNVERIFIED)** | May be part of `orderAddress` or a contact sub-object. Needs Swagger verification. |
| `url_general` | Not clearly available **(UNVERIFIED)** | May be part of the contracting authority or project data. Needs Swagger verification. |
| `url_buyer` | `None` | SIMAP does not appear to expose a buyer profile URL. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | Contracting authority name from `orderAddress` or project-level data **(UNVERIFIED)** | The changelog mentions `orderAddress` contains the contracting authority info. The it-beschaffung.ch wrapper has implicit authority fields (`auth_city`, `auth_canton`, `auth_country`). The exact JSON path needs Swagger verification. |
| `address` | `orderAddress.street` or similar **(UNVERIFIED)** | Part of the order/contracting authority address block. Needs verification. |
| `town` | `auth_city` (it-beschaffung.ch) or `orderAddress.city` **(UNVERIFIED)** | The it-beschaffung.ch wrapper exposes `auth_city`. The native API likely has this in an address sub-object. |
| `postal_code` | `orderAddress.postalCode` or similar **(UNVERIFIED)** | Part of the address block. Needs verification. |
| `country_code` | `auth_country` (it-beschaffung.ch) or `orderAddress.country` **(UNVERIFIED)** | Almost always `"CH"` but may include cross-border authorities. The it-beschaffung.ch wrapper exposes `auth_country`. |
| `nuts_code` | `None` | Switzerland does not use NUTS codes (not an EU/EEA member). Switzerland has its own statistical regions but they are not NUTS-coded. Always `None`. |
| `authority_type` | `auth_category` (it-beschaffung.ch) or `projectSubType`-related field **(UNVERIFIED)** | Swiss authority types are: Bund (federal), Kanton (cantonal), Gemeinde (municipal), Trager kantonaler/kommunaler Aufgaben (carriers of cantonal/municipal tasks). See "Code Normalization" section for mapping to eForms codes. |
| `main_activity_code` | `auth_activity` (it-beschaffung.ch) or `auth_sector` **(UNVERIFIED)** | The it-beschaffung.ch wrapper exposes `auth_activity` and `auth_sector`. Exact SIMAP native field name needs verification. Values will need mapping -- see "Code Normalization". |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `title` | The publication/project title. Available in the it-beschaffung.ch wrapper as `title`. Likely the same field name in the native API. |
| `short_description` | `text` (it-beschaffung.ch) or project description **(UNVERIFIED)** | The it-beschaffung.ch wrapper has `text` which likely contains the publication description. The native API may use a more structured field. |
| `main_cpv_code` | CPV code from the project/lot data **(UNVERIFIED)** | SIMAP uses CPV codes. The search form has CPV filtering. The exact JSON field path needs Swagger verification. May be nested under lot data. |
| `cpv_codes` | CPV codes array from project/lot data **(UNVERIFIED)** | Multiple CPV codes may be associated with a project or lot. Exact path needs verification. |
| `nuts_code` | `None` | Switzerland does not use NUTS codes. Always `None`. |
| `contract_nature_code` | Derived from project type or `procurement` field **(UNVERIFIED)** | The it-beschaffung.ch wrapper has `procurement` (with observed value `"OTHER"`). SIMAP's `projectSubType` consolidated from `orderType`/`studyType`/`competitionType` likely encodes this. Needs mapping -- see "Code Normalization". |
| `procedure_type` | `procedure` (it-beschaffung.ch) or procedure field in native API **(UNVERIFIED)** | The it-beschaffung.ch wrapper exposes `procedure`. Swiss procedure types are: offenes Verfahren (open), selektives Verfahren (selective), Einladungsverfahren (invitation), freihändiges Verfahren (direct/free-hand). See "Code Normalization" for mapping to eForms codes. |
| `accelerated` | `False` (default) | Swiss procurement law (BöB/IVöB) does not have an "accelerated procedure" concept analogous to eForms BT-106. Always `False`. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `title` or lot-level title **(UNVERIFIED)** | May be the same as the project title, or a lot-specific title if the project has multiple lots. |
| `contract_number` | `lot_nr` (it-beschaffung.ch) or lot identifier **(UNVERIFIED)** | The it-beschaffung.ch wrapper has `lot_nr` and `lots`. The native API likely has a lot/contract identifier. |
| `tenders_received` | `nr_of_offers` (it-beschaffung.ch) **(UNVERIFIED)** | The it-beschaffung.ch wrapper exposes `nr_of_offers`. The native API likely has this at the award/lot level. |
| `awarded_value` | `award_price` (it-beschaffung.ch) **(UNVERIFIED)** | The it-beschaffung.ch wrapper exposes `award_price`. Needs verification of the exact field name and whether it is a numeric value or a string requiring parsing. |
| `awarded_value_currency` | Likely hardcode `"CHF"` or from a currency field **(UNVERIFIED)** | Swiss procurement is overwhelmingly in CHF. There may be an explicit currency field, or it may need to be defaulted. Needs verification. |
| `contractors` | `award_companies` (it-beschaffung.ch) **(UNVERIFIED)** | The it-beschaffung.ch wrapper exposes `award_companies` as a list. The native API likely has structured contractor objects. See ContractorModel below. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `award_companies[n].name` or similar **(UNVERIFIED)** | Contractor/supplier company name. The exact sub-object structure within the award companies list needs Swagger verification. |
| `address` | `award_companies[n].address` or similar **(UNVERIFIED)** | Contractor street address. Needs verification. |
| `town` | `award_companies[n].city` or similar **(UNVERIFIED)** | Contractor city. Needs verification. |
| `postal_code` | `award_companies[n].postalCode` or similar **(UNVERIFIED)** | Contractor postal code. Needs verification. |
| `country_code` | `award_companies[n].country` or similar **(UNVERIFIED)** | Contractor country. Likely `"CH"` for most. Needs verification. |
| `nuts_code` | `None` | Switzerland does not use NUTS codes. Always `None`. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | CPV code value from project/lot **(UNVERIFIED)** | SIMAP uses standard CPV codes (the search interface has CPV filtering). Format likely matches EU standard (e.g. `"45000000-7"`). Needs verification of format (with or without check digit). |
| `description` | CPV description if provided **(UNVERIFIED)** | SIMAP may include CPV descriptions in the API response. If not, use a local CPV lookup table. Needs verification. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Derived from `procedure` field after normalization | The raw value will be a Swiss procedure type code/name. Must be mapped to eForms codes -- see "Code Normalization". |
| `description` | Raw procedure name from the API | Use the original Swiss procedure type name as the description (e.g. "Offenes Verfahren"). |

### Unmappable Schema Fields

These schema fields cannot be populated from SIMAP data and should always be `None`:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | SIMAP has no OJ edition concept. |
| `DocumentModel.reception_id` | TED-specific concept. Not applicable to national portals. |
| `DocumentModel.official_journal_ref` | Swiss national publications are not in the EU Official Journal. |
| `DocumentModel.dispatch_date` | SIMAP does not track dispatch-to-publication-office dates. |
| `DocumentModel.url_buyer` | SIMAP does not expose buyer profile URLs. |
| `ContractingBodyModel.nuts_code` | Switzerland is not in the EU/EEA and does not use NUTS codes. |
| `ContractModel.nuts_code` | Same reason -- no NUTS codes for Switzerland. |
| `ContractModel.accelerated` | Swiss procurement law has no "accelerated procedure" concept. Always `False`. |
| `ContractorModel.nuts_code` | Same reason -- no NUTS codes for Switzerland. |

### Extra Portal Fields

These fields are available in SIMAP but not covered by the current schema. Flagged for review.

| Portal Field | Description | Notes |
|---|---|---|
| `is_wto` | Whether the procurement exceeds WTO (GPA) thresholds | Schema doesn't cover -- flagging for review. Useful for distinguishing WTO-threshold from below-threshold procurements. Key for deduplication against TED data (WTO-threshold Swiss notices may also appear on TED). |
| `auth_canton` | Canton of the contracting authority (e.g. "BE", "ZH") | Schema doesn't cover -- flagging for review. Swiss-specific geographic classification more useful than NUTS for Switzerland. |
| `award_date` | Date the award was made | Schema doesn't cover -- flagging for review. Distinct from publication date. |
| `date_project_start` / `date_project_end` | Contract duration/period | Schema doesn't cover -- flagging for review. |
| `datetime_deadline` | Tender submission deadline | Schema doesn't cover -- flagging for review. |
| `prior_id_simap` / `prior_ob_code` / `prior_date` | Reference to the original tender publication | Schema doesn't cover -- flagging for review. Useful for linking awards back to their tender notices. |
| `lots` (structured lot data) | Per-lot breakdown of the procurement | Schema doesn't cover multi-lot structure -- flagging for review. The current schema flattens to one contract, but SIMAP projects can have multiple lots, each with separate awards. |
| `legalFormCode` | Legal form of the vendor/contractor | Schema doesn't cover -- flagging for review. Useful for entity classification. |
| `ob_code` | Official gazette reference code | Schema doesn't cover -- flagging for review. Reference to the Swiss Official Gazette (Schweizerisches Handelsamtsblatt). |
| `bund_nr` | Federal procurement number | Schema doesn't cover -- flagging for review. Federal-level identifier. |
| `date_doc_available_start` / `date_doc_available_end` | Document availability period | Schema doesn't cover -- flagging for review. |
| Sustainability/environmental criteria | May include green procurement flags | Schema doesn't cover -- flagging for review. Swiss procurement increasingly includes sustainability criteria. Availability needs Swagger verification. |
| Vendor/contractor registration IDs | Company registration numbers (UID/CHE number) | Schema doesn't cover -- flagging for review. Very useful for entity resolution. Swiss companies have a UID (Unternehmens-Identifikationsnummer, e.g. CHE-123.456.789). |

### Code Normalization

#### Procedure Type Codes

Swiss procurement law (BöB - Bundesgesetz über das öffentliche Beschaffungswesen; IVöB - Interkantonale Vereinbarung über das öffentliche Beschaffungswesen) defines four procedure types. These must be mapped to eForms equivalents:

| Swiss Procedure Type (DE) | Swiss Procedure Type (FR) | eForms Code | Notes |
|---|---|---|---|
| Offenes Verfahren | Procédure ouverte | `open` | Direct match. All providers may submit offers. |
| Selektives Verfahren | Procédure sélective | `restricted` | Two-stage procedure with pre-qualification. Equivalent to EU restricted procedure. |
| Einladungsverfahren | Procédure sur invitation | `neg-w-call` | Invitation-only procedure (typically 3+ invited). Closest eForms equivalent is negotiated with call, but this is an imperfect match -- Swiss invitation procedure is a distinct concept. Could alternatively map to `oth-single` or `oth-mult`. **Mapping decision needed.** |
| Freihändiges Verfahren | Procédure de gré à gré | `neg-wo-call` | Direct award without competition. Equivalent to negotiated without prior call. |

**Important considerations**:
- The exact procedure type codes/strings returned by the SIMAP API are unknown. They may be German strings ("Offenes Verfahren"), abbreviation codes, or numeric codes. The implementor must inspect actual API responses to build the mapping.
- The procedure names may appear in German, French, or Italian depending on the contracting authority's language region. The mapping must handle all three languages.
- The Einladungsverfahren (invitation procedure) has no exact EU equivalent. The recommended mapping to `neg-w-call` is an approximation. Consider mapping to `oth-single` ("Other single stage procedure") if a more neutral code is preferred.

#### Authority Type Codes

Swiss contracting authority categories must be mapped to eForms buyer-legal-type codes:

| Swiss Authority Category | eForms Code | Notes |
|---|---|---|
| Bund (Federal) | `cga` | Central government authority |
| Kanton (Cantonal) | `ra` | Regional authority |
| Gemeinde (Municipal) | `la` | Local authority |
| Träger kantonaler Aufgaben (Carrier of cantonal tasks) | `body-pl-ra` | Body governed by public law, controlled by regional authority |
| Träger kommunaler Aufgaben (Carrier of municipal tasks) | `body-pl-la` | Body governed by public law, controlled by local authority |
| Öffentliche Unternehmen (Public enterprises) | `pub-undert` | Public undertaking |

**Important considerations**:
- The exact authority category codes returned by the SIMAP API are unknown. The it-beschaffung.ch wrapper uses `auth_category` but the values and their format need verification against the native API.
- The mapping above is based on the known Swiss authority hierarchy. Some categories may not have a clean 1:1 mapping to eForms codes.
- Additional Swiss-specific categories may exist (e.g. intercantonal bodies, public-private partnerships). Log warnings for unrecognized values per the project's fail-loud principle.

#### Contract Nature Codes

Swiss procurement distinguishes between contract types. The mapping to eForms codes:

| Swiss Contract Type (DE) | Swiss Contract Type (FR) | eForms Code | Notes |
|---|---|---|---|
| Bauauftrag / Bauleistung | Marché de construction / Travaux | `works` | Construction/works contracts |
| Lieferauftrag | Marché de fournitures | `supplies` | Supply/goods contracts |
| Dienstleistungsauftrag | Marché de services | `services` | Service contracts |

**Important considerations**:
- The it-beschaffung.ch wrapper has a `procurement` field with observed value `"OTHER"`, suggesting there may be additional categories or a different coding scheme in the native API.
- The SIMAP changelog mentions `projectSubType` which consolidated `orderType`, `studyType`, and `competitionType`. The implementor must inspect the Swagger spec to understand how contract nature is encoded.
- Studies ("Studienauftrag") and competitions ("Wettbewerb") are distinct project types in SIMAP that may not map cleanly to the three eForms contract nature codes. Log warnings for unrecognized values.

#### Activity Codes

The it-beschaffung.ch wrapper exposes `auth_activity` and `auth_sector`. Swiss procurement does not use EU main-activity codes (BT-10). If the SIMAP API provides activity/sector information, it will use Swiss-specific categories that need mapping to eForms activity codes. **The exact values and mapping need investigation against the Swagger spec and real API responses.** If no reasonable mapping exists, set `main_activity_code` to `None`.

### Implementation Recommendations

1. **First step -- access the Swagger spec**: Visit https://www.simap.ch/api-doc, export the OpenAPI JSON/YAML, and verify all field names documented above. This is a hard prerequisite before writing any parser code. Nearly every field path above is marked **(UNVERIFIED)**.

2. **Authentication strategy**: Test unauthenticated access first. The FAQ states the API can be used without a user account for public data. If unauthenticated access is insufficient (e.g. missing fields, rate limits), register for Machine-to-Machine access and implement OAuth 2.0 Authorization Code Flow with PKCE.

3. **Doc ID strategy**: Use `CH-{simap_publication_id}` as the `doc_id` to avoid collisions with TED doc_ids.

4. **Multi-lot handling**: SIMAP projects commonly have multiple lots. Each lot may have its own award (Zuschlag) with separate contractors and values. The parser must iterate over lots and create one `AwardModel` per lot, or one `AwardDataModel` per lot if the schema requires a single contract title per entry. Inspect how the FI and NL implementations handle multi-lot notices for guidance.

5. **Deduplication with TED**: WTO-threshold Swiss notices (`is_wto == true`) may also appear on TED. Use the `is_wto` flag to identify potential duplicates. There may also be a reference to the TED publication in the SIMAP data (needs verification).

6. **Historical data**: The new REST API (July 2024) may not expose historical data from before the platform migration. For pre-2024 data, investigate the archive at https://archiv.simap.ch/ and the legacy SOAP interface documented at https://www.simap.ch/EN/PDF/COMMON/soapservice_simap_en.pdf.

7. **Language handling**: SIMAP data comes in German, French, or Italian. Do not filter by language. Store data in the original language, consistent with the TED approach.

8. **Currency**: Default to `"CHF"` if no explicit currency field is found. Switzerland is not in the eurozone, so exchange rate conversion (CHF to EUR) will be needed for cross-country analysis using the existing `exchange_rates` table.

9. **Register for API updates**: The SIMAP platform offers registration for developers to receive notifications about API changes. Register at the KISSimap forum to stay informed of breaking changes.
