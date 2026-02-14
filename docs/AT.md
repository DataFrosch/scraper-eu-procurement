# Austria (AT)

**Feasibility: Tier 2**

## Portal

- **Name**: Bundesvergabeportal / USP eProcurement
- **URL**: https://ausschreibungen.usp.gv.at
- **Open data**: https://www.data.gv.at/

## Data Access

- **Method**: Web search portal + metadata on data.gv.at
- **Format**: XML, CSV (on data.gv.at); HTML on portal
- **Auth**: Open browse, registration for participation
- **OCDS**: No

## Coverage

All tenders under Austrian BVergG 2018 (federal, state, municipal).

## Language

German

## Notes

- Multiple regional platforms exist alongside the federal portal
- data.gv.at has general API docs but procurement-specific API documentation is sparse
- OGD metadata available since March 2019

## Schema Mapping

### Data Flow Overview

Austrian procurement core data ("Kerndaten") is published as XML files under the [Kerndaten-Verordnung (KDV)](https://ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20010591), implementing [BVergG 2018 Annex VIII](https://www.jusline.at/gesetz/bvergg_2018/paragraf/anlage8). The data architecture has three layers:

1. **Metadata on data.gv.at** -- Each contracting authority publishes a CKAN dataset on data.gv.at containing a reference to their Kerndaten source URL. The [data.gv.at CKAN API](https://www.data.gv.at/katalog/api/3/) (`package_search` with `organization=usp-ausschreibungen` or equivalent) provides discovery of all publishers.

2. **Kerndatenquelle (core data source)** -- An XML index file listing all individual Kerndaten records (URLs + last-modified timestamps). Each publisher hosts their own source, e.g. `https://opendata.bbg.gv.at/kerndaten/bbg_kerndaten_viii-2-1.xml` for the Bundesbeschaffung GmbH (BBG).

3. **Individual Kerndaten XML files** -- One XML file per procurement procedure, e.g. `https://opendata.bbg.gv.at/kerndaten/5567.xml`. These contain the actual award data fields defined in BVergG 2018 Annex VIII Section 2.

**Recommended strategy**: Use the data.gv.at CKAN API to discover all Kerndaten source URLs (step 1), parse each source to get individual Kerndaten record URLs (step 2), then fetch and parse each record (step 3). The [OffeneVergaben-Scraper](https://github.com/Forum-Informationsfreiheit/OffeneVergaben-Scraper) project (PHP/Laravel) implements this exact pipeline and serves as a reference implementation.

There are 12 XML schemas corresponding to different annexes of BVergG 2018 and BVergGKonz 2018. For contract award data, the relevant schema is **Annex VIII Section 2 Item 1** ("Kerndaten fuer Bekanntgaben" -- core data for notifications of awarded contracts).

### Data Format Notes

- **Format**: Custom Austrian XML schema (NOT eForms, NOT OCDS, NOT TED XML). The schemas were created following BVergG 2018 and are published on [data.gv.at](https://www.data.gv.at/infos/bvergg2018/) and [ref.gv.at](https://www.ref.gv.at/).
- **Language**: All data is in German.
- **Coverage threshold**: Only contracts with a value of at least EUR 50,000 (excl. VAT) must be published.
- **Temporal coverage**: Since March 1, 2019 (when the BVergG 2018 publication obligations took effect).
- **Currency**: Always EUR (Austria uses the euro).
- **Auth**: No authentication required -- all Kerndaten sources and individual records are publicly accessible.
- **Rate limits**: Not documented. Individual publishers host their own XML files, so rate limits vary by host.
- **Incremental scraping**: The Kerndatenquelle (source index) includes last-modified timestamps per record, enabling incremental updates.
- **CRITICAL LIMITATION**: The exact XML element names used in the Kerndaten schema are not well-documented publicly. The field names below are based on the BVergG 2018 Annex VIII legal text, the Kerndaten-VO regulation, and inference from search results. **Before implementation, the parser author MUST fetch a sample XML file (e.g. `https://opendata.bbg.gv.at/kerndaten/5567.xml`) and inspect the actual element names.** The XSD schema files should also be retrieved from ref.gv.at or data.gv.at if available.

### Field Mapping: Kerndaten XML (Annex VIII Section 2)

The Kerndaten XML for notifications (Bekanntgaben) is defined by BVergG 2018 Annex VIII Section 2. The fields below are derived from the legal text and regulation; **exact XML element names need verification against actual XML files**.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | Unique identifier from the Kerndatenquelle index or the XML file URL/filename | Each Kerndaten record has a unique ID in the source index. Use the numeric ID from the URL (e.g. `5567` from `kerndaten/5567.xml`) prefixed with publisher code to ensure global uniqueness, e.g. `AT-BBG-5567`. |
| `edition` | Not available | `None`. No concept of edition in Kerndaten. |
| `version` | Hardcode `"Kerndaten-AT"` | Identifies the data source format. |
| `reception_id` | Not available | `None`. TED-specific concept. |
| `official_journal_ref` | Not available | `None`. National below-threshold notices have no OJ reference. |
| `publication_date` | Last-modified timestamp from the Kerndatenquelle index, or a date element within the XML | The source index provides a timestamp per record. Alternatively, extract from XML if a publication/award date element exists. **Exact XML element name needs verification.** |
| `dispatch_date` | Not available | `None`. No dispatch concept in Kerndaten. |
| `source_country` | Hardcode `"AT"` | All Kerndaten are Austrian. |
| `contact_point` | Not expected in Kerndaten | `None`. Kerndaten is a summary format with limited contact info. **Needs verification.** |
| `phone` | Not expected in Kerndaten | `None`. **Needs verification.** |
| `email` | Not expected in Kerndaten | `None`. **Needs verification.** |
| `url_general` | Contracting authority URL if present in XML | **Needs verification.** May contain a URL to the contracting authority or to the original tender notice. |
| `url_buyer` | Not available | `None`. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | XML element for Auftraggeber (contracting authority) name | BVergG 2018 Annex VIII requires identification of the contracting authority. **Exact XML element name (e.g. `Auftraggeber/Name` or `AuftraggeberName`) needs verification.** |
| `address` | Auftraggeber address fields if present | **Needs verification.** Kerndaten may include full address or only name. |
| `town` | Auftraggeber town/city | **Needs verification.** |
| `postal_code` | Auftraggeber postal code | **Needs verification.** |
| `country_code` | Hardcode `"AT"` | All contracting authorities in Austrian Kerndaten are Austrian. If a country element exists, use it; otherwise default to `"AT"`. |
| `nuts_code` | Auftraggeber NUTS code if present | Likely not included in Kerndaten (summary format). `None` unless XML inspection reveals otherwise. |
| `authority_type` | Not expected in Kerndaten | `None`. Kerndaten is a minimal data format focused on award facts. **Needs verification.** |
| `main_activity_code` | Not expected in Kerndaten | `None`. **Needs verification.** |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | Gegenstand (subject/object of the contract) | BVergG 2018 Annex VIII requires the subject of the contract ("Gegenstand des Auftrages"). **Exact XML element name needs verification.** |
| `short_description` | Same as title, or a separate description field if available | Kerndaten likely has a single subject/description field. Use same value as title if no separate description exists. |
| `main_cpv_code` | CPV-Code element | BVergG 2018 Annex VIII requires CPV codes. **Exact XML element name (e.g. `CPV`, `CPVCode`, `CPV-Code`) needs verification.** Expected format: 8-digit CPV code (e.g. `45000000`). May or may not include the check digit suffix (`-X`). |
| `cpv_codes` | All CPV code elements | May contain main + additional CPV codes. Build `CpvCodeEntry` list from all CPV elements found. |
| `nuts_code` | NUTS code for place of performance if present | BVergG 2018 Annex VIII includes "Ort der Leistung" (place of performance). May be a NUTS code or free text. **Needs verification.** |
| `contract_nature_code` | Auftragsart (contract type) -- Lieferauftrag / Dienstleistungsauftrag / Bauauftrag | BVergG 2018 Annex VIII requires the type of contract. See code normalization section below. **Exact XML element name needs verification.** |
| `procedure_type` | Verfahrensart (procedure type) | BVergG 2018 Annex VIII requires the procedure type. See code normalization section below. **Exact XML element name needs verification.** |
| `accelerated` | Not available in Kerndaten | `False`. Kerndaten procedure types do not distinguish accelerated variants. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | Same as contract title (Gegenstand) | Kerndaten does not distinguish award title from contract title. Use the same value. |
| `contract_number` | Geschaeftszahl (business/file number) if present | BVergG 2018 Annex VIII may include a file reference number. **Exact XML element name needs verification.** |
| `tenders_received` | Anzahl der Angebote (number of tenders received) if present | BVergG 2018 Annex VIII requires "Anzahl der eingegangenen Angebote". **Exact XML element name needs verification.** |
| `awarded_value` | Zuschlagspreis or Auftragswert (award price / contract value) | BVergG 2018 Annex VIII requires the award price ("Zuschlagspreis"). Parse as float. **Exact XML element name needs verification.** The value may include or exclude VAT -- verify which convention is used. |
| `awarded_value_currency` | Hardcode `"EUR"` | Austria uses the euro. If a currency attribute exists in the XML, use it; otherwise default to `"EUR"`. |
| `contractors` | See ContractorModel below | Single award per Kerndaten record. Wrap in a single-element list. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | Auftragnehmer (contractor) name | BVergG 2018 Annex VIII requires identification of the contractor ("Auftragnehmer"). **Exact XML element name needs verification.** |
| `address` | Auftragnehmer address if present | **Needs verification.** May or may not be included in Kerndaten. |
| `town` | Auftragnehmer town if present | **Needs verification.** |
| `postal_code` | Auftragnehmer postal code if present | **Needs verification.** |
| `country_code` | Auftragnehmer country if present, else `None` | Contractors may be from any country. Do not default to `"AT"`. |
| `nuts_code` | Not expected in Kerndaten | `None`. Contractor NUTS codes are unlikely to be in the minimal Kerndaten format. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | CPV code value from XML | BVergG 2018 requires CPV codes. Expected format: 8 digits, possibly with check digit suffix (`-X`). Strip the `-X` suffix if present to match TED convention. **Exact XML element name and format need verification.** |
| `description` | Not expected in Kerndaten XML | `None`. CPV descriptions are standardized and can be looked up from a reference table if needed. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Mapped from Verfahrensart value | Austrian procedure types need mapping to eForms codes. See code normalization below. |
| `description` | Derived from mapped eForms code | Use the standard eForms description lookup after mapping. |

### Unmappable Schema Fields

These fields will be `None` for Austrian Kerndaten-sourced records:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | No edition concept in Kerndaten. |
| `DocumentModel.reception_id` | TED-specific concept. |
| `DocumentModel.official_journal_ref` | National below-threshold notices have no OJ reference. |
| `DocumentModel.dispatch_date` | No dispatch concept in Kerndaten. |
| `DocumentModel.contact_point` | Not expected in the summary Kerndaten format. Needs verification. |
| `DocumentModel.phone` | Not expected in the summary Kerndaten format. Needs verification. |
| `DocumentModel.email` | Not expected in the summary Kerndaten format. Needs verification. |
| `DocumentModel.url_buyer` | No buyer profile URL in Kerndaten. |
| `ContractingBodyModel.nuts_code` | Not expected in Kerndaten. Needs verification. |
| `ContractingBodyModel.authority_type` | Not part of the Kerndaten data model. |
| `ContractingBodyModel.main_activity_code` | Not part of the Kerndaten data model. |
| `ContractModel.accelerated` | Always `False`. Kerndaten does not track accelerated procedure status. |
| `ContractorModel.nuts_code` | Not expected in Kerndaten. |
| `CpvCodeEntry.description` | Not included in XML. Use static lookup if needed. |

### Extra Portal Fields

These fields may be available in Austrian Kerndaten but are not covered by the current schema. Flagged for review.

| Portal Field | Description | Notes |
|---|---|---|
| Geschaeftszahl (file/business number) | Internal reference number of the contracting authority | Schema doesn't cover -- flagging for review. May partially map to `AwardModel.contract_number`. |
| Schwellenbereich (threshold category) | Whether the contract is above or below EU thresholds (Oberschwellenbereich / Unterschwellenbereich) | Schema doesn't cover -- flagging for review. Useful for filtering: above-threshold contracts overlap with TED data; below-threshold are the unique value-add. |
| Geschaetzter Auftragswert (estimated contract value) | Estimated value before award | Schema doesn't cover -- flagging for review. Only the awarded value is captured. |
| Subunternehmer (subcontractor) information | Whether subcontractors were used | Schema doesn't cover -- flagging for review. BVergG 2018 Annex VIII may require subcontractor disclosure. |
| Zuschlagskriterium (award criterion) | Best price-quality ratio vs. lowest price | Schema doesn't cover -- flagging for review. |
| Rahmenvereinbarung (framework agreement) indicator | Whether this is a call-off from a framework agreement | Schema doesn't cover -- flagging for review. Framework agreements have specific data requirements under BVergG 2018. |
| Datum des Zuschlags (award date) | Date when the contract was awarded | Schema doesn't cover as a separate field -- flagging for review. Currently only `publication_date` exists. |
| Laufzeit (contract duration) | Duration of the contract | Schema doesn't cover -- flagging for review. |
| Regional publisher identity | Which contracting authority / platform published the data | Schema doesn't cover -- flagging for review. Useful for tracing data provenance since Austria has many publishers (BBG, ANKOE, WKO, state governments, etc.). |

### Code Normalization

#### Contract Nature Codes (Auftragsart)

Austrian Kerndaten uses German-language contract type values that need mapping to eForms codes. The exact values used in the XML need verification, but they are expected to follow the BVergG 2018 terminology:

| Austrian Value (expected) | eForms Code | Description |
|---|---|---|
| `Bauauftrag` or `Bauauftraege` | `works` | Works |
| `Lieferauftrag` or `Lieferauftraege` | `supplies` | Supplies |
| `Dienstleistungsauftrag` or `Dienstleistungsauftraege` | `services` | Services |

**Implementation note**: The exact German values need verification against actual XML files. They may also appear as codes (e.g. numeric codes like `1`, `2`, `4` following TED conventions) or abbreviated forms. Our existing `_normalize_contract_nature_code()` in `ted_v2.py` handles TED numeric codes and can be extended with the Austrian German-language values.

#### Procedure Type Codes (Verfahrensart)

Austrian procedure types under BVergG 2018 need mapping to eForms equivalents. The [BVergG 2018](https://www.jusline.at/gesetz/bvergg_2018) defines these procedure types:

| Austrian Procedure Type | eForms Code | Notes |
|---|---|---|
| `Offenes Verfahren` | `open` | Open procedure |
| `Nicht offenes Verfahren` | `restricted` | Restricted procedure (non-open, with prior notice) |
| `Verhandlungsverfahren mit vorheriger Bekanntmachung` | `neg-w-call` | Negotiated procedure with prior publication |
| `Verhandlungsverfahren ohne vorherige Bekanntmachung` | `neg-wo-call` | Negotiated procedure without prior publication |
| `Wettbewerblicher Dialog` | `comp-dial` | Competitive dialogue |
| `Innovationspartnerschaft` | `innovation` | Innovation partnership |
| `Direktvergabe` | `neg-wo-call` | Direct award (below-threshold). Maps to negotiated without call as nearest eForms equivalent. |
| `Direktvergabe mit vorheriger Bekanntmachung` | `neg-w-call` | Direct award with prior notice. Maps to negotiated with call as nearest eForms equivalent. |
| `Rahmenvereinbarung` | `None` | Framework agreement is not a procedure type in eForms -- it is a technique. Map to `None` or to the underlying procedure type if specified. |

**Implementation note**: The exact string values used in the XML need verification. They may be full German text (as above), abbreviated codes, or numeric values. The mapping should be case-insensitive and handle common variations. Our existing `_normalize_procedure_type()` in `ted_v2.py` can be extended with these Austrian values as a new mapping table.

Austrian below-threshold procedure types (Direktvergabe, Direktvergabe mit vorheriger Bekanntmachung) have no exact eForms equivalent since eForms was designed for above-threshold EU procurement. The mappings above use the nearest logical equivalent. Consider adding new codes (e.g. `direct-award`) if differentiation is needed.

#### Authority Type Codes

Kerndaten XML is not expected to include authority type information. If it does, the values would need mapping to eForms `buyer-legal-type` codes. **Verify against actual XML files.**

### Implementation Recommendations

1. **Start with sample XML inspection**: Before writing any parser code, fetch several sample Kerndaten XML files from different publishers (e.g. [BBG](https://opendata.bbg.gv.at/kerndaten/5567.xml), ANKOE, WKO, state government portals) and document the actual XML element names and structure. Also attempt to locate the XSD schema files on [ref.gv.at](https://www.ref.gv.at/) or [data.gv.at](https://www.data.gv.at/infos/bvergg2018/). This step is **blocking** -- the field mappings above cannot be finalized without it.

2. **Use the OffeneVergaben-Scraper as reference**: The [OffeneVergaben-Scraper](https://github.com/Forum-Informationsfreiheit/OffeneVergaben-Scraper) (PHP/Laravel) implements the complete discovery and download pipeline. Study its code to understand the CKAN API queries, Kerndatenquelle parsing, and individual XML parsing.

3. **Multi-publisher discovery**: Unlike most national portals, Austrian data is federated across many publishers. The scraper must discover all publishers via the data.gv.at CKAN API, track their individual Kerndatenquelle URLs, and iterate across all of them. Expect dozens of publishers (BBG, ANKOE, various state governments, WKO branches, etc.).

4. **Deduplication with TED**: Above-threshold Austrian contracts (`Oberschwellenbereich`) are also published on TED. Use the threshold category field (`Schwellenbereich`) if available to identify overlap, or rely on title/contracting-body/value matching. Below-threshold contracts (`Unterschwellenbereich` and `Direktvergabe`) are the unique value-add of this portal.

5. **Incremental updates**: The Kerndatenquelle index includes last-modified timestamps. Store the last-seen timestamp per publisher and only fetch records newer than that on subsequent runs.

6. **`doc_id` generation**: Since Kerndaten records do not have a globally unique ID, construct one from the publisher identifier and the record's numeric ID within that publisher's system, e.g. `AT-BBG-5567`. This prevents collisions across publishers.
