# Suppliers (Supplier Model)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Supplier master: header (party), addresses, sites (per procurement BU), site assignments (per client BU = where POs/invoices can be raised), contacts, business classifications, products & services categories, attachments. A site without an active assignment for the client BU cannot be used on POs or invoices. Bank accounts and payment attributes live in Financials (Payments/iby), not in the Suppliers resource.

## Where in Fusion (FSM)
- UI: Procurement > Suppliers (Create Supplier / Manage Suppliers). Not an FSM setup task; this is transactional master data.
- Setup that drives behaviour: Configure Procurement Business Function (supplier site assignment defaults), Supplier numbering (UNVERIFIED task names, not researched here).

## Prerequisites & dependencies
- Procurement BU (site owner), client BU served by that procurement BU (assignment), bill-to BU, ship-to/bill-to locations.
- Lookups: POZ_VENDOR_TYPE (SupplierTypeCode), POZ_ORGANIZATION_TYPE (TaxOrganizationTypeCode), ORA_POZ_BUSINESS_RELATIONSHIP (BusinessRelationshipCode), POZ_BUSINESS_CLASSIFICATIONS, POZ_MINORITY_GROUP, CONTACT_TITLE, DOCUMENT_COMMUNICATION_METHOD.
- Downstream: requisitions, POs, agreements, receipts, AP invoices all reference supplier + site.

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Supplier | `Supplier` | Supplier name (max 360) | schema-required |
| Supplier Number | `SupplierNumber` | max 30 | schema lists as required; playbook recommends leaving blank (auto-number) in FBDI. REST behaviour if omitted: UNVERIFIED |
| (party) | `SupplierPartyId` | TCA party | schema lists as required; for a NEW supplier it is generated (UNVERIFIED) |
| Tax Organization Type | `TaxOrganizationType` / `TaxOrganizationTypeCode` | lookup POZ_ORGANIZATION_TYPE | e.g. CORPORATION (UNVERIFIED code) |
| Supplier Type | `SupplierType` / `SupplierTypeCode` | lookup POZ_VENDOR_TYPE | |
| Business Relationship | `BusinessRelationship` / `BusinessRelationshipCode` | lookup ORA_POZ_BUSINESS_RELATIONSHIP | SPEND_AUTHORIZED / PROSPECTIVE (codes UNVERIFIED) |
| Creation source | `CreationSourceCode` | default `WEB_SERVICE` | |
| Address name | addresses `AddressName` | max 240 | |
| Country | addresses `CountryCode` (req) / `Country` | ISO2 | schema required: `CountryCode`, `Email` |
| Address lines | `AddressLine1`, `City`, `State`, `PostalCode` | | |
| Address purposes | `AddressPurposeOrderingFlag`, `AddressPurposeRemitToFlag`, `AddressPurposeRFQOrBiddingFlag` | booleans, default false | doc descriptions of RemitTo/RFQ appear swapped |
| Site | sites `SupplierSite` (req, max 240) | site code/name | |
| Procurement BU | sites `ProcurementBUId` (req) / `ProcurementBU` | | |
| Address | sites `SupplierAddressId` / `SupplierAddressName` | link to supplier address | NOT `AddressName` |
| Site purposes | `SitePurposePurchasingFlag`, `SitePurposePayFlag`, `SitePurposePrimaryPayFlag`, `SitePurposeProcurementCardFlag`, `SitePurposeSourcingOnlyFlag` | booleans | purchasing + pay for P2P test |
| Communication | `CommunicationMethodCode` (NONE/FAX/EMAIL/PRINT), `Email` | PO communication | |
| Client BU | assignments `ClientBUId` / `ClientBU` | BU that may transact | |
| Bill-to BU | assignments `BillToBUId` / `BillToBU` | | |
| Ship-to / Bill-to location | `ShipToLocationId`/`ShipToLocationCode`, `BillToLocationId`/`BillToLocationCode` | | |
| Distributions | `LiabilityDistribution`, `PrepaymentDistribution`, `BillPayableDistribution`, `DistributionSet` | AP defaults | |
| Withholding | `UseWithholdingTaxFlag`, `WithholdingTaxGroup(Id)` | boolean (example sends "Y"; schema boolean) | |
| Inactive date | assignments `InactiveDate` | blank = open (`4712-12-31` returned) | |
| Contact name | contacts `FirstName`, `LastName`, `MiddleName`, `Salutation`/`SalutationCode`, `JobTitle` | | |
| Contact email | contacts `Email` | schema-required (with `InactiveDate`!) | docs example omits both; send Email, omit InactiveDate first |
| Admin contact | `AdministrativeContactFlag` | boolean | |
| Contact phones | `PhoneCountryCode`, `PhoneAreaCode`, `PhoneNumber`, `MobileCountryCode`, `MobileAreaCode`, `MobileNumber` | | |
| Contact address link | contact child addresses `SupplierAddressId` / `AddressName` | | |
| Business classification | `ClassificationCode` (req), `SubclassificationCode`, `CertifyingAgencyId`, `CertificateNumber`, `CertificateStartDate`, `CertificateExpirationDate` | | |
| Products & services | `ProductsServicesCategoryId`, `CategoryName`, `CategoryType` | | example `CategoryType: "BROWSING"` |

## Common mistakes
- Sending supplier + addresses + sites + assignments + contacts in one deep POST. The supplier POST schema accepts child arrays (`addresses`, `sites`, `contacts`, `businessClassifications`, `productsAndServices`, `attachments`, `DFF`, `globalDFF`, ...), but a site needs a `SupplierAddressId` that only exists after the address is committed, and a site's `assignments` need the site. Do it step by step. The specific error code POZ-2130403 for this failure: UNVERIFIED (not found on docs.oracle.com).
- Using `AddressName` on a site (correct: `SupplierAddressName` / `SupplierAddressId`).
- Forgetting the site assignment: site exists but PO/requisition cannot pick it for the client BU.
- Using an ID path segment you generated. `SupplierId`, `SupplierSiteId`, `SupplierContactId` come from responses / GET.
- Supplier profile is locked (REST and FBDI updates fail) while a profile change request is draft/pending or a spend-authorization request is pending approval (playbook).
- If change control is enabled on a supplier entity, POST/PATCH are allowed only for integration users (playbook).
- Contacts/addresses DFF: REST supports GET only; use FBDI/SOAP for writes (playbook).
- Max ~500 records per POST batch (playbook best practice).
- Bank data: cannot be created in the same BATCH as Suppliers resources (playbook). Never log bank account numbers/IBAN.

## Channel & exact technique
- Preferred channel: A (REST) for low volume / test data (real time, returns IDs). C (FBDI) for migration volumes (>a few hundred suppliers; 25,000 rows per batch, max 4 concurrent batches).
- Base: `/fscmRestApi/resources/11.13.18.05`
- Media types: create/update items `Content-Type: application/vnd.oracle.adf.resourceitem+json` (docs cURL examples) — schema also lists `application/json`. Custom actions `application/vnd.oracle.adf.action+json`. Optional header `Upsert-Mode: true`.

### A (REST) resources
| Resource | Path | Methods |
|---|---|---|
| suppliers | `/suppliers`, `/suppliers/{SupplierId}` | GET, POST, PATCH |
| addresses | `/suppliers/{SupplierId}/child/addresses[/{SupplierAddressId}]` | GET, POST, PATCH (UNVERIFIED: DELETE) |
| sites | `/suppliers/{SupplierId}/child/sites[/{SupplierSiteId}]` | GET, POST, PATCH (no DELETE) |
| site assignments | `/suppliers/{SupplierId}/child/sites/{SupplierSiteId}/child/assignments[/{AssignmentId}]` | GET, POST, PATCH |
| site children | `.../sites/{SupplierSiteId}/child/attachments`, `.../child/DFF`, `.../child/globalDFF`, `.../child/thirdPartyPaymentRelationships` | per page |
| contacts | `/suppliers/{SupplierId}/child/contacts[/{SupplierContactId}]` | GET, POST, PATCH |
| contact addresses | `/suppliers/{SupplierId}/child/contacts/{SupplierContactId}/child/addresses[/{SupplierContactAddressId}]` | GET, POST, DELETE |
| contact children | `.../contacts/{SupplierContactId}/child/roles`, `.../child/dataaccess` (body array name `dataaccess`), person DFF | |
| business classifications | `/suppliers/{SupplierId}/child/businessClassifications[/{ClassificationId}]` | GET, POST, PATCH, DELETE (+ child attachments) |
| products & services | `/suppliers/{SupplierId}/child/productsAndServices[/{SupplierProductsServicesId}]` | GET, POST, DELETE; read-only view `/child/productsAndServicesView` |
| attachments | `/suppliers/{SupplierId}/child/attachments[/{attachmentsUniqID}]` | GET, POST, PATCH, DELETE |
| LOV | `/suppliersLOV`, `/suppliersLOV/{SupplierId}/child/sitesLOV` | GET |
| other children | `DFF`, `globalDFF`, `externalDataProviderIdentifiers`, `mergeHistory`, `spendAuthorizationApprovalRequests` | |

Supplier custom actions (POST `/suppliers/{SupplierId}/action/<name>`, `application/vnd.oracle.adf.action+json`): `addRecentSupplier`, `getSupplierProfileOptions`, `markSupplierChanged`, `resubmitSpendAuthorizationRequest`, `scores`, `signals`, `submitSpendAuthorizationRequest`, `submitSpendAuthorizationRequestWithSites`, `externalValidationForSupplierAttributes`; collection action `/suppliers/action/callExternalProviderAPI`. Action parameters: UNVERIFIED (not read).

### Call order (each step needs the ID from the previous response)
1. `POST /suppliers` → `SupplierId`
   ```json
   {"Supplier":"ACME TEST SUPPLIER","TaxOrganizationTypeCode":"CORPORATION","SupplierTypeCode":"SUPPLIER","BusinessRelationshipCode":"SPEND_AUTHORIZED"}
   ```
   (constructed from schema names; codes UNVERIFIED — resolve via lookups or `rest_describe`; no example on the 26D page)
2. `POST /suppliers/{SupplierId}/child/addresses` → `SupplierAddressId`. Docs example:
   ```json
   {"AddressName":"Headquarter","Country":"United States","AddressLine1":"Example Road","City":"Redwood City","State":"CA","PostalCode":"94065","AddressPurposeOrderingFlag":true,"AddressPurposeRemitToFlag":true,"AddressPurposeRFQOrBiddingFlag":false}
   ```
   Add `"CountryCode":"US"` (schema-required; docs example omits it).
3. `POST /suppliers/{SupplierId}/child/sites` on the **procurement BU** → `SupplierSiteId`
   ```json
   {"SupplierSite":"ACME-HQ","ProcurementBUId":204,"SupplierAddressId":<from 2>,"SitePurposePurchasingFlag":true,"SitePurposePayFlag":true}
   ```
   (constructed; required = `SupplierSite`, `ProcurementBUId`)
4. `POST /suppliers/{SupplierId}/child/sites/{SupplierSiteId}/child/assignments` for the **client BU**. Docs example:
   ```json
   {"ClientBUId":5186,"BillToBU":"Vision Construction","ShipToLocationId":2510,"BillToLocationCode":"FLDSVC_0_2452104113000","UseWithholdingTaxFlag":"Y","WithholdingTaxGroupId":100100019061302,"DistributionSet":"1 Line Set QA","LiabilityDistribution":"01-000-2372-0000-000","PrepaymentDistribution":"01-510-7430-0000-000","InactiveDate":""}
   ```
   Minimal: `{"ClientBUId":<id>,"BillToBUId":<id>}` (send booleans as true/false; omit InactiveDate).
5. `POST /suppliers/{SupplierId}/child/contacts`. Docs example:
   ```json
   {"Salutation":"Ms.","FirstName":"Jill","LastName":"Smith","AdministrativeContactFlag":true,"MobileCountryCode":"1","MobileAreaCode":"650","MobileNumber":"555-2234"}
   ```
   Add `"Email"`. Then optionally `POST .../contacts/{SupplierContactId}/child/addresses` `{"SupplierAddressId":<from 2>}`.
6. Optional: `POST .../businessClassifications` (docs example: `{"ClassificationCode":"HUB_ZONE","CertifyingAgencyId":4,"CertificateNumber":"0099","CertificateStartDate":"2019-11-12","CertificateExpirationDate":"2029-11-13"}`), `POST .../productsAndServices` (`{"CategoryName":"Desktop","CategoryType":"BROWSING"}`).
- Auto-creation of site assignments on spend authorization (`AutoCreateSiteAssignmentFlag` in supplier options): UNVERIFIED.

### Bank account hand-off (Financials REST, separate calls, not batchable with Suppliers)
- HIGH-IMPACT DATA: bank account numbers, IBAN, branch numbers must never be logged, echoed in tool output, or stored in knowledge/logs. Mask in any trace. Require explicit user confirmation before any write.
- `POST /fscmRestApi/resources/11.13.18.05/paymentsExternalPayees` — payee: `PaymentFunctionCode` (req, e.g. `SUPPLIER_PAYMENT`), `PartyName`, `PayeePartyIdentifier`, `PayeePartyNumber` (req), `Intent` (`PAYABLES_DISB` = Supplier), `SupplierNumber`, `SupplierSiteCode`/`SupplierSiteIdentifier`, `OrganizationName`.
- `POST /fscmRestApi/resources/11.13.18.05/externalBankAccounts` — `BankAccountNumber`, `BankAccountName`, `CountryCode`, `CurrencyCode`, `IBAN`, `BankIdentifier`/`BankName`, `BankBranchIdentifier`/`BankBranchName`, `Intent` (`PAYABLES_DISB` for suppliers), child `accountOwners` (`AccountOwnerPartyIdentifier`, ...). `PayeeCreation` is internal use only — do not use.
- `POST /fscmRestApi/resources/11.13.18.05/instrumentAssignments` — links bank account to payee: docs example `{"PaymentPartyId":300100180882048,"PaymentInstrumentId":300100181126859,"PaymentFlow":"DISBURSEMENTS","PaymentInstrumentType":"BANKACCOUNT","Intent":"Supplier"}`.
- Bank accounts can be created by FBDI (Financials "Supplier Bank Account Import") but only updated via externalBankAccounts/instrumentAssignments REST or the UI (playbook).

### C (FBDI) — UCM account `prc/supplier/import` for all supplier objects
| Object | Template | Control file(s) / interface table(s) | Scheduled process |
|---|---|---|---|
| Suppliers | `SupplierImportTemplate.xlsm` | `PozSuppliersInt.ctl` / `POZ_SUPPLIERS_INT` | Import Suppliers |
| Addresses | `SupplierAddressImportTemplate.xlsm` | `PozSupAddressesInt.ctl` / `POZ_SUP_ADDRESSES_INT` | Import Supplier Addresses |
| Sites | `SupplierSiteImportTemplate.xlsm` | `PozSupplierSitesInt.ctl`, `PozSupThirdPartyInt.ctl` / `POZ_SUPPLIER_SITES_INT`, `POZ_SUP_THIRDPARTY_INT` | Import Supplier Sites |
| Site assignments | `SupplierSiteAssignmentImportTemplate.xlsm` | `PozSiteAssignmentsInt.ctl` / `POZ_SITE_ASSIGNMENTS_INT` | Import Supplier Site Assignments |
| Contacts | `SupplierContactImportTemplate.xlsm` | `PozSupContactsInt.ctl`, `PozSupContactAddressesInt.ctl` / `POZ_SUP_CONTACTS_INT`, `POZ_SUP_CONTACT_ADDRESSES_INT` | Import Supplier Contacts |
| Business classifications | page `importsupplierbusinessclassifications-3127` | not read | Import Supplier Business Classifications (UNVERIFIED) |
| Products & services | page `importsupplierproductsandservicescategories-3130` | not read | UNVERIFIED |
- Flow: generate CSV/zip from template → upload to UCM `prc/supplier/import` → Load Interface File for Import → run import process in order Suppliers → Addresses → Sites → Site Assignments → Contacts. ESS job paths and parameter lists: UNVERIFIED (pages give display names only).
- Keep the CSV file-name prefix (e.g. `PozSupplierSitesInt_<suffix>.csv`). `#NULL` blanks a value. Re-run with "Rejected" option. Supplier FBDI updates skip approval.

## How to verify
- `GET /suppliers?q=Supplier='ACME TEST SUPPLIER'` → `SupplierId`, `SupplierNumber`.
- `GET /suppliers/{SupplierId}/child/sites` → site on correct `ProcurementBU`, purposes set.
- `GET .../sites/{SupplierSiteId}/child/assignments` → `ClientBU`, `Status` = `ACTIVE`, `InactiveDate` 4712-12-31.
- `GET /suppliersLOV/{SupplierId}/child/sitesLOV` to see what a transaction LOV will offer.
- Functional: create a requisition/PO line with that supplier+site in the client BU.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-suppliers.html — supplier endpoints and actions
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliers-post.html — supplier attributes, child collections, Upsert-Mode
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-suppliers-sites.html — site endpoints + child pages
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliers-supplierid-child-sites-post.html — site required attrs
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-suppliers-sites-site-assignments.html — assignment endpoints
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliers-supplierid-child-sites-suppliersiteid-child-assignments-post.html — assignment attrs + example
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliers-supplierid-child-addresses-post.html — address attrs + example
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-suppliers-contacts.html, .../api-suppliers-contacts-contact-addresses.html, .../op-suppliers-supplierid-child-contacts-post.html — contacts
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-suppliers-business-classifications.html, .../op-suppliers-supplierid-child-businessclassifications-post.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-suppliers-products-and-services.html, .../op-suppliers-supplierid-child-productsandservices-post.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-suppliers-attachments.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/rest-endpoints.html — suppliersLOV
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fainp/integration-playbooks-for-procurement.pdf — Supplier Model FBDI/REST best practices, constraints, bank-account resources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oefbp/toc.htm and importsuppliers-3129.html, importsupplieraddresses-3125.html, importsuppliersites-3132.html, importsuppliersiteassignments-3131.html, importsuppliercontacts-3128.html — FBDI templates
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-externalbankaccounts-post.html, op-paymentsexternalpayees-post.html, op-instrumentassignments-post.html — bank/payee

## UNVERIFIED
- POZ-2130403 meaning and that it is the error for a combined deep POST (not found in docs).
- Whether `SupplierNumber` / `SupplierPartyId` can be omitted on REST create (schema marks them required; expected auto-generated).
- Lookup codes: TaxOrganizationTypeCode `CORPORATION`, SupplierTypeCode `SUPPLIER`, BusinessRelationshipCode `SPEND_AUTHORIZED`/`PROSPECTIVE`.
- Address DELETE/PATCH support (address endpoint list page not read).
- Site POST example payload (none found on 26D page; payload constructed).
- Contact `InactiveDate` really mandatory (schema says required; example omits it).
- Parameters of `submitSpendAuthorizationRequest*` actions; auto-create site assignments flag behaviour.
- FBDI ESS job paths/parameters; business classification and products/services FBDI template names.
- Exact supplier payee/bank example payloads (only instrumentAssignments example verified).
