# Czech Republic (CZ)

**Feasibility: Tier 2**

## Portal

- **Name**: NIPEZ system (NEN + VVZ)
- **VVZ (Procurement Bulletin)**: https://vvz.nipez.cz/
- **NEN (National Electronic Tool)**: https://nen.nipez.cz/en/
- **Open data**: https://data.gov.cz/

## Data Access

- **Method**: Public search portal; XML open data exports
- **Format**: XML
- **Auth**: Open for reading
- **OCDS**: No

## Coverage

All mandatory procurement publications under Czech Public Procurement Act.

## Language

Czech

## Notes

- XML open data exports available
- Czech-only documentation, non-standard format
- XML format is directly usable by external applications (per Open Government Partnership)

## Schema Mapping

### Data Source Selection

The ISVZ system provides **three separate datasets**, each corresponding to a different legal regime:

| Dataset | Code | Legal Basis | Years | Description |
|---------|------|-------------|-------|-------------|
| VVZ | `VVZ` | Act 137/2006 | 2006-2016 | Older Public Procurement Act |
| ZZVZ | `ZZVZ` | Act 134/2016 | 2016-present | Current Public Procurement Act |
| ZZVZ (F16-F19) | `ZZVZMO` | Act 134/2016 | 2016-present | Concession/utility forms only |
| eTrziste | `etrziste` | N/A | 2012-2017 | Electronic marketplaces (discontinued) |

**Recommendation**: Use **ZZVZ** as the primary dataset for current data (2016+) and **VVZ** for historical data (2006-2016). The eTrziste dataset is discontinued and lower priority.

### Download Endpoint

**URL pattern**: `https://isvz.nipez.cz/sites/default/files/content/opendata-predchozi/{dataset}/{year}/{filename}`

Alternative (may redirect): `https://www.isvz.cz/ReportingSuite/Explorer/Download/Data/{FORMAT}/{DATASET}/{YEAR}`

Where:
- `FORMAT` = `XML`, `CSV`, or `XLS`
- `DATASET` = `VVZ`, `ZZVZ`, `ZZVZMO`, or `etrziste`
- `YEAR` = four-digit year (e.g., `2024`)

Downloads are unauthenticated. Data is organized as yearly bulk exports (one file per year per dataset).

### Data Format Notes

- **Format**: XML (preferred) or CSV (semicolon-delimited, quoted fields)
- **Encoding**: UTF-8
- **XML structure**: Flat sections with repeating elements (not hierarchical). Each XML section corresponds to a logical table (VZ, CastiVZ, Zadani, Dodavatele, HodnoticiKriteria). Sections are linked by key fields (typically `IDZakazky` or `EvidencniCisloVZnaVVZ`).
- **CSV quirks**: Known data quality issues including extra trailing semicolons in some years (observed in 2021 ZZVZ data). Use robust CSV parsing.
- **Monetary values**: Numeric fields use comma as decimal separator in CSV exports. XML uses period. Amounts are `Numeric(16,2)`.
- **Dates**: Multiple formats observed: ISO dates (`YYYY-MM-DD`), ISO datetimes, and Czech format (`dd.mm.yyyy`). Parser must handle all three.
- **ICO (Company ID)**: Czech-specific 8-digit organization identifier. Strip spaces, validate < 100,000,000.

### ZZVZ Field Mapping (Primary Dataset, 2016+)

The ZZVZ dataset is organized into five XML sections. All sections are linked by `IDZakazky` (internal ID) and/or `EvidencniCisloVZnaVVZ` (VVZ evidence number).

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `ZZVZ.VZ.IDZakazky` | Internal system ID; unique per procurement. Prefix with `CZ-` to avoid collisions with TED doc_ids. |
| `edition` | -- | `None`. No edition concept in Czech system. |
| `version` | -- | Set to `"ZZVZ"` to identify the data source variant. |
| `reception_id` | -- | `None`. No reception ID concept. |
| `official_journal_ref` | `ZZVZ.VZ.EvidencniCisloVZnaVVZ` | The VVZ evidence number (e.g., "Z2024-012345"). Serves as the official publication reference. |
| `publication_date` | `ZZVZ.VZ.DatumUverejneni` | Date of publication on VVZ. |
| `dispatch_date` | `ZZVZ.VZ.DatumOdeslaniFormulareNaVVZ` | Date the form was dispatched to VVZ. |
| `source_country` | -- | Hardcode to `"CZ"`. |
| `contact_point` | `ZZVZ.VZ.ZadavatelKontaktniOsoba` | Contact person at the contracting authority. |
| `phone` | `ZZVZ.VZ.ZadavatelTelefon` | Phone number of the contracting authority. |
| `email` | `ZZVZ.VZ.ZadavatelEmail` | Email of the contracting authority. |
| `url_general` | -- | `None`. Not in ZZVZ dataset. |
| `url_buyer` | `ZZVZ.VZ.ZadavatelProfilURL` | Contracting authority's buyer profile URL. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `ZZVZ.VZ.ZadavatelUredniNazev` | Official name of the contracting authority. |
| `address` | -- | `None`. No street address field in ZZVZ VZ section. Supplier addresses exist in Dodavatele section only. |
| `town` | -- | `None`. No town field for the contracting authority in ZZVZ. |
| `postal_code` | -- | `None`. No postal code for the contracting authority in ZZVZ. |
| `country_code` | -- | Hardcode to `"CZ"`. The data is a national portal; all contracting bodies are Czech. |
| `nuts_code` | -- | `None`. No NUTS code for the contracting body in ZZVZ VZ section. NUTS codes appear only in `ZZVZ.CastiVZ.HlavniMistoPlneniNUTS` (performance location). |
| `authority_type` | `ZZVZ.VZ.ZadavatelDruh` | Authority type. **Requires code normalization** (see Code Normalization section below). |
| `main_activity_code` | `ZZVZ.VZ.ZadavatelHlavniPredmetCinnosti` | Main activity of the contracting authority. Free text in Czech; **requires mapping to eForms activity codes** or store as-is. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `ZZVZ.VZ.NazevVZ` | Name of the public contract. In Czech language. |
| `short_description` | `ZZVZ.VZ.StrucnyPopisVZ` | Brief description of the contract. In Czech. |
| `main_cpv_code` | `ZZVZ.VZ.CPVhlavni` | Main CPV code. Standard EU CPV codes, no normalization needed. |
| `cpv_codes` | `ZZVZ.VZ.CPVhlavni` + `ZZVZ.VZ.CPVdoplnkovy1` + `ZZVZ.CastiVZ.CPVkod` | Main + supplementary CPV codes. ZZVZ VZ section has only `CPVhlavni` and `CPVdoplnkovy1`. Additional CPV codes appear per-part in `CastiVZ.CPVkod`. |
| `nuts_code` | `ZZVZ.CastiVZ.HlavniMistoPlneniNUTS` | Performance location NUTS code. Found in the parts section, not the main VZ section. For multi-part contracts, use the first part's NUTS or aggregate. |
| `contract_nature_code` | `ZZVZ.VZ.DruhVZ` | Contract nature (works/supplies/services). **Requires code normalization** (see below). |
| `procedure_type` | `ZZVZ.VZ.DruhRizeni` | Procedure type. **Requires code normalization** (see below). |
| `accelerated` | -- | `False`. The Czech system does not separately flag accelerated procedures in the open data export. Accelerated variants may appear as distinct `DruhRizeni` values (needs verification during implementation). |

#### AwardModel

Award data comes from the `ZZVZ.Zadani` section. One procurement (VZ) can have multiple awards (Zadani), linked by `IDZakazky`.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `ZZVZ.Zadani.NazevCastiVZ` | Name of the awarded part. May be `None` for undivided contracts. |
| `contract_number` | `ZZVZ.Zadani.CisloCastiZadaniVZ` | Part/lot number within the procurement. |
| `tenders_received` | `ZZVZ.Zadani.PocetObdrzenychNabidek` | Number of bids received. |
| `awarded_value` | `ZZVZ.Zadani.CelkovaKonecnaHodnotaVZzaZadani` | Final contract value for this award. Numeric(16,2). |
| `awarded_value_currency` | `ZZVZ.Zadani.CelkovaKonecnaHodnotaVZmenaZaZadani` | Currency code (typically `"CZK"` or `"EUR"`). |
| `contractors` | Join to `ZZVZ.Dodavatele` via `IDZakazky` + `IDZadani` | See ContractorModel below. |

**Filtering**: Only import records where `ZadaniCastiZakazky` is populated (indicating an actual award, not a cancellation). Check `InformaceONezadaniCastiZakazky` for cancellation information. Also check `PlatnyFormular` = true to get only the latest valid form.

#### ContractorModel

Contractor data comes from the `ZZVZ.Dodavatele` section. Multiple contractors per award are supported (joint ventures). Linked to awards via `IDZakazky` + `IDZadani`.

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `ZZVZ.Dodavatele.DodavatelNazev` | Official name of the contractor. |
| `address` | `ZZVZ.Dodavatele.DodavatelPostovniAdresa` | Postal address. |
| `town` | `ZZVZ.Dodavatele.DodavatelObec` | Town/municipality. |
| `postal_code` | `ZZVZ.Dodavatele.DodavatelPSC` | Postal code. |
| `country_code` | `ZZVZ.Dodavatele.DodavatelStat` | Country. **May be a Czech country name string rather than ISO code** -- needs normalization to 2-letter ISO code during implementation. |
| `nuts_code` | -- | `None`. No NUTS code for contractors in ZZVZ. |

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `ZZVZ.VZ.CPVhlavni`, `ZZVZ.VZ.CPVdoplnkovy1`, `ZZVZ.CastiVZ.CPVkod` | Standard EU CPV codes. No normalization needed. |
| `description` | -- | `None`. ZZVZ does not include CPV descriptions in the export. Can be looked up from the CPV codelist if needed. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `ZZVZ.VZ.DruhRizeni` | Czech procedure type text. **Requires mapping** to eForms codes (see below). |
| `description` | `ZZVZ.VZ.DruhRizeni` | The raw Czech text can be stored as the description. |

#### AuthorityTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `ZZVZ.VZ.ZadavatelDruh` | Czech authority type text. **Requires mapping** to eForms codes (see below). |
| `description` | `ZZVZ.VZ.ZadavatelDruh` | The raw Czech text can be stored as the description. |

### VVZ Field Mapping (Historical Dataset, 2006-2016)

The VVZ dataset has a similar but not identical structure. Key differences from ZZVZ:

- Award/supplier data is combined in `VVZ.CastiVerejneZakazky` (no separate Zadani/Dodavatele sections)
- Supplier fields (`DodavatelNazev`, `DodavatelICOZeZadani`, `DodavatelPostovniAdresa`, `DodavatelObec`, `DodavatelPSC`, `DodavatelStat`) are in `CastiVerejneZakazky`
- More CPV code fields available: up to 5 CPV subjects with main + 2 supplementary each (15 total CPV fields)
- Evaluation criteria are inline in the VZ section (10 pairs of `Kriterium`/`VahaKriteria` fields)

The mapping logic is essentially the same as ZZVZ with minor path adjustments. The same code normalization applies. See the `mapping.json` reference from the kokes/od project for exact field names.

### Unmappable Schema Fields

These schema fields cannot be populated from the Czech portal data:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | No edition concept in the Czech system. Set to `None`. |
| `DocumentModel.reception_id` | Not available. Set to `None`. |
| `DocumentModel.url_general` | Not in ZZVZ export. Set to `None`. |
| `ContractingBodyModel.address` | Contracting authority address not in ZZVZ VZ section. Set to `None`. |
| `ContractingBodyModel.town` | Contracting authority town not in ZZVZ VZ section. Set to `None`. |
| `ContractingBodyModel.postal_code` | Contracting authority postal code not in ZZVZ VZ section. Set to `None`. |
| `ContractingBodyModel.nuts_code` | No NUTS for the body itself (only for performance location). Set to `None`. |
| `ContractModel.accelerated` | Not separately flagged. Default to `False`. |
| `ContractorModel.nuts_code` | No NUTS code for contractors. Set to `None`. |
| `CpvCodeEntry.description` | CPV descriptions not included in export. Set to `None`. |

### Extra Portal Fields

These fields are available in the Czech portal but not covered by the current schema. Flagged for review.

| Portal Field | Section | Description | Notes |
|---|---|---|---|
| `ZadavatelICO` | VZ | Contracting authority's ICO (8-digit Czech org ID) | Schema doesn't cover -- flagging for review. Valuable for entity deduplication. |
| `DodavatelICO` | Dodavatele | Contractor's ICO (8-digit Czech org ID) | Schema doesn't cover -- flagging for review. Valuable for entity deduplication. |
| `LimitVZ` | VZ | Contract value limit category (above/below threshold) | Schema doesn't cover -- flagging for review. Useful for filtering below-threshold data. |
| `DruhFormulare` | VZ | Form type (e.g., contract notice, award notice, etc.) | Schema doesn't cover -- flagging for review. Needed to filter for award notices only. |
| `TypFormulare` | VZ | Form subtype | Schema doesn't cover -- flagging for review. |
| `VZdelenaNaCasti` | VZ | Whether the contract is divided into lots | Schema doesn't cover -- flagging for review. |
| `OdhadovanaHodnotaVZbezDPH` | VZ | Estimated value excluding VAT | Schema doesn't cover -- flagging for review. Useful for analysis. |
| `OdhadovanaHodnotaVZmena` | VZ | Estimated value currency | Schema doesn't cover -- flagging for review. |
| `PuvodniOdhadovanaCelkovaHodnotaVZ` | Zadani | Original estimated total value | Schema doesn't cover -- flagging for review. |
| `HodnotaNejnizsiNabidky` | Zadani | Lowest bid value | Schema doesn't cover -- flagging for review. Useful for bid spread analysis. |
| `HodnotaNejvyssiNabidky` | Zadani | Highest bid value | Schema doesn't cover -- flagging for review. |
| `SubdodavkyHodnotaBezDPH` | Zadani | Subcontracting value excl. VAT | Schema doesn't cover -- flagging for review. |
| `SubdodavkyPomer` | Zadani | Subcontracting ratio (%) | Schema doesn't cover -- flagging for review. |
| `DatumZadaniVZ` | Zadani | Date of contract award | Schema doesn't cover -- flagging for review. Could be stored as award date. |
| `DodavatelWww` | Dodavatele | Contractor website | Schema doesn't cover -- flagging for review. |
| `PlatnyFormular` | All sections | Whether this is the currently valid form version | Schema doesn't cover -- flagging for review. Critical for deduplication: only import records where `PlatnyFormular` = true. |
| `ZadavatelProfilURL` | VZ | Buyer profile URL | Mapped to `url_buyer`, but availability/validity flag `ZadavatelProfilURLPlatnost` is extra. |
| `NaVZseVztahujeGPA` | VZ | Whether GPA (Government Procurement Agreement) applies | Schema doesn't cover -- flagging for review. |
| `BylaPouzitaElektronickaDrazba` | VZ | Whether electronic auction was used | Schema doesn't cover -- flagging for review. |
| `ZakazkaSeVztahujeKprojektuFinZes` | CastiVZ | Whether related to EU-funded project | Schema doesn't cover -- flagging for review. |
| `ProjektyCiProgramyFinZes` | CastiVZ | EU funding programme reference | Schema doesn't cover -- flagging for review. |
| `InformaceONezadaniCastiZakazky` | Zadani | Information about non-award (cancellation reason) | Schema doesn't cover -- flagging for review. Useful for filtering cancelled awards. |

### Code Normalization

The Czech portal uses **Czech-language text values** (not numeric or standardized codes) for procedure types, authority types, and contract nature. These must be mapped to eForms equivalents. The exact text values need to be discovered empirically from the data, but the expected mappings are:

#### Procedure Types (`DruhRizeni` to eForms `procurement-procedure-type`)

| Czech Value (expected) | eForms Code | eForms Description |
|---|---|---|
| `Otevřené řízení` | `open` | Open procedure |
| `Užší řízení` | `restricted` | Restricted procedure |
| `Jednací řízení s uveřejněním` | `neg-w-call` | Negotiated with prior call for competition |
| `Jednací řízení bez uveřejnění` | `neg-wo-call` | Negotiated without prior call for competition |
| `Soutěžní dialog` | `comp-dial` | Competitive dialogue |
| `Inovační partnerství` | `innovation` | Innovation partnership |
| `Zjednodušené podlimitní řízení` | -- | Simplified sub-threshold procedure. No eForms equivalent; this is a Czech-specific below-threshold type. Map to `None` or consider `oth-single`. |
| `Řízení o inovačním partnerství` | `innovation` | Alternative wording for innovation partnership. |
| `Koncesní řízení` | -- | Concession procedure. No direct eForms procedure type equivalent. Map to `None`. |

**Implementation note**: The exact text values used in the data must be verified empirically by downloading a sample year and extracting distinct `DruhRizeni` values. The Czech VVZ/ZZVZ may use slightly different spellings or additional procedure types not listed above. Build the mapping as a dictionary and log warnings for unknown values (consistent with the fail-loud principle).

#### Authority Types (`ZadavatelDruh` to eForms `buyer-legal-type`)

| Czech Value (expected) | eForms Code | eForms Description |
|---|---|---|
| `Ministerstvo nebo jiný celostátní orgán` | `cga` | Central government authority |
| `Celostátní či federální agentura/úřad` | `cga` | Central government authority |
| `Regionální či místní orgán` | `ra` | Regional authority |
| `Regionální či místní agentura/úřad` | `body-pl-ra` | Body governed by public law, controlled by regional authority |
| `Veřejnoprávní instituce` | `body-pl` | Body governed by public law |
| `Evropská instituce/agentura nebo mezinárodní organizace` | `eu-ins-bod-ag` | EU institution, body or agency |
| `Jiný` | `None` | Other -- no eForms equivalent |

**Implementation note**: Same as procedure types -- verify empirically and build a mapping dictionary. The Czech descriptions may not match the above exactly.

#### Contract Nature (`DruhVZ` to eForms `contract-nature-type`)

| Czech Value (expected) | eForms Code |
|---|---|
| `Stavební práce` | `works` |
| `Dodávky` | `supplies` |
| `Služby` | `services` |

This mapping is simpler and should be exhaustive. Any unknown values should log a warning and return `None`.

#### Country Codes (`DodavatelStat`)

The `DodavatelStat` field in the Dodavatele section may contain Czech-language country names (e.g., `"Česká republika"`, `"Slovensko"`, `"Německo"`) rather than ISO 3166-1 alpha-2 codes. A mapping from Czech country names to ISO codes will be needed. Alternatively, the field may already use ISO codes -- this must be verified empirically from the data.

### Key Implementation Considerations

1. **Award filtering**: The ZZVZ dataset contains **all form types** (contract notices, award notices, prior information notices, etc.). The `DruhFormulare` field must be used to filter for award-related forms only. Alternatively, filter by the presence of data in the `Zadani` section (which contains award results).

2. **Form validity**: Multiple form versions can exist for the same procurement. Always filter on `PlatnyFormular` = true to get the latest valid version.

3. **Multi-section joins**: Unlike TED XML (one document per file), the Czech data is a flat export requiring joins across sections. The `IDZakazky` field links VZ to CastiVZ, Zadani, Dodavatele, and HodnoticiKriteria. Within awards, `IDZadani` links Zadani to Dodavatele.

4. **Cancellations**: Some Zadani records represent cancelled awards. Check `InformaceONezadaniCastiZakazky` for cancellation text and `ZadaniCastiZakazky` for the award confirmation flag.

5. **doc_id uniqueness**: Prefix Czech IDs with `"CZ-ZZVZ-"` or `"CZ-VVZ-"` to avoid collisions with TED doc_ids in the shared database.

6. **Reference implementation**: The [kokes/od](https://github.com/kokes/od) project (`data/zakazky/`) provides a working Python parser for this exact data source, including XML streaming parse, date normalization, and ICO validation. Its `mapping.json` file is the authoritative field reference.
