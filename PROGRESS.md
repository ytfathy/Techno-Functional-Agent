# oracle-scm-agent — Progress & handoff

> Updated at the end of every phase. To continue in another Claude account/session: open Claude Code in this folder and paste the "Resume prompt" at the bottom.
> Last update: 2026-11-25 — Phases 1–6 done; backlog items 1, 2, 4 done and 3 started (see "2026-11-25" section at the end). **Next work = "Next steps — backlog" below (priority order).** Dated sections after it are history.

## Goal (short)
An executing AI agent (Claude Code project) that acts as a senior Oracle Fusion Cloud SCM & Procurement consultant. The user writes a request (Arabic/English) and the agent does the setup or transaction in Fusion itself via 4 channels (A REST, B FSM CSV, C FBDI/ESS, D UI in the Claude browser pane — only on request or for UI-only tasks), with safety rules, backups, an audit log and config docs. Full original brief: [SPEC.md](SPEC.md). User guide: [README.md](README.md).

## Decisions taken
| Item | Decision |
|---|---|
| Fusion release | **26D** |
| TEST pod | User-filled `.env.test` (connection form). **Since 2026-11-25: new demo pod `fa-eteo-saasfademo1`, user `HCM`** (was `fa-etat…`, user `hcm_impl`; everything created before 2026-11-25 — supplier 1501, YT Business Unit, hcm_impl roles — lives on the OLD pod only). Basic Auth. Base URL is normalized to the pod root automatically. |
| Auth | Basic Auth on TEST. OAuth client credentials is coded, but per the 26D docs it does NOT work for `/fscmRestApi`, `/hcmRestApi` or SCIM (only `/api/...`). Use Basic or JWT user assertion. |
| Python / SDK | System Python 3.14 in `.venv`; **`mcp>=1.2,<2`** (mcp 2.x renamed FastMCP → pinned to keep FastMCP as the brief asks) |
| Browser for channel D | Claude desktop app browser pane (`mcp__Claude_Browser__*`). Playwright/Edge removed 2026-11-14. Backend (A/B/C) is the default since 2026-11-15 |
| Agent reply language | **English** (user asked 2026-11-14), Oracle terms exactly as Oracle names them |

## Phase status
| Phase | Status | Evidence |
|---|---|---|
| 0. Questions + folder structure | DONE | 26D, TEST pod, Basic |
| 1. client + generic tools + smoke test | **DONE** | Live smoke test on TEST 13/13 OK (real JSON); live describe incl. child resources; live reads of BUs/suppliers |
| 2. knowledge/ + dependencies.md | **DONE** | 41 files in `knowledge/` (6 oracle-researcher batches, doc URLs cited, UNVERIFIED marked), `INDEX.md`, `dependencies.md`, **`fsm-task-codes.md` (verified live)**; all role codes verified live via SCIM |
| 3. shortcut tools + tests | **DONE** | `suppliers.py` (5 tools), `procurement.py` (5), `locations.py`, `enterprise.py` (`find_business_unit`, `lookup_values`), `inventory.py` (org find + carrier flow); field names checked against the live describe; tests pass |
| 4. FSM CSV + FBDI/ESS tools | **DONE** | `fsm.py` (find/export/status/download/import), `fbdi.py` (template columns, build zip, importBulkData, ESS submit/status/output); `fsm_find_task` works live |
| 5. Playwright playbooks | DRAFTED | 6 playbooks DRAFT-FROM-DOCS: create-business-unit, assign-business-unit-business-function, configure-procurement-bf, configure-requisitioning-bf, document-styles, approval-rules. **Need a first live run** (the user signs in to Edge once) |
| 6. commands, subagents, bulk, README | **DONE** | 14 slash commands, 3 subagents, bulk module, README (access setup + verified role codes + examples) |

Tests: **47 passed** (pytest + respx, mocked HTTP only). MCP server: **45 tools** (new: `fbdi_ctl_columns`, `fbdi_import_job`). `knowledge/`: **50 files**.
Writes done (all with the user's OK): OLD pod — 4 roles + US1 data access for `hcm_impl`; supplier 1501 + address + site CAIRO-TEST (FBDI); BU "YT Business Unit". NEW pod (2026-11-25) — 9 roles + inventory-org data access (8 US1 orgs) for `HCM`. See the dated sections below and `config-docs/security.md`.

## Key findings that changed the design
- **Channel B covers almost all setup on 26D.** These tasks have `CSVExportImportSupportedFlag=Y`:
  - Manage Business Unit, Assign BU Business Function, BU Set Assignment
  - Configure Procurement BF, Configure Requisitioning BF, Service Provider Relationships, Procurement Document Numbering
  - Document Styles, Procurement Agents, Supplier Numbering, Negotiation Styles
  - Inventory Orgs, Subinventories/Locators, UOMs, Interorg Parameters, Receiving Parameters, Carriers, Item Classes, Purchasing Profile Options

  CSV is **not** supported (so channel D) for: the approval tasks (Requisition / Purchasing Document / Supplier Registration) and Manage BU Data Access for Users. See `knowledge/fsm-task-codes.md`.
- **Child describe:** Fusion only describes the root resource (`suppliers/describe`), with child descriptors nested inside it. The code walks root → child.
- **Real REST is used where it exists:**
  - `purchasingDocumentStyles`, `purchasingLineTypes`, `procurementAgents`
  - `carriers` → `shippingMethods` → `organizationAssociations`
  - `setIdAssignmentsBusinessUnit`, `dataSecurities`
  - `supplyRequests` for transfer orders
  - `requisitionProcessingRequests` + `processRequest` for req → PO
- **`procurementAgents` codes** (seen on the pod): `StatusCode` Y/N; `AccessLevelToOtherAgents*Code` = FULL/NONE…
- **Lookups:** `standardLookupsLOV` and `commonLookupsLOV` work on the pod.
- **ESS job paths** for SCM/Procurement imports are not published in the docs. Read them on the pod (Manage Enterprise Scheduler Job Definitions) before `fbdi_import`.
- **POZ-2130403** is not documented. The supplier flow still runs as separate calls, because a site needs the address created first.

## Files (what exists)
- `CLAUDE.md`, `README.md`, `SPEC.md`, `PROGRESS.md`, `.mcp.json`, `.claude/settings.json` (pre-allows both MCPs; denies `.env*` read/edit), `.claude/agents/` (3), `.claude/commands/` (14).
- `oracle_fusion_mcp/`:
  - `server.py`, `client.py`, `generic.py`, `fsm.py`, `fbdi.py`, `suppliers.py`, `procurement.py`
  - `inventory.py`, `locations.py`, `enterprise.py`, `bulk.py`, `smoke.py`
- `scripts/smoke_test.py`, `tests/` (conftest, test_client_generic, test_tools).
- `knowledge/` (41 files), `playbooks/` (6 + template), `config-docs/`, `reports/`, `backups/`, `logs/`, `fbdi/templates/` (empty: download official 26D XLSM templates on demand, asking the user first).

## Next steps — backlog (priority order; written 2026-11-15 for the next Claude account)
Rules for whoever continues: read `CLAUDE.md` first. Never write to the pod without the user's "yes". Update this file after each item. Reply to the user in English.

**State at handoff:** agent OFF. The `oracle-fusion` MCP often hits CONNECT_TIMEOUT (30 s) at session start; server import takes ~1.2 s, so it is a cold start: reconnect it from the MCP menu / reload the project, then `/agent on`.

1. ✅ **DONE 2026-11-25** — **FBDI file builder bug (code, blocks every bulk load).** `fbdi.fbdi_template_columns` / `fbdi_build_zip` take the column order from the XLSM sheet via openpyxl. Oracle loads the CSV in **control-file (.ctl) order**, and openpyxl cannot read Oracle's `.xlsm` reliably (supplier-site load failed until the CSV was rebuilt by hand in ctl order; see `knowledge/channel-c-fbdi-ess.md`).
   - Fix: read sheet XML with `zipfile` (no openpyxl); take column order from the ctl (SQL*Loader log of a failed load, or Oracle's published controlfiles); let the caller pass an explicit column list.
   - `fbdi_import` / `ess_status`: the import job is a **separate request id (load ReqstId + 1)**, not a child of the load. Add a helper that waits for and reports that import job.
   - Add tests (mocked). Affects: ItemImportTemplate, SupplierSiteImportTemplate, SupplierSiteAssignmentImportTemplate, ASL, on-hand, locators.
2. ✅ **DONE 2026-11-25 on the new pod for user `HCM`** (open: BU data access for the procurement roles, cost-org data access for Cost Accountant — ask the user) — **Roles for inventory/item/cost work (pod write — ask the user first).** `hcm_impl` only has the 4 procurement roles → inventory/item/costing writes will 403. Grant via SCIM `PATCH Roles/{id}` members ADD (same method as before, `knowledge/users-roles.md`): Inventory Manager `ORA_INV_INVENTORY_MANAGER_JOB`, Product Data Steward `ORA_EGI_PRODUCT_DATA_STEWARD_JOB`, Cost Accountant (look up the code on the pod), + data access to the inventory orgs. Back up roles first; run `smoke_test` after.
3. 🟡 **STARTED 2026-11-25** (commands written; first real run + shortcuts still to do) — **Inventory / item org flow.** New commands `/new-inv-org` and `/new-item-org` (like `/new-bu`): fixed prerequisite checklist (location, workday/schedule calendar, item master org, reference data set, cost org assignment, interorg parameters) → reads → creates. After the first real run add shortcuts `create_inventory_org`, `create_subinventory`, `create_item` (with duplicate checks + tests). Knowledge: `inventory-organizations.md` (5 UNVERIFIED), `subinventories-locators.md` (3), `item-organizations.md` (2), `items-item-classes.md` (2) — confirm on the pod and clear the flags.
4. ✅ **DONE 2026-11-25** (7 files, merged into INDEX / dependencies / fsm-task-codes; ~95 UNVERIFIED items left inside them) — **Missing knowledge areas** (no file in `knowledge/`; use the `oracle-researcher` subagent, 26D docs, cite URLs, then add to `INDEX.md` + `dependencies.md` + `fsm-task-codes.md`). Order:
   1. Cost Management (cost orgs, cost books, valuation units/structures, cost profiles, cost org relationships) — needed before inventory transactions.
   2. Inventory transactions (misc. issue/receipt, subinventory transfer, interorg transfer, cycle count, physical inventory, min-max, ABC).
   3. Shipping execution (release rules, pick wave, pick confirm, ship confirm, shipping parameters).
   4. Order Management (order types, orchestration, pricing basics, Global Order Promising).
   5. Supply Chain Financial Orchestration (intercompany flows).
   6. Workday / schedule calendars; flexfields (DFF/EFF segments + deploy); sourcing negotiations.
5. **UI-only tasks (channel D) — verify playbooks once.** Approval rules (BPM), Manage BU Data Access for Users, flexfield deploy, some profile options. All 6 playbooks are still DRAFT-FROM-DOCS: run each once on TEST (with the user's OK) and set VERIFIED-ON-POD.
6. **Pending from earlier work (ask the user before continuing):**
   - Supplier 1501 site CAIRO-TEST has **no site assignment** to US1 (would use `SupplierSiteAssignmentImportTemplate.xlsm` → `ImportSupplierSiteAssignments`; needs item 1 fixed first).
   - YT Business Unit has **0 set assignments**; the import zip `fbdi/work/FUN_MANAGE_BUSINESS_UNIT-YT-setassign-import.zip` (69 groups → COMMON) is ready; user said "leave as is".
7. **Speed items proposed but not approved:** run `config-reviewer` only for high-impact or PROD plans (not every plan > 3 steps).
8. **Production readiness:** dedicated `AI_SCM_AGENT` user with the roles in README (demo pod uses `hcm_impl`); first FSM CSV structure notes in `knowledge/channel-b-fsm-csv.md`.

Already done (do not redo): describe disk cache (2026-11-15); backend-default channels (2026-11-15); `/agent on|off`; connection form; cookie clear per request; SCIM GET fix; `fsm._first()` fix.

<details><summary>Old next-steps list (history)</summary>

1. ~~Reopen Claude Code in this folder~~ **DONE 2026-11-14**: both MCPs load (oracle-fusion 42 tools, playwright); `env_info` = TEST / 26D / basic / `hcm_impl` / mode `confirm`; live `smoke_test` 13/13 OK.
2. **First real write test on TEST** — IN PROGRESS. Prepared (reads only): no supplier `AI Agent Test Supplier 01` exists; procurement BU candidate `US1 Business Unit` (exists, active). `create_supplier` dry run OK, field_check clean (warning: `SupplierPartyId`, `SupplierNumber` mandatory per describe but expected to default). User said yes; **live POST `suppliers` → HTTP 403** (empty body, no Oracle code). Read-back: nothing created. `hcm_impl` can read but not create suppliers (missing Supplier Manager `ORA_POZ_SUPPLIER_MANAGER_ABSTRACT` and/or BU data access). `hcm_impl`'s own roles are not visible via `userAccounts` (exact-name query returns 0 rows). **Blocked**: need a pod user with procurement write roles (or roles granted to `hcm_impl`), then rerun the same 4-step flow. Recorded in `knowledge/error-codes.md`; `log_request` done.
   - 2026-11-14 user chose "grant roles to `hcm_impl`". Done (reads only): fixed `client.get` for SCIM (ADF params were rejected; httpx dropped the path query) + test (30 passed; **MCP server must be restarted to pick up the fix**); found `hcm_impl` has IT Security Manager (can PATCH SCIM Roles); role GUIDs and `dataSecurities` BU row format verified (in `knowledge/users-roles.md`, `knowledge/bu-data-access.md`); backup `backups/2026-11-14/security-hcm_impl-roles-before.json` (35 roles, 0 data access rows); dry runs OK for SCIM `PATCH Roles/{id}` members ADD and `POST dataSecurities`. User approved. **DONE**: 4 roles granted to `hcm_impl` (SCIM 204 ×4) + 4 `dataSecurities` rows on US1 (see `config-docs/security.md`). Supplier retry from the MCP still 403 (stale session cookie) → fixed `client.py` (clear cookies per call). From a fresh process: **supplier created** `SupplierId 300000349308087`, `SupplierNumber 1501`; **address** `Cairo HQ` `300000349308094`. **Site `CAIRO-TEST` → 403** (likely: `hcm_impl` is not a procurement agent on US1 with Manage Suppliers; no agent row for `<shared demo email>`). User OK'd the agent. **`POST procurementAgents` → PO-2055145** (AgentEmail invalid): `<shared demo email>` is shared by 25+ "HCM Implementation*" persons and `hcm_impl` has no person of its own → `hcm_impl` cannot be a procurement agent → cannot create supplier sites by REST. **Blocked; options for the user:** (a) switch the agent profile to a demo user that is already a US1 agent with Manage Suppliers (e.g. `CALVIN.ROTH`, also has Manage Orders — good for `/p2p-test`; user fills creds in `.env.*`); (b) create the site with FBDI Import Supplier Sites as `hcm_impl` (UNVERIFIED whether import skips agent BU security). **User then rejected CALVIN.ROTH ("dont use calvin") — do NOT use it.** Remaining route: (b) FBDI Import Supplier Sites as `hcm_impl` (needs the 26D `SupplierSiteImportTemplate.xlsm`, download only with the user's OK). **FBDI route DONE for the site (2026-11-14):** template `fbdi/templates/SupplierSiteImportTemplate.xlsm` downloaded (user OK); importBulkData `/oracle/apps/ess/prc/poz/supplierImport,ImportSupplierSites` `NEW,N,AIAGENT1114` → Import Supplier Sites 10198003 SUCCEEDED, 1 processed / 0 rejected → **site CAIRO-TEST created** (not readable via REST by `hcm_impl`). Lessons in `knowledge/channel-c-fbdi-ess.md` (CSV order = ctl order; import child is a separate request id). Code: `fbdi_import` no longer sends AP `JobOptions` by default. **Known bug:** `fbdi_build_zip`/`fbdi_template_columns` use sheet order + openpyxl → wrong/failing for supplier templates; fix = take column order from the ctl (SQL*Loader log or Oracle controlfiles URL). **User said stop here (2026-11-14).** Not done: site assignment to US1 (would use `SupplierSiteAssignmentImportTemplate.xlsm`, 386 KB, ask before download → `ImportSupplierSiteAssignments`). Test supplier 1501 is left with address + site, no assignment. Earlier notes on Calvin kept for reference: Read check: CALVIN.ROTH already has Supplier Manager, Buyer, Procurement Requester, Procurement Manager, Receiving Agent, Supplier Administrator and an active US1 agent row with Manage Suppliers (`AssignmentId 300000047348441`) → no grants needed. **Waiting for the user to create `.env.calvin`** (copy of `.env.test` with `ORACLE_USERNAME=CALVIN.ROTH` + its password, `ORACLE_ENV_NAME=TEST`); then `switch_environment("calvin")` → site `CAIRO-TEST` → assignment US1 → read-back. US1 agents with Manage Suppliers: Casey Brown, Karen Curtis, Calvin Roth, Tiffany Irving, May Gee, Saville Miller, Amy Marlin, Rosario Arrendondo, Ava Clark, John Dunbar. Restart/reconnect the MCP server so it loads the SCIM + cookie fixes. See `config-docs/suppliers.md`.
   - Lesson: smoke test checks reads only. Consider a write-privilege check (dry run can't tell; only a real POST or a role read can). (only with the user's OK), e.g. `/new-supplier` with a test supplier, or `/p2p-test`. Fix any payload issue the pod reports and record it in knowledge/.
3. **First live channel-D run** (e.g. approval rule) → playbooks become VERIFIED-ON-POD.
4. **First FSM CSV export** (e.g. `/export-setup Manage Document Styles`) to see the real CSV structure; record it in `knowledge/channel-b-fsm-csv.md`.
5. When a bulk FBDI load is needed: download the 26D template (ask the user) and read the ESS job path on the pod.
6. Production: create the dedicated `AI_SCM_AGENT` user with the roles in README (the demo pod uses `hcm_impl`).

</details>

## 2026-11-14 — Connection form (session start)
- User asked for a start-up screen for instance URL / username / password (they change). Monitoring page and in-browser chat were proposed and **dropped by the user**.
- Built: `scripts/setup_env.py` (stdlib server, 127.0.0.1:8765; writes only URL/username/password into `.env.<profile>`, creates it from `.env.example`; empty password = keep; tests one GET; password never logged/echoed), `.claude/launch.json` (`oracle-setup`), `CLAUDE.md` "Session start" rule, tests `tests/test_setup_env.py` (suite 41 passed). Design/plan: `docs/superpowers/specs/2026-11-14-credentials-setup-design.md`, `docs/superpowers/plans/2026-11-14-credentials-setup.md`.
- Verified: form renders in the Claude browser pane with URL/username prefilled; user's real Save → log `SAVED profile=test ok=True`, page "Connected: TEST · 26D · hcm_impl"; `switch_environment("test")` reloaded the profile without restarting the MCP server.

## 2026-11-14 — New BU "YT Business Unit" (TEST) — IN PROGRESS
- Request: create BU "YT Business Unit"; Default Set = Common Set (user choice). Only the BU (no business functions).
- Channel B `FUN_MANAGE_BUSINESS_UNIT`. Export/backup: `backups/2026-11-14/FUN_MANAGE_BUSINESS_UNIT-export-100009384801263-FileContent.zip` (CSVs: FUN_BUSINESS_UNIT, FUN_BU_USAGE, FUN_BU_SERVICE_PROVIDERS, LE_1214416713655 = set assignments, + ASM_SETUP_CSV_METADATA.xml). Import zip `fbdi/work/FUN_MANAGE_BUSINESS_UNIT-YT-import.zip` (1 BU row, other CSVs header only); dry run OK. User said yes → **BU created**: `BusinessUnitId 300000349393496`, active (FSM import 100009384801395, 1 row, 0 failed). Re-export: BU row OK, **0 set assignment rows** (import of a BU row alone does not create them). Prepared `fbdi/work/FUN_MANAGE_BUSINESS_UNIT-YT-setassign-import.zip` (69 groups → COMMON, cloned from "5 Tech Business Unit"); the import was blocked by the permission check as not explicitly approved; **user chose "Leave as is" → not imported** (zip kept for later). See `config-docs/enterprise-structure.md`.
- Fixed `fsm.py`: pod returns POST child as `{"items":[...]}` → `fsm_export` crashed with `0`; new `_first()` helper (export + import).

## 2026-11-14 — Channel D moved to the Claude browser pane
- User asked to watch the agent in the browser and chose **hybrid by default + browser mode on request**.
- Changed: `CLAUDE.md` (tools table, channel D row, new "Browser pane — let the user watch" section), `.claude/agents/fusion-ui-operator.md` (pane tools first, Playwright fallback, FuseTaskListManagerTop navigation), `oracle-researcher.md`, all `playbooks/*.md` headers, `README.md` §4.
- Verified in the pane (read-only): pod session persists; Setup and Maintenance via `/fscmUI/faces/FuseTaskListManagerTop` → Manage Business Units → YT Business Unit Active ✓ (recorded in `playbooks/create-business-unit.md`).
- Not done: pre-allowing `mcp__Claude_Browser__*` in `.claude/settings.json` (blocked: the agent must not grant itself permissions; the user can add it). No write has been done through the pane yet; playbooks are still DRAFT-FROM-DOCS.
- User asked for English replies (memory saved); `CLAUDE.md` still says Egyptian Arabic.
- **Update (same day): user said "just use the Claude browser pane as default".** Now: every change with a Fusion screen is done in the pane (channel D default); A/B/C only for reads, backups, verification, bulk loads, scheduled processes, or on request. **Playwright removed** from `.mcp.json`, `.claude/settings.json`, `CLAUDE.md`, agent, README and playbooks (`.browser-profile/` stays git-ignored). Takes effect after Claude Code reloads the project.

## 2026-11-15 — /agent on|off
- New `/agent on` (connection form → `switch_environment` → pod in the pane) and `/agent off` (`disconnect` tool + close pane tabs + stop preview servers). New MCP tool `disconnect` (client `_state["off"]`): every Fusion call raises "Agent is off" until `switch_environment`. Test added (suite 42 passed). `CLAUDE.md` session-start + README updated. MCP now 43 tools; needs a Claude Code reload.
- `find_business_unit()` with no name now returns 3 fields only (was ~58 KB).
- Session note: oracle-fusion MCP hit CONNECT_TIMEOUT (30 s) at resume; import takes 2.2 s → cold start, retry via /mcp.
- Token/speed setup **applied** (user OK): `fusion-ui-operator` `model: sonnet` + interactive `read_page`/`browser_batch`, screenshots scale 0.5; `CLAUDE.md`: delegate pane work to that subagent, "keep context small" rule, **language now English** (was Egyptian Arabic); README "Model and cost". Main session Opus 5.5 effort medium must be set by the user in the app picker (a session can't change its own effort).

## Resume prompt (paste into a new Claude Code session in this folder)
```
Read SPEC.md (the full brief), PROGRESS.md (what is done) and CLAUDE.md. Continue from "Next steps" in PROGRESS.md.
Do not redo finished phases. Never run a write against the real pod without asking me. After each phase/step, update PROGRESS.md.
```

## 2026-11-15 — Backend is the default again; browser pane only on request
- User asked for speed: the agent works on the backend (A → B → C) by default and does not open the pane. Channel D is used only when the user asks to watch ("show me in the browser") or the task has no API path (e.g. BPM approval rules).
- Changed: `CLAUDE.md` (tools table, Channels, D row, loop step 3, session start), `.claude/commands/agent.md` (`/agent on` no longer opens Fusion in the pane), `.claude/agents/fusion-ui-operator.md` description, `README.md`. Playbooks kept for D.
- Not done (proposed, not approved yet): run `config-reviewer` only for high-impact/PROD; shortcuts `create_inventory_org` / `create_subinventory` / `create_item`; investigate the `oracle-fusion` MCP CONNECT_TIMEOUT at session start.
- 2026-11-15: **describe disk cache added** (`generic._describe_raw`): REST `describe` saved to `.cache/describe/<hash>.json` keyed by pod + `ORACLE_RELEASE` + root resource (git-ignored; `ORACLE_AGENT_CACHE_DIR` overrides). Later sessions skip the download. `rest_describe(..., refresh=True)` re-reads from Fusion (e.g. after new DFF segments). Test added; suite 43 passed. Takes effect after the MCP server restarts.

## 2026-11-25 — Backlog items 1–4 (FBDI fix, roles on the new pod, inv-org commands, 7 knowledge areas)
- **Pod changed.** The user re-saved the connection form: `.env.test` now points to demo pod `fa-eteo-saasfademo1`, user `HCM` (the old `hcm_impl` password had expired → every call 401). Old-pod objects (supplier 1501 / site CAIRO-TEST, YT Business Unit, the zip for its set assignments) are not on this pod, so backlog item 6 only applies if the user goes back to the old pod.
- **Item 1 (code) DONE.** `fbdi.py`:
  - `fbdi_ctl_columns(<.ctl | SQL*Loader .log>)` gives the CSV column order (drops EXPRESSION / CONSTANT fields).
  - `fbdi_build_zip(data, zip_name, columns)` writes header-less CSVs in that order; `columns` per CSV is a list or a ctl/log path; unknown keys block.
  - `fbdi_template_columns` reads labels from the sheet XML with `zipfile` (openpyxl removed from fbdi.py); the real `SupplierSiteImportTemplate.xlsm` now opens (200 columns).
  - `fbdi_import_job(load_request_id)` scans the next request ids and returns the separate import job + status.
  - Tests added (47 passed). `knowledge/channel-c-fbdi-ess.md` and `/bulk` updated. Takes effect after the MCP server restarts.
- **Item 2 DONE (user OK, user chose "all SCM roles" + "all US1 BU orgs").** User `HCM` on the new pod, SCIM `PATCH Roles/{id}` members ADD:
  - Roles: Inventory Manager, Product Data Steward, Cost Accountant, Supplier Manager, Buyer, Procurement Requester, Procurement Application Administrator, Integration Specialist, Functional Setups User (122 → 131 roles).
  - Data access: `dataSecurities` Inventory Manager × `Inventory organization` 001, 002, 003, 004, 005, 020, 030, M001.
  - Backup: `backups/2026-11-25/security-HCM-roles-before.json`.
  - Verified: SCIM read, `dataSecurities` read by id, `smoke_test` 13/13.
  - Logged in `config-docs/security.md` + `log_request`.
  - **Open (ask the user):** BU data access for the procurement roles (`Business unit` = US1 Business Unit, as on the old pod); cost-org data access for Cost Accountant.
- **Item 3 STARTED.** `.claude/commands/new-inv-org.md` and `new-item-org.md`: 9-point prerequisite checklist (location, Materials Management BU, legal entity, profit center BU, schedule, item master, sets, cost org, duplicates) → plan → backup → create (`inventoryOrganizations` POST or `copyInventoryOrganizations`) → verify. Shortcuts `create_inventory_org` / `create_subinventory` / `create_item` come after the first real run.
- **Item 4 DONE.** 3 oracle-researcher batches (Sonnet) wrote:
  - `cost-management.md`, `inventory-transactions.md`
  - `shipping-execution.md`, `order-management.md`
  - `financial-orchestration.md`, `calendars-flexfields.md`, `sourcing-negotiations.md`

  All are PARTIAL with UNVERIFIED items marked. Merged into `INDEX.md` (7 rows) and `dependencies.md` (6 chains).
  - Verified on the pod: 43 TaskCodes added to `fsm-task-codes.md`. **Cost Accounting, Supply Chain Financial Orchestration, Shipping, Order Management and flexfield setup tasks are all CSV-enabled → channel B**, although the docs only describe the UI. The one exception is Manage Shipping Document Job Set Rules (CSV N).
  - 9 more role codes confirmed (Order Manager, Order Entry Specialist, Order Administrator, Pricing Administrator, Shipping Agent, Sourcing Project Collaborator…) in `access-and-roles.md`.
- **Next (priority):**
  1. Ask the user about the 2 open data-access items above.
  2. First real `/new-inv-org` on TEST (with the user's OK), then the `create_inventory_org` / `create_subinventory` / `create_item` shortcuts + tests.
  3. First FSM CSV export of a cost task (e.g. `CST_MANAGE_COST_ORGANIZATIONS`) to learn the CSV structure.
  4. Backlog item 5 (verify the UI playbooks).
  5. Reduce UNVERIFIED items in the 7 new files with pod reads.
