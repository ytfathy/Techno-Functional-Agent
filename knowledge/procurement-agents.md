# Procurement Agents (Manage Procurement Agents)

> Release: 26D · Last researched: 2026-11-14 · Status: VERIFIED (REST) / PARTIAL (code values)

## Business purpose
Buyers, catalog administrators, category managers, procurement contract administrators, procurement managers, supplier administrators, supplier managers and supplier qualification users must be procurement agents to work on procurement documents. Each assignment is **per procurement BU**. It defines which procurement actions the agent may perform, and the agent's access level to documents owned by **other** agents. Agents always have full action on their own documents within a BU they can access.

## Where in Fusion (FSM)
- Offering: Procurement
- Functional areas: **Procurement Foundation** and **Payables**
- Task name: **Manage Procurement Agents**

## Prerequisites & dependencies
- The user is registered as an **employee** (worker). The user account exists with buyer or other roles.
- The procurement BU is configured (Configure Procurement Business Function).
- Optional: a default requisitioning BU that is a client of the procurement BU.
- Dependents: buyer assignment rules, PO/BPA buyer, sourcing, catalog authoring, supplier maintenance, OTBI spend.

## Key fields
| Field (UI label) | REST attribute | Meaning | Notes / typical value |
|---|---|---|---|
| Agent (Name) | `Agent` (240), `AgentId` (required), `AgentEmail` | Worker | "Last Name, First Name" |
| Procurement BU | `ProcurementBU`, `ProcurementBUId` (required) | Assignment scope | One row per agent + BU, keyed by `AssignmentId` |
| Default Requisitioning BU | `DefaultRequisitioningBU`, `DefaultRequisitioningBUId` | | |
| Default Printer | `DefaultPrinter` | | LOV via `POST procurementAgents/action/getPrinters` |
| Status | `Status` (Active/Inactive), `StatusCode` (Y/N, default Y) | | |
| **Action: Manage Requisitions** | `ManageRequisitionsAllowedFlag` | | default false |
| **Action: Manage Purchase Orders** (incl. work confirmations) | `ManageOrdersAllowedFlag` | | |
| **Action: Manage Purchase Agreements** (blanket + contract) | `ManageAgreementsAllowedFlag` | | |
| **Action: Manage Negotiations** | `ManageNegotiationsAllowedFlag` | | |
| **Action: Manage Sourcing Programs** | `ManageSourcingProgramsAllowedFlag` | | |
| **Action: Manage Catalog Content** (local/punchout catalogs, content zones, smart forms, information templates, collaborative authoring) | `ManageCatalogContentAllowedFlag` | | |
| **Action: Manage Suppliers** | `ManageSuppliersAllowedFlag` | | |
| **Action: Manage Supplier Qualifications** (initiatives, qualifications, assessments) | `ManageQualificationsAllowedFlag` | | |
| **Action: Manage Approved Supplier List Entries** | `ManageAslAllowedFlag` | | |
| **Action: Analyze Spend** (BI invoice spend) | `AnalyzeSpendAllowedFlag` | | |
| Action: Manage Checklists (compliance) | `ManageChecklistsAllowedFlag` | | REST only in docs |
| Action: Manage Intake Requests | `ManageIntakeRequestsAllowedFlag` | | REST only in docs (26C+ feature) |
| **Access to Other Agents' Documents: Requisitions** | `AccessLevelToOtherAgentsRequisitions` / `...RequisitionsCode` | None/View/Full | |
| ... Purchase Orders | `AccessLevelToOtherAgentsOrders` / `...OrdersCode` | None/View/**Modify**/Full | |
| ... Purchase Agreements | `AccessLevelToOtherAgentsAgreements` / `...AgreementsCode` | None/View/**Modify**/Full | |
| ... Negotiations | `AccessLevelToOtherAgentsNegotiations` / `...NegotiationsCode` | None/View/Full | |
| ... Sourcing Programs | `AccessLevelToOtherAgentsSourcingPrograms` / `...SourcingProgramsCode` | None/View/Full | |
| ... Qualifications | `AccessLevelToOtherAgentsQualifications` / `...QualificationsCode` | None/View/Full | |
| ... Checklists | `AccessLevelToOtherAgentsChecklists` / `...ChecklistsCode` | None/View/Full | |
| ... Intake Requests | `AccessLevelToOtherAgentsIntakeRequests` / `...IntakeRequestsCode` | None/Full | |
| DFF | child `DFF` (`__FLEX_Context`) | | |

Access levels:
- **None**: no access.
- **View**: search and view.
- **Modify**: view, modify, delete, withdraw.
- **Full**: view, modify, delete, withdraw, freeze, hold, close, cancel, finally close.

There are no "other agents" access fields for catalog content, suppliers, ASL or spend. Those are action flags only.

### "All access" mapping (for code)
Set all 12 `Manage*AllowedFlag` / `AnalyzeSpendAllowedFlag` = `true`, and all 8 `AccessLevelToOtherAgents*` = `Full`. The REST docs show title-case meanings ("None", "View", "Full") for the non-Code attributes. The stored strings for the `*Code` attributes are **not shown** in the docs; run `rest_describe` or GET an existing agent first. Do not assume `FULL`.

## Common mistakes
- The user is not an employee, so they can't be added as an agent.
- The agent has the buyer role but is missing the procurement BU row, so documents don't show.
- Giving Manage Orders with Access None and expecting the agent to see others' POs. Agents only see their own.
- Expecting "Modify" on requisitions or negotiations. It exists only for orders and agreements.
- Creating a duplicate agent+BU row. Use PATCH on the `AssignmentId`.

## Channel & exact technique
- Preferred channel: **A (REST)**.
- `GET /fscmRestApi/resources/11.13.18.05/procurementAgents` (finders `PrimaryKey;AssignmentId=`, `ByAssignmentId;AssignmentId=`). `q` is queryable on: AgentId, Agent, AgentEmail, AssignmentId, ProcurementBU, ProcurementBUId, DefaultRequisitioningBU, Status, StatusCode, ManageOrdersAllowedFlag, ManageChecklistsAllowedFlag, ManageIntakeRequestsAllowedFlag, AccessLevelToOtherAgentsChecklistsCode.
- `GET .../procurementAgents/{AssignmentId}`
- `POST .../procurementAgents` (header `Upsert-Mode: true` is supported). The schema marks `AgentId`, `ProcurementBUId`, `Status`, all `Manage*AllowedFlag`, `AnalyzeSpendAllowedFlag` and all `AccessLevelToOtherAgents*Code` as required, so send them all.
- `PATCH .../procurementAgents/{AssignmentId}`
- `POST .../procurementAgents/action/getPrinters`
- Child: `.../procurementAgents/{AssignmentId}/child/DFF`
- There is **no DELETE**. Inactivate with `StatusCode=N` / `Status=Inactive`.
- B / C: not needed. FBDI / spreadsheet upload for agents was not researched.
- D (UI): Manage Procurement Agents (fallback only).

## How to verify
- `GET procurementAgents?q=AgentId=<id>;ProcurementBUId=<bu>`. Compare the flags.
- Functional test: sign in as the agent and open Manage Orders in the BU.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/procurement-agents.html — UI actions, access levels, employee prerequisite
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/how-you-manage-procurement-agent-security.html — agent types, functional areas
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-procurement-agents.html — operations
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-procurementagents-post.html — attribute names, values, required list
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-procurementagents-get.html — finders, queryable attributes, example values

## UNVERIFIED
- Stored value strings for the `AccessLevelToOtherAgents*Code` attributes (title case vs upper case).
- Allowed values of `AccessLevelToOtherAgentsIntakeRequestsCode` (not listed).
- Whether Checklists and Intake Requests appear on the 26D UI page (not in the oapro topic).
- Whether all the `*Code` fields are really required on POST, or default server-side.
