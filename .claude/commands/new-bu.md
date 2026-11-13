---
description: Full end-to-end Business Unit setup using knowledge/dependencies.md
argument-hint: <BU name, location/city, business functions, ledger/legal entity…>
---
Request: $ARGUMENTS

High-impact request (BU business functions). Follow the CLAUDE.md loop and walk the "New BU end-to-end" chain in `knowledge/dependencies.md`:
Location → reference data set → Business Unit → assign business functions (ledger / legal entity where required) → BU set assignment → Configure Procurement BF → Configure Requisitioning BF → service provider relationship → procurement agent access → data access for users → document numbering/styles → approval rules → test req → PO → receipt.

1. Read the current state for every node (existing location, set, BU name, ledger, legal entity). Ask one short question for anything mandatory that is missing, listing what exists.
2. Build the full numbered plan with the channel per step (most BU tasks are channel D: `playbooks/create-business-unit.md`, `playbooks/assign-business-unit-business-function.md`, `playbooks/configure-procurement-bf.md`, `playbooks/configure-requisitioning-bf.md`).
3. Run the **config-reviewer** subagent on the plan and fix its findings.
4. Show before/after for business functions and numbering; ask twice (safety rule 6).
5. Back up, execute step by step (UI steps via **fusion-ui-operator**), verify each step, then run `/p2p-test` on the new BU.
6. Document in config-docs/enterprise-structure.md and config-docs/procurement-setup.md; `log_request`.
