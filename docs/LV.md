# Latvia (LV)

**Feasibility: Tier 2**

## Portal

- **Name**: EIS (Electronic Procurement System / Elektronisko Iepirkumu Sistema)
- **URL**: https://www.eis.gov.lv/EKEIS/Supplier/
- **Open data**: https://data.gov.lv/dati/lv/dataset?tags=EIS

## Data Access

- **Method**: Open data portal with CSV exports
- **Format**: CSV
- **Auth**: Open
- **OCDS**: No

## Coverage

All public procurement (first e-procurement system in the Baltic states).

## Language

Latvian

## Notes

- Modules: e-orders, e-auctions, e-tenders, e-certificates
- Limited API documentation; data.gov.lv has dataset descriptions

## Schema Mapping

### Data Sources

Latvia has two complementary open data sources for procurement:

1. **EIS CSV exports** (data.gov.lv) — Primary source. Yearly CSV files from the Electronic Procurement System. Two relevant datasets:
   - **Announced procurements** (`EIS_E_IEPIRKUMI_IZSLUDINATIE_{YYYY}.csv`) — procurement metadata, CPV codes, procedure types, planned values.
   - **Procurement results** (`EIS_E_IEPIRKUMI_REZULTATI_{YYYY}.csv`) — award outcomes, winners, contract amounts. Must be joined with announced procurements by `Iepirkuma_ID` to get a complete picture.
   - Download URLs: `https://data.gov.lv/dati/lv/dataset/izsludinato-iepirkumu-datu-grupa` and `https://data.gov.lv/dati/lv/dataset/iepirkumu-rezultatu-datu-grupa`
   - Additional datasets exist for amendments (`EIS_E_IEPIRKUMI_GROZIJUMI_{YYYY}.csv`) and deliveries (`EIS_E_PASUT_{YYYY}.csv`), but are not needed for award extraction.

2. **IUB JSON open data** (open.iub.gov.lv) — Secondary/alternative source. The Procurement Monitoring Bureau publishes daily JSON files of eForms notices from October 2023 onward. Richer data but limited historical coverage. The data structure follows eForms since 25 Oct 2023, with daily updates at 00:15. Not used in this mapping (EIS CSV is preferred for its longer historical range and simpler format).

**Recommended approach**: Use the EIS CSV exports as the primary source. Both the "announced" and "results" CSVs must be joined on `Iepirkuma_ID` to produce a complete award record. The "announced" CSV carries contract metadata (CPV, procedure type, subject type), while the "results" CSV carries award outcomes (winner, value, dates).

### Data Format Notes

- **Format**: CSV with comma separator, UTF-8 encoding
- **One row per lot/award**: When `Ir_dalijums_dalas` (has lots) is true, each lot produces a separate row in both CSVs. When false, `Iepirkuma_dalas_nr` is typically empty or 0.
- **Yearly files**: Each year is a separate CSV file. The scraper should iterate over available years.
- **Language**: All text fields are in Latvian.
- **Monetary values**: Values appear to use decimal point (standard CSV numeric). Currency is in a separate column (`Aktuala_liguma_summas_valuta`), expected to be `EUR` for post-2014 data (Latvia adopted EUR on 2014-01-01; older records may use `LVL`).
- **Identifiers**: `Iepirkuma_ID` is numeric, `Iepirkuma_identifikacijas_numurs` is the human-readable procurement reference number (e.g., "LU 2025/66").

### Field Mapping: Announced Procurements CSV (`IZSLUDINATIE`)

These are the known columns (Latvian names) from the announced procurements CSV, with English translations:

| Latvian Column | English Translation |
|---|---|
| `Iepirkuma_ID` | Procurement ID (numeric) |
| `Iepirkuma_nosaukums` | Procurement title |
| `Iepirkuma_identifikacijas_numurs` | Procurement identification number |
| `Pasutitaja_nosaukums` | Contracting authority name |
| `Pasutitaja_registracijas_numurs` | Contracting authority registration number |
| `Pasutitaja_registracijas_numura_veids` | Registration number type |
| `Pasutitaja_PVS_ID` | Contracting authority PVS ID |
| `Augstak_stavosa_organizacija` | Superior organization |
| `Citu_pasutitaju_vajadzibam` | On behalf of other contracting authorities |
| `Faktiskais_sanemejs` | Actual recipient |
| `Iepirkuma_prieksmeta_veids` | Procurement subject type (contract nature) |
| `CPV_kods_galvenais_prieksmets` | Main CPV code |
| `CPV_kodi_papildus_prieksmeti` | Additional CPV codes |
| `Iepirkuma_statuss` | Procurement status |
| `Iepirkuma_izsludinasanas_datums` | Procurement announcement date |
| `Piedavajumu_iesniegsanas_datums` | Tender submission date |
| `Piedavajumu_iesniegsanas_laiks` | Tender submission time |
| `Ieintereseto_personu_sanaksmes` | Interested parties meetings |
| `Precu_vai_pakalpojumu_sniegsanas_vieta` | Place of delivery of goods/services |
| `Planotais_liguma_darbibas_termina_termina_veids` | Planned contract duration type |
| `Planotais_liguma_darbibas_termins` | Planned contract duration |
| `Planota_liguma_darbibas_termina_mervieniba` | Planned contract duration unit |
| `Planota_liguma_izpilde_no` | Planned contract performance from |
| `Planota_liguma_izpilde_lidz` | Planned contract performance until |
| `Ligumcenas_veids` | Contract price type |
| `Planota_ligumcena` | Planned contract price |
| `Planota_ligumcena_no` | Planned contract price from |
| `Planota_ligumcena_lidz` | Planned contract price to |
| `Ligumcenas_valuta` | Contract price currency |
| `Regulejosais_tiesibu_akts` | Regulating legal act |
| `Proceduras_veids` | Procedure type |
| `Pasutitaja_kontaktpersona` | Contracting authority contact person |

### Field Mapping: Procurement Results CSV (`REZULTATI`)

| Latvian Column | English Translation |
|---|---|
| `Iepirkuma_ID` | Procurement ID (join key to announced CSV) |
| `Iepirkuma_nosaukums` | Procurement title |
| `Iepirkuma_identifikacijas_numurs` | Procurement identification number |
| `Pasutitaja_nosaukums` | Contracting authority name |
| `Pasutitaja_registracijas_numurs` | Contracting authority registration number |
| `Pasutitaja_registracijas_numura_veids` | Registration number type |
| `Pasutitaja_PVS_ID` | Contracting authority PVS ID |
| `Augstak_stavosa_organizacija` | Superior organization |
| `Iepirkuma_statuss` | Procurement status |
| `Regulejosais_tiesibu_akts` | Regulating legal act |
| `Proceduras_veids` | Procedure type |
| `Hipersaite_EIS_kura_pieejams_zinojums` | Hyperlink to EIS report |
| `Hipersaite_uz_IUB_publikaciju` | Hyperlink to IUB publication |
| `Ir_dalijums_dalas` | Has lots (boolean) |
| `Iepirkuma_dalas_nr` | Lot number |
| `Iepirkuma_dalas_nosaukums` | Lot title |
| `Iepirkuma_dalas_statuss` | Lot status |
| `Uzvaretaja_nosaukums` | Winner name |
| `Uzvaretaja_registracijas_numurs` | Winner registration number |
| `Uzvaretaja_registracijas_numura_veids` | Winner registration number type |
| `Uzvaretaja_valsts` | Winner country |
| `Liguma_dok_veids` | Contract document type |
| `Noslegta_liguma_dok_ID` | Concluded contract document ID |
| `Saistita_liguma_ID` | Related contract ID |
| `Aktuala_liguma_summa` | Current contract amount |
| `Aktuala_liguma_summas_valuta` | Current contract amount currency |
| `Sakotneja_liguma_summa` | Initial contract amount |
| `Sakotneja_liguma_summas_valuta` | Initial contract amount currency |
| `Liguma_izpildes_termins` | Contract execution deadline |
| `Liguma_izpilde_no` | Contract execution from |
| `Liguma_izpilde_lidz` | Contract execution until |
| `Ligums_ir_vispariga_vienosanas` | Contract is framework agreement |
| `Liguma_dok_noslegsanas_datums` | Contract document conclusion date |
| `Liguma_dok_publicesanas_datums` | Contract document publication date |
| `Izbeigsanas_datums` | Termination date |
| `Izbeigsanas_iemesls` | Termination reason |

### Schema Field Mapping

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `"LV-EIS-" + Iepirkuma_ID` | Synthetic ID; prefix with `LV-EIS-` to avoid collision with TED doc_ids. `Iepirkuma_ID` is from the results CSV. |
| `edition` | None | Not available in EIS data. |
| `version` | None | Not available in EIS data. |
| `reception_id` | None | TED-specific concept; not applicable. |
| `official_journal_ref` | `Hipersaite_uz_IUB_publikaciju` (results CSV) | Not an OJ reference, but the closest equivalent — the IUB publication link. Store as-is or set to `None` if purity is preferred. |
| `publication_date` | `Liguma_dok_publicesanas_datums` (results CSV) | Contract document publication date. Parse date format (likely `YYYY-MM-DD` or `DD.MM.YYYY` — must verify from actual data). |
| `dispatch_date` | `Iepirkuma_izsludinasanas_datums` (announced CSV) | Announcement date — closest to dispatch. |
| `source_country` | `"LV"` (hardcoded) | All EIS records are Latvian procurement. |
| `contact_point` | `Pasutitaja_kontaktpersona` (announced CSV) | Contact person name. |
| `phone` | None | Not available in EIS CSV exports. |
| `email` | None | Not available in EIS CSV exports. |
| `url_general` | `Hipersaite_EIS_kura_pieejams_zinojums` (results CSV) | Direct link to the procurement on EIS. |
| `url_buyer` | None | Not available in EIS CSV exports. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `Pasutitaja_nosaukums` (either CSV) | Contracting authority name. Present in both CSVs. |
| `address` | None | Not available in EIS CSV exports. |
| `town` | None | Not available in EIS CSV exports. Town/city not provided. |
| `postal_code` | None | Not available in EIS CSV exports. |
| `country_code` | `"LV"` (hardcoded) | All EIS contracting bodies are Latvian. |
| `nuts_code` | None | **Not available.** EIS CSV does not include NUTS codes. `Precu_vai_pakalpojumu_sniegsanas_vieta` (place of delivery) in the announced CSV is free text, not a NUTS code. |
| `authority_type` | None | **Not available.** EIS CSV does not include authority type classification. `Regulejosais_tiesibu_akts` (regulating legal act) indicates which procurement law applies but is not an authority type code. |
| `main_activity_code` | None | Not available in EIS CSV exports. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `Iepirkuma_nosaukums` (either CSV) | Procurement title. If lots exist, `Iepirkuma_dalas_nosaukums` (lot title, results CSV) may be more specific per award. Use lot title when available, falling back to procurement title. |
| `short_description` | None | Not available in EIS CSV exports. No description field beyond the title. |
| `main_cpv_code` | `CPV_kods_galvenais_prieksmets` (announced CSV) | Main CPV code. Format needs verification — may be just the numeric code (e.g., `"45000000"`) or include check digit (`"45000000-7"`). |
| `cpv_codes` | `CPV_kods_galvenais_prieksmets` + `CPV_kodi_papildus_prieksmeti` (announced CSV) | Main + additional CPV codes. The additional codes field may be semicolon- or comma-delimited (must verify from actual data). Build list of `CpvCodeEntry` objects. CPV descriptions are not provided in the CSV — set `description` to `None` or look up from a CPV reference table. |
| `nuts_code` | None | **Not available.** See note on `ContractingBodyModel.nuts_code`. |
| `contract_nature_code` | `Iepirkuma_prieksmeta_veids` (announced CSV) | Procurement subject type. Values are in Latvian (e.g., "Piegade" = supplies, "Pakalpojumi" = services, "Būvdarbi" = works). Must be mapped to eForms codes. See Code Normalization section below. |
| `procedure_type` | `Proceduras_veids` (either CSV) | Procedure type. Values are in Latvian (e.g., "Atklāts konkurss" = open procedure). Must be mapped to eForms codes. See Code Normalization section below. |
| `accelerated` | None | **Not available.** EIS CSV does not distinguish accelerated procedures. Always set to `False`. |

#### AwardModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `Iepirkuma_dalas_nosaukums` (results CSV) | Lot title if lots exist, otherwise `None`. |
| `contract_number` | `Noslegta_liguma_dok_ID` (results CSV) | Concluded contract document ID. |
| `tenders_received` | None | **Not available.** EIS CSV does not include tender count. |
| `awarded_value` | `Sakotneja_liguma_summa` (results CSV) | Initial contract amount. Use `Sakotneja_liguma_summa` (initial) rather than `Aktuala_liguma_summa` (current/amended) to match the award-time value. Parse as float. |
| `awarded_value_currency` | `Sakotneja_liguma_summas_valuta` (results CSV) | Currency of the initial contract amount. Expected to be `"EUR"` for post-2014 records. |
| `contractors` | See ContractorModel below | One contractor per results CSV row. |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `Uzvaretaja_nosaukums` (results CSV) | Winner name. |
| `address` | None | Not available in EIS CSV exports. |
| `town` | None | Not available in EIS CSV exports. |
| `postal_code` | None | Not available in EIS CSV exports. |
| `country_code` | `Uzvaretaja_valsts` (results CSV) | Winner country. Format needs verification — may be ISO 3166-1 alpha-2 (e.g., `"LV"`) or a Latvian name (e.g., `"Latvija"`). Must normalize to ISO alpha-2. |
| `nuts_code` | None | Not available in EIS CSV exports. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `CPV_kods_galvenais_prieksmets` / `CPV_kodi_papildus_prieksmeti` (announced CSV) | Numeric CPV codes. May include check digit suffix (`-N`). Normalize to match format used by TED parser. |
| `description` | None | CPV descriptions not provided in CSV. Set to `None`. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | Mapped from `Proceduras_veids` (either CSV) | Latvian text must be mapped to eForms code. See Code Normalization. |
| `description` | `Proceduras_veids` (either CSV) | Latvian-language procedure type name as-is, or use the eForms English description. |

### Unmappable Schema Fields

The following schema fields cannot be populated from EIS CSV data and will always be `None`:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | TED-specific field |
| `DocumentModel.version` | TED-specific field |
| `DocumentModel.reception_id` | TED-specific field |
| `DocumentModel.phone` | Not in CSV export |
| `DocumentModel.email` | Not in CSV export |
| `DocumentModel.url_buyer` | Not in CSV export |
| `ContractingBodyModel.address` | Not in CSV export |
| `ContractingBodyModel.town` | Not in CSV export |
| `ContractingBodyModel.postal_code` | Not in CSV export |
| `ContractingBodyModel.nuts_code` | Not in CSV export |
| `ContractingBodyModel.authority_type` | Not in CSV export (no authority type classification) |
| `ContractingBodyModel.main_activity_code` | Not in CSV export |
| `ContractModel.short_description` | Not in CSV export |
| `ContractModel.nuts_code` | Not in CSV export (delivery place is free text, not NUTS) |
| `ContractModel.accelerated` | Not in CSV export; always `False` |
| `AwardModel.tenders_received` | Not in CSV export |
| `ContractorModel.address` | Not in CSV export |
| `ContractorModel.town` | Not in CSV export |
| `ContractorModel.postal_code` | Not in CSV export |
| `ContractorModel.nuts_code` | Not in CSV export |

### Extra Portal Fields

The following EIS CSV fields are not covered by the current schema but contain potentially useful data. Flagging for review:

**From announced procurements CSV:**

| Portal Field | English | Notes — schema doesn't cover, flagging for review |
|---|---|---|
| `Pasutitaja_registracijas_numurs` | Contracting authority registration number | National business registry ID — useful for entity deduplication |
| `Pasutitaja_PVS_ID` | Contracting authority PVS ID | Internal EIS identifier for the buyer |
| `Augstak_stavosa_organizacija` | Superior organization | Parent body — useful for organizational hierarchy |
| `Citu_pasutitaju_vajadzibam` | On behalf of other contracting authorities | Joint/centralized procurement flag |
| `Faktiskais_sanemejs` | Actual recipient | The real beneficiary if different from buyer |
| `Piedavajumu_iesniegsanas_datums` | Tender submission deadline | Useful for timeline analysis |
| `Precu_vai_pakalpojumu_sniegsanas_vieta` | Place of delivery (free text) | Could be parsed for region info |
| `Planota_ligumcena` / `Planota_ligumcena_no` / `Planota_ligumcena_lidz` | Planned/estimated contract price (or range) | Enables planned-vs-actual analysis |
| `Ligumcenas_valuta` | Planned price currency | Associated with planned price |
| `Regulejosais_tiesibu_akts` | Regulating legal act | Indicates which procurement law applies (above/below threshold) |

**From procurement results CSV:**

| Portal Field | English | Notes — schema doesn't cover, flagging for review |
|---|---|---|
| `Uzvaretaja_registracijas_numurs` | Winner registration number | National business registry ID — useful for entity deduplication |
| `Liguma_dok_veids` | Contract document type | Type of contract document |
| `Saistita_liguma_ID` | Related contract ID | Links to parent/framework contract |
| `Aktuala_liguma_summa` / `Aktuala_liguma_summas_valuta` | Current (amended) contract amount | Useful for tracking contract value changes |
| `Liguma_izpilde_no` / `Liguma_izpilde_lidz` | Contract performance start/end dates | Useful for duration analysis |
| `Ligums_ir_vispariga_vienosanas` | Is framework agreement | Framework agreement flag |
| `Liguma_dok_noslegsanas_datums` | Contract conclusion date | Actual signing date |
| `Izbeigsanas_datums` / `Izbeigsanas_iemesls` | Termination date/reason | Useful for cancelled-contract analysis |
| `Iepirkuma_dalas_statuss` | Lot status | Whether the lot was awarded, cancelled, etc. |

### Code Normalization

#### Contract Nature Codes (`Iepirkuma_prieksmeta_veids`)

Latvian-language values must be mapped to eForms canonical codes. The exact values need to be verified from actual CSV data, but expected mappings based on Latvian procurement law terminology:

| Latvian Value (expected) | eForms Code | Notes |
|---|---|---|
| `Būvdarbi` | `works` | Construction works |
| `Piegāde` or `Piegādes` | `supplies` | Supply of goods |
| `Pakalpojumi` or `Pakalpojums` | `services` | Services |

**Implementation note**: Download a sample CSV file and extract distinct values of `Iepirkuma_prieksmeta_veids` to build the complete mapping. There may be additional values or variant spellings. Unknown values should log a warning and map to `None`, following the project's fail-loud principle.

#### Procedure Type Codes (`Proceduras_veids`)

Latvian-language procedure type names must be mapped to eForms codes. Expected mappings based on Latvia's Public Procurement Law:

| Latvian Value (expected) | eForms Code | Notes |
|---|---|---|
| `Atklāts konkurss` | `open` | Open procedure |
| `Slēgts konkurss` | `restricted` | Restricted procedure |
| `Konkursa dialogs` | `comp-dial` | Competitive dialogue |
| `Sarunu procedūra, publicējot dalības uzaicinājumu` or similar | `neg-w-call` | Negotiated with prior publication |
| `Sarunu procedūra, nepublicējot dalības uzaicinājumu` or similar | `neg-wo-call` | Negotiated without prior publication |
| `Inovācijas partnerība` | `innovation` | Innovation partnership |
| `Konkursa procedūra ar sarunām` | `neg-w-call` | Competitive procedure with negotiation |

**Implementation note**: The exact text values used in the `Proceduras_veids` field must be verified from actual CSV data. Latvia's Public Procurement Law (Publisko iepirkumu likums) defines these procedure types, but the EIS system may use abbreviated or variant forms. Download a sample CSV and extract distinct values. Build the mapping dictionary in the parser module, following the pattern in `ted_v2.py` (`_PROCEDURE_TYPE_CODE_MAP` / `_TED_V2_TO_CANONICAL`). Unknown values should log a warning and return `None`.

#### Authority Type Codes

**Not applicable** — the EIS CSV does not provide authority type classification. This field will always be `None`.

#### Country Codes (`Uzvaretaja_valsts`)

The winner country field format must be verified from actual data. If it uses Latvian country names (e.g., "Latvija", "Lietuva", "Igaunija"), a mapping to ISO 3166-1 alpha-2 codes will be needed. If it already uses ISO codes, no mapping is required.

### Implementation Considerations

1. **Two-CSV join**: The parser must download and join both the announced and results CSVs for each year. Join on `Iepirkuma_ID`. The results CSV is the primary driver (one row per award), enriched with contract metadata from the announced CSV.

2. **Lot handling**: When `Ir_dalijums_dalas` is true, each lot is a separate row in the results CSV with its own `Iepirkuma_dalas_nr`. All lots under the same `Iepirkuma_ID` share the same contracting body and document metadata. Each lot becomes a separate `AwardModel` within the same `AwardDataModel`. The announced CSV likely has one row per procurement (not per lot) — verify this assumption.

3. **Multiple winners per lot**: It is unclear whether the EIS CSV can have multiple winner rows for the same lot (e.g., joint ventures). Verify from actual data. If so, group them as multiple `ContractorModel` entries in a single `AwardModel`.

4. **Filtering for awards only**: Not all rows in the results CSV represent concluded contracts. Filter by `Iepirkuma_statuss` and/or `Iepirkuma_dalas_statuss` to select only awarded/concluded procurements. The exact status values need to be discovered from actual data.

5. **Date format**: Date formats in the CSV must be verified empirically. Latvian conventions use `DD.MM.YYYY`, but CSV exports may use `YYYY-MM-DD` or other formats.

6. **Historical coverage**: EIS CSV data availability on data.gov.lv needs verification — files appear to exist from at least 2017 onward based on search results. The scraper should attempt to download each year and handle missing files gracefully.

7. **Encoding and delimiters**: Verify CSV encoding (expected UTF-8) and delimiter (expected comma) from actual downloaded files. Some Latvian open data exports use semicolons.

8. **doc_id uniqueness**: The synthetic `doc_id` (`LV-EIS-{Iepirkuma_ID}`) should be unique across the database since TED doc_ids follow a different format. However, for procurements that also appear on TED (above-threshold), there will be a separate TED document with a different `doc_id` — this is expected and correct (national and EU-level records coexist).
