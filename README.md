# oracle-scm-agent

**A techno-functional AI consultant for Oracle Fusion Cloud SCM & Procurement.** Open Claude Code in this folder and write a request in English or Arabic. The agent does the work in Fusion itself, the way a senior consultant who covers both sides would:

| | Functional (supply chain) | Technical |
|---|---|---|
| **What it does** | Configures and runs the business: enterprise structure, procurement, suppliers, inventory, cost, shipping, order management, financial orchestration | Builds and runs reports, analyzes data with SQL, troubleshoots approvals and jobs, integrates via REST/SOAP/FBDI, manages security and roles |
| **How** | Business REST, FSM setup CSV, FBDI, UI playbooks | BI Publisher (reports + SQL), BPM workflow REST, SOAP services, ESS, SCIM |
| **Typical output** | A configured BU, a supplier with sites, a PO received end-to-end | A report in `reports/`, a root-cause analysis, a fixed approval, a granted role |

It is **not an advisor**. For every request it reads the current state, checks prerequisites, picks the fastest safe channel, backs up, executes, verifies, and documents. The operating rules (request loop, safety rules, modes) are in [CLAUDE.md](CLAUDE.md); the original brief is in [SPEC.md](SPEC.md); build status and the backlog are in [PROGRESS.md](PROGRESS.md).

---

## What it covers

### Functional — supply chain & procurement
| Area | Examples of what the agent does | Knowledge |
|---|---|---|
| Enterprise structure | Locations, reference data sets, business units, business functions, BU set assignment, data access | `locations.md`, `business-units.md`, `reference-data-sets.md`, `bu-data-access.md` |
| Procurement setup | Configure Procurement / Requisitioning BF, service providers, document styles, line types, numbering, procurement agents, catalogs | `configure-procurement-bf.md`, `procurement-agents.md`, `document-styles.md` … |
| Suppliers | Supplier → address → site → BU assignment → contacts, supplier numbering, registration, ASL | `suppliers.md`, `supplier-setup.md`, `approved-supplier-list.md` |
| Procure-to-pay | Requisitions, purchase orders, change orders, agreements, receipts, full Req → PO → Receipt test | `requisitions.md`, `purchase-orders.md`, `receipts.md`, `p2p-test-cycle.md` |
| Approvals (functional) | Approval rules, stages, participants, approval groups | `approvals.md`, `playbooks/approval-rules.md` |
| Sourcing | Negotiation styles, RFQs / auctions, responses, awards | `negotiation-styles.md`, `sourcing-negotiations.md` |
| Inventory | Inventory / item orgs, subinventories, locators, UOMs, items, transactions, cycle counts, min-max, ABC | `inventory-organizations.md`, `inventory-transactions.md`, `items-item-classes.md` … |
| Cost management | Cost orgs, cost books, valuation, cost profiles, standard costs | `cost-management.md` |
| Shipping & carriers | Carriers, ship methods, release rules, pick wave, pick / ship confirm, shipping networks, transfer orders | `carriers.md`, `shipping-execution.md`, `transfer-orders.md` |
| Order management | Order types, orchestration, pricing basics, sales orders | `order-management.md` |
| Financial orchestration | Intercompany flows, transfer pricing, profit center BU relationships | `financial-orchestration.md` |
| Common setup | Lookups, value sets, flexfields, profile options, calendars | `common-setup.md`, `calendars-flexfields.md` |

### Technical — reporting, analysis, workflow, integration, security
| Area | Examples of what the agent does | Tools / commands | Knowledge |
|---|---|---|---|
| Reports | Run any BI Publisher report with parameters; build new reports under `/Custom`; schedule them as ESS jobs | `bi_run_report`, `bi_catalog_list`, `bi_deploy_object`, `/report` | `tech-bi-publisher.md` |
| SQL analysis | Read-only SQL on Fusion tables (PO, requisitions, suppliers, receipts, on-hand, items…) with masked results saved to `reports/` | `bi_sql`, `/sql` | `tech-bi-publisher.md` |
| Root-cause analysis | Why is a document stuck? Which setup is missing? Which rows failed in an import? | `/analyze` (REST + SQL + workflow + ESS logs) | all |
| Approval workflow | List, read, approve, reject or reassign tasks; find faulted approvals; read approval history; test a new rule | `wf_tasks`, `wf_task`, `wf_task_action` | `tech-approvals-workflow.md` |
| Integrations | Any SOAP service, FBDI loads (control-file order), ESS jobs, HDL, business events, callbacks | `soap_call`, `fbdi_*`, `ess_*` | `tech-integrations.md`, `channel-c-fbdi-ess.md` |
| Setup migration / backup | Export and import setup with FSM CSV (also the backup before every change) | `fsm_*`, `/export-setup` | `channel-b-fsm-csv.md`, `fsm-task-codes.md` |
| Security | Search any role; read, add or remove a user's roles; data access; self-grant a missing role when a job hits 403 | `find_role`, `user_roles`, `assign_roles`, `grant_data_access`, `ensure_access` | `tech-security.md`, `users-roles.md` |
| Extensions | Sandboxes, VB Studio (Redwood), Application Composer, Alerts Composer, flexfields — guided in the UI (no API) | channel D | `tech-extensions.md`, `calendars-flexfields.md` |
| OTBI / BICC | Subject areas for analyses, BICC extracts | channel D / ESS | `tech-otbi-bicc.md` |

`knowledge/INDEX.md` maps any request to its file; `knowledge/dependencies.md` holds the setup dependency chains.

---

## How it works

### Channels — backend first
| # | Channel | Functional use | Technical use |
|---|---|---|---|
| A | REST & web services: business REST (`/fscmRestApi`, `/hcmRestApi`), BIP SOAP, BPM REST, SCIM, SOAP services | Master data and transactions | Reports, SQL analysis, workflow tasks, roles, integrations |
| B | FSM setup task CSV (`setupTaskCSVExports/Imports`) | Setup tasks. On 26D almost every SCM setup task supports CSV, including BU, business functions, procurement / requisitioning BF, cost, shipping and orders ([fsm-task-codes.md](knowledge/fsm-task-codes.md)) | Setup migration and backup |
| C | FBDI + ESS (`erpintegrations`) | Bulk loads | Scheduled processes, BIP jobs, import troubleshooting |
| D | Fusion UI in the Claude browser pane, **only on request** or when no API exists | Approval rules, a few setup pages | Sandboxes, VB Studio, custom roles, BIP catalog design |

The backend is much faster, so the agent opens the browser pane only when you ask to watch ("show me in the browser") or when the task has no API.

### The request loop (every request)
Understand → check prerequisites → choose the channel → plan (with impact) → back up → execute after your "yes" → verify by reading back → document in `config-docs/` + the audit log.

---

## Example requests

**Functional**
- "Create a supplier called Nile Trading, tax registration number 123, with a site in Cairo on the BU Egypt Operations." The agent runs `create_supplier` → `add_supplier_address` → `create_supplier_site` → `assign_site_to_bu` → `add_supplier_contact`, as separate calls with duplicate checks.
- "Create a new BU called KSA Retail with a location in Riyadh, enable Requisitioning, Procurement and Payables, and complete its procurement setup." The agent runs `/new-bu`: the full chain from `dependencies.md`, reviewed by config-reviewer, with a double confirmation.
- "Create a PO Document Style called Services PO." REST `purchasingDocumentStyles`, or FSM CSV `PO_MANAGE_DOCUMENT_STYLES`.
- "Make Ahmed a buyer on the new BU with all actions." `create_procurement_agent(all_access=True)`.
- "Create a test requisition, turn it into a PO and receive it." `/p2p-test`.
- "Create a carrier FastShip and enable it on the Cairo inventory org." `create_carrier` → `add_carrier_ship_method` → `enable_ship_method_on_org`.
- "Create a new inventory org for Riyadh." `/new-inv-org`: a prerequisite checklist, then the create.

**Technical**
- "List all approved POs with no receipt on US1 since the start of the month." `/sql`: one SELECT, a short table and an Excel/CSV file in `reports/`.
- "Why is requisition 1001 stuck in approval?" `/analyze`: workflow task state and history, approval status, faulted tasks, root cause and fix.
- "Build a report of suppliers without a bank account and schedule it weekly." `/report`: SQL proven with `bi_sql`, a report under `/Custom`, then an ESS job.
- "Create an approval rule: requisitions above 50,000 go to the manager, then Finance — and prove it works." `/approval-rule`: rule in the UI, a test requisition, then `wf_tasks` shows who it went to.
- "Give user Ahmed Inventory Manager and Shipping Manager with access to org 001." `assign_roles` + `grant_data_access` (high-impact: before/after, asked twice).
- "Load these 300 items from Excel." `/bulk`: validates every row, then FBDI in control-file order, then a result report.
- "Get PO 1234 through the SOAP PurchaseOrderServiceV2." `soap_call` (a read operation, so it runs directly).

Arabic works too, e.g. «ليه الريكوزيشن 1001 واقفة في الـ approval؟» or «طلعلي كل السبلايرز اللي مالهمش site assignment على BU Egypt Operations».

---

## Slash commands

| Group | Commands |
|---|---|
| Session | `/agent on` (connection form + connect), `/agent off` (disconnect + close the pane), `/env`, `/mode` |
| Functional | `/new-supplier`, `/new-bu`, `/new-location`, `/new-inv-org`, `/new-item-org`, `/procurement-setup`, `/approval-rule`, `/new-req`, `/new-po`, `/p2p-test` |
| Technical | `/sql`, `/report`, `/analyze`, `/find`, `/export-setup`, `/bulk`, `/config-doc` |

### Modes
- `confirm` (default; forced on PROD): plan → one "yes" → everything runs end-to-end.
- `auto` (DEV/TEST only): runs directly and reports IDs. High-impact items still ask once.

### Subagents
- **oracle-researcher** — researches official Oracle 26D docs and writes `knowledge/` files (cited, UNVERIFIED marked).
- **fusion-ui-operator** (Sonnet) — runs UI playbooks in the browser pane.
- **config-reviewer** — reviews a plan against dependencies and safety rules.

---

## Install

You need Python 3.11+ (tested on 3.14) and the Claude desktop app (Code tab) for the browser pane.

```bash
python -m venv .venv
```
```bash
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
```bash
.venv/Scripts/python.exe -m pytest -q
```

The MCP server `oracle-fusion` (58 tools) is registered in [.mcp.json](.mcp.json) and loads automatically when Claude Code opens this folder. [.claude/settings.json](.claude/settings.json) pre-allows its tools, so Claude Code does not prompt on every call; Oracle-side confirmation is handled by the agent's modes. The same file blocks Claude from reading or editing your `.env*` files.

---

## Access setup

### 1. Environment profiles
Run `/agent on`: a small connection form opens in the browser pane, where you enter the instance URL, username and password. It writes `.env.test` (or another profile) for you and tests the connection. You can also copy [.env.example](.env.example) by hand. All `.env*` files are git-ignored, and the password is never shown or logged.

| Variable | Meaning |
|---|---|
| `ORACLE_ENV_NAME` | DEV / TEST / PROD. PROD turns on the `CONFIRM PROD` guard |
| `ORACLE_BASE_URL` | Pod root, e.g. `https://xxxx-test.fa.ocs.oraclecloud.com` (UI paths are stripped automatically) |
| `ORACLE_AUTH_MODE` | `basic` or `oauth` |
| `ORACLE_USERNAME` / `ORACLE_PASSWORD` | The agent user (basic) |
| `ORACLE_OAUTH_TOKEN_URL`, `ORACLE_CLIENT_ID`, `ORACLE_CLIENT_SECRET`, `ORACLE_SCOPE` | OAuth (see note) |
| `ORACLE_RELEASE` | e.g. `26D` |
| `ORACLE_BI_SQL_REPORT` (optional) | Path of the SQL runner report (default `/Custom/AI_SCM_AGENT/SQL_RUNNER.xdo`) |

> **OAuth note:** the client-credentials grant works only for the newer `/api/...` endpoints, not for `/fscmRestApi`, `/hcmRestApi` or SCIM. Use Basic Auth on TEST, or JWT user assertion ([knowledge/access-and-roles.md](knowledge/access-and-roles.md)).

### 2. Agent user + roles
Use a dedicated user (e.g. **`AI_SCM_AGENT`**) with a worker/person record, because procurement agent access, requisition preparer and receiving require one. All codes below were confirmed on a 26D pod via SCIM.

**Functional roles**

| Role | Code | Why |
|---|---|---|
| Application Implementation Consultant | `ORA_ASM_APPLICATION_IMPLEMENTATION_CONSULTANT_JOB` | All setup tasks (FSM) |
| Functional Setups User | `ORA_ASM_FUNCTIONAL_SETUPS_USER_ABSTRACT` | FSM CSV export/import by API |
| Procurement Application Administrator | `ORA_PO_PROCUREMENT_APPLICATION_ADMIN_JOB` | Procurement setup |
| Supplier Administrator / Supplier Manager | `ORA_POZ_SUPPLIER_ADMINISTRATOR_ABSTRACT` / `ORA_POZ_SUPPLIER_MANAGER_ABSTRACT` | Suppliers, supplier import |
| Buyer / Procurement Manager | `ORA_PO_BUYER_JOB` / `ORA_PO_PROCUREMENT_MANAGER_JOB` | POs, agreements, agents, ASL |
| Procurement Requester / Employee | `ORA_POR_PROCUREMENT_REQUESTER_ABSTRACT` / `ORA_PER_EMPLOYEE_ABSTRACT` | Requisitions (P2P test) |
| Category Manager (sourcing) | `ORA_PON_CATEGORY_MANAGER_JOB` | Negotiations, categories |
| Inventory Manager / Warehouse Manager | `ORA_INV_INVENTORY_MANAGER_JOB` / `ORA_INV_WAREHOUSE_MANAGER_JOB` | Inventory, receiving |
| Product Data Steward | `ORA_EGI_PRODUCT_DATA_STEWARD_JOB` | Items, item import |
| Cost Accountant | `ORA_CST_COST_ACCOUNTANT_JOB` | Cost orgs, books, standard costs |
| Shipping Manager | `ORA_WSH_SHIPPING_MANAGER_JOB` | Carriers, shipping |
| Order Manager / Order Administrator (if in scope) | `ORA_DOO_ORDER_MANAGER_JOB` / `ORA_DOO_ORDER_ADMINISTRATOR_JOB` | Sales orders, orchestration |
| Human Resource Specialist | `ORA_PER_HUMAN_RESOURCE_SPECIALIST_JOB` | Locations |

**Technical roles**

| Role | Code | Why |
|---|---|---|
| Integration Specialist | `ORA_FND_INTEGRATION_SPECIALIST_JOB` | FBDI / ESS (`erpintegrations`) |
| IT Security Manager | `ORA_FND_IT_SECURITY_MANAGER_JOB` | Manage users' roles and data access; self-grant on 403 |
| BI Consumer / BI Author | read the codes on the pod (`find_role("BI Author")`) | Run reports / create the SQL runner and custom reports |

Plus **data access** to the relevant BUs and inventory orgs (`grant_data_access`, or Manage Data Access for Users), and a **procurement agent** record on each procurement BU (`create_procurement_agent`). With IT Security Manager the agent can add any missing role itself (see Safety).

### 3. Smoke test (read-only)
```bash
.venv/Scripts/python.exe scripts/smoke_test.py test
```
One GET per area. Each area reports `OK`, `MISSING PRIVILEGE` (with the role that grants it), `AUTH FAILED` or `NOT FOUND`. Inside Claude Code you can just say "run the smoke test".

### 4. One-time technical setup (only when needed, with your OK)
- **SQL runner** for `/sql`: a private BI Publisher report under `/Custom/AI_SCM_AGENT` ([playbooks/bi-sql-runner.md](playbooks/bi-sql-runner.md)). It can read any table, so it is created only with your OK and is visible only to the agent's role.
- **FBDI templates / control files** for bulk loads are downloaded per object with your OK, into `fbdi/templates/`.

### 5. Browser pane (watch the agent)
Say "show me in the browser" to watch a change click by click. Sign in to the pod in the pane once; the pane keeps the session. The agent never types passwords or one-time codes. The pane exists only in the Claude desktop app; in the plain CLI the agent uses channels A, B and C.

---

## Safety (summary — full rules in CLAUDE.md)
- **Read before write.** Duplicate checks run before every create. Deletes are refused unless you explicitly ask.
- **Preview → yes → execute.** Every write defaults to `dry_run=True`, and REST field names are checked against the live `describe`. On PROD every change needs `CONFIRM PROD`.
- **High-impact items** (approval rules, numbering, BU business functions, role and data-access changes, anything financial) show before/after and are asked twice.
- **Self-grant:** when a job hits 403, the agent adds only the missing role to its own user (add-only). On DEV/TEST that takes one confirmation in confirm mode and is automatic in auto mode; PROD needs `CONFIRM PROD`.
- **Technical work is read-only by default.** Reports and SQL analysis run without asking. The SQL tool allows only SELECT/WITH, caps rows, and masks bank and secret columns. BI content goes only under `/Custom`; seeded reports are never changed.
- **Backups** of setup and user roles go to `backups/<date>/`. Every write lands in `logs/audit-YYYY-MM-DD.jsonl` with passwords, tokens and bank numbers masked.
- **Oracle errors** (POZ-, PO-, INV-, ORA-…) are parsed, explained and never retried blindly.

## Bulk mode
`/bulk path/to/file.xlsx suppliers` reads and validates every row, shows a summary, then runs through REST batch (small loads) or FBDI (large loads, columns in control-file order). It writes a per-row result report to `reports/`.

## Model and cost
- Main session: **Opus 5.5, effort medium** (set it in the app's model / effort picker).
- UI work runs in the `fusion-ui-operator` subagent on **Sonnet**; docs research runs in oracle-researcher (Sonnet is enough).
- Context is kept small: `fields=` on every REST read, results saved to files rather than pasted into the chat.

---

## Project layout
```
oracle_fusion_mcp/  server.py  client.py (auth, retries, REST + SOAP, audit)  generic.py (REST/SOAP generic tools)
                    functional: suppliers.py procurement.py inventory.py locations.py enterprise.py bulk.py
                    channels:   fsm.py (FSM CSV)  fbdi.py (FBDI / ESS)
                    technical:  bi.py (reports, SQL, catalog)  workflow.py (approval tasks)  security.py (roles, access)
                    smoke.py
knowledge/          functional + tech-*.md files, INDEX.md, dependencies.md, fsm-task-codes.md (cited Oracle 26D docs)
playbooks/          UI flows (channel D), incl. bi-sql-runner.md
.claude/            settings.json, commands/, agents/ (oracle-researcher, fusion-ui-operator, config-reviewer)
scripts/            smoke_test.py, setup_env.py (connection form)
tests/              pytest + respx, mocked HTTP only
config-docs/ reports/ backups/ logs/ fbdi/
```

## Optional third-party Oracle MCPs
CData, StackOne and `mcp-oraclefusion` (PyPI) exist, but they are read-only or route data through outside vendors. They are not installed, and are added only if you ask.
