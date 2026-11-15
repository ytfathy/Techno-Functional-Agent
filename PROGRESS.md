# oracle-scm-agent — Progress & handoff

> Updated at the end of every phase. To continue in another Claude account/session: open Claude Code in this folder and paste the "Resume prompt" at the bottom.
> Last update: 2026-11-14 — Phases 1–4 and 6 done; Phase 5 playbooks drafted (need first live run).

## Goal (short)
An executing AI agent (Claude Code project) that acts as a senior Oracle Fusion Cloud SCM & Procurement consultant. The user writes a request (Arabic/English) and the agent does the setup or transaction in Fusion itself via 4 channels (A REST, B FSM CSV, C FBDI/ESS, D Playwright UI), with safety rules, backups, an audit log and config docs. Full original brief: [SPEC.md](SPEC.md). User guide: [README.md](README.md).

## Decisions taken
| Item | Decision |
|---|---|
| Fusion release | **26D** |
| TEST pod | User-filled `.env.test`: an Oracle demo pod, user `hcm_impl`, Basic Auth. Base URL is normalized to the pod root automatically. |
| Auth | Basic Auth on TEST. OAuth client credentials is coded, but per the 26D docs it does NOT work for `/fscmRestApi`, `/hcmRestApi` or SCIM (only `/api/...`). Use Basic or JWT user assertion. |
| Python / SDK | System Python 3.14 in `.venv`; **`mcp>=1.2,<2`** (mcp 2.x renamed FastMCP → pinned to keep FastMCP as the brief asks) |
| Browser for channel D | Microsoft Edge (`--browser msedge`, Chrome not installed); profile in `.browser-profile/` |
| Agent reply language | Egyptian Arabic, Oracle terms in English (CLAUDE.md) |

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

Tests: **29 passed** (pytest + respx, mocked HTTP only). MCP server verified over a real stdio connection: **42 tools**, `env_info` OK.
**No write has been sent to the real pod yet** (only reads, describe, setupTasks, SCIM role lookups).

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

## Next steps
1. ~~Reopen Claude Code in this folder~~ **DONE 2026-11-14**: both MCPs load (oracle-fusion 42 tools, playwright); `env_info` = TEST / 26D / basic / `hcm_impl` / mode `confirm`; live `smoke_test` 13/13 OK.
2. **First real write test on TEST** — IN PROGRESS. Prepared (reads only): no supplier `AI Agent Test Supplier 01` exists; procurement BU candidate `US1 Business Unit` (exists, active). `create_supplier` dry run OK, field_check clean (warning: `SupplierPartyId`, `SupplierNumber` mandatory per describe but expected to default). User said yes; **live POST `suppliers` → HTTP 403** (empty body, no Oracle code). Read-back: nothing created. `hcm_impl` can read but not create suppliers (missing Supplier Manager `ORA_POZ_SUPPLIER_MANAGER_ABSTRACT` and/or BU data access). `hcm_impl`'s own roles are not visible via `userAccounts` (exact-name query returns 0 rows). **Blocked**: need a pod user with procurement write roles (or roles granted to `hcm_impl`), then rerun the same 4-step flow. Recorded in `knowledge/error-codes.md`; `log_request` done.
   - 2026-11-14 user chose "grant roles to `hcm_impl`". Done (reads only): fixed `client.get` for SCIM (ADF params were rejected; httpx dropped the path query) + test (30 passed; **MCP server must be restarted to pick up the fix**); found `hcm_impl` has IT Security Manager (can PATCH SCIM Roles); role GUIDs and `dataSecurities` BU row format verified (in `knowledge/users-roles.md`, `knowledge/bu-data-access.md`); backup `backups/2026-11-14/security-hcm_impl-roles-before.json` (35 roles, 0 data access rows); dry runs OK for SCIM `PATCH Roles/{id}` members ADD and `POST dataSecurities`. User approved. **DONE**: 4 roles granted to `hcm_impl` (SCIM 204 ×4) + 4 `dataSecurities` rows on US1 (see `config-docs/security.md`). Supplier retry from the MCP still 403 (stale session cookie) → fixed `client.py` (clear cookies per call). From a fresh process: **supplier created** `SupplierId 300000349308087`, `SupplierNumber 1501`; **address** `Cairo HQ` `300000349308094`. **Site `CAIRO-TEST` → 403** (likely: `hcm_impl` is not a procurement agent on US1 with Manage Suppliers; no agent row for `<shared demo email>`). User OK'd the agent. **`POST procurementAgents` → PO-2055145** (AgentEmail invalid): `<shared demo email>` is shared by 25+ "HCM Implementation*" persons and `hcm_impl` has no person of its own → `hcm_impl` cannot be a procurement agent → cannot create supplier sites by REST. **Blocked; options for the user:** (a) switch the agent profile to a demo user that is already a US1 agent with Manage Suppliers (e.g. `CALVIN.ROTH`, also has Manage Orders — good for `/p2p-test`; user fills creds in `.env.*`); (b) create the site with FBDI Import Supplier Sites as `hcm_impl` (UNVERIFIED whether import skips agent BU security). **User then rejected CALVIN.ROTH ("dont use calvin") — do NOT use it.** Remaining route: (b) FBDI Import Supplier Sites as `hcm_impl` (needs the 26D `SupplierSiteImportTemplate.xlsm`, download only with the user's OK). **FBDI route DONE for the site (2026-11-14):** template `fbdi/templates/SupplierSiteImportTemplate.xlsm` downloaded (user OK); importBulkData `/oracle/apps/ess/prc/poz/supplierImport,ImportSupplierSites` `NEW,N,AIAGENT1114` → Import Supplier Sites 10198003 SUCCEEDED, 1 processed / 0 rejected → **site CAIRO-TEST created** (not readable via REST by `hcm_impl`). Lessons in `knowledge/channel-c-fbdi-ess.md` (CSV order = ctl order; import child is a separate request id). Code: `fbdi_import` no longer sends AP `JobOptions` by default. **Known bug:** `fbdi_build_zip`/`fbdi_template_columns` use sheet order + openpyxl → wrong/failing for supplier templates; fix = take column order from the ctl (SQL*Loader log or Oracle controlfiles URL). **User said stop here (2026-11-14).** Not done: site assignment to US1 (would use `SupplierSiteAssignmentImportTemplate.xlsm`, 386 KB, ask before download → `ImportSupplierSiteAssignments`). Test supplier 1501 is left with address + site, no assignment. Earlier notes on Calvin kept for reference: Read check: CALVIN.ROTH already has Supplier Manager, Buyer, Procurement Requester, Procurement Manager, Receiving Agent, Supplier Administrator and an active US1 agent row with Manage Suppliers (`AssignmentId 300000047348441`) → no grants needed. **Waiting for the user to create `.env.calvin`** (copy of `.env.test` with `ORACLE_USERNAME=CALVIN.ROTH` + its password, `ORACLE_ENV_NAME=TEST`); then `switch_environment("calvin")` → site `CAIRO-TEST` → assignment US1 → read-back. US1 agents with Manage Suppliers: Casey Brown, Karen Curtis, Calvin Roth, Tiffany Irving, May Gee, Saville Miller, Amy Marlin, Rosario Arrendondo, Ava Clark, John Dunbar. Restart/reconnect the MCP server so it loads the SCIM + cookie fixes. See `config-docs/suppliers.md`.
   - Lesson: smoke test checks reads only. Consider a write-privilege check (dry run can't tell; only a real POST or a role read can). (only with the user's OK), e.g. `/new-supplier` with a test supplier, or `/p2p-test`. Fix any payload issue the pod reports and record it in knowledge/.
3. **First live channel-D run** (e.g. approval rule) → playbooks become VERIFIED-ON-POD.
4. **First FSM CSV export** (e.g. `/export-setup Manage Document Styles`) to see the real CSV structure; record it in `knowledge/channel-b-fsm-csv.md`.
5. When a bulk FBDI load is needed: download the 26D template (ask the user) and read the ESS job path on the pod.
6. Production: create the dedicated `AI_SCM_AGENT` user with the roles in README (the demo pod uses `hcm_impl`).

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
