# oracle-scm-agent

An executing AI agent for **Oracle Fusion Cloud SCM & Procurement**. Open Claude Code in this folder, write a request in English (Arabic also works), and the agent does the setup or transaction in Fusion itself, the way a senior implementation consultant would. It reads the current setup and checks prerequisites first, picks the right channel, backs up, executes, verifies and documents.

It is not an advisor. It acts through 4 channels:

| # | Channel | Used for |
|---|---|---|
| A | Business REST (`/fscmRestApi`, `/hcmRestApi`) | Master data and transactions (suppliers, agents, requisitions, POs, receipts, carriers, locations…) |
| B | FSM Setup Task CSV (`setupTaskCSVExports/Imports`) | Setup tasks. On 26D this includes BU, business functions, Configure Procurement/Requisitioning BF, numbering, service providers… ([knowledge/fsm-task-codes.md](knowledge/fsm-task-codes.md)) |
| C | FBDI + ESS (`erpintegrations`) | Bulk loads and scheduled processes |
| D | Fusion UI in the Claude browser pane — **only on request** | When you ask to watch the work, or the task has no API path (e.g. approval rules). Everything else runs on the backend (A/B/C), which is much faster |

The operating rules are in [CLAUDE.md](CLAUDE.md): the request loop, safety rules and modes. The original brief is in [SPEC.md](SPEC.md), and build status is in [PROGRESS.md](PROGRESS.md).

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

The MCP server is registered in [.mcp.json](.mcp.json) and loads automatically when Claude Code opens this folder:

- `oracle-fusion` — this project's Python MCP server (42 tools).

The browser channel uses the Claude desktop app's built-in browser pane (no extra install).

[.claude/settings.json](.claude/settings.json) pre-allows the `oracle-fusion` tools, so Claude Code does not prompt on every call. Oracle-side confirmation is handled by the agent's modes. The same file blocks Claude from reading or editing your `.env*` files.

---

## Access setup

### 1. Environment profiles
Copy [.env.example](.env.example) to `.env.test` (and to `.env.dev` / `.env.prod` if needed), then fill it in yourself. All `.env*` files are git-ignored.

| Variable | Meaning |
|---|---|
| `ORACLE_ENV_NAME` | DEV / TEST / PROD. PROD turns on the `CONFIRM PROD` guard |
| `ORACLE_BASE_URL` | Pod root, e.g. `https://xxxx-test.fa.ocs.oraclecloud.com`. Any UI path you paste is stripped automatically |
| `ORACLE_AUTH_MODE` | `basic` or `oauth` |
| `ORACLE_USERNAME` / `ORACLE_PASSWORD` | The dedicated agent user (basic) |
| `ORACLE_OAUTH_TOKEN_URL`, `ORACLE_CLIENT_ID`, `ORACLE_CLIENT_SECRET`, `ORACLE_SCOPE` | OAuth (see note) |
| `ORACLE_RELEASE` | e.g. `26D` |

Switch profiles inside Claude Code with `/env test`, `/env prod` and so on.

> **OAuth note (from the 26D docs, see [knowledge/access-and-roles.md](knowledge/access-and-roles.md)):** the *client credentials* grant only works for the newer `/api/...` endpoints, not for `/fscmRestApi`, `/hcmRestApi` or SCIM. For those, use Basic Auth on TEST, or JWT user assertion on behalf of the agent user. The code's `oauth` mode sends a client-credentials token, so it only works where Oracle accepts one.

### 2. Dedicated Fusion user + roles (ask your security admin)
Create a user **`AI_SCM_AGENT`** on TEST first. It needs a worker/person record, because procurement agent access, requisition preparer and receiving all require one. Request these roles. Every code below was confirmed on a 26D pod via SCIM.

| Role | Code | Why |
|---|---|---|
| Application Implementation Consultant | `ORA_ASM_APPLICATION_IMPLEMENTATION_CONSULTANT_JOB` | All setup tasks (FSM) |
| Functional Setups User | `ORA_ASM_FUNCTIONAL_SETUPS_USER_ABSTRACT` | FSM CSV export/import by API (channel B) |
| Procurement Application Administrator | `ORA_PO_PROCUREMENT_APPLICATION_ADMIN_JOB` | Procurement setup tasks |
| Supplier Administrator | `ORA_POZ_SUPPLIER_ADMINISTRATOR_ABSTRACT` | Supplier profile, supplier import |
| Supplier Manager | `ORA_POZ_SUPPLIER_MANAGER_ABSTRACT` | Create suppliers, spend authorization |
| Buyer | `ORA_PO_BUYER_JOB` | POs, agreements, PO/agreement imports |
| Procurement Manager | `ORA_PO_PROCUREMENT_MANAGER_JOB` | Procurement agents, ASL |
| Category Manager (optional) | `ORA_PON_CATEGORY_MANAGER_JOB` | Categories / sourcing |
| Procurement Requester | `ORA_POR_PROCUREMENT_REQUESTER_ABSTRACT` | Requisitions (P2P test) |
| Employee | `ORA_PER_EMPLOYEE_ABSTRACT` | Self-service base |
| Inventory Manager | `ORA_INV_INVENTORY_MANAGER_JOB` | Inventory setup and transactions |
| Warehouse Manager | `ORA_INV_WAREHOUSE_MANAGER_JOB` | Receiving / warehouse |
| Shipping Manager | `ORA_WSH_SHIPPING_MANAGER_JOB` | Carriers, shipping |
| Product Data Steward (optional) | `ORA_EGI_PRODUCT_DATA_STEWARD_JOB` | Items, item import |
| Integration Specialist | `ORA_FND_INTEGRATION_SPECIALIST_JOB` | FBDI / ESS (`erpintegrations`) |
| Human Resource Specialist | `ORA_PER_HUMAN_RESOURCE_SPECIALIST_JOB` | Locations (`locationsV2`) |
| IT Security Manager | `ORA_FND_IT_SECURITY_MANAGER_JOB` | Lets the agent manage users' roles and data access (`assign_roles`, `grant_data_access`) |
| Cost Accountant | `ORA_CST_COST_ACCOUNTANT_JOB` | Cost organizations, cost books, standard costs |
| Order Manager / Order Administrator (if Order Management is in scope) | `ORA_DOO_ORDER_MANAGER_JOB` / `ORA_DOO_ORDER_ADMINISTRATOR_JOB` | Sales orders, orchestration setup |

**Role management by the agent.** With IT Security Manager, the agent can search any role (`find_role`), list any user's roles (`user_roles`), add or remove roles (`assign_roles`) and add data access (`grant_data_access`). It covers supply chain, procurement, finance and custom roles. Role changes are high-impact: the agent shows the before/after, asks twice and backs up the user's roles first. Example: «اعمل للـ user أحمد Inventory Manager و Shipping Manager وأديله access على org 001».

Also request:
- **Data access** to the relevant BUs (Requisitioning / Procurement / Payables contexts) and inventory orgs. Use Manage Data Access for Users (task `ORA_FUN_MANAGE_DATA_ACCESS_FOR_USERS`).
- **A procurement agent record** for `AI_SCM_AGENT` on each procurement BU (Manage Procurement Agents), with order, agreement and supplier actions.

### 3. Smoke test (read-only)
```bash
.venv/Scripts/python.exe scripts/smoke_test.py test
```
It makes one GET per area and reports `OK`, `MISSING PRIVILEGE` (403, with the role that grants it), `AUTH FAILED` (401) or `NOT FOUND`. Inside Claude Code you can also just ask "run the smoke test".

### 4. Browser channel (watch the agent)
When you ask to watch, the agent uses the **Claude browser pane** in the Claude desktop app (Code tab). Sign in to the pod there once (SSO/MFA); the pane keeps the session. The agent never types passwords or one-time codes.
- **Default:** the agent works on the backend (REST / FSM CSV / FBDI) and does not open the pane. Say "show me in the browser" to watch a change click by click; tasks with no API path (e.g. approval rules) also open the pane.
- Optional: to stop Claude Code asking before each pane action, allow the `mcp__Claude_Browser__*` tools in your own settings.
- The pane exists only in the Claude desktop app; in the plain CLI the agent falls back to A/B/C.

---

## Using it

Open Claude Code in this folder and write a request. The agent replies in English and keeps Oracle terms exactly as Oracle names them.

### Example requests
- "Create a supplier called Nile Trading, tax registration number 123, with a site in Cairo on the BU Egypt Operations"
  → `create_supplier` → `add_supplier_address` → `create_supplier_site` → `assign_site_to_bu` → `add_supplier_contact`, as separate calls with duplicate checks.
- "Create a new BU called KSA Retail with a location in Riyadh, enable Requisitioning, Procurement and Payables on it, and complete its procurement setup"
  → `/new-bu`: full chain from [knowledge/dependencies.md](knowledge/dependencies.md). The plan is reviewed by config-reviewer and needs a double confirmation (high-impact).
- "Create a new PO Document Style called Services PO" → REST `purchasingDocumentStyles` (or FSM CSV `PO_MANAGE_DOCUMENT_STYLES`).
- "Create an approval rule: any requisition above 50,000 goes to the manager, then to Finance" → `/approval-rule`, channel D ([playbooks/approval-rules.md](playbooks/approval-rules.md)), then a test requisition to check the routing.
- "Make Ahmed a buyer on the new BU with all actions" → `create_procurement_agent(all_access=True)`, which sets every action flag and Full access to other agents' documents.
- "Create a test requisition, turn it into a PO and receive it, to check the setup works" → `/p2p-test`.
- "List all suppliers with no site assignment on BU Egypt Operations" → `/find` (read-only, saved to `reports/` if large).
- "Create a new carrier called FastShip and enable it on the Cairo inventory org" → `create_carrier` → `add_carrier_ship_method` → `enable_ship_method_on_org`.

### Model and cost
- Main session: **Opus 5.5, effort medium** (set it in the app's model / effort picker). Planning, safety rules and Oracle errors need Opus; high effort adds little here.
- Browser work runs in the `fusion-ui-operator` subagent on **Sonnet** (`model: sonnet` in its file), so page reads and screenshots stay out of the main context.
- `CLAUDE.md` keeps context small: `fields=` on every REST read, page structure instead of screenshots, logs saved to files instead of pasted.

### Slash commands
- `/agent on` — opens the connection form (URL / user / password) and connects. Fusion opens in the pane only when you ask to watch.
- `/agent off` — closes the Oracle connection and the browser pane. Fusion tools refuse to run until `/agent on`.

`/new-supplier` `/new-bu` `/new-location` `/procurement-setup` `/approval-rule` `/new-req` `/new-po` `/p2p-test` `/find` `/env` `/mode` `/export-setup` `/config-doc` `/bulk`

### Modes
- `confirm` (default; forced on PROD): plan → one "yes" → everything runs end-to-end.
- `auto` (DEV/TEST only): runs directly and reports IDs. High-impact items still ask once.

### Safety (summary — full rules in CLAUDE.md)
- Every write tool defaults to `dry_run=True`, and field names are checked against the live `describe`. Unknown fields are blocked with a "did you mean" suggestion.
- Duplicate checks run before creates. Deletes are refused unless you explicitly ask.
- On PROD, every write needs you to type `CONFIRM PROD`.
- Setup changes are backed up to `backups/<date>/` first.
- Writes go to the audit log `logs/audit-YYYY-MM-DD.jsonl`, with passwords, tokens and bank numbers masked.
- Config documentation goes in `config-docs/`.
- Oracle errors are parsed by code (POZ-, PO-, INV-…), explained, and never retried blindly.

### Bulk mode
`/bulk path/to/file.xlsx suppliers` reads and validates every row, shows a summary, then runs through REST batch (small loads) or FBDI (large loads). It writes a per-row result report to `reports/`.

---

## Project layout
```
oracle_fusion_mcp/  server.py client.py generic.py fsm.py fbdi.py suppliers.py procurement.py
                    inventory.py locations.py enterprise.py bulk.py smoke.py
knowledge/          one file per setup area + INDEX.md + dependencies.md + fsm-task-codes.md (cited Oracle docs)
playbooks/          channel-D UI flows (updated by the agent when the UI differs)
.claude/            settings.json, commands/, agents/ (oracle-researcher, fusion-ui-operator, config-reviewer)
tests/              pytest + respx, mocked HTTP only
config-docs/ reports/ backups/ logs/ fbdi/
```

## Optional third-party Oracle MCPs
CData, StackOne and `mcp-oraclefusion` (PyPI) exist, but they are read-only or route data through outside vendors. They are not installed and are added only if you ask.
