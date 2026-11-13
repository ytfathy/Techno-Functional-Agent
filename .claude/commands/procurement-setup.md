---
description: Configure or review procurement setup for a BU (procurement BF, requisitioning BF, service providers, agents, styles, numbering, approvals)
argument-hint: <BU name and what to set up / review>
---
Request: $ARGUMENTS

1. Read knowledge files: configure-procurement-bf, configure-requisitioning-bf, service-provider-relationships, procurement-agents, document-styles, line-types, approvals, dependencies.
2. Read the current setup of the BU (REST reads, `fsm_export` where the task supports CSV, or a UI snapshot via fusion-ui-operator). Produce a gap list against a working P2P setup.
3. Plan the fixes (channel per step), run config-reviewer for > 3 steps, back up, execute after approval, verify, and offer `/p2p-test`.
4. Document in config-docs/procurement-setup.md; `log_request`.
