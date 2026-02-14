# Spain (ES)

**Feasibility: Tier 2**

## Portal

- **Name**: PLACSP (Plataforma de Contratacion del Sector Publico)
- **URL**: https://contrataciondelestado.es/ / https://contrataciondelsectorpublico.gob.es/
- **Open data**: https://contrataciondelsectorpublico.gob.es/wps/portal/DatosAbiertos
- **Web services**: https://contrataciondelestado.es/wps/portal/servicioswebPLACSP
- **Tool docs**: https://contrataciondelestado.es/datosabiertos/DGPE_PLACSP_OpenPLACSP_v.1.3.pdf
- **datos.gob.es**: https://datos.gob.es/en/catalogo/l01241152-licitaciones

## Data Access

- **Method**: Atom/XML feeds (daily updates, monthly/annual files); CODICE web services for B2B integration
- **Format**: XML (.atom extension), CODICE format
- **Auth**: Open for data feeds; B2B integration requires setup
- **OCDS**: No (uses CODICE, a Spanish national standard)

## Coverage

All public sector procurement since 2012. Central platform for all contracting authorities.

## Language

Spanish

## Notes

- CODICE is not OCDS-compatible; requires custom XML parser
- Key data fields: tender status, contract purpose, estimated amount, CPV code, place of execution, successful bidder, award amount, number of bidders
- Academic paper: https://www.sciencedirect.com/science/article/pii/S1877050919322513
- Good historical coverage but non-standard format

## Schema Mapping

### Data Format Notes

- **Format**: CODICE XML (Componentes y Documentos Interoperables para la Contratacion Electronica), a Spanish national standard based on UBL (Universal Business Language) from OASIS. Not OCDS-compatible.
- **Delivery**: Atom 1.0 feeds (RFC 4287). Downloaded as `.zip` archives containing `.atom` XML files. Each atom file contains `<entry>` elements, each wrapping a `<cac-place-ext:ContractFolderStatus>` element with the full procurement record.
- **URL pattern**: `https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_{YYYY}.zip` (annual archives; the exact syndication number and profile name may vary by contracting entity type).
- **Coverage**: 2012 onwards. ~250 issues/year (daily on business days).
- **XML namespaces**: The CODICE Atom feeds use UBL-derived namespace prefixes including `cbc:` (CommonBasicComponents), `cac:` (CommonAggregateComponents), and `cac-place-ext:` / `cbc-place-ext:` (PLACE extensions). The root element per entry is `cac-place-ext:ContractFolderStatus`.
- **Parser library**: `lxml` with explicit namespace maps. XPath expressions needed for all field extraction.
- **Award filtering**: PLACSP data includes all procurement lifecycle stages (planning, tendering, award, formalization). To extract only awarded contracts, filter on `ContractFolderStatusCode` (values like `ADJ` for adjudicada/awarded, `RES` for resuelta/formalized) **and** check for the presence of `TenderResult` elements with a `ResultCode` indicating award (not void/desert).
- **Multiple lots**: A single `ContractFolderStatus` may contain multiple `ProcurementProjectLot` elements and multiple `TenderResult` elements (one per lot). Each `TenderResult` can have its own `WinningParty` and `AwardedTenderedProject`.
- **Encoding**: UTF-8. All text content is in Spanish.
- **Reference parser**: [juanfont/codice](https://github.com/juanfont/codice) (Go) provides a verified reference implementation with 82 extracted fields. [BquantFinance/licitaciones-espana](https://github.com/BquantFinance/licitaciones-espana) provides a Python dataset with 48 columns extracted from PLACSP.

### Data Flow Overview

1. **Download**: Fetch annual/monthly `.zip` archives from the PLACSP open data syndication endpoint.
2. **Extract**: Unzip to get `.atom` XML files.
3. **Parse**: For each `<entry>` in each atom file, extract the `<cac-place-ext:ContractFolderStatus>` element.
4. **Filter**: Only process entries where `ContractFolderStatusCode` indicates an award/formalization AND `TenderResult/ResultCode` indicates an actual award (not void/deserted).
5. **Map**: Extract fields per the mapping tables below into `AwardDataModel`.
6. **Deduplicate**: Use `ContractFolderID` as the basis for `doc_id` (prefixed with `ES-` to avoid collisions with TED doc IDs).

### Field Mapping Tables

All XML paths below are relative to `entry/cac-place-ext:ContractFolderStatus/` unless otherwise noted. Namespace prefixes: `cbc:` = CommonBasicComponents, `cac:` = CommonAggregateComponents, `cac-place-ext:` / `cbc-place-ext:` = PLACE extensions.

#### DocumentModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `doc_id` | `cbc:ContractFolderID` | Prefix with `ES-` to namespace (e.g. `ES-12345678`). This is the expediente number. |
| `edition` | Not directly available | Derive from publication date if needed, or set to `None`. |
| `version` | Hardcode `"CODICE"` | Or include CODICE schema version if detectable from XML namespace. |
| `reception_id` | Not available | `None`. TED-specific concept. |
| `official_journal_ref` | Not available | `None`. National notices have no OJ S reference. If cross-published to TED, that is handled by the TED portal. |
| `publication_date` | `entry/updated` (Atom standard) | ISO 8601 datetime in the Atom `<updated>` element. Parse date portion. |
| `dispatch_date` | Not directly available | `None`. CODICE does not have a dispatch date concept. |
| `source_country` | Hardcode `"ES"` | All PLACSP notices are Spanish. |
| `contact_point` | `cac:LocatedContractingParty/cac:Party/cac:Contact/cbc:Name` | Contact person name. |
| `phone` | `cac:LocatedContractingParty/cac:Party/cac:Contact/cbc:Telephone` | |
| `email` | `cac:LocatedContractingParty/cac:Party/cac:Contact/cbc:ElectronicMail` | |
| `url_general` | `cac:LocatedContractingParty/cac:Party/cbc:WebsiteURI` | |
| `url_buyer` | Not available | `None`. CODICE does not have a separate buyer profile URL field. |

#### ContractingBodyModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `cac:LocatedContractingParty/cac:Party/cac:PartyName/cbc:Name` | Mandatory. |
| `address` | `cac:LocatedContractingParty/cac:Party/cac:PostalAddress/cac:AddressLine/cbc:Line` | |
| `town` | `cac:LocatedContractingParty/cac:Party/cac:PostalAddress/cbc:CityName` | |
| `postal_code` | `cac:LocatedContractingParty/cac:Party/cac:PostalAddress/cbc:PostalZone` | |
| `country_code` | `cac:LocatedContractingParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode` | ISO 3166-1 alpha-2. Typically `ES`. |
| `nuts_code` | `cac:ProcurementProject/cac:RealizedLocation/cbc:CountrySubentityCode` | NUTS code for the performance location. Note: this is on the procurement project, not the contracting party. Contracting body location NUTS is not directly available as a separate field. |
| `authority_type` | `cac:LocatedContractingParty/cbc:ContractingPartyTypeCode` | CODICE-specific code. Needs mapping to eForms equivalents -- see Code Normalization below. The `@listURI` attribute references the CODICE code list. |
| `main_activity_code` | Not directly available in a single field | CODICE does not have a direct equivalent to the eForms BT-10 main activity code. Set to `None`. |

#### ContractModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `title` | `cac:ProcurementProject/cbc:Name` | Contract/procurement project title. |
| `short_description` | `entry/summary` (Atom standard) | The Atom `<summary>` element contains a description. Alternatively, a description may exist within `ProcurementProject` but is not guaranteed. |
| `main_cpv_code` | `cac:ProcurementProject/cac:RequiredCommodityClassification/cbc:ItemClassificationCode` (first occurrence) | CPV codes. If multiple `RequiredCommodityClassification` elements exist, the first is typically the main CPV. |
| `cpv_codes` | `cac:ProcurementProject/cac:RequiredCommodityClassification[]/cbc:ItemClassificationCode` (all occurrences) | Collect all CPV codes from the array. Also check lot-level CPV codes in `ProcurementProjectLot/ProcurementProject/RequiredCommodityClassification`. |
| `nuts_code` | `cac:ProcurementProject/cac:RealizedLocation/cbc:CountrySubentityCode` | NUTS code for place of performance. |
| `contract_nature_code` | `cac:ProcurementProject/cbc:TypeCode` | CODICE code for contract type (works/supplies/services). Needs mapping to eForms equivalents -- see Code Normalization below. |
| `procedure_type` | `cac:TenderingProcess/cbc:ProcedureCode` | CODICE procedure code. Needs mapping to eForms equivalents -- see Code Normalization below. The `@listURI` attribute references the CODICE code list. |
| `accelerated` | `cac:TenderingProcess/cbc:UrgencyCode` | CODICE uses `UrgencyCode` rather than a separate accelerated boolean. If the urgency code indicates an accelerated/urgent procedure, set `accelerated=True`. The exact code values need verification from the CODICE code list. Default `False`. |

#### AwardModel

One `AwardModel` per `TenderResult` element. A single contract folder may contain multiple `TenderResult` elements (one per lot or per award decision).

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `award_title` | `cac:ProcurementProject/cbc:Name` or lot-level `cac:ProcurementProjectLot[]/cac:ProcurementProject/cbc:Name` | CODICE does not have a separate award title. Use the contract/lot title. If `TenderResult/AwardedTenderedProject/ProcurementProjectLotID` is present, resolve the lot name from the corresponding `ProcurementProjectLot`. |
| `contract_number` | `cac:TenderResult/cac:Contract/cbc:ID` | The formal contract ID assigned after award. |
| `tenders_received` | `cac:TenderResult/cbc:ReceivedTenderQuantity` | Integer: number of tenders received. |
| `awarded_value` | `cac:TenderResult/cac:AwardedTenderedProject/cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount` | Award amount excluding taxes. The `@currencyID` attribute provides the currency. Alternatively, `cbc:PayableAmount` may be available. Prefer `TaxExclusiveAmount` for consistency. |
| `awarded_value_currency` | `cac:TenderResult/cac:AwardedTenderedProject/cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount/@currencyID` | ISO 4217 currency code. Typically `EUR` for Spain. |
| `contractors` | `cac:TenderResult/cac:WinningParty` | See ContractorModel below. A `TenderResult` may have one or more `WinningParty` elements (joint ventures/consortia). |

#### ContractorModel

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `official_name` | `cac:WinningParty/cac:PartyName/cbc:Name` | Mandatory when award is made. |
| `address` | Not available in `WinningParty` | `None`. CODICE `WinningParty` typically only contains identification and name, not postal address. The winning party's address may exist in a separate section not linked by ID. |
| `town` | Not available in `WinningParty` | `None`. Same reason as above. |
| `postal_code` | Not available in `WinningParty` | `None`. |
| `country_code` | Not available in `WinningParty` | `None`. The `WinningParty` element in CODICE does not typically include address details. |
| `nuts_code` | Not available in `WinningParty` | `None`. |

**Important**: CODICE's `WinningParty` is minimal -- it provides the party name and an ID (`PartyIdentification/ID` with `@schemeName` attribute, typically NIF/CIF for Spanish entities). Contractor address details are not available in the award data. This is a significant limitation compared to TED data.

#### CpvCodeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `cbc:ItemClassificationCode` text content | From `RequiredCommodityClassification` elements. Standard CPV code format (8-digit + check digit, e.g. `45000000-7`). |
| `description` | Not available in CODICE XML | `None`. CODICE does not include CPV descriptions inline. Descriptions must come from a local CPV lookup table if needed. |

#### ProcedureTypeEntry

| Schema Field | Portal Field/Path | Notes |
|---|---|---|
| `code` | `cbc:ProcedureCode` text content, after mapping to eForms | See Code Normalization below. The raw CODICE code must be mapped to the eForms equivalent. |
| `description` | Not in XML | Populate from static lookup table of eForms procedure type descriptions after mapping. |

### Unmappable Schema Fields

These fields will be `None` for PLACSP-sourced notices:

| Schema Field | Reason |
|---|---|
| `DocumentModel.edition` | No OJ S edition concept in national notices. Could be derived from publication date but not natively available. |
| `DocumentModel.reception_id` | TED-specific concept (reception ID from EU Publications Office). |
| `DocumentModel.official_journal_ref` | National notices are not published in the OJ S. |
| `DocumentModel.dispatch_date` | CODICE does not track a dispatch date. |
| `DocumentModel.url_buyer` | No separate buyer profile URL in CODICE. |
| `ContractingBodyModel.main_activity_code` | CODICE does not have a direct equivalent to eForms BT-10. |
| `ContractorModel.address` | `WinningParty` in CODICE only provides name and ID, not postal address. |
| `ContractorModel.town` | Same as above. |
| `ContractorModel.postal_code` | Same as above. |
| `ContractorModel.country_code` | Same as above. |
| `ContractorModel.nuts_code` | Same as above. |
| `CpvCodeEntry.description` | CODICE does not include CPV descriptions inline. |
| `ProcedureTypeEntry.description` | Not in XML. Populate from static lookup after code mapping. |
| `AuthorityTypeEntry.description` | Not in XML. Populate from static lookup after code mapping. |

### Extra Portal Fields

These fields are available in PLACSP/CODICE but not covered by the current schema. Flagged for review.

| Portal Field | CODICE Path | Notes |
|---|---|---|
| Contractor NIF/CIF (tax ID) | `WinningParty/PartyIdentification/ID` (with `@schemeName`) | Schema doesn't cover -- flagging for review. Very useful for entity resolution/deduplication. The `@schemeName` attribute indicates the ID scheme (typically NIF for Spanish entities). |
| Contracting party NIF/ID | `LocatedContractingParty/Party/PartyIdentification/ID` (with `@schemeName="DIR3"`) | Schema doesn't cover -- flagging for review. DIR3 is Spain's administrative unit directory code. |
| Budget estimated amount | `ProcurementProject/BudgetAmount/EstimatedOverallContractAmount` | Schema doesn't cover -- flagging for review. Useful for analyzing award-to-estimate ratios. |
| Budget total amount (incl. tax) | `ProcurementProject/BudgetAmount/TotalAmount` | Schema doesn't cover -- flagging for review. |
| Budget tax-exclusive amount | `ProcurementProject/BudgetAmount/TaxExclusiveAmount` | Schema doesn't cover -- flagging for review. |
| Contract duration | `ProcurementProject/PlannedPeriod/DurationMeasure` (with `@unitCode`) | Schema doesn't cover -- flagging for review. Duration in months/days with unit code. |
| Contract start/end dates | `ProcurementProject/PlannedPeriod/StartDate`, `EndDate` | Schema doesn't cover -- flagging for review. |
| Contract extension options | `ProcurementProject/ContractExtension/OptionsDescription` | Schema doesn't cover -- flagging for review. |
| SME indicator | Not directly in CODICE XML (available in BquantFinance dataset as `es_pyme`) | Schema doesn't cover -- flagging for review. May be derivable from contractor data. |
| Award date | `TenderResult/AwardDate` | Schema doesn't cover -- flagging for review. Distinct from publication date; the actual date the award decision was made. |
| Contract formalization date | `TenderResult/Contract/IssueDate` | Schema doesn't cover -- flagging for review. The date the contract was formally signed. |
| Tender start date | `TenderResult/StartDate` | Schema doesn't cover -- flagging for review. |
| Lower/higher tender amounts | `TenderResult/LowerTenderAmount`, `HigherTenderAmount` | Schema doesn't cover -- flagging for review. Useful for analyzing price dispersion. |
| Result code | `TenderResult/ResultCode` | Schema doesn't cover -- flagging for review. Indicates whether the result is an actual award, void, desert, etc. Essential for filtering. |
| Submission method | `TenderingProcess/SubmissionMethodCode` | Schema doesn't cover -- flagging for review. Electronic vs. paper submission. |
| Urgency code | `TenderingProcess/UrgencyCode` | Schema doesn't cover -- flagging for review. Related to accelerated procedures. |
| Funding program | `TenderingTerms/FundingProgramCode` | Schema doesn't cover -- flagging for review. EU funding program references. |
| Financial guarantees | `TenderingTerms/RequiredFinancialGuarantee[]` | Schema doesn't cover -- flagging for review. Type, rate, and amount of required guarantees. |
| Variant constraint indicator | `TenderingTerms/VariantConstraintIndicator` | Schema doesn't cover -- flagging for review. Whether variants are allowed. |
| Subcontract terms | `TenderingTerms/AllowedSubcontractTerms` | Schema doesn't cover -- flagging for review. |
| Parent contracting authority | `LocatedContractingParty/ParentLocatedParty` (recursive, up to 6 levels) | Schema doesn't cover -- flagging for review. Hierarchical structure of the contracting body's parent organizations. |
| Lot-level data | `ProcurementProjectLot[]/ProcurementProject/*` | Schema captures awards per lot via multiple `AwardModel` entries, but lot-level budget, CPV, and description data is not separately preserved. |
| Contract modifications | `ContractModification[]` | Schema doesn't cover -- flagging for review. Amendments to awarded contracts including value changes and duration extensions. |
| Document references | `LegalDocumentReference`, `TechnicalDocumentReference`, `AdditionalDocumentReference` | Schema doesn't cover -- flagging for review. Links to specification documents and legal references. |
| Contracting system code | `TenderingProcess/ContractingSystemCode` | Schema doesn't cover -- flagging for review. Framework agreements, dynamic purchasing systems, etc. |
| Subtype code | `ProcurementProject/SubTypeCode` | Schema doesn't cover -- flagging for review. Finer-grained contract type classification. |
| Realized location details | `ProcurementProject/RealizedLocation/CountrySubentity`, `Address/*` | Schema only captures NUTS code, not free-text location descriptions or full address. |

### Code Normalization

CODICE uses its own code lists, published at `https://contrataciondelestado.es/codice/cl/`. These must be mapped to eForms equivalents. The `@listURI` attribute on coded elements references the specific CODICE code list URL, which can be used to verify code versions.

**Important caveat**: The exact CODICE code list values below are based on the reference Go parser ([juanfont/codice](https://github.com/juanfont/codice)), the BquantFinance dataset, and Spanish procurement law (Ley 9/2017). The definitive values are in the CODICE code list files (`.gc` format) published at the URLs referenced in `@listURI` attributes. **Before implementation, download a sample `.atom` file and inspect the actual `@listURI` URLs and code values in use.**

#### Contract Nature Codes (TypeCode)

The `ProcurementProject/TypeCode` field uses CODICE contract type codes. These need mapping to eForms `contract-nature` codes:

| CODICE TypeCode | Spanish Description | eForms Code |
|---|---|---|
| `1` | Obras (Works) | `works` |
| `2` | Suministros (Supplies) | `supplies` |
| `3` | Servicios (Services) | `services` |
| `21` | Gestion de Servicios Publicos | `services` (closest match) |
| `31` | Concesion de Servicios | `services` (closest match) |
| `40` | Colaboracion publico-privada | Needs investigation -- may map to `works` or `services` depending on context |
| `50` | Administrativo especial | Needs investigation |
| `7` | Patrimonial | Needs investigation |
| `8` | Privado | Needs investigation |

**Note**: The exact numeric codes and their completeness need verification against a real CODICE code list file. Spanish procurement law defines more contract types than EU directives (which only have works/supplies/services/combined). Types 21, 31, 40, 50, 7, 8 are Spain-specific and may require a best-effort mapping or be set to `None` if no eForms equivalent exists. The SubTypeCode field provides additional granularity.

#### Procedure Type Codes (ProcedureCode)

The `TenderingProcess/ProcedureCode` field uses CODICE procedure codes. These need mapping to eForms `procurement-procedure-type` codes:

| CODICE ProcedureCode | Spanish Description | eForms Code | Notes |
|---|---|---|---|
| `1` | Abierto (Open) | `open` | |
| `2` | Restringido (Restricted) | `restricted` | |
| `3` | Negociado con publicidad (Negotiated with publication) | `neg-w-call` | |
| `4` | Negociado sin publicidad (Negotiated without publication) | `neg-wo-call` | |
| `5` | Dialogo competitivo (Competitive dialogue) | `comp-dial` | |
| `6` | Asociacion para la innovacion (Innovation partnership) | `innovation` | |
| `7` | Basado en Acuerdo Marco (Based on framework agreement) | `oth-single` or `None` | No direct eForms equivalent for framework call-offs. Needs investigation. |
| `8` | Contrato menor (Minor contract) | `oth-single` or `None` | Below-threshold direct award. No direct eForms equivalent. |
| `9` | Derivado de Acuerdo Marco (Derived from framework) | `oth-single` or `None` | Same as 7. |
| `100` | Normas internas | `None` | Internal rules -- no eForms equivalent. |

**Note**: The exact numeric codes and completeness need verification against a real CODICE code list file (referenced by `@listURI` on the `ProcedureCode` element). Spanish procurement law (Ley 9/2017) defines more procedure types than the EU directive framework. Codes 7, 8, 9, and 100 are Spain-specific.

#### Authority Type Codes (ContractingPartyTypeCode)

The `LocatedContractingParty/ContractingPartyTypeCode` field uses CODICE authority type codes. These need mapping to eForms `buyer-legal-type` codes:

| CODICE Code | Spanish Description | eForms Code | Notes |
|---|---|---|---|
| `1` | Administracion General del Estado (Central government) | `cga` | |
| `2` | Comunidad Autonoma (Regional government) | `ra` | |
| `3` | Entidad Local (Local authority) | `la` | |
| `4` | Organismo Autonomo (Autonomous body) | `body-pl` | |
| `5` | Entidad Publica Empresarial (Public business entity) | `pub-undert` | |
| `6` | Universidad Publica (Public university) | `body-pl` | Closest match. |
| `7` | Poder adjudicador no AA.PP. (Contracting authority, not public admin) | `body-pl` | |
| `8` | Otro (Other) | `None` | No eForms equivalent. |

**Note**: The exact code values and completeness need verification against a real CODICE code list file. Spanish law defines finer-grained contracting authority types than the EU framework. The mapping above is a best-effort approximation; some codes may need adjustment based on the actual code list values observed in data.

#### Result Code (TenderResult/ResultCode)

This is not mapped to a schema field but is **critical for filtering** award notices:

| CODICE ResultCode | Description | Action |
|---|---|---|
| `1` or `ADJ` | Adjudicada (Awarded) | Include |
| `2` or `RES` | Resuelta/Formalizada (Formalized) | Include |
| `3` or `DES` | Desierta (Deserted/no valid tenders) | Exclude |
| `4` or `ANU` | Anulada (Annulled) | Exclude |
| `8` or other | Various | Investigate; exclude if not a valid award |

**Note**: The exact result code values (numeric vs. string) need verification. Both numeric and abbreviated string forms may appear depending on the CODICE version. The `@listURI` attribute on the `ResultCode` element will identify the specific code list in use.

#### Contract Folder Status Code (ContractFolderStatusCode)

Also critical for filtering, at the folder level:

| Likely Values | Description | Action |
|---|---|---|
| `PUB` | Publicada (Published) | Tendering phase -- skip |
| `EV` | En evaluacion (Under evaluation) | Skip |
| `ADJ` | Adjudicada (Awarded) | Include |
| `RES` | Resuelta/Formalizada (Formalized/signed) | Include |
| `DES` | Desierta (Deserted) | Skip |
| `ANU` | Anulada (Annulled) | Skip |
| `PRE` | Preanuncio (Prior information) | Skip |

**Note**: The exact status code values need verification. The `@listURI` attribute will reference the code list. Filter for awarded and formalized statuses only.

### Implementation Recommendations

1. **Start with sample data**: Download a single annual `.zip` file (e.g., 2024) and inspect the actual XML structure, namespace URIs, `@listURI` values on coded elements, and field population patterns before writing the parser. The CODICE schema has evolved over time and field availability may differ between years.

2. **Two-level filtering**: Filter at both `ContractFolderStatusCode` level (only awarded/formalized) AND `TenderResult/ResultCode` level (only actual awards, not deserted/annulled). A contract folder in "awarded" status may still have individual lots that were deserted.

3. **Code list verification**: Before hardcoding the code normalization maps, download the `.gc` code list files referenced by `@listURI` attributes in the XML. These are the authoritative source for code values and will reveal any codes not covered by the estimates above.

4. **Contractor data limitation**: The most significant schema gap is the lack of contractor address data in CODICE's `WinningParty`. The contractor NIF/CIF (`PartyIdentification/ID`) is available and highly valuable for entity resolution, but would require a schema extension to store. Consider adding a `tax_id` field to `ContractorModel` in a future iteration.

5. **Lot handling**: Map each `TenderResult` to a separate `AwardModel`. If `TenderResult/AwardedTenderedProject/ProcurementProjectLotID` is present, resolve lot-level CPV codes and title from the corresponding `ProcurementProjectLot` element. If no lot structure exists, use the project-level data.

6. **Deduplication with TED**: Above-threshold Spanish notices are cross-published to TED. Use `doc_id` namespacing (`ES-` prefix) to prevent collisions. There is no reliable cross-reference field to link a PLACSP record to its TED counterpart, so deduplication would need to be done at the analysis layer (matching on contracting body + title + date + value).

7. **Reference implementations**: The [juanfont/codice](https://github.com/juanfont/codice) Go parser extracts 82 fields from CODICE XML and provides verified XML paths. Use it as the primary reference for field extraction logic. The `codice.go` file contains the complete XPath hierarchy.
