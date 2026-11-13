# Error Codes and Common Errors (Procurement / SCM)

> Release: 26D · Last researched: 2026-11-14 · Status: UNVERIFIED (official docs publish almost no message-code catalogue)

## Business purpose
Quick lookup for errors the agent meets when writing to Fusion (REST, FBDI, UI). Oracle docs.oracle.com does **not** publish a catalogue of POZ-, PO-, POR-, RCV-, INV-, EGP- or FND- message numbers. Message text lives in the pod's message dictionary. So: verified rows below are causes documented in official topics (often without a code). Every row with a specific code is UNVERIFIED until seen on a pod or in the pod's Manage Messages.

## Where in Fusion (FSM)
- Task **Manage Messages** (Setup and Maintenance): search by message name or number, filter by application/module. Read-only use is safe; do not edit predefined messages. Custom message numbers use range 10,000,000–10,999,999. Common shared messages start with `FND_CMN_`.
- Supplier import rejections: table `POZ_SUPPLIER_INT_REJECTIONS` (rejection reason, attribute, value) and the import PDF report.
- Requisition approval: diagnostic **Requisition Approval - Validate** (see `approvals.md`).
- Requisition to PO: diagnostic report column `REQTOPO_AUTO_FAILED_REASON` (21C topic; re-check).

## Prerequisites & dependencies
- Roles: Business Flow Troubleshooting (diagnostics), access to Scheduled Processes output.

## Key fields
### HTTP status codes (REST, verified)
| Code | Meaning | Typical fix |
|---|---|---|
| 400 Bad Request | Validation error, missing required value | Read the response body message; `rest_describe` and fix payload |
| 401 Unauthorized | Missing/invalid credentials | Fix auth |
| 403 Forbidden | Missing role/privilege (or Global Trade Compliance location block) | Add privilege to the integration user's role |
| 403 on POST, GET works (VERIFIED-ON-POD 2026-11-14) | `POST suppliers` as `hcm_impl` on the demo pod: 403, empty body, no Oracle code, nothing created. Read access ≠ write access. | Grant Supplier Manager `ORA_POZ_SUPPLIER_MANAGER_ABSTRACT` (+ BU data access) to the agent user, or use a user that has it. Smoke test (reads only) cannot detect this. |
| 403 right after a role grant (VERIFIED-ON-POD 2026-11-14) | Same POST still 403 from a long-running client: the reused session cookie keeps the old role set. A fresh process succeeded at once. | Fixed in `client.py` (cookies cleared before every call). Restart the MCP server after role changes on older builds. |
| PO-2055145 (VERIFIED-ON-POD 2026-11-14) | `POST procurementAgents` with `AgentEmail` → "You must provide a valid value for the AgentEmail attribute." Cause seen: the email is shared by 25+ persons (`<shared demo email>` on HCM Implementation* workers) and user `hcm_impl` has no own person record. | Use a user linked to a unique worker; or pass `AgentId` (PersonId) — but agent access only helps the user linked to that person. |
| 403 on `POST suppliers/{id}/child/sites` with Supplier Manager + BU data access (2026-11-14) | User is not a procurement agent on the site's procurement BU. UNVERIFIED cause. | Create a procurement agent (`procurementAgents`, `ManageSuppliersAllowedFlag=true`) for the user on that BU. |
| 404 Not Found | Wrong resource URI or key | Re-query the key; do not build keys |
| 405 Method Not Allowed | Method not supported (for example DELETE on ASL entries) | Use the supported method |
| 406 / 415 | Wrong Accept / Content-Type | Use `application/json` or `application/vnd.oracle.adf.resourceitem+json`; actions use `application/vnd.oracle.adf.action+json` |
| 500 / 503 / 504 | Server error, overload, gateway timeout | Retry with backoff; check whether the write happened before retrying |

### Documented causes (verified, no code in docs)
| Area | Symptom / cause | Fix |
|---|---|---|
| Supplier import | Address Name sent when updating an existing supplier site → error. Site-address link cannot change. | Do not send Address Name (PARTY_SITE_NAME) on site updates |
| Supplier import | Sites / site assignments for **prospective** suppliers rejected | Promote to spend authorized first |
| Supplier import | Business relationship update via import not allowed | Use UI promote / spend authorization flow |
| Supplier import | Child rejected because parent missing (for example site assignment without site) | Load parents first, same order as import processes |
| Supplier import | Duplicate contact | Give distinct email for contacts with same last name |
| Supplier import | Certifying Agency "Other" unsupported | Use Create New Certifying Agency attribute |
| Supplier import | Attachment file name with `< > * ? \| ; " : / \ % $ ( )` | Rename files |
| Supplier import | Batch over 25,000 records; zip > 300 attachments or > 1.5 GB | Split batch / zip |
| Supplier import | Rejected rows reprocessed | Use import option **New**; run Purge Supplier Interface Records after success |
| Supplier user accounts | User actions stuck | Run Send Pending LDAP Requests (User Type = Party, Batch Size = A) |
| Supplier registration | Two suppliers share a taxpayer ID | Make one the child of the other, or change one taxpayer ID before clearing the parent |
| Supplier numbering | Next Supplier Number already used | Pick an unused number |
| ASL REST | Category-type, manufacturer or distributor ASL entries not creatable/readable via REST | Use UI |
| ASL REST | Ship-to-specific supplier item attributes on a Global entry not allowed | Create a ship-to org entry |
| BPA submit | Supplier lacks approved ASL status for lines that use only approved suppliers (`PO_ASL_VALIDATION_FOR_BPA` = Yes) | Create/approve ASL entry or set profile No |
| Requisition approval | Participant in use has no applying rule → not auto-approved | Add catch-all Automatic rule |
| Requisition approval | Mapping set returns null (wrong attribute name, extra spaces) | Fix mapping set; add null-handling rule |
| Req → PO automation | No valid buyer; negotiation required; no supplier/site; item not purchasable in BU default inventory org; P-Card inactive or site does not accept P-Card or active financial orchestration flow; emergency PO already exists; no valid source agreement; CPA-sourced line without Negotiated checked; "Automatically generate orders" not selected on agreement; consolidation on and Generate Orders not run | Fix the listed condition |
| Import Orders (PO import) | Validation errors listed in the process error log | Fix and resubmit |

### Message codes (all UNVERIFIED)
| Code | Reported meaning | Likely cause / fix | Status |
|---|---|---|---|
| POZ-2130403 | Error when creating supplier sites and addresses in one payload | Create the address first (`suppliers/{SupplierId}/child/addresses`), then the site referencing `SupplierAddressName`/`SupplierAddressId` in a separate call | UNVERIFIED: not found on docs.oracle.com |
| PO-*, POR-*, RCV-*, INV-*, EGP-*, FND-* | Module message prefixes (Purchasing, Self Service Procurement, Receiving, Inventory, Product Hub/Item, Applications Core) | Look up in Manage Messages on the pod; record here with date and pod | UNVERIFIED: no official catalogue found |

## Common mistakes
- Treating a REST 400 as permanent without reading the message text. The body carries the Fusion message.
- Retrying a timed-out POST without checking: it may have created the record.
- Inventing a meaning for a code. Record only codes seen on the pod, with the exact text.

## Channel & exact technique
- Preferred channel: read-only. Errors come from A/C/D writes. To decode: REST response body; ESS process log/output; `POZ_SUPPLIER_INT_REJECTIONS`; UI task Manage Messages (channel D, read-only).
- Supplier sites REST: `POST /fscmRestApi/resources/11.13.18.05/suppliers/{SupplierId}/child/sites` requires `SupplierSite` and `ProcurementBUId`; address via `SupplierAddressName` / `SupplierAddressId`. Address child: `POST /fscmRestApi/resources/11.13.18.05/suppliers/{SupplierId}/child/addresses`.

## How to verify
- Reproduce on a test pod; capture the full message (name, number, text); look it up in Manage Messages; add the row here with date and pod.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/Status_Codes.html — HTTP status codes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/create-suppliers-with-the-import-suppliers-process.html — supplier import errors and constraints
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/why-my-requisition-wasn-t-automatically-converted-into-a.html — req to PO causes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oaprc/using-procurement.pdf — taxpayer ID sharing error (via search snippet)
- https://docs.oracle.com/en/cloud/saas/procurement/26d/faspp/import-orders.html — Import Orders error log (via search snippet)
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/document-approvals-in-procurement.html — approval diagnostic
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-procurement-approved-supplier-list-entries.html — ASL REST restrictions
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliers-supplierid-child-sites-post.html — site required attributes, SupplierAddressName
- https://docs.oracle.com/en/cloud/saas/financials/26d/fafcf/implementing-common-features-for-financials-and-project-management.pdf — Manage Messages, number ranges, FND_CMN_ (via search snippet)
- https://docs.oracle.com/en/cloud/saas/procurement/25d/oedmp/pozsupplierintrejections-27748.html — POZ_SUPPLIER_INT_REJECTIONS (25D)

## UNVERIFIED
- POZ-2130403 meaning and fix.
- Any specific PO-, POR-, RCV-, INV-, EGP-, FND- message number.
- Prefix-to-module mapping (PO=Purchasing, POR=Self Service Procurement, RCV=Receiving, INV=Inventory, EGP=Product Hub/Items, FND=Applications Core).
- `REQTOPO_AUTO_FAILED_REASON` diagnostic column in 26D (21C topic).
- Whether a supplier POST with nested `addresses` and `sites` in one payload is supported in 26D.
