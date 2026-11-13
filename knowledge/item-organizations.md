# Item Organizations and Item Master

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
- **Item organization**: defines items only. It holds no balances or transactions, for example retail outlets or sales catalogs. It has no BU or legal entity dependency. Financial and accounting item attributes are hidden in it.
- **Inventory organization**: stores and transacts items (see `inventory-organizations.md`).
- **Item master organization**: lists items shared across inventory and item orgs.
  - Docs best practice: use a single item master. Make it an item org, separate from transacting orgs.
  - Item numbers must be unique across all item masters.
- An item org can be changed into an inventory org: Edit Item Organization, then Usage = Inventory management.
- Item grouping behavior:
  - Definition org: holds its own attribute values.
  - Reference org: takes all values from an item definition org.
  - Change it with Actions > *Process Item Grouping Change* (scheduled process). Then grant privileges on Manage Item Classes.

## Where in Fusion (FSM)
- Offering: Product Management (also in Manufacturing and Supply Chain Materials Management). Task: **Manage Item Organizations**. Related task: **Manage Organization Trees**, used by mass changes such as Assign to Organization.
- Functional area name for Manage Item Organizations: UNVERIFIED. The Product Management roadmap groups it under "Define Item Organizations for Product Management".
- Inventory-org variant: Offering Product Management, Functional area **Inventory Organizations**, Task **Manage Inventory Organizations**.

## Prerequisites & dependencies
- At least one item org must exist before you can create items (Product Hub).
- Inventory orgs point to the master through `MasterOrganizationId`.
- Items are created in the master org, then assigned to child orgs (see `items-item-classes.md`).

## Key fields
| Field (UI label) | REST attribute (`inventoryOrganizations`) | Meaning | Notes |
|---|---|---|---|
| Usage | `InventoryFlag` | false = item org, true = inventory org | required on create |
| Item Master Organization | `MasterOrganizationId` / `MasterOrganizationCode` | | |
| Item Grouping Behavior | `ItemGroupingCode` | `ORA_RCS_IGB_DFTN` / `ORA_RCS_IGB_RFRC` | |
| Item Definition Organization | `ItemDefinitionOrganizationId` / `Code` | source org for a reference org | |
| Name / Code | `OrganizationName` / `OrganizationCode` | | code max 18 |

## Common mistakes
- Making the item master a transacting inventory org.
- Multiple item masters without a reason. The docs warn to use this sparingly.
- Reference org without the correct definition org. Converting it later needs a scheduled process plus security grants.

## Channel & exact technique
- Preferred channel: **A (REST)**. Item orgs use the same resource as inventory orgs.
- A:
  - `POST /fscmRestApi/resources/11.13.18.05/inventoryOrganizations` with `"InventoryFlag": false`. The doc says BU and legal entity are only required when the org is an inventory org.
  - List item orgs: `GET .../inventoryOrganizations?finder=itemOrgs;Status=Active`.
  - The item master is the value of `MasterOrganizationId` on the orgs.
- D (UI): Manage Item Organizations, then Edit Item Organization (Usage field).

## How to verify
`GET inventoryOrganizations?finder=itemOrgs` lists the orgs. Then check `InventoryFlag=false` and `MasterOrganizationCode`.

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faicf/implementing-common-features-for-scm.pdf — ch. 24 Item Organizations (setup tasks, item master, FAQs)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faipr/implementing-product-management.pdf — ch. 2 Item Organizations, Process Item Grouping Change procedure, roadmap
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventoryorganizations-post.html — InventoryFlag semantics, item grouping attributes
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-inventoryorganizations-get.html — `itemOrgs` finder

## UNVERIFIED
- Functional area name that holds Manage Item Organizations in 26D.
- Whether `LocationId` / `ScheduleId` are mandatory for an item org created through REST.
- FSM CSV support for Manage Item Organizations.
