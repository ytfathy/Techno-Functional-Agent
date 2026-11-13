# Knowledge index — map a request to a file

Start every request here. Then `dependencies.md` for prerequisites, `fsm-task-codes.md` for channel B, `error-codes.md` for errors.

| Request is about… | File | Main channel |
|---|---|---|
| Location, ship-to / bill-to / receiving location | locations.md | A `locationsV2` / B |
| Reference data set, set assignment | reference-data-sets.md | A `setIdSets`, `setIdAssignmentsBusinessUnit` / B |
| Business unit, business functions | business-units.md | B / D |
| Legal entity, ledger (lookup) | legal-entities-ledgers.md | A read-only |
| User data access (BU, inventory org) | bu-data-access.md | A `dataSecurities` / D |
| Users, roles | users-roles.md, access-and-roles.md | A SCIM |
| Configure Procurement BF, numbering | configure-procurement-bf.md | B |
| Configure Requisitioning BF | configure-requisitioning-bf.md | B |
| Service provider relationships | service-provider-relationships.md | B |
| Document styles | document-styles.md | A `purchasingDocumentStyles` / B |
| Line types | line-types.md | A `purchasingLineTypes` |
| Catalogs, categories, category hierarchy | procurement-categories-catalogs.md | A / D |
| Procurement agents (buyer access) | procurement-agents.md | A `procurementAgents` |
| Supplier numbering, registration setup | supplier-setup.md | A `supplierNumbering`, `supplierOptions` / B |
| Approved supplier list | approved-supplier-list.md | A |
| Approval rules, approval groups | approvals.md | D |
| Negotiation styles / sourcing | negotiation-styles.md | B / D |
| Procurement profile options, lookups | procurement-profile-options-lookups.md, common-setup.md | B / A lookups |
| Suppliers, addresses, sites, assignments, contacts, bank | suppliers.md | A (separate calls) / C bulk |
| Requisitions | requisitions.md | A |
| Purchase orders, change orders, cancel, close | purchase-orders.md | A |
| Blanket / contract agreements | agreements.md | A / C |
| Receipts | receipts.md | A |
| End-to-end test req → PO → receipt | p2p-test-cycle.md | A |
| Inventory organizations | inventory-organizations.md | A / B |
| Item organizations, item master | item-organizations.md | A / B |
| Subinventories, locators | subinventories-locators.md | A / B |
| Items, item classes | items-item-classes.md | A / C / D |
| UOMs | uoms.md | A / B |
| Shipping networks (interorg parameters) | shipping-networks.md | A / B |
| Transfer orders | transfer-orders.md | A `supplyRequests` |
| Receiving parameters | receiving-parameters.md | B / D (REST read-only) |
| Carriers, ship methods | carriers.md | A `carriers` |
| Lookups, value sets, DFFs, profile options, scheduled processes | common-setup.md | A / B / C |
| REST mechanics (describe, q, actions, batch, errors) | rest-api-conventions.md | — |
| FSM CSV mechanics | channel-b-fsm-csv.md, fsm-task-codes.md | B |
| FBDI / ESS mechanics, templates, UCM accounts | channel-c-fbdi-ess.md | C |
| Oracle error codes | error-codes.md | — |

Not in this list → research it first (oracle-researcher subagent) and add a file + a row here.
