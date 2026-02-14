# Lithuania (LT)

**Feasibility: Tier 1**

## Portal

- **Name**: CVP IS (Central Public Procurement Information System)
- **URL**: https://viesiejipirkimai.lt (new system since Dec 2024)
- **Previous**: https://cvpp.eviesiejipirkimai.lt/
- **Open data**: https://vpt.lrv.lt/en/links/open-data-of-ppo
- **OCP Registry**: https://data.open-contracting.org/en/publication/68

## Data Access

- **Method**: API + downloadable datasets
- **Format**: JSON, CSV, Excel (OCDS format)
- **Auth**: Open
- **OCDS**: Yes

## Coverage

All public procurement (single portal for all procedures). Supplements TED for below-threshold.

## Language

Lithuanian (English info available)

## Notes

- Strong commitment to open data
- Used open contracting data effectively during COVID-19 response (1,214 contracts published)
- New system launched December 2024

## Schema Mapping

### Data Sources

Lithuania has two OCDS data sources:

1. **OpenTender/Digiwhist** (https://opentender.eu/lt) -- OCDS data converted from TED + national CVP IS data. Available via OCP Data Registry (publication 68). OCID prefix: `ocds-70d2nz`. Date range: Jan 2006 -- Dec 2024. Updated weekly. This is the source indexed by Kingfisher Collect (`lithuania_digiwhist` spider).
2. **VPT Open Data** (https://atviriduomenys.vpt.lt/) -- Native OCDS published directly by the Public Procurement Office (VPT). Covers 2017+ data from the CVP IS system.

**Recommended primary source**: OpenTender/Digiwhist bulk JSONL download, because it has wider date coverage (2006+), is already in OCDS format, and combines TED + national data. The VPT open data portal should be investigated as a secondary/validation source. The new viesiejipirkimai.lt system (Dec 2024+) may eventually supersede both, but its API is not yet documented.

### Data Format Notes

- **Format**: OCDS 1.1 release packages as JSONL (gzipped). Each line is one JSON release object representing a contracting process.
- **Download URL pattern**: Bulk download from https://opentender.eu/lt/download -- one `.jsonl.gz` file per year, or a single file for all years.
- **Parsing**: Standard JSON parsing (one `json.loads()` per line). Decompress gzip first.
- **Character encoding**: UTF-8.
- **Language**: Data values (titles, descriptions, organization names) are in Lithuanian. Field names follow OCDS English schema.
- **One release per contracting process**: Unlike TED which has one XML per document, OCDS groups all releases for a contracting process together. A single release may contain multiple awards (one per lot). The parser must handle the OCDS structure where awards reference suppliers via organization IDs in the top-level `parties` array.

### Field Mapping Tables

OCDS structures data differently from our schema. Organizations (buyers, suppliers) live in a top-level `parties` array and are referenced by ID from `buyer`, `awards[].suppliers[]`, etc. The mapping below shows the OCDS JSON path for each schema field.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `ocid` | OCDS contracting process identifier (e.g., `ocds-70d2nz-...`). Globally unique. Use as-is. |
| `edition` | -- | `None`. OCDS has no edition concept. |
| `version` | `id` | The release ID could serve as a version identifier. |
| `reception_id` | -- | `None`. No reception ID in OCDS. |
| `official_journal_ref` | -- | `None`. No OJ reference in national portal data. TED-sourced records may have this in extensions but it is not standard OCDS. |
| `publication_date` | `date` | ISO 8601 datetime (e.g., `2024-01-15T00:00:00Z`). Parse to `date`. |
| `dispatch_date` | `tender.tenderPeriod.startDate` | Approximate mapping. OCDS has no direct dispatch date. Could also be `None`. |
| `source_country` | `"LT"` (hardcoded) | All data from this portal is Lithuanian. |
| `contact_point` | `buyer.contactPoint.name` or `parties[buyer].contactPoint.name` | May not be populated in all releases. |
| `phone` | `parties[buyer].contactPoint.telephone` | Look up the buyer party by matching `buyer.id` to `parties[].id`. |
| `email` | `parties[buyer].contactPoint.email` | Same lookup as phone. |
| `url_general` | `parties[buyer].contactPoint.url` | General URL of the buyer organization. |
| `url_buyer` | `parties[buyer].details.buyerProfile` | Buyer profile URL, if present. This is an OCDS extension field; may not always be populated. |

#### ContractingBodyModel

The contracting body is the `buyer` in OCDS. Look up `buyer.id` in the `parties` array to get full details.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[buyer].name` | Required in OCDS. |
| `address` | `parties[buyer].address.streetAddress` | May be `null`. |
| `town` | `parties[buyer].address.locality` | May be `null`. |
| `postal_code` | `parties[buyer].address.postalCode` | May be `null`. |
| `country_code` | `parties[buyer].address.countryName` | OCDS uses country name, not ISO code. Need to map `"Lithuania"` / `"Lietuva"` to `"LT"`. Alternatively hardcode `"LT"` for this portal. |
| `nuts_code` | -- | `None`. OCDS does not have a standard NUTS code field. Some publishers include it in extensions or `parties[buyer].address.region`, but this is not guaranteed. |
| `authority_type` | `parties[buyer].details.classifications` | OCDS extension field. If populated, look for a classification with `scheme` = `"eu-buyer-legal-type"` or similar. The `id` value would need mapping to eForms codes (see Code Normalization below). **Likely `None`** for OpenTender data -- authority type classification is not standard OCDS. |
| `main_activity_code` | `parties[buyer].details.classifications` | Same as authority_type -- look for `scheme` matching activity codes. **Likely `None`** in practice. |

#### ContractModel

In OCDS, contract-level data is split between `tender` (procedure-level) and individual `awards`/`contracts` entries.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `tender.title` | The procurement title. Should always be present. Will be in Lithuanian. |
| `short_description` | `tender.description` | May be `null`. |
| `main_cpv_code` | `tender.items[0].classification.id` | OCDS uses `items[].classification` with `scheme: "CPV"`. The first item's classification is typically the main CPV. Need to verify `scheme == "CPV"`. |
| `cpv_codes` | `tender.items[*].classification` + `tender.items[*].additionalClassifications[*]` | Collect all classifications where `scheme == "CPV"`. Each has `id` (the code) and `description`. |
| `nuts_code` | `tender.items[*].deliveryLocation.gazetteer.identifiers` or `tender.items[*].deliveryAddress.region` | Not standard OCDS. **Likely `None`**. Some publishers include NUTS in delivery addresses but this is not guaranteed. |
| `contract_nature_code` | `tender.mainProcurementCategory` | Values: `"goods"`, `"works"`, `"services"`. Must map to eForms codes (see Code Normalization below). |
| `procedure_type` | `tender.procurementMethod` + `tender.procurementMethodDetails` | `procurementMethod` is a closed codelist: `"open"`, `"selective"`, `"limited"`, `"direct"`. `procurementMethodDetails` has the free-text detail. Must map to eForms procedure type codes (see Code Normalization below). |
| `accelerated` | `tender.procurementMethodDetails` | OCDS has no dedicated accelerated flag. If `procurementMethodDetails` contains "accelerated" (or Lithuanian equivalent "pagreitinta"), set `True`. Otherwise `False`. **Likely always `False`** in practice. |

#### AwardModel

Each entry in the OCDS `awards` array maps to one AwardModel. A single contracting process can have multiple awards (one per lot).

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `awards[i].title` | May be `null`. Not always populated in OCDS. |
| `contract_number` | `awards[i].id` or `contracts[i].id` | OCDS award ID. Could also use `contracts[i].id` if a matching contract exists (linked via `contracts[i].awardID`). |
| `tenders_received` | `tender.numberOfTenderers` | This is at the tender level, not per award. In multi-lot procurements, the per-lot count may not be available. Apply the same value to all awards from the same tender, or set `None` if it seems wrong. |
| `awarded_value` | `awards[i].value.amount` | Numeric value. May be `null`. |
| `awarded_value_currency` | `awards[i].value.currency` | ISO 4217 3-letter code (e.g., `"EUR"`, `"LTL"` for pre-2015 data in Litas). |
| `contractors` | `awards[i].suppliers[*]` | Array of organization references. Each has `id` and `name`. Look up full details in `parties` array by matching `suppliers[j].id` to `parties[].id`. |

#### ContractorModel

Each supplier in `awards[i].suppliers` maps to a ContractorModel. Full organization details come from the `parties` array.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `parties[supplier].name` | Required field in OCDS. |
| `address` | `parties[supplier].address.streetAddress` | May be `null`. |
| `town` | `parties[supplier].address.locality` | May be `null`. |
| `postal_code` | `parties[supplier].address.postalCode` | May be `null`. |
| `country_code` | `parties[supplier].address.countryName` | Same issue as buyer -- need to map country name to ISO code. |
| `nuts_code` | -- | `None`. Not in standard OCDS. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `tender.items[*].classification.id` where `scheme == "CPV"` | CPV code string (e.g., `"45000000"`). May or may not include the check digit. |
| `description` | `tender.items[*].classification.description` | CPV description in Lithuanian. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Derived from `tender.procurementMethod` + `tender.procurementMethodDetails` | Must be mapped to eForms codes. See Code Normalization below. |
| `description` | `tender.procurementMethodDetails` | Free-text procedure description. Often in Lithuanian. |

#### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `parties[buyer].details.classifications[*].id` | If a classification with an authority-type scheme exists. **Likely unavailable** in OpenTender data. |
| `description` | `parties[buyer].details.classifications[*].description` | Same caveat. |

### Unmappable Schema Fields

The following schema fields have no mapping in OCDS and should be set to `None`:

| Field | Model | Reason |
|---|---|---|
| `edition` | DocumentModel | No OCDS equivalent. |
| `reception_id` | DocumentModel | No OCDS equivalent. |
| `official_journal_ref` | DocumentModel | National portal data has no OJ reference. |
| `dispatch_date` | DocumentModel | No direct OCDS equivalent. |
| `nuts_code` | ContractingBodyModel | Not in standard OCDS. Might appear in extensions but cannot be relied upon. |
| `authority_type` | ContractingBodyModel | Not standard OCDS. OpenTender data unlikely to include buyer-legal-type classifications. |
| `main_activity_code` | ContractingBodyModel | Not standard OCDS. |
| `nuts_code` | ContractModel | Not standard OCDS for delivery location. |
| `accelerated` | ContractModel | No dedicated OCDS field. Always `False` unless detected in `procurementMethodDetails` text. |
| `nuts_code` | ContractorModel | Not in standard OCDS. |

### Extra Portal Fields

The following OCDS fields are available but not covered by the current schema. Flagged for review:

| Portal Field | Description | Notes |
|---|---|---|
| `tender.tenderPeriod` | Start/end dates of the tender period | schema doesn't cover -- flagging for review |
| `tender.awardPeriod` | Start/end dates of the award period | schema doesn't cover -- flagging for review |
| `awards[i].date` | Date of the award decision | schema doesn't cover -- flagging for review. Could be useful for time-to-award analysis. |
| `awards[i].status` | Award status (`"active"`, `"cancelled"`, `"unsuccessful"`) | schema doesn't cover -- flagging for review. Useful for filtering cancelled awards. |
| `contracts[i].period` | Contract execution period | schema doesn't cover -- flagging for review |
| `contracts[i].value` | Contract value (may differ from award value) | schema doesn't cover -- flagging for review |
| `contracts[i].dateSigned` | Date the contract was signed | schema doesn't cover -- flagging for review |
| `parties[].identifier.id` | Organization registration number (e.g., Lithuanian company code) | schema doesn't cover -- flagging for review. Very valuable for entity resolution. |
| `parties[].identifier.scheme` | Registration scheme (e.g., `"LT-RC"` for Lithuanian Register of Legal Entities) | schema doesn't cover -- flagging for review |
| `tender.numberOfTenderers` | Total number of tenderers | schema has `tenders_received` per award, but OCDS provides it per tender. Mapping works for single-lot but is approximate for multi-lot. |
| `tender.value` | Estimated total procurement value | schema doesn't cover -- flagging for review |
| `tender.procurementMethodRationale` | Justification for non-open procedure | schema doesn't cover -- flagging for review |
| `tender.lots[*]` | Lot-level breakdown (if lots extension is used) | schema doesn't cover -- flagging for review |
| `planning.budget` | Budget information | schema doesn't cover -- flagging for review |

### Code Normalization

Our schema uses exact eForms codes (lowercase, hyphens). OCDS uses its own codelists. The following mappings are needed:

#### Contract Nature Code (`tender.mainProcurementCategory` to eForms)

| OCDS Value | eForms Code | Notes |
|---|---|---|
| `"goods"` | `"supplies"` | OCDS uses "goods", eForms uses "supplies" |
| `"works"` | `"works"` | Direct match |
| `"services"` | `"services"` | Direct match |

#### Procedure Type (`tender.procurementMethod` to eForms)

OCDS has a closed 4-value codelist for `procurementMethod`. The mapping to eForms procedure types is lossy -- OCDS groups many eForms types together. Use `procurementMethodDetails` for disambiguation when possible.

| OCDS `procurementMethod` | Likely eForms Code | Notes |
|---|---|---|
| `"open"` | `"open"` | Direct match. |
| `"selective"` | `"restricted"` | OCDS "selective" covers eForms "restricted", "comp-dial", "innovation". Default to `"restricted"` unless `procurementMethodDetails` indicates competitive dialogue or innovation partnership. |
| `"limited"` | `"neg-w-call"` or `"neg-wo-call"` | Ambiguous. "limited" covers negotiated procedures with and without prior call. Check `procurementMethodDetails` for disambiguation. If text contains "without" / "be isankstinio" (Lithuanian), map to `"neg-wo-call"`. Otherwise default to `"neg-w-call"`. |
| `"direct"` | `"neg-wo-call"` | Direct award without competition maps to negotiated without prior call. |

**Implementation note**: The `procurementMethodDetails` field is free-text and often in Lithuanian. A best-effort keyword mapping should be implemented, with unmappable values logged as warnings. This is inherently lossy -- accept `None` when the mapping is ambiguous.

#### Authority Type

OCDS has no standard codelist for authority/buyer legal type. If `parties[buyer].details.classifications` contains a classification with a recognized scheme, map it. Otherwise set to `None`.

If a classification scheme matching eForms buyer-legal-type is found, the values should already be eForms codes (`"cga"`, `"ra"`, `"la"`, `"body-pl"`, etc.) and can be used directly. This is unlikely for OpenTender data.

#### Country Code

OCDS `address.countryName` is a free-text string (e.g., `"Lithuania"`, `"Lietuva"`, `"Latvija"`). Must be mapped to ISO 3166-1 alpha-2 codes. Options:
- Hardcode `"LT"` for the buyer (all data is from Lithuania).
- For suppliers, use a country name lookup table. The `pycountry` library or a simple dictionary of common Lithuanian-language country names can handle this.
- Alternatively, some OCDS publishers include the country code extension (`address.country` as ISO code). Check if OpenTender data includes this.

### Implementation Considerations

1. **OCDS release vs. record**: Prefer compiled records if available (they merge all releases for a process). If only releases are available, use the latest release per `ocid` (the one with the most recent `date`).
2. **Multi-lot handling**: A single OCDS release can contain multiple awards (one per lot). Each award becomes a separate AwardModel, but they all share the same DocumentModel, ContractingBodyModel, and ContractModel. This mirrors how TED multi-lot notices work.
3. **Award-only filtering**: Filter to releases where `tag` includes `"award"` or `"contract"`. Skip planning-only or tender-only releases.
4. **Deduplication with TED**: OpenTender data includes TED-sourced above-threshold data. To avoid duplicates, either: (a) filter to below-threshold only (check if `tender.value.amount` is below EU thresholds), or (b) skip records whose `ocid` can be traced back to a TED document ID already in the database. The OCID prefix `ocds-70d2nz` is OpenTender-specific, so matching by contracting body + title + date may be needed.
5. **Currency**: Pre-2015 Lithuanian data may use `"LTL"` (Lithuanian Litas). The exchange rate table already handles currency conversion. Post-2015 data should be `"EUR"`.
