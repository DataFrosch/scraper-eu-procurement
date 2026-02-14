# Germany (DE)

**Feasibility: Tier 2**

## Portals

1. **service.bund.de**: https://www.service.bund.de/ (centralized tender search)
2. **DTVP** (Deutsches Vergabeportal): https://en.dtvp.de/
3. **Datenservice oeffentlicher Einkauf**: https://oeffentlichevergabe.de (eForms-based data service)
4. **bund.dev**: https://bund.dev/ (federal API portal)
5. **GitHub**: https://github.com/bundesAPI (Federal Open Data Office)

## Data Access

- **Method**: eForms data service + bund.dev API portal
- **Format**: JSON, CSV, XML
- **Auth**: Open
- **OCDS**: Emerging (via XBeschaffung bridge to OCDS)
- **OCP Registry**: https://data.open-contracting.org/en/publication/136
- **Download sizes**: 2024 data = 166 MB, 2025 data = 190 MB (JSON/CSV)

## Coverage

Federal, state, and local procurement. Fragmented across multiple platforms.

## Language

German

## Notes

- **XBeschaffung Standard**: New German data standard implementing eForms fields, interoperable with OCDS
- Historically very fragmented landscape with multiple competing platforms (vergabe24.de, evergabe-online.de, etc.)
- The oeffentlichevergabe.de data service is relatively new and consolidating
- Existing Apify scraper: https://apify.com/stephaniehhnbrg/public-tender-scraper-germany
- Rapidly improving with eForms/XBeschaffung — main challenge is historical fragmentation

## Schema Mapping

### Recommended Data Source

Use the **Datenservice oeffentlicher Einkauf** (DOEEV) via the bund.dev API portal as the primary data source. The DOEEV aggregates procurement notices from all German e-procurement platforms into a single data service at oeffentlichevergabe.de. The bund.dev portal (https://bund.dev/) exposes the DOEEV REST API with OpenAPI/Swagger documentation.

The DOEEV provides data in **XBeschaffung** format, Germany's national eForms implementation. XBeschaffung maps directly to EU eForms BT (Business Term) fields, making it structurally very close to the eForms UBL XML already handled by the existing `eforms_ubl.py` parser. However, the API returns **JSON** (not XML), so a dedicated JSON parser is needed.

**Alternative paths** (not recommended as primary):
- **Bulk CSV/JSON downloads**: Yearly archives available via oeffentlichevergabe.de (2024 = 166 MB, 2025 = 190 MB). Could be used for initial backfill. The exact download URLs and format need to be discovered from the portal.
- **eForms XML**: Some notices may also be available as raw eForms XML via TED (for above-threshold), but the DOEEV API is the canonical source for national below-threshold data.

### Data Format Notes

- **Format**: JSON via REST API. Bulk downloads available as JSON and CSV.
- **Standard**: XBeschaffung — Germany's national implementation of eForms. Field names use eForms Business Term (BT) identifiers. The JSON structure follows the XBeschaffung schema, which maps eForms XML elements to JSON properties.
- **API base URL**: Available via bund.dev; the exact endpoint URL for the DOEEV API must be confirmed from the bund.dev API catalog. Expected pattern: `https://api.oeffentlichevergabe.de/` or similar, proxied through bund.dev.
- **Auth**: Open access, no authentication required (per the portal documentation). **Needs verification** -- bund.dev may require a free API key for rate limiting purposes.
- **Filtering**: The API likely supports filtering by notice type (Bekanntmachungsart). Filter to `Vergabebekanntmachung` (contract award notice) or the eForms equivalent subtype to get only award notices.
- **Pagination**: REST APIs typically use `offset`/`limit` or `page`/`size` parameters. The exact pagination mechanism must be confirmed from the Swagger/OpenAPI documentation.
- **Currency**: Almost always EUR (Germany uses the euro), but the currency field should still be read from the data as some contracts may involve other currencies.
- **Language**: All data is in German. Field values (titles, descriptions, organization names) will be in German.
- **Coverage**: Federal, state (Land), and local (Gemeinde) procurement. The DOEEV aims to consolidate all German public procurement, but coverage of sub-federal entities may be incomplete, especially for historical data.
- **Historical data**: The DOEEV/XBeschaffung data service is relatively new. Data availability likely starts from 2023-2024 onwards. Earlier data may not be available through this channel.

**IMPORTANT**: The exact API structure, endpoints, field names, and pagination behavior described below are based on the XBeschaffung standard specification and eForms BT mappings. Because the bund.dev API documentation could not be fetched during this analysis, **all JSON paths below are best-effort approximations that must be verified against actual API responses before implementation**. The implementor should:
1. Explore the bund.dev API catalog to find the exact DOEEV endpoint.
2. Fetch sample award notices and inspect the actual JSON structure.
3. Adjust the field paths below to match the real response format.

### Field Mapping Tables

XBeschaffung uses eForms Business Term (BT) identifiers. The JSON paths below use dot notation based on the expected XBeschaffung JSON structure. Where the exact JSON path is uncertain, the eForms BT number is provided so the implementor can locate the correct field in the actual API response.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | Notice identifier (BT-701) | The unique notice identifier assigned by the DOEEV. Format and field name must be confirmed from actual API data. Prefix with `DE-` to avoid collisions with TED doc IDs. |
| `edition` | `None` | No OJ edition equivalent in German national data. Set to `None`. |
| `version` | (hardcoded `"XBeschaffung"`) | Hardcode to identify the source format. |
| `reception_id` | `None` | TED-specific field. No XBeschaffung equivalent. Set to `None`. |
| `official_journal_ref` | `None` | German national notices are not published in the EU Official Journal. Set to `None`. |
| `publication_date` | BT-702 (Notice Publication Date) | ISO 8601 date. The date the notice was published on the DOEEV platform. |
| `dispatch_date` | BT-05 (Notice Dispatch Date) | ISO 8601 date. The date the notice was dispatched to the publication platform. May or may not be present for national notices. |
| `source_country` | (hardcoded `"DE"`) | All DOEEV data is German procurement. Hardcode `"DE"`. Could also be read from BT-514 (Organisation Country Code) of the buyer if available. |
| `contact_point` | BT-502 (Organisation Contact Point) | Contact point name from the buyer/contracting authority. |
| `phone` | BT-503 (Organisation Contact Telephone Number) | Buyer's telephone number. |
| `email` | BT-506 (Organisation Contact Email Address) | Buyer's email address. |
| `url_general` | BT-505 (Organisation Internet Address) | Buyer's website URL. |
| `url_buyer` | BT-508 (Buyer Profile URL) | Buyer profile URL. XBeschaffung/eForms has a dedicated BT for this. **Needs verification** that this field is populated in practice. |

#### ContractingBodyModel

The buyer (Auftraggeber) organization in XBeschaffung corresponds to the eForms `Organization` with role `buyer` (BT-10).

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | BT-500 (Organisation Name) | Official name of the contracting authority. Required in eForms. |
| `address` | BT-510 (Organisation Street) | Street address of the buyer. |
| `town` | BT-513 (Organisation City) | City/town of the buyer. |
| `postal_code` | BT-512 (Organisation Post Code) | Postal code. |
| `country_code` | BT-514 (Organisation Country Code) | ISO 3166-1 alpha-2 country code. eForms uses ISO codes directly, so no mapping needed. Will almost always be `"DE"`. |
| `nuts_code` | BT-507 (Organisation Country Subdivision) | NUTS code for the buyer's location. eForms stores this as a NUTS code directly (e.g. `"DE111"`). |
| `authority_type` | BT-11 (Buyer Legal Type) | eForms buyer-legal-type codelist. XBeschaffung uses the same eForms codelist values (e.g. `"cga"`, `"ra"`, `"la"`, `"body-pl"`). See Code Normalization section. |
| `main_activity_code` | BT-10 (Activity of the Contracting Authority / Entity) | eForms main-activity codelist. XBeschaffung uses the same eForms codelist values. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | BT-21 (Title) | The procurement title. Available at the procedure level. |
| `short_description` | BT-24 (Description) | Procurement description at the procedure level. |
| `main_cpv_code` | BT-262 (Main Classification Code) | The main CPV code at the procedure or lot level. eForms stores CPV codes with the full code including check digit (e.g. `"45000000-7"`). |
| `cpv_codes` | BT-262 + BT-263 (Additional Classification Code) | Main CPV plus any additional CPV codes. Each entry has a code; descriptions may or may not be provided in the JSON. |
| `nuts_code` | BT-5101 (Place Performance Country Subdivision) | NUTS code for the contract performance location. Available at the lot level in eForms. |
| `contract_nature_code` | BT-23 (Nature of Contract) | eForms `contract-nature-type` codelist. XBeschaffung uses the same eForms codes: `"works"`, `"supplies"`, `"services"`, `"combined"`. No mapping needed -- values should already be in eForms format. **Needs verification.** |
| `procedure_type` | BT-105 (Procedure Type) | eForms `procurement-procedure-type` codelist. XBeschaffung uses the same eForms codes: `"open"`, `"restricted"`, `"neg-w-call"`, `"neg-wo-call"`, `"comp-dial"`, `"innovation"`, etc. No mapping needed if already in eForms format. **Needs verification** -- XBeschaffung may use German-language labels or different codes for below-threshold procedures (e.g. `Verhandlungsvergabe`, `Beschraenkte Ausschreibung`). See Code Normalization. |
| `accelerated` | BT-106 (Procedure Accelerated) | Boolean field in eForms. XBeschaffung should carry this as a boolean. Default to `False` if absent. |

#### AwardModel

In eForms/XBeschaffung, award information is structured around `LotResult` (BG-7) and `SettledContract` (BG-310). Each lot can have its own result.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | BT-721 (Contract Title) | Title of the settled contract. May or may not be populated; could fall back to the lot title (BT-21 at lot level). |
| `contract_number` | BT-150 (Contract Identifier) | The identifier of the awarded contract. |
| `tenders_received` | BT-759 (Received Submissions Count) | Number of tenders received for the lot. In eForms this is per-lot, within `LotResult`. |
| `awarded_value` | BT-161 (Award Value) | The total value of the award. In eForms, this is within `LotTender` (BG-320) as `PayableAmount`. |
| `awarded_value_currency` | BT-161 currency attribute | ISO 4217 currency code from the `currencyID` attribute of the value element. Will almost always be `"EUR"`. |
| `contractors` | BT-720 (Tender Organisation Identifier Reference) / BG-7 | Winning tenderer organizations, resolved from `TenderingParty`/`Tenderer` references to full organization records. See ContractorModel below. |

#### ContractorModel

Contractors (Auftragnehmer / winning tenderers) are eForms `Organization` entities with role `tenderer` or `winner`, referenced from the lot result.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | BT-500 (Organisation Name) | Supplier/contractor organization name. Resolved from the winning tenderer's organization reference. |
| `address` | BT-510 (Organisation Street) | Contractor street address. |
| `town` | BT-513 (Organisation City) | Contractor city/town. |
| `postal_code` | BT-512 (Organisation Post Code) | Contractor postal code. |
| `country_code` | BT-514 (Organisation Country Code) | ISO 3166-1 alpha-2 code. No mapping needed. |
| `nuts_code` | BT-507 (Organisation Country Subdivision) | NUTS code for the contractor's location. May not be populated for all contractors. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | BT-262 / BT-263 (Classification Code) | CPV code string. eForms format includes the check digit (e.g. `"45000000-7"`). Normalize to match existing CPV code format in the database. |
| `description` | Classification description | eForms may or may not include the CPV description text in the JSON. If absent, can be looked up from the `cpv_codes` table. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | BT-105 (Procedure Type) | After any necessary mapping to eForms codes (see Code Normalization). If XBeschaffung already uses eForms codes, no mapping needed. |
| `description` | Procedure type label | The human-readable procedure type description. May be in German. Use the standard eForms English description from `_PROCEDURE_TYPE_DESCRIPTIONS` after mapping. |

#### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | BT-11 (Buyer Legal Type) | eForms buyer-legal-type code. XBeschaffung should use the same codelist. See Code Normalization. |
| `description` | Buyer legal type label | Use the standard eForms description from `_AUTHORITY_TYPE_DESCRIPTIONS` after mapping. |

### Unmappable Schema Fields

The following schema fields likely cannot be populated from DOEEV/XBeschaffung data and should be set to `None`:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | No OJ edition concept in German national data. Not applicable. |
| `DocumentModel.reception_id` | TED-specific concept. Not applicable to national portals. |
| `DocumentModel.official_journal_ref` | National notices are not published in the EU Official Journal. |

**Note**: Compared to the French (DECP) and Italian (ANAC) portals, XBeschaffung/eForms is the most complete data source -- very few fields are truly unmappable because XBeschaffung implements the full eForms specification. The fields above are TED-publication-specific metadata that do not exist in any national portal.

The following fields are **theoretically available** in XBeschaffung/eForms but may not always be populated in practice. The implementor should check sample data and fall back to `None` if absent:

- `DocumentModel.dispatch_date` (BT-05) -- may not be used for national-only notices
- `DocumentModel.url_buyer` (BT-508) -- buyer profile URLs may not be routinely provided
- `ContractModel.accelerated` (BT-106) -- uncommon for below-threshold national procurement
- `ContractingBodyModel.main_activity_code` (BT-10) -- may not be populated for all buyer types

### Extra Portal Fields

The following XBeschaffung/eForms fields are potentially useful but not covered by the current schema. Flagged for review:

| Portal Field | eForms BT | Notes |
|---|---|---|
| Lot information | BG-3 (Lot) | eForms structures data by lot. Each lot has its own title, description, CPV, NUTS, value. The current schema flattens everything to one contract. Schema doesn't cover -- flagging for review. |
| Estimated value | BT-27 (Estimated Value) | The estimated/maximum contract value at lot or procedure level. Schema doesn't cover -- flagging for review. |
| Award date | BT-1451 (Winner Decision Date) | The date the award decision was made. Schema doesn't cover -- flagging for review. |
| Contract conclusion date | BT-145 (Contract Conclusion Date) | Date the contract was signed. Schema doesn't cover -- flagging for review. |
| Framework agreement indicator | BT-765 (Framework Agreement) | Whether the procurement uses a framework agreement. Schema doesn't cover -- flagging for review. |
| Organisation identifier | BT-501 (Organisation Identifier) | Formal organization identifiers (e.g. German Leitweg-ID, Handelsregisternummer). Highly valuable for entity deduplication. Schema doesn't cover -- flagging for review. |
| Organisation size / SME | BT-165 (Winner Size) | Whether the winner is an SME (small/medium enterprise). Schema doesn't cover -- flagging for review. |
| Subcontracting | BT-773 (Subcontracting) | Subcontracting information and value. Schema doesn't cover -- flagging for review. |
| Contract duration | BT-536 / BT-537 (Duration Start Date / End Date) | Contract execution period. Schema doesn't cover -- flagging for review. |
| European funds | BT-60 (EU Funds) | Whether the contract is co-financed by EU funds. Schema doesn't cover -- flagging for review. |
| Legal basis | BT-01 (Legal Basis) | The directive or regulation under which the procurement was conducted (e.g. Directive 2014/24/EU, or national VgV/UVgO/VOB). Schema doesn't cover -- flagging for review. |
| Notice subtype | BT-02 (Notice Type) | The specific eForms notice subtype (e.g. subtype 29 = contract award notice for standard directive). Useful for filtering. Schema doesn't cover -- flagging for review. |
| GPA coverage | BT-115 (GPA Coverage) | Whether the procurement is covered by the WTO Government Procurement Agreement. Schema doesn't cover -- flagging for review. |
| Electronic auction | BT-767 (Electronic Auction) | Whether an electronic auction was used. Schema doesn't cover -- flagging for review. |

### Code Normalization

#### Contract Nature Codes (`contract_nature_code`)

XBeschaffung uses the eForms `contract-nature-type` codelist (BT-23). If the values are already eForms codes, no mapping is needed:

| XBeschaffung Value | eForms Code | Notes |
|---|---|---|
| `"works"` | `"works"` | Direct match (Bauauftrag) |
| `"supplies"` | `"supplies"` | Direct match (Lieferauftrag) |
| `"services"` | `"services"` | Direct match (Dienstleistungsauftrag) |
| `"combined"` | `"combined"` | Direct match (if present) |

**Needs verification**: The actual values in the JSON response may be eForms codes (lowercase English) or could be German-language labels (e.g. `"Bauauftrag"`, `"Lieferauftrag"`, `"Dienstleistung"`). If German labels are used, the following mapping is needed:

| German Label | eForms Code |
|---|---|
| `"Bauauftrag"` / `"Bauleistung"` | `"works"` |
| `"Lieferauftrag"` / `"Lieferleistung"` | `"supplies"` |
| `"Dienstleistungsauftrag"` / `"Dienstleistung"` | `"services"` |

The existing `_normalize_contract_nature_code()` function in `ted_v2.py` already handles eForms codes as pass-through. If XBeschaffung uses raw eForms codes, it can be reused directly.

#### Procedure Type Codes (`procedure_type`)

XBeschaffung uses BT-105 (Procedure Type). For above-threshold procurement (subject to EU directives), the values should match the eForms `procurement-procedure-type` codelist exactly:

| eForms Code | Description | German Term |
|---|---|---|
| `"open"` | Open procedure | Offenes Verfahren |
| `"restricted"` | Restricted procedure | Nichtoffenes Verfahren |
| `"neg-w-call"` | Negotiated with prior call | Verhandlungsverfahren mit Teilnahmewettbewerb |
| `"neg-wo-call"` | Negotiated without prior call | Verhandlungsverfahren ohne Teilnahmewettbewerb |
| `"comp-dial"` | Competitive dialogue | Wettbewerblicher Dialog |
| `"innovation"` | Innovation partnership | Innovationspartnerschaft |
| `"comp-tend"` | Competitive tendering | Wettbewerbliches Verfahren |

**Below-threshold procedures** (Unterschwellenvergaben): German national procurement law (UVgO, VOB/A) defines procedure types that have no direct eForms equivalent. These may appear in the data and will need mapping:

| German Below-Threshold Procedure | Proposed eForms Code | Notes |
|---|---|---|
| `"Oeffentliche Ausschreibung"` (public tender) | `"open"` | Functionally equivalent to open procedure. UVgO Section 9. |
| `"Beschraenkte Ausschreibung mit Teilnahmewettbewerb"` (restricted tender with competition) | `"restricted"` | Functionally equivalent to restricted procedure. UVgO Section 10. |
| `"Beschraenkte Ausschreibung ohne Teilnahmewettbewerb"` (restricted tender without competition) | `"restricted"` | Variant without prior competition phase. Map to restricted as closest eForms equivalent. |
| `"Verhandlungsvergabe mit Teilnahmewettbewerb"` (negotiated award with competition) | `"neg-w-call"` | Functionally equivalent. UVgO Section 12. |
| `"Verhandlungsvergabe ohne Teilnahmewettbewerb"` (negotiated award without competition) | `"neg-wo-call"` | Functionally equivalent. UVgO Section 12. |
| `"Direktauftrag"` (direct award) | `"neg-wo-call"` | Direct award below micro-threshold. Maps to negotiated without call. |
| `"Freiberufliche Leistung"` (freelance services) | `"neg-wo-call"` | Direct commissioning of freelance services (architecture, engineering). |

**Critical uncertainty**: It is unclear whether XBeschaffung uses eForms codes (lowercase English), German-language labels, or its own codelist for below-threshold procedures. The implementor must:
1. Fetch sample award notices from the API.
2. Inspect the actual values used for BT-105.
3. Build the mapping from observed values.
4. Log warnings for unrecognized procedure types, per the fail-loud principle.

The existing `_normalize_procedure_type()` function in `ted_v2.py` already handles eForms codes as pass-through. If XBeschaffung uses eForms codes for above-threshold notices, it can be reused. A supplementary mapping for German below-threshold procedure names will likely be needed.

#### Authority Type Codes (`authority_type`)

XBeschaffung uses BT-11 (Buyer Legal Type). For EU-directive-scope procurement, these should match the eForms `buyer-legal-type` codelist:

| eForms Code | Description | German Term |
|---|---|---|
| `"cga"` | Central government authority | Oberste Bundesbehoerde |
| `"ra"` | Regional authority | Landesbehoerde |
| `"la"` | Local authority | Kommunalbehoerde |
| `"body-pl"` | Body governed by public law | Einrichtung des oeffentlichen Rechts |
| `"body-pl-cga"` | Body governed by public law, controlled by central govt | Einrichtung des oeffentlichen Rechts, kontrolliert von Bundesbehoerde |
| `"body-pl-ra"` | Body governed by public law, controlled by regional authority | Einrichtung des oeffentlichen Rechts, kontrolliert von Landesbehoerde |
| `"body-pl-la"` | Body governed by public law, controlled by local authority | Einrichtung des oeffentlichen Rechts, kontrolliert von Kommunalbehoerde |
| `"pub-undert"` | Public undertaking | Oeffentliches Unternehmen |
| `"eu-ins-bod-ag"` | EU institution, body or agency | EU-Institution (unlikely for German national data) |

The existing `_make_authority_type_entry()` function in `ted_v2.py` handles eForms codes as pass-through and can be reused if XBeschaffung provides standard eForms codes. **Needs verification** against actual data -- German buyer type values may use XBeschaffung-specific codes or German-language labels that need mapping.

#### Accelerated Procedure (`accelerated`)

XBeschaffung/eForms provides BT-106 (Procedure Accelerated) as a dedicated boolean field. This maps directly to `ContractModel.accelerated`. Read the boolean value from the JSON; default to `False` if the field is absent. No code normalization needed.

### Implementation Notes

1. **Doc ID strategy**: Use the DOEEV notice identifier (BT-701 or equivalent) as the base. Prefix with `DE-` to avoid collisions with TED doc IDs (e.g. `DE-{notice_id}`). The exact format of the notice ID must be confirmed from actual API data.

2. **Award filtering**: The API likely supports filtering by notice type. Filter to eForms subtypes that correspond to contract award notices:
   - Subtype 29: Contract award notice (standard directive)
   - Subtype 30: Contract award notice (utilities directive)
   - Subtype 31: Contract award notice (defence directive)
   - Subtype 32: Contract award notice (concessions directive)
   - Subtype 33-35: Contract award notices for social and other specific services
   If filtering by subtype is not supported, filter by `BT-02` (Notice Type) or the XBeschaffung equivalent of `Vergabebekanntmachung` in the response data.

3. **eForms parser reuse**: The existing `eforms_ubl.py` parser handles eForms XML. If the DOEEV also provides eForms XML alongside JSON, the existing parser could potentially be reused with minor adjustments (doc_id derivation, file source). However, since the primary API format is JSON, a new JSON parser is the expected path.

4. **XBeschaffung to eForms structural mapping**: XBeschaffung is designed to be interoperable with eForms. The JSON structure should closely mirror the eForms XML structure, with the same BT identifiers. The key structural elements to look for in the JSON response:
   - `Organization` objects (with roles: buyer, tenderer/winner)
   - `ProcurementProject` (title, description, CPV, NUTS)
   - `TenderingProcess` (procedure type, accelerated)
   - `LotResult` / `SettledContract` (award information)
   - `LotTender` (tender value, winning tenderer reference)

5. **Multiple lots / awards**: Like eForms, XBeschaffung structures data by lot. Each lot can have its own result and winner. This maps to the schema's `awards: List[AwardModel]`, with one `AwardModel` per awarded lot.

6. **Idempotency**: Use `DE-{notice_id}` as the `doc_id`. Re-importing the same data should be idempotent, consistent with the existing TED import behavior.

7. **Bulk download vs. API**: For initial backfill, the yearly bulk downloads (JSON/CSV, ~166-190 MB) may be more efficient than paginating through the API. For incremental updates, the API with date filtering is appropriate. The parser should handle both input modes.

8. **Rate limiting**: The bund.dev portal may impose rate limits. The exact limits must be confirmed from the API documentation. Implement respectful request pacing consistent with the TED scraper approach (3 concurrent downloads, respect 429 responses).

9. **Encoding**: German text with umlauts (ae, oe, ue, ss) and special characters. Ensure UTF-8 handling throughout. Organization names will use German characters (e.g. "Bundesministerium fuer Digitales und Verkehr", "Landeshauptstadt Muenchen").

10. **Data quality**: As with all procurement data, expect some records with missing or anomalous values. Apply the same sanity filtering used for TED data (`awarded_value >= 1 AND awarded_value < 1000000000`). The fail-loud principle applies: missing data is `None`, never a default value.
