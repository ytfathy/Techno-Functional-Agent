# Technical extensions (sandboxes, VB Studio, Application Composer, Alerts Composer, personalization)

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL (several 26D pages only reachable as older-release or readiness pages; see UNVERIFIED)

## Business purpose
Extend/configure Fusion SCM and Procurement without touching Oracle code: add fields/rules to pages, scripts on objects, alerts, flexfields. Technical consultant decides: configuration (supported) vs extension (VB Studio / Application Composer) vs integration. Affects all users of the pod once published; changes are in mainline metadata and survive patches only if made with the supported tools.

## Where in Fusion (FSM)
- Sandboxes: Navigator > Configuration > Sandboxes (not an FSM task). Publish also there.
- Redwood pages: page Settings and Actions menu > "Edit Page in Visual Builder Studio" (only shown if page is extensible AND user has privilege).
- Alerts Composer: Navigator > Alerts Composer (HCM-documented; SCM path UNVERIFIED).
- Flexfields / lookups / profile options: FSM tasks Manage Descriptive Flexfields, Manage Standard Lookups, Manage Profile Options (see `calendars-flexfields.md`, `procurement-profile-options-lookups.md`, `common-setup.md`).

## Prerequisites & dependencies
- Sandbox needed before Page Composer / Application Composer edits (changes saved in sandbox, merged on publish). VB Studio: sandbox optional; needed only if underlying data-model changes (DFF etc.) must be published together with the extension deploy.
- Privilege `FND_ADMINISTER_SANDBOX_PRIV` (Administer Sandbox) to publish and to use Redwood VB Studio Express; "Manage Sandbox" can edit but not publish.
- VB Studio initial setup by sysadmin: doc topic "Set Up VB Studio to Extend Oracle Cloud Applications".

## Key facts
| Topic | Fact | Notes |
|---|---|---|
| Sandbox types | Test-only; Publish (integration sandbox, final staging) | Access levels: Full / Edit and preview / View only |
| Publish steps | Navigator > Configuration > Sandboxes > open sandbox > Publish > Continue to Publish > Done | Test first: Sandbox Mode > "Preview as if Published (Context: All)"; close Page Composer first; resolve merge-log conflicts |
| Publish blockers | no changes; profile `FND_ALLOW_PUBLISH_SANDBOX` ("Control Publish Sandbox Action in Production Environment") = No; missing privilege; unresolved conflicts | After publish the sandbox is frozen |
| Patch hygiene | Publish or delete sandboxes before each patch/upgrade | Else restart with new sandbox |
| Migration | Migration UI moves sandbox changes between environments (registered target env) | VB Studio extensions are deployed to the target, not migrated (21B doc; re-verify) |
| Redwood extensions (HCM, SCM, Procurement) | VB Studio **Express mode only**; Advanced mode not supported | |
| Express mode can | show/hide, required/optional, read-only/editable fields and regions by criteria; add DFF fields; rearrange/add content in dynamic containers; default values via form rules | Varies per page; not all pages support business rules |
| Redwood PO examples (release notes) | 25B view PO extensibility; 25D edit PO lines/schedules/distributions tables, rules per party type (requester/buyer/supplier) and page mode; 26C default document style ID via form rules on PO search, Agreement search, Staged Document pages | Oracle: only features listed in the extension doc are supported |
| Classic (non-Redwood) pages | Page Composer, Transaction Design Studio, Autocomplete Rules apply to responsive/classic pages only, NOT Redwood | Context layer of sandbox must be one the page supports |
| Application Composer | Groovy server scripts: validation rules, triggers, object functions on standard/custom objects; Actions call object functions | Object availability is per product family; Procurement objects UNVERIFIED |
| Groovy cautions | no save/rollback inside script; check publish warnings; allow-listed classes only | |
| Alerts Composer | Resource alert (based on a REST resource, expression-driven recipients, templates) vs Event alert (predefined triggers, only templates editable) | "Simulate Run = Yes" for test; no notification in non-prod |
| Procurement requisition extensibility | DFF at header/line/distribution (declarative) | older guide; verify per page |

## Common mistakes
- Using Page Composer/Application Composer on a Redwood page: not applicable; use VB Studio Express.
- Looking for "Edit Page in Visual Builder Studio" with no `FND_ADMINISTER_SANDBOX_PRIV`: task hidden.
- Publish disabled in PROD by `FND_ALLOW_PUBLISH_SANDBOX=No`.
- Leaving sandboxes open across a quarterly update.
- Enabling a DFF in FSM but not showing it on the Redwood page (needs VB Studio deploy).
- Doing record-level business logic in page rules instead of object validation.

## Channel & exact technique
- Preferred channel: D (UI/VB Studio) for page extensions and sandboxes; A for flexfield/lookup/profile values (REST) where available. No documented REST for sandbox create/publish found (UNVERIFIED) -> D.
- A: lookups/profile values/value sets via common REST (see `common-setup.md`: `/fscmRestApi/resources/11.13.18.05/...` lookups, profileValues, valueSets, setupTasks). Always `rest_describe` first.
- B: FSM CSV for flexfield/lookup tasks only if the task supports it (check `fsm-task-codes.md`).
- C: not applicable.
- D: sandbox playbook to create (`playbooks/`), then VB Studio Express edit, deploy, verify as end user, publish sandbox if one was used.
- Deploy flow VB Studio (from docs): confirm "Edit Page in Visual Builder Studio" present > open VB Studio > confirm Express mode > apply rules > deploy extension (details in VB Studio doc; UNVERIFIED for exact buttons).

## How to verify
Sign in as an end user (not admin) after publish/deploy and open the page; check Sandboxes page shows status Published; profile `FND_ALLOW_PUBLISH_SANDBOX` via Manage Profile Options.

## Sources
- https://docs.oracle.com/en/cloud/saas/applications-common/25d/oaext/publish-sandboxes.html — publish steps, privilege, profile option, failures
- https://docs.oracle.com/en/cloud/saas/applications-common/26b/oaext/overview-of-sandboxes.html — sandbox types, access levels, patch advice, Migration UI
- https://docs.oracle.com/en/cloud/saas/human-resources/fauvb/overview-of-redwood-application-extensions.html — Express only for HCM/SCM/Procurement; extensible elements
- https://docs.oracle.com/en/cloud/saas/readiness/scm/24c/ssproc24c/24C-ssproc-wn-f32742.htm — Edit Page in VB Studio task, Administer Sandbox, rule capabilities
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26c/proc26c/26C-procurement-wn-f49334.htm — default document style via form rules (26C)
- https://docs.oracle.com/en/cloud/saas/readiness/scm/25d/proc25d/25D-procurement-wn-f39549.htm — edit PO extensibility (25D)
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/oaext/configuring-and-extending-applications.pdf — 26D guide (PDF not machine-readable here; used via search snippets only)
- https://docs.oracle.com/cd/G24923_01/trans/G17759-01/configuring-and-extending-product-lifecycle-management.pdf — Application Composer Groovy server scripts (PLM, older)
- https://docs.oracle.com/en/cloud/saas/human-resources/fahcc/what-is-alerts-composer.html and https://docs.oracle.com/en/cloud/saas/human-resources/20b/faigh/alerts-composer.html — Alerts Composer (HCM, 20B)

## UNVERIFIED
- Any REST/SOAP API to create or publish sandboxes: none found in docs.
- Which SCM/Procurement objects are exposed in Application Composer on 26D (Requisition, PO, Supplier unconfirmed; PLM Item objects documented in older PLM guide).
- Exact VB Studio deploy/publish click path and role names for 26D; Advanced-mode exclusion beyond HCM/SCM/Procurement overview.
- Alerts Composer navigation/privilege for SCM (only HCM `HRC_ACCESS_ALERTS_COMPOSER_PRIV` seen).
- Full list of Redwood Procurement pages supporting Express rules in 26D.
- Business rules (Oracle "business rules" beyond VB Studio form rules) for SCM: not researched.
- Personalization (user-level "Personalize" in Redwood) vs customization rule details: not confirmed from a 26D page.
