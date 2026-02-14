# Belgium (BE)

**Feasibility: Tier 3**

## Portal

- **Name**: e-Procurement (BOSA)
- **URL**: https://www.publicprocurement.be/
- **Modules**: e-Notification, e-Tendering, e-Catalogue, e-Awarding, e-Auction

## Data Access

- **Method**: Web-only for searching; requires registration
- **Format**: HTML (web interface)
- **Auth**: Registration required for all modules
- **OCDS**: No

## Coverage

Federal, regional, and local procurement.

## Language

French, Dutch, German

## Notes

- Five separate e-modules; complex federated structure (Flanders, Wallonia, Brussels each have authority)
- No known public API
- Would require web scraping of a registration-gated platform

## Schema Mapping

> **Critical caveat**: Belgium's e-Procurement portal (publicprocurement.be) has **no known public API** and **no structured data export** (no OCDS, no XML feed, no CSV/JSON download). The portal is web-only and registration-gated. The mapping below is therefore **speculative** -- it documents the *expected* field availability based on what typical Belgian procurement notices contain on the web interface. Actual field paths cannot be determined until someone registers, inspects the HTML structure, and/or discovers undocumented API endpoints. Every "Portal Field/Path" entry below is a best-effort guess based on the web interface's visible fields. **An implementation agent should treat this entire mapping as provisional and must perform exploratory scraping first.**

### Data Format Notes

- **Format**: HTML pages rendered by a Java-based web application. No structured data format (no JSON API, no XML feed, no OCDS).
- **Parsing approach**: Would require HTML scraping (e.g., with `lxml.html` or `beautifulsoup4`) after authenticating via a session/cookie mechanism.
- **Languages**: Notices appear in French, Dutch, or German depending on the contracting authority's region. A single notice may have parallel translations. The parser should extract whichever language version is present without filtering.
- **Authentication**: Registration required. The scraper would need to handle login (likely form-based POST to obtain a session cookie). This is a significant implementation barrier.
- **Pagination**: The search interface likely paginates results. The scraper would need to iterate through result pages.
- **Rate limiting**: Unknown. Must be discovered empirically; conservative throttling is essential to avoid being blocked.
- **Document IDs**: Belgian notices have their own identifiers (e.g., "BDA number" or "Bulletin des Adjudications" reference). These are not TED doc_ids. The `doc_id` must be prefixed or namespaced to avoid collisions with TED documents (e.g., `BE-{bda_number}`).

### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | BDA/publication number | Belgian notices have a national publication number (Bulletin des Adjudications). Must be prefixed, e.g., `BE-{number}`, to avoid collision with TED doc_ids. |
| `edition` | Unknown | Likely not available. The portal does not appear to use edition numbering. Map to `None`. |
| `version` | Unknown | Likely not available. Map to `None`. |
| `reception_id` | Unknown | TED-specific concept. Map to `None`. |
| `official_journal_ref` | BDA reference / publication reference | If the notice references a Bulletin des Adjudications issue, use that. Otherwise `None`. |
| `publication_date` | Publication date on notice page | Should be available on every notice. Parse from HTML. Date format likely `DD/MM/YYYY` (Belgian convention). |
| `dispatch_date` | Dispatch/submission date | May be present on the notice. If not visible, map to `None`. |
| `source_country` | Hard-coded `"BE"` | All notices from this portal are Belgian. |
| `contact_point` | Contact person name in buyer section | Typically shown on the notice page. |
| `phone` | Phone number in buyer section | Typically shown on the notice page. |
| `email` | Email in buyer section | Typically shown on the notice page. |
| `url_general` | URL to the notice on the portal | The permalink to the notice page itself. |
| `url_buyer` | Buyer website (if listed) | May or may not be present. |

### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | Contracting authority name | Should be present on every notice. Appears in French, Dutch, or German depending on notice language. |
| `address` | Street address of authority | Usually present in the authority details section. |
| `town` | City/town of authority | Usually present. |
| `postal_code` | Postal code of authority | Usually present. Belgian postal codes are 4 digits. |
| `country_code` | Hard-coded `"BE"` or from authority details | Almost always `"BE"` but cross-border joint procurement is possible. |
| `nuts_code` | NUTS code if listed | Belgian notices may include NUTS codes (e.g., `BE100` for Brussels). Not guaranteed. May need to derive from postal code if not explicitly present. |
| `authority_type` | Type of contracting authority | May be present (e.g., "Federal authority", "Regional authority", "Municipal authority"). **Requires code normalization** -- see Code Normalization section below. |
| `main_activity_code` | Main activity of contracting authority | May be present. **Requires code normalization.** |

### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | Notice/contract title | Should always be present. Will be in FR, NL, or DE. |
| `short_description` | Description/object of contract | Usually present as a free-text description. |
| `main_cpv_code` | Main CPV code | Belgian notices typically include CPV codes. Should be available. |
| `cpv_codes` | All listed CPV codes (main + additional) | Parse all CPV codes listed on the notice. |
| `nuts_code` | Place of performance NUTS code | May be listed. Not guaranteed for all notices. |
| `contract_nature_code` | Type of contract (works/supplies/services) | Should be available. Belgian portal likely uses the standard trichotomy. **Requires code normalization** to eForms codes (`works`, `supplies`, `services`). |
| `procedure_type` | Procedure type | Should be available. Belgian procurement uses standard EU procedure types. **Requires code normalization** -- see below. |
| `accelerated` | Accelerated procedure indicator | Unlikely to be a separate field. May be mentioned in the procedure type text (e.g., "procédure accélérée"). Would need text-based detection. Default to `False` unless explicitly indicated. |

### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | Lot title or award section title | May be present if the contract has multiple lots. |
| `contract_number` | Contract/lot number | May be present. |
| `tenders_received` | Number of tenders received | May be listed in the award result section. Not guaranteed. |
| `awarded_value` | Contract value / award amount | Should be present for award notices. Belgian notices typically show values in EUR. **Monetary parsing**: values will likely be in Belgian/French format (e.g., `1.234.567,89` or `1 234 567,89`). |
| `awarded_value_currency` | Currency | Almost always `"EUR"` for Belgian procurement. May be explicitly stated or can be defaulted to `"EUR"` if not present. **Do not hard-code** -- extract from page if available, only use `"EUR"` as last resort. |
| `contractors` | Awarded contractor(s) | See ContractorModel below. |

### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | Winning tenderer / contractor name | Should be present on award notices. |
| `address` | Contractor street address | May or may not be present. |
| `town` | Contractor city/town | May be present. |
| `postal_code` | Contractor postal code | May be present. |
| `country_code` | Contractor country | May be present. Likely `"BE"` for most awards but cross-border contractors are common in EU procurement. |
| `nuts_code` | Contractor NUTS code | Unlikely to be present for contractors. Map to `None` in most cases. |

### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | CPV code digits | Parse from the notice. Format should be standard (e.g., `45000000`). May include check digit (e.g., `45000000-7`); strip the check digit suffix to store just the code portion, consistent with existing TED parser behavior. |
| `description` | CPV code description text | May be shown next to the code on the portal. Extract if present. |

### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Procedure type (after normalization) | See Code Normalization below. Must be mapped to eForms codes. |
| `description` | Procedure type description text | Extract the original text from the portal as the description. |

### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Authority type (after normalization) | See Code Normalization below. Must be mapped to eForms codes. |
| `description` | Authority type description text | Extract the original text from the portal as the description. |

### Unmappable Schema Fields

The following fields **cannot be populated** from the Belgian portal and should always be `None`:

| Field | Model | Reason |
|---|---|---|
| `edition` | DocumentModel | TED-specific concept (OJ edition). Not applicable to national portals. |
| `version` | DocumentModel | TED-specific concept. Not applicable. |
| `reception_id` | DocumentModel | TED-specific concept. Not applicable. |
| `dispatch_date` | DocumentModel | May not be exposed on the web interface. Provisionally `None` unless discovered during implementation. |
| `url_buyer` | DocumentModel | Buyer profile URLs are rarely published on national portals. Provisionally `None` unless discovered. |
| `nuts_code` (contractor) | ContractorModel | National portals rarely provide NUTS codes for contractors. |

### Extra Portal Fields

The following fields are potentially available on the Belgian portal but **not covered by the current schema** -- flagging for review:

| Portal Field | Description | Notes |
|---|---|---|
| Enterprise number (KBO/BCE) | Belgian company registration number | Unique identifier for Belgian legal entities. Very valuable for entity resolution. Schema doesn't cover -- flagging for review. |
| Lot structure | Multiple lots per notice | The portal may expose lot-level detail beyond what our flat contract/award model captures. Schema doesn't cover -- flagging for review. |
| Estimated value | Pre-award estimated contract value | Separate from awarded value. Schema doesn't cover -- flagging for review. |
| Framework agreement indicator | Whether the contract is a framework agreement | Present on many Belgian notices. Schema doesn't cover -- flagging for review. |
| Subcontracting information | Subcontracting percentage or details | Sometimes present. Schema doesn't cover -- flagging for review. |
| Award criteria | Price/quality weighting | Often detailed on Belgian notices. Schema doesn't cover -- flagging for review. |
| Appeal/review deadline | Standstill period and appeal information | Belgian law requires specific standstill periods. Schema doesn't cover -- flagging for review. |
| Joint procurement indicator | Whether multiple authorities are procuring jointly | Sometimes present. Schema doesn't cover -- flagging for review. |
| TED cross-reference | Reference to the TED notice (for above-threshold) | Belgian above-threshold notices are also published on TED. This cross-reference could be used for deduplication. Schema doesn't cover -- flagging for review. |
| Modification notices | Contract modification details | May appear as separate notice types. Schema currently only covers original awards. Flagging for review. |

### Code Normalization

All coded values must be mapped to eForms equivalents (lowercase, hyphens) per the project convention. The specific values used on the Belgian portal are **unknown until exploratory scraping is performed**, but the expected categories and likely mappings are:

#### Procedure Types

Belgian procurement follows EU directives, so procedure types should map to standard eForms codes. Expected portal values (in FR/NL/DE) and their eForms mappings:

| Expected Belgian Value (FR) | Expected Belgian Value (NL) | eForms Code |
|---|---|---|
| Procédure ouverte | Open procedure | `open` |
| Procédure restreinte | Beperkte procedure | `restricted` |
| Procédure concurrentielle avec négociation | Mededingingsprocedure met onderhandeling | `comp-negotiation` |
| Procédure négociée sans publication préalable | Onderhandelingsprocedure zonder voorafgaande bekendmaking | `neg-wo-call` |
| Dialogue compétitif | Concurrentiegerichte dialoog | `comp-dialogue` |
| Partenariat d'innovation | Innovatiepartnerschap | `innovation` |
| Procédure négociée directe avec publication préalable | Vereenvoudigde onderhandelingsprocedure met voorafgaande bekendmaking | `neg-w-call` |

**Note**: Belgian law also has below-threshold simplified procedures (e.g., "aanvaarde factuur" / "facture acceptée" for very small amounts) that may not have direct eForms equivalents. These will need custom mapping decisions during implementation.

#### Authority Types

| Expected Belgian Value (FR) | Expected Belgian Value (NL) | eForms Code |
|---|---|---|
| Autorité fédérale | Federale overheid | `nat-fed` |
| Autorité régionale ou locale | Regionale of lokale overheid | `reg-loc-au` |
| Organisme de droit public | Publiekrechtelijke instelling | `pub-undert` |
| Pouvoir adjudicateur communal | Gemeentelijke aanbestedende overheid | `reg-loc-au` |
| Intercommunale | Intercommunale | `reg-loc-au` (closest match) |

**Note**: Belgium's complex institutional structure (federal, regional, community, provincial, municipal, intercommunal) may produce authority type values that do not map cleanly to eForms categories. The implementer should log unmapped values rather than silently dropping them.

#### Contract Nature Codes

| Expected Belgian Value (FR) | Expected Belgian Value (NL) | eForms Code |
|---|---|---|
| Travaux | Werken | `works` |
| Fournitures | Leveringen | `supplies` |
| Services | Diensten | `services` |

### Implementation Blockers

This portal is rated **Tier 3** for good reason. Before any schema mapping can be finalized, the following blockers must be resolved:

1. **Registration**: An account must be created on publicprocurement.be to access the search interface.
2. **Exploratory scraping**: After registration, the HTML structure must be inspected to determine actual field locations, CSS selectors / XPaths, and pagination mechanisms.
3. **Undocumented APIs**: The web application may make XHR/fetch calls to internal JSON APIs. Browser developer tools should be used to check for hidden API endpoints that could provide structured data, which would dramatically simplify implementation.
4. **Legal review**: Web scraping of a registration-gated government platform may have legal implications under Belgian law and the platform's terms of service.
5. **Alternative data sources**: Before investing in scraping, check whether Belgian open data portals (data.gov.be, openprocurement.be) or the BOSA open data initiative provide machine-readable procurement data that could be used instead.
