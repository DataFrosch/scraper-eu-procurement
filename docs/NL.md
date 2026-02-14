# Netherlands (NL)

**Feasibility: Tier 1**

## Portal

- **Name**: TenderNed
- **URL**: https://www.tenderned.nl/
- **Swagger API**: https://www.tenderned.nl/info/swagger/
- **GitHub examples**: https://github.com/tenderned-analyse/code-example-tn-xml-api
- **Open data**: https://data.overheid.nl/en/dataset/aankondigingen-van-overheidsopdrachten---tenderned
- **OCP Registry**: https://data.open-contracting.org/en/publication/133

## Data Access

- **Method**: REST API (XML API for bulk data export)
- **Format**: XML (primary), OCDS format available
- **Auth**: Free API key required (request via functioneelbeheer@tenderned.nl)
- **OCDS**: Yes

## Coverage

All public procurement announcements. All announcements are public.

## Language

Dutch (English info pages available)

## Notes

- Swagger docs auto-updated with releases; GitHub code examples
- n8n workflow available: https://n8n.io/workflows/10076-automate-dutch-public-procurement-data-collection-with-tenderned/
- OCP case study on data excellence: https://www.open-contracting.org/2023/07/05/striving-for-data-excellence-how-the-netherlands-tenderned-is-enabling-procurement-insights-for-government-and-public-users/
- Free API key — request by email

## Schema Mapping

### Recommended Data Path

TenderNed offers two data paths:

1. **XML API** (`/papi/tenderned-rs-tns/v2/publicaties/{pub_id}/public-xml`): Returns individual publications in eForms XML format. Requires paginated listing via the JSON search endpoint first, then fetching each publication's XML individually. Requires Basic Auth credentials (username + password requested by email).

2. **OCDS JSONL bulk download** (via data.overheid.nl / data.open-contracting.org): Half-yearly JSONL dumps in OCDS format, covering data from 2016 onwards. Each line is one OCDS release. Uses the OCDS for eForms profile with extensions (bids, lots, bid opening, covered by, legal basis, organization classification, organization scale, other requirements, sources, techniques, tender classification). Available in JSON, Excel, and CSV formats.

**Recommendation**: Use the **OCDS JSONL bulk download** as the primary data path. It avoids per-publication API calls and rate limiting, provides structured OCDS JSON (easier to parse than eForms XML), and covers all publication types. Filter to `"tag": ["award"]` releases to get contract award notices. For incremental updates, the XML API can supplement with publications newer than the latest bulk dump.

If using the XML API path instead, the returned XML is standard eForms format and can potentially reuse the existing `eforms_ubl.py` parser with minor adjustments (the doc_id would come from TenderNed's publication ID rather than the filename).

### Data Format Notes

- **OCDS path**: JSONL (one JSON object per line), each line is an OCDS release conforming to OCDS 1.1 with the eForms profile. Standard JSON parsing with `json.loads()` per line.
- **XML API path**: eForms UBL XML, same format as TED eForms (2025+). Can use `lxml.etree` parsing. The search/listing endpoint (`/papi/tenderned-rs-tns/v2/publicaties?page=0&size=100&publicatieType=AGO&publicatieDatumVanaf=YYYY-MM-DD&publicatieDatumTot=YYYY-MM-DD`) returns JSON with pagination metadata (`totalElements`, `totalPages`, `size`, `number`, `contents[]`).
- **Auth**: Both paths require Basic Auth (username/password). Request credentials from functioneelbeheer@tenderned.nl.
- **Coverage**: OCDS data from 2016 onwards. XML API may have older data but this is unconfirmed.
- **Language**: All data is in Dutch. Field values (titles, descriptions, organization names) will be in Dutch.
- **Currency**: Almost always EUR for Dutch procurement, but the currency field should still be read from the data.

### Field Mapping Tables

The tables below map schema fields to OCDS JSON paths (primary recommendation). The XML API path would use the same eForms XML structure already handled by `eforms_ubl.py`.

In OCDS, organizations (buyers, suppliers) are stored in a top-level `parties[]` array with role tags. References from `buyer`, `awards[].suppliers[]`, etc. point into `parties[]` by `id`. The mapping below shows the resolved paths.

#### DocumentModel

| Schema Field | OCDS JSON Path | Notes |
|---|---|---|
| `doc_id` | `ocid` or `id` | Use `ocid` (contracting process ID) as the document identifier. Format: `ocds-xxxxxx-{tenderned_id}`. Alternatively use `id` (release ID) if multiple releases per process. |
| `edition` | _derive from `date`_ | Not a direct OCDS field. Could derive from publication date (e.g. `YYYYDDD` format) to match TED convention, or set to `None`. |
| `version` | `"OCDS-TenderNed"` | Hardcode to identify the source format. Not present in OCDS data. |
| `reception_id` | `None` | OCDS does not have a reception ID concept. |
| `official_journal_ref` | `None` | National publications do not appear in the EU Official Journal. If the notice was also published on TED, the TED reference may appear in extensions but this is not guaranteed. |
| `publication_date` | `date` | ISO 8601 datetime string (e.g. `"2024-06-15T10:00:00Z"`). Parse date portion only. |
| `dispatch_date` | `None` | Not available in OCDS. Could potentially be derived from `date` but semantically different. Set to `None`. |
| `source_country` | `"NL"` | Hardcode. All TenderNed publications are Dutch. Could also be read from `buyer.address.countryName` or `parties[buyer].address.countryName` if present. |
| `contact_point` | `parties[buyer].contactPoint.name` | The buyer's contact point name. May not always be populated. |
| `phone` | `parties[buyer].contactPoint.telephone` | Buyer's phone number. |
| `email` | `parties[buyer].contactPoint.email` | Buyer's email address. |
| `url_general` | `parties[buyer].contactPoint.url` | Buyer's website URL. May also appear in `parties[buyer].details.url`. |
| `url_buyer` | `parties[buyer].contactPoint.url` | Same as above; OCDS does not distinguish between general URL and buyer profile URL. |

#### ContractingBodyModel

| Schema Field | OCDS JSON Path | Notes |
|---|---|---|
| `official_name` | `parties[buyer].name` | The buyer organization's name. Required in OCDS. |
| `address` | `parties[buyer].address.streetAddress` | Street address of the buyer. |
| `town` | `parties[buyer].address.locality` | City/town of the buyer. |
| `postal_code` | `parties[buyer].address.postalCode` | Postal code. |
| `country_code` | `parties[buyer].address.countryName` | OCDS uses full country name by default, but eForms profile may include ISO code. May need to map `"Netherlands"` / `"Nederland"` to `"NL"`. Check if `parties[buyer].address.country` (ISO code) is present in the eForms profile. |
| `nuts_code` | `parties[buyer].address.region` | OCDS eForms profile maps NUTS codes here. The exact field name depends on extensions used. **Needs verification against actual data** -- may be absent or in a different location. |
| `authority_type` | `parties[buyer].details.classifications[]` | The organization classification extension provides buyer type. See "Code Normalization" section below for mapping. **Needs verification** -- may use `parties[buyer].details.scale` or a classification scheme. |
| `main_activity_code` | `parties[buyer].details.classifications[]` | Main activity may appear as a separate classification entry with a different scheme. **Needs verification against actual data.** |

#### ContractModel

| Schema Field | OCDS JSON Path | Notes |
|---|---|---|
| `title` | `tender.title` | The tender/contract title. |
| `short_description` | `tender.description` | The tender description. |
| `main_cpv_code` | `tender.items[0].classification.id` | The main CPV code. In OCDS, items use `classification` with `scheme: "CPV"`. The first item's classification is typically the main CPV. |
| `cpv_codes` | `tender.items[].classification.id` + `tender.items[].additionalClassifications[].id` | Collect all CPV codes from all items. Filter by `scheme == "CPV"`. Each entry has `id` (code) and `description`. |
| `nuts_code` | `tender.items[].deliveryLocation.region` or `tender.deliveryAddresses[].region` | Performance location NUTS code. Depends on eForms extensions. **Needs verification against actual data.** |
| `contract_nature_code` | `tender.mainProcurementCategory` | OCDS uses `"goods"`, `"works"`, `"services"`. See "Code Normalization" section for mapping to eForms codes. |
| `procedure_type` | `tender.procurementMethod` + `tender.procurementMethodDetails` | OCDS uses coarse-grained `procurementMethod` (`"open"`, `"selective"`, `"limited"`, `"direct"`) and freetext `procurementMethodDetails` for the specific procedure name. See "Code Normalization" section. |
| `accelerated` | `tender.procurementMethodRationale` or eForms extension field | OCDS does not have a dedicated accelerated boolean. If the eForms profile includes BT-106, it may appear in an extension field. Otherwise check `procurementMethodDetails` for keywords like "versneld" (Dutch for accelerated). **Likely `False` by default; needs verification.** |

#### AwardModel

| Schema Field | OCDS JSON Path | Notes |
|---|---|---|
| `award_title` | `awards[].title` | Award title. May be the same as the tender title or lot-specific. |
| `contract_number` | `contracts[].id` or `awards[].contractPeriod` | OCDS separates awards and contracts. The contract number may be in `contracts[].id` linked via `contracts[].awardID`. May also appear in `awards[].id`. |
| `tenders_received` | `bids.statistics[].value` where `measure == "numberOfBids"` | Requires the bids extension. Filter statistics by `relatedLot` if lot-specific. **May not always be populated.** |
| `awarded_value` | `awards[].value.amount` | The award value as a number. |
| `awarded_value_currency` | `awards[].value.currency` | ISO 4217 currency code (e.g. `"EUR"`). |
| `contractors` | `awards[].suppliers[]` | Array of supplier references. Resolve via `parties[]` by matching `suppliers[].id` to `parties[].id`. See ContractorModel below. |

#### ContractorModel

| Schema Field | OCDS JSON Path | Notes |
|---|---|---|
| `official_name` | `parties[supplier].name` | Resolved from `awards[].suppliers[].id` -> `parties[].name` where role includes `"supplier"`. |
| `address` | `parties[supplier].address.streetAddress` | Supplier street address. |
| `town` | `parties[supplier].address.locality` | Supplier city/town. |
| `postal_code` | `parties[supplier].address.postalCode` | Supplier postal code. |
| `country_code` | `parties[supplier].address.countryName` | May need mapping from full name to ISO code. See ContractingBodyModel note above. |
| `nuts_code` | `parties[supplier].address.region` | NUTS code for supplier location. **May not be populated for suppliers.** |

#### CpvCodeEntry

| Schema Field | OCDS JSON Path | Notes |
|---|---|---|
| `code` | `tender.items[].classification.id` (where `scheme == "CPV"`) | The CPV code string (e.g. `"45000000"`). May or may not include the check digit suffix (e.g. `"45000000-7"`). Normalize to match existing CPV code format in the database. |
| `description` | `tender.items[].classification.description` | Human-readable CPV description. Available in OCDS. |

#### ProcedureTypeEntry

| Schema Field | OCDS JSON Path | Notes |
|---|---|---|
| `code` | _derived from `tender.procurementMethod` + `tender.procurementMethodDetails`_ | Requires mapping. See "Code Normalization" section. |
| `description` | `tender.procurementMethodDetails` | The freetext procedure type name (e.g. `"Openbare procedure"`, `"Niet-openbare procedure"`). In Dutch. |

### Unmappable Schema Fields

These schema fields cannot be populated from TenderNed OCDS data and should be set to `None`:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | No OCDS equivalent. Could be synthesized from publication date but not semantically equivalent to OJ edition numbers. |
| `DocumentModel.reception_id` | EU-specific concept (TED reception ID). Not applicable to national portals. |
| `DocumentModel.official_journal_ref` | National publications are not in the EU Official Journal. |
| `DocumentModel.dispatch_date` | OCDS does not track the dispatch-to-publication-office date. |
| `DocumentModel.url_buyer` | OCDS does not distinguish general URL from buyer profile URL. `url_general` and `url_buyer` would contain the same value or one would be `None`. |

### Extra Portal Fields

These fields are available in TenderNed OCDS data but are not covered by the current schema. Flagged for review:

| Portal Field | OCDS Path | Notes |
|---|---|---|
| Lot information | `tender.lots[]` | TenderNed uses the lots extension. Lots have their own titles, descriptions, values, and CPV codes. The current schema flattens everything to one contract. Schema doesn't cover -- flagging for review. |
| Estimated value | `tender.value.amount` / `tender.value.currency` | The estimated/maximum contract value (as opposed to awarded value). Schema doesn't cover -- flagging for review. |
| Award date | `awards[].date` | The date the award was made. Could be useful for analysis. Schema doesn't cover -- flagging for review. |
| Award status | `awards[].status` | Whether the award is `"active"`, `"cancelled"`, `"unsuccessful"`. Schema doesn't cover -- flagging for review. |
| Contract period | `awards[].contractPeriod.startDate` / `.endDate` | Duration of the awarded contract. Schema doesn't cover -- flagging for review. |
| Bid statistics | `bids.statistics[]` | Detailed bid statistics beyond just count (e.g. SME bids, electronic bids). Schema doesn't cover -- flagging for review. |
| Organization identifiers | `parties[].identifier.id` / `.scheme` | Legal entity identifiers (e.g. KVK number for Dutch entities). Schema doesn't cover -- flagging for review. |
| Organization scale | `parties[].details.scale` | Whether organization is `"micro"`, `"small"`, `"medium"`, `"large"`. From organization-scale extension. Schema doesn't cover -- flagging for review. |
| Legal basis | `tender.legalBasis.id` / `.description` | The legal framework for the procurement (EU directives, national law). Schema doesn't cover -- flagging for review. |
| Tender value breakdown by lot | `tender.lots[].value` | Per-lot estimated values. Schema doesn't cover -- flagging for review. |
| Award value tax information | `awards[].value.hasTax` / `.tax` | Whether the award value includes tax. TenderNed-specific extension. Schema doesn't cover -- flagging for review. |
| Delivery addresses | `tender.deliveryAddresses[]` | Specific delivery/performance locations. Schema only has one NUTS code. Schema doesn't cover -- flagging for review. |

### Code Normalization

The following code values require mapping from OCDS/TenderNed values to eForms equivalents used in our database.

#### Contract Nature Codes (`contract_nature_code`)

OCDS uses `tender.mainProcurementCategory` with values that map directly:

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"goods"` | `"supplies"` | OCDS "goods" = eForms "supplies" |
| `"works"` | `"works"` | Direct match |
| `"services"` | `"services"` | Direct match |

Note: OCDS does not have a `"combined"` category. If a TenderNed notice covers multiple categories, it will likely use the dominant one.

#### Procedure Type Codes (`procedure_type`)

OCDS `tender.procurementMethod` is coarse-grained (only 4 values). The freetext `tender.procurementMethodDetails` contains the specific procedure name (in Dutch). Mapping requires combining both fields:

| OCDS `procurementMethod` | `procurementMethodDetails` (Dutch) | eForms Code | Notes |
|---|---|---|---|
| `"open"` | `"Openbare procedure"` | `"open"` | Direct match |
| `"selective"` | `"Niet-openbare procedure"` | `"restricted"` | OCDS "selective" = eForms "restricted" |
| `"selective"` | `"Concurrentiegerichte dialoog"` | `"comp-dial"` | Competitive dialogue |
| `"selective"` | `"Innovatiepartnerschap"` | `"innovation"` | Innovation partnership |
| `"limited"` | `"Onderhandelingsprocedure met voorafgaande oproep tot mededinging"` | `"neg-w-call"` | Negotiated with prior call |
| `"limited"` | `"Onderhandelingsprocedure zonder voorafgaande bekendmaking"` | `"neg-wo-call"` | Negotiated without prior publication |
| `"direct"` | various | `"neg-wo-call"` | Direct award, maps to negotiated without call |

**Important**: The `procurementMethodDetails` values listed above are approximate Dutch translations. The exact strings used by TenderNed must be verified against actual data. A robust implementation should:
1. Build the mapping from observed `procurementMethodDetails` values in a sample dataset.
2. Fall back to the coarse OCDS `procurementMethod` when `procurementMethodDetails` is missing or unrecognized.
3. Log warnings for unrecognized values, consistent with the project's fail-loud principle.

Fallback mapping when `procurementMethodDetails` is unavailable:

| OCDS `procurementMethod` | eForms Code | Notes |
|---|---|---|
| `"open"` | `"open"` | Direct match |
| `"selective"` | `"restricted"` | Best approximation |
| `"limited"` | `"neg-w-call"` | Best approximation |
| `"direct"` | `"neg-wo-call"` | Best approximation |

#### Authority Type Codes (`authority_type`)

OCDS does not have a single standard field for authority type. TenderNed's eForms profile uses the organization classification extension (`parties[].details.classifications[]`). The mapping depends on the classification scheme and values used. **The exact field location and values must be verified against actual TenderNed OCDS data.** Expected mappings based on eForms codes:

| TenderNed / eForms Value | eForms Code | Description |
|---|---|---|
| `"ministry"` / `"cga"` | `"cga"` | Central government authority |
| `"regional-authority"` / `"ra"` | `"ra"` | Regional authority |
| `"local-authority"` / `"la"` | `"la"` | Local authority |
| `"body-governed-by-public-law"` / `"body-pl"` | `"body-pl"` | Body governed by public law |
| `"eu-institution"` | `"eu-ins-bod-ag"` | EU institution (unlikely for NL national data) |

**This mapping is speculative.** The actual classification scheme and values in TenderNed OCDS data must be inspected before implementation.

#### Accelerated Procedure (`accelerated`)

OCDS does not have a dedicated field for BT-106 (accelerated procedure). Options:
1. Check if the eForms profile adds this as an extension field (inspect actual data).
2. Parse `tender.procurementMethodDetails` for Dutch keywords: `"versneld"`, `"versnelde"`.
3. Default to `False` if no signal found.

### Implementation Notes

1. **Doc ID strategy**: Use the OCDS `ocid` stripped of the publisher prefix as `doc_id`. The format is typically `ocds-xxxxxx-{tenderned_id}`. Prefix with `NL-` to avoid collisions with TED doc IDs (e.g. `NL-{tenderned_id}`).

2. **Award filtering**: OCDS releases have a `tag` field. Filter to releases containing `"award"` or `"contract"` to get only contract award notices. Skip releases tagged only with `"tender"`, `"planning"`, etc.

3. **Party resolution**: OCDS stores all organizations in a flat `parties[]` array with `roles[]` tags (`"buyer"`, `"supplier"`, `"tenderer"`, etc.). The `buyer` field and `awards[].suppliers[]` contain references by `id` only. The parser must resolve these references against `parties[]` to extract full organization details.

4. **Multiple awards per release**: A single OCDS release can contain multiple `awards[]` entries (one per lot). Each award may have different suppliers and values. This maps naturally to the schema's `awards: List[AwardModel]`.

5. **Idempotency**: The `doc_id` derived from `ocid` ensures re-importing the same data is idempotent, consistent with the existing TED import behavior.

6. **Swagger API exploration**: The implementor should request API credentials and explore the live Swagger docs at https://www.tenderned.nl/info/swagger/ to verify all field paths above against actual response data. The OCDS field paths documented here are based on the OCDS 1.1 standard with eForms profile, but TenderNed's specific implementation may have deviations.
