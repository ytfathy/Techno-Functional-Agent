# oracle-scm-agent — original brief (from the user, verbatim)

You are going to build me a project called oracle-scm-agent: an AI agent that works as a senior Oracle Fusion Cloud SCM & Procurement implementation consultant. I am an Oracle SCM consultant. When it's done, I open Claude Code in this folder, write a request in plain language (Arabic or English), and the agent does the configuration or transaction in Oracle Fusion itself, the way an experienced consultant would: it knows which setup task to use, what the prerequisites are, what to check first, how to do it, and how to verify it.

The key requirement: the agent must be able to handle ANY functional request an SCM consultant handles, not a fixed list of tools. Fixed tools are just shortcuts; the agent must also be able to work out how to do something new.

## THIS IS AN EXECUTING AGENT, NOT AN ADVISOR
When I say "create carrier X" or "create supplier site Y", the agent does it in Oracle itself (via REST, FSM CSV, FBDI, or by driving the browser). It must never answer with "here are the steps to do it" — explaining is only acceptable if every channel failed, and then it says exactly why.

Autonomy modes (switch with /mode):
- confirm (default for PROD): show the plan, one "yes" from me, then execute everything end-to-end.
- auto (allowed only on DEV/TEST): execute directly without asking, then report what was done with the IDs. High-impact items in the safety rules still need one confirmation.

Configure .claude/settings.json permissions so the oracle-fusion and playwright MCP tools are pre-allowed and Claude Code doesn't stop to ask me on every single tool call (Oracle-side confirmation is handled by the agent's own modes above).

### Oracle access the agent needs (document this in README → "Access setup")
- A dedicated Fusion user for the agent (e.g. AI_SCM_AGENT) on TEST first, with the roles needed for the scope, e.g.: Application Implementation Consultant (setup tasks), Procurement Application Administrator, Supplier Administrator / Supplier Manager, Buyer / Procurement Manager, Inventory Manager, Integration Specialist (FBDI/ESS), plus data access to the relevant BUs/inventory orgs. Tell me the exact role codes to request from the security admin for my release.
- REST access with Basic Auth (TEST) or OAuth client credentials (recommended).
- For the browser channel: a persistent Playwright browser profile in .browser-profile/ (git-ignored) so the session stays signed in after I log in once.
- Smoke test that checks each role actually works (one read per area) and tells me which privilege is missing if a call returns 401/403.

## 1. The agent's "hands" — 4 execution channels
Fusion is SaaS (no database access), so the agent works through these channels. For every request it picks the best one in this order:

| # | Channel | Use for | Notes |
|---|---|---|---|
| A | Business REST APIs (/fscmRestApi/resources/11.13.18.05/..., /hcmRestApi/...) | Master data & transactions: suppliers, sites, contacts, procurement agents, requisitions, POs, agreements, ASL, items, receipts, locations, etc. | Always call GET <resource>/describe first to read real fields. Never invent field names. |
| B | FSM Setup Task CSV REST (setupTaskCSVExports / setupTaskCSVImports) | Setup tasks that support CSV export/import | Pattern: find TaskCode → export current setup (zip) → modify the CSV → import → poll status → read the import log. The export is also the backup before any change. |
| C | FBDI via ERP Integrations REST (/erpintegrations, importBulkData, submitESSJobRequest) | Bulk loads (suppliers, items, POs, agreements…) and running scheduled processes | Generate the CSV/zip from the official FBDI template for my release, upload, poll the ESS job, read the output/log. |
| D | Browser automation of the Fusion UI (Playwright MCP) | Anything with no API: Setup & Maintenance tasks such as Manage Business Unit, Assign Business Unit Business Function, Configure Procurement/Requisitioning Business Function, Manage Document Styles, approval rules (Manage Requisition/Purchasing Document Approvals), etc. | I sign in myself once (SSO/MFA). Every successful UI flow gets saved as a reusable playbook. |

Install Playwright MCP: `claude mcp add playwright -- npx @playwright/mcp@latest`

## 2. Build the custom MCP server oracle-fusion
Python 3.11+, official mcp SDK (FastMCP), httpx, pydantic, python-dotenv, openpyxl.
Structure:
```
oracle_fusion_mcp/
  server.py          # registers all tools
  client.py          # auth, retries, pagination (offset/limit/hasMore), q= filters, error parsing, batch (application/vnd.oracle.adf.batch+json)
  generic.py         # GENERIC tools (most important)
  fsm.py             # setup task CSV export/import
  fbdi.py            # erpintegrations: upload, importBulkData, ESS job submit/status/output
  suppliers.py, procurement.py, inventory.py, locations.py, enterprise.py   # shortcut tools
```
Generic tools (so the agent is never limited to a fixed list):
- rest_describe(resource_path) – read a resource's metadata
- rest_get(resource_path, q, fields, expand, limit, offset)
- rest_create(resource_path, payload, dry_run=True)
- rest_update(resource_path, payload, dry_run=True)
- rest_action(resource_path, action_name, payload, dry_run=True) – e.g. submit/cancel a PO
- fsm_find_task(name) – find a setup task's TaskCode and whether CSV import/export is supported
- fsm_export(task_code, scope) / fsm_import(task_code, zip_path, dry_run=True) / fsm_status(process_id)
- fbdi_import(template, file_path, job_params, dry_run=True) / ess_submit(job, params) / ess_status(request_id)

Shortcut tools for the frequent stuff: create_supplier, add_supplier_address, create_supplier_site, assign_site_to_bu, add_supplier_contact, create_procurement_agent, create_requisition, create_purchase_order, submit_purchase_order, create_location, find_business_unit, lookup_values.

Supplier flow: separate calls in order: supplier → address → site (procurement BU) → site assignment (client BU) → contacts. Don't combine them in one payload (it often fails with POZ-2130403).

Every write supports dry_run=True (returns endpoint + exact payload without sending).

Register in a project-level .mcp.json together with playwright, so both load automatically when I open Claude Code here.

## 3. The agent's "brain" — consultant knowledge base
Create knowledge/ with one markdown file per setup area. Each file must contain: business purpose, FSM offering/functional area/task name(s), prerequisites & dependencies, key fields and what they mean, common mistakes, which channel (A/B/C/D) to use and the exact endpoint/TaskCode/playbook, and how to verify. Research each from the official Oracle docs for my release (docs.oracle.com → Procurement / SCM / Applications Common → REST API & implementation guides) — don't write from memory. Mark anything you couldn't verify as UNVERIFIED.

Cover at least:

Enterprise structure — Locations (Manage Locations), reference data sets, business units (Manage Business Unit), Assign Business Unit Business Function, Manage Business Unit Set Assignment, legal entities & ledgers (read-only lookup), Manage Business Unit Data Access for Users.

Procurement setup
- Configure Procurement Business Function (document numbering, line types, currency/rate, buyer defaults, etc.)
- Configure Requisitioning Business Function (deliver-to, destination org, one-time location, etc.)
- Service provider relationships (requisitioning BU ↔ procurement BU)
- Document styles (Manage Document Styles), line types, procurement categories/catalogs, purchasing category hierarchy
- Procurement agents (buyer/catalog admin/supplier manager access per BU)
- Supplier numbering, supplier registration/spend authorization setup, Approved Supplier List
- Approvals: Manage Requisition Approvals, Manage Purchasing Document Approvals, Manage Supplier Registration Approvals — rules, stages, participants, conditions (amount, category, BU…)
- Sourcing basics (negotiation styles), purchasing profile options, procurement lookups

Procurement transactions — Requisitions (create/submit/check status), purchase orders (create, submit, change order, cancel, close), blanket & contract agreements, receipts, and the full Req → PO → Receipt test cycle.

Supplier management — Suppliers, addresses, sites, site assignments, contacts, bank account hand-off (note: payment/bank data needs special care — see safety rules).

Inventory & SCM — Inventory organizations, item organizations, subinventories & locators, items & item classes, UOMs, shipping networks, transfer orders, receiving parameters, ship-to/bill-to locations.

Common — Lookups, value sets, descriptive flexfields, profile options, scheduled processes, users/roles needed for the above (users & role assignment through the SCIM/user REST APIs where available).

Also create knowledge/dependencies.md: a dependency graph of setup (what must exist before what), e.g. for a new BU end-to-end: Location → Reference data set → Business Unit → Assign business functions (Requisitioning, Procurement, Payables, …) with ledger/legal entity where required → BU set assignment → Configure Procurement BF → Configure Requisitioning BF → Service provider relationship → Procurement agent access → Data access for users → Document numbering/styles → Approval rules → Test: requisition → PO → receipt.

## 4. How the agent handles any request (put this loop in CLAUDE.md)
1. Understand the request; map it to Fusion objects and FSM task(s). If something mandatory is missing, ask me in one short question (with the options it found in the system, e.g. list of existing BUs).
2. Check prerequisites using knowledge/dependencies.md; read the current configuration from Fusion.
3. Choose the channel (A → B → C → D). If the task isn't in knowledge/ yet, research the official Oracle docs first, then add a new knowledge file.
4. Plan: show me a short numbered plan — steps, channel per step, records/values to be created or changed, impact (who/what it affects), and the target environment.
5. Back up: for setup changes, export the current setup (channel B) or capture the current values (screenshot/JSON) before changing anything.
6. Execute only after my "yes".
7. Verify by reading back from Fusion (and for setup, a real test if relevant, e.g. create a test requisition to check an approval rule).
8. Document: append the change to config-docs/<area>.md (consultant-style configuration document: what, why, values, date, environment), and to the audit log.

## 5. Safety rules (mandatory, in CLAUDE.md)
- Read before write; check for duplicates.
- Preview → my confirmation → execute. No silent writes.
- PROD guard: if the environment is PROD, I must type CONFIRM PROD for any change. Default environment is TEST.
- No deletes unless I explicitly ask; prefer inactivation/end-dating.
- Backup before any setup change (step 5 above); keep backups in backups/<date>/.
- Approval rules, document numbering, BU business functions and anything financial (bank accounts, payment methods, ledgers) are high-impact: show the before/after and ask twice.
- Never type, log, or store passwords, tokens, or bank account numbers in plain text; credentials live only in .env. I sign in to the browser myself.
- On errors, parse the Oracle message (POZ-, PO-, INV-… codes), explain it simply, propose the fix; never retry blindly.
- Audit log: logs/audit-YYYY-MM-DD.jsonl (request, channel, endpoint/task, payload without secrets, result, IDs).

## 6. Auth & environments
- .env.example with: ORACLE_ENV_NAME, ORACLE_BASE_URL, ORACLE_AUTH_MODE (basic | oauth), ORACLE_USERNAME, ORACLE_PASSWORD, ORACLE_OAUTH_TOKEN_URL, ORACLE_CLIENT_ID, ORACLE_CLIENT_SECRET, ORACLE_SCOPE, ORACLE_RELEASE (e.g. 26A).
- Profiles .env.dev / .env.test / .env.prod + tool switch_environment. .env* git-ignored.

## 7. Claude Code project setup
- CLAUDE.md: persona (senior Oracle Fusion SCM/Procurement consultant), the request loop (section 4), safety rules (section 5), channel selection (section 1), and "answer me in Egyptian Arabic, keep Oracle terms in English".
- Slash commands in .claude/commands/: /new-supplier, /new-bu (full end-to-end BU setup using the dependency graph), /new-location, /procurement-setup, /approval-rule, /new-req, /new-po, /p2p-test (Req→PO→Receipt test), /find, /env, /export-setup, /config-doc.
- Subagents in .claude/agents/: oracle-researcher (reads Oracle docs and writes knowledge files), fusion-ui-operator (runs Playwright playbooks), config-reviewer (reviews a plan against dependencies & safety rules before execution).
- playbooks/ for UI flows (channel D): exact navigation path, fields, screenshots of key screens, verification step. The agent updates a playbook whenever the UI differs from it.
- Bulk mode: read an Excel/CSV (suppliers, sites, items, agents…), validate all rows, show a summary, then run (REST batch or FBDI), and produce a result report in reports/.

## 8. Build order
- Ask me only: Fusion release, do I have a TEST pod URL, auth method. Then show me the folder structure.
- Phase 1: client.py + generic tools + smoke test (read-only) against TEST.
- Phase 2: knowledge/ + dependencies.md (use the oracle-researcher subagent; cite the doc URL in each file).
- Phase 3: shortcut tools (suppliers, procurement agents, req/PO) with dry_run + tests.
- Phase 4: FSM CSV export/import + FBDI/ESS tools.
- Phase 5: Playwright playbooks for: create BU, assign business functions, configure procurement BF, configure requisitioning BF, document styles, approval rules.
- Phase 6: slash commands, subagents, bulk mode, README with examples.
- Unit tests with mocked HTTP (pytest, respx) for every tool. Never run a write against a real pod during development without asking me.

## 9. Example requests it must handle (put in README)
- "اعمل سبلاير اسمه Nile Trading، رقمه الضريبي 123، سايت في القاهرة على BU اسمه Egypt Operations"
- "اعمل BU جديد اسمه KSA Retail، بلوكيشن في الرياض، وفعّل عليه Requisitioning و Procurement و Payables، وظبط له الـ procurement كامل"
- "اعمل Document Style جديد للـ PO اسمه Services PO"
- "اعمل approval rule: أي ريكوزيشن أكبر من 50,000 تروح للمدير وبعدين لـ Finance"
- "خلي أحمد buyer على الـ BU الجديد بكل الصلاحيات"
- "اعمل ريكوزيشن تست وحولها PO وعمل receipt عشان أتأكد إن الـ setup شغال"
- "طلعلي كل السبلايرز اللي مالهمش site assignment على BU Egypt Operations"
- "اعمل Carrier جديد اسمه FastShip وفعّله على الـ inventory org بتاع القاهرة"

## Optional (only if I ask)
Ready-made third-party MCPs for Oracle Fusion (CData, StackOne, mcp-oraclefusion on PyPI) — they are read-only or send data through outside vendors, so don't install them by default.
