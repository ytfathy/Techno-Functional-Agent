# Calendars / Schedules and Flexfields (DFF, EFF, KFF, value sets)

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL

## Business purpose
- **Schedules** (shifts -> workday patterns -> schedule, plus exceptions) define working/non-working time. Inventory orgs need one (`ScheduleId` in org parameters); manufacturing plants use a manufacturing calendar; supply chain collaboration/cycle count use them for time buckets and transit time. Affects: inventory org setup, manufacturing, planning, cycle counts.
- **Flexfields** add custom attributes (DFF, EFF) or build intelligent codes (KFF, e.g. Stock Locators). **Value sets** validate segment values. After deploy, DFF/EFF attributes show in the UI and (via the object's `DFF` child) in REST/web services.

## Where in Fusion (FSM)
### Calendars
- Offering **Manufacturing and Supply Chain Materials Management** > Functional area **Facilities** > task **Manage Facility Schedules** (26C Workforce Scheduling guide and 25B readiness name this task and area; 26D page not found, offering inferred from 26A/26C getting-started guides).
- Shift / workday pattern / schedule tasks as named in other products (same page names "Manage Shifts", "Manage Workday Patterns", "Manage Schedules", "Manage Schedule Exceptions"): Project Management offering uses **Manage Project Shifts**, **Manage Project Workday Patterns**, **Manage Project Schedule Exceptions**, **Manage Project Schedules** (26D PPM guide). Scope: Elapsed type only, 7-day pattern, one project shift; not for plant/org calendars.
- Whether Manage Facility Schedules is one task covering shifts + patterns + schedules, or separate SCM tasks, in 26D: UNVERIFIED.
- Manufacturing: plant calendar is assigned in **Manage Plant Parameters** (Using Manufacturing, 26D "How You Manage Production Calendars"). Only shifts of type **Time**, shift details **Punch** or **None**; schedule and shifts must be Time (no Elapsed/Duration, no Flexible shift) per 25C plant parameter guide. Shift times use the plant time zone from Manage Inventory Organization Parameters. Shift exceptions: work execution > Manage Production Calendar page.
- HCM Workforce Scheduling (separate): offering Workforce Deployment > Workforce Scheduling tasks Shifts, Work Pattern Types, Work Pattern Templates, Work Patterns. Time and Labor uses Manage Work Shifts / Manage Work Weekday Patterns / Manage Work Schedules (older R12 doc). Not the SCM facility calendar.
### Flexfields and value sets
- Offering-independent: Setup and Maintenance > Functional area **Application Extensions**:
  - **Manage Descriptive Flexfields** (action **Deploy Flexfield** to mainline or **Deploy Flexfield to Sandbox**)
  - **Manage Extensible Flexfields**
  - **Manage Key Flexfields**
  - **Manage Value Sets**
- Product-specific copies of the same pages: **Manage Inventory Descriptive Flexfields**, **Manage Inventory Value Sets**, **Manage Inventory Account Alias Key Flexfield**, **Manage Inventory Locator Key Flexfield** (Inventory Management functional area, listed Conditional; Oracle says locator and account alias KFFs "must be defined for inventory to operate correctly"). Also **Manage Maintenance Descriptive Flexfields**, **Manage Maintenance Value Sets** (Maintenance).
- Item EFF: flexfield code `EGO_ITEM_EFF` (not `EGP_ITEM_EFF`). Product Management offering > Items functional area: task **Deploy Item Extensible Flexfields** (26C guide; 26D guide is a PDF, unread). Attribute groups are tied to item classes, then deploy again.
- Highlight Flexfields (Administration menu in a page) lets you configure/deploy from the page.
- Scheduled process (Scheduled Processes work area): **Synchronize Flexfields with Business Objects**.

## Prerequisites & dependencies
- Calendar chain: shifts (Time) -> workday pattern -> schedule (+ exceptions) -> active schedule -> Inventory Organization parameter Schedule (`ScheduleId`/`ScheduleName` in `inventoryOrganizations`, REST doc seen for 22D-24A) / plant parameters manufacturing calendar (`ManufacturingCalendarId`, labelled required in 24A org REST). Schedules are time-zone neutral; org supplies Time Zone. Do not delete a calendar in use (Oracle warns of scheduling data corruption in manufacturing).
- Flexfield chain: value sets first (not sandbox-deployable) -> segments/contexts/structures -> **deploy** -> (UI: sign out/in) -> REST describe refresh. Locator KFF must be deployed before subinventory locators / locator-controlled orgs work. Item EFF: attribute group -> item class association -> deploy.
- Depends on this: inventory org creation (schedule), plant parameters, cycle counts (`cycleCountSchedules` REST exists but is a different object), item classes (EFF), locators (KFF).

## Key fields
| Field (UI label) | REST attribute / CSV column | Meaning | Notes / typical value |
|---|---|---|---|
| Schedule (Inventory Settings, org parameters) | `ScheduleId`, `ScheduleName` on inventory organization | Warehouse working time | must exist/active before; set in Manage Inventory Organization Parameters |
| Manufacturing Calendar | `ManufacturingCalendarId` | Plant calendar | Time type |
| Flexfield Code | n/a | Identifier used in Scheduled Process params | e.g. `FND_VS_VALUES_B` (value set values DFF), `MTLL` (Stock Locators KFF, code per SaaS data dictionary), `EGO_ITEM_EFF` |
| Deployment status | n/a | State vs last deployed definition | exact status values not documented on 26D overview page |
| Value set `valueSets/{valueSets_Id}` | REST | value set header | GET only (see below) |
| Locator Structure | `StructureInstanceNumber` in subinventory `locators` REST | locator KFF structure instance | seen in 25C locators POST page |

## Rules (deploy)
- **Descriptive** flexfields: deploy to sandbox, test, publish sandbox (Deploy Flexfield to Sandbox), then mainline Deploy Flexfield. From Highlight Flexfields: Save and Deploy.
- **Extensible, key, value sets: mainline only** (cannot go to sandbox).
- Users must sign out/in to see UI changes (session cache).
- After deploy, XSD regenerates so attributes are available to web services (older 11g text; REST DFF behaviour under 26D not stated).

## Common mistakes
- Creating the inventory org without an active schedule.
- Using Elapsed/Duration schedules or Flexible shifts for plant calendars.
- Using Project calendar tasks (Elapsed, 7-day) for inventory/plant calendars.
- Forgetting to deploy after adding segments: no change in UI/REST.
- Trying to deploy a KFF/EFF/value set to sandbox.
- Deleting a value set or calendar already in use.
- Defining the locator KFF late: locators fail; segments 19/20 are auto-enabled for project/task if Project Manufacturing is on (EBS text; Fusion UNVERIFIED).
- Searching for `EGP_ITEM_EFF`; the code is `EGO_ITEM_EFF`.

## Channel & exact technique
- Preferred channel: **D (UI)** for shifts/patterns/schedules and for flexfield definition and deploy (no REST/FSM-CSV/ESS deploy operation found). A for value sets (read, values CRUD) and for verification of DFF attributes.
- A (REST, `/fscmRestApi/resources/11.13.18.05/`):
  - `valueSets` GET all, `valueSets/{valueSets_Id}` GET (Applications Common 26D page: **view only** for header). Subcategories: Table-Validated Value Sets, **Values**.
  - `valueSets/{valueSets_Id}/child/values` POST, GET; `.../child/values/{valueSets_values_Id}` GET, PATCH, DELETE. Value set must already exist (create it in UI).
  - Lookups (related): `commonLookups`, `setEnabledLookups`, `genericLookups` with `child/lookupCodes` (26D list).
  - No REST resource for workday patterns/shifts/schedules found (`cycleCountSchedules` is cycle counting only). `inventoryOrganizations` carries ScheduleId.
  - DFF on business objects: each resource exposes a `DFF` (or `...DFF`) child, e.g. `supplierNegotiations/{id}/child/DFF`. Always `rest_describe` after a deploy; if the new attribute is missing, run the sync process below.
  - ESS REST (generic): `POST ess/rest/scheduler/v1/requests` for submitting scheduled processes (26D Applications Common list). Job path/name for Synchronize Flexfields: not confirmed (UNVERIFIED).
- B (FSM CSV): UNVERIFIED for all of these tasks.
- C: no FBDI for schedules or flexfield setup found. Scheduled process **Synchronize Flexfields with Business Objects** parameters: Flexfield Type (**All Flexfields**, **Descriptive Flexfields**, **Key Flexfields**), Flexfield Code, **Enforce Synchronization**. All-flexfields resync = "deploys all flexfields marked as deployed"; single = type + code; force options ignore deployment history. Runs automatically at each patch.
- D (UI): `playbooks/` none yet. Flow: Setup and Maintenance > search task > open flexfield (search by code) > Edit > add context/segment (value set, display, required) > Save > Deploy Flexfield > check status > sign out/in.

## How to verify
- Schedule: open org parameters, schedule LOV shows it; `GET inventoryOrganizations?q=OrganizationCode='X'&fields=ScheduleId,ScheduleName`.
- Flexfield: deployment status "Deployed" in Manage page; `rest_describe` on the owning resource shows the DFF child attribute; PATCH a test value.
- Value set: `GET valueSets` then `child/values`.

## Sources
- https://docs.oracle.com/en/cloud/saas/project-management/26d/fapfm/create-calendars-for-projects-and-resources.html - Manage Project Shifts/Workday Patterns/Schedule Exceptions/Schedules steps and limits
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faicf/inventory-organization-parameters.html - Schedule field; task Manage Inventory Organizations (MSCM offering > Facilities)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faumf/how-you-manage-production-calendars.html - plant calendar, Time shifts, exceptions
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faims/use-workforce-scheduling-to-manage-shifts-and-operator-assignments.html - Manage Facility Schedules task, Facilities area (26C, from search snippet)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/faims/critical-choices-for-setting-up-plant-parameters.html - Time schedule/shifts only (25C, snippet)
- https://docs.oracle.com/en/cloud/saas/human-resources/faiws/workforce-scheduling-setup-and-maintenance-tasks.html - HCM workforce scheduling tasks
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/24a/fasrp/op-inventoryorganizations-post.html - `ManufacturingCalendarId`, `ScheduleId` (24A)
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/oaext/overview-of-flexfield-configuration.html - flexfield types, tasks, deploy rules
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/oaext/considerations-for-managing-flexfields.html - Deploy Flexfield vs Deploy to Sandbox, restrictions
- https://docs.oracle.com/en/cloud/saas/applications-common/faaqa/how-can-i-resolve-synchronization-issues-between-flexfields-and-business-objects-in-fusion-applications.html - Synchronize Flexfields with Business Objects parameters
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/api-value-sets.html - valueSets GET operations
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/api-value-sets-values.html - values CRUD
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/farca/rest-endpoints.html - lookups and ESS scheduler REST list
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/overview-of-implementing-inventory-management.html - Manage Inventory Locator Key Flexfield and other Inventory flexfield tasks
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25c/fasrp/op-subinventories-subinventoriesuniqid-child-locators-post.html - `StructureInstanceNumber` locator structure (25C, snippet)
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26c/faipr/implementing-product-management.pdf - Deploy Item Extensible Flexfields, EGO_ITEM_EFF (26C, via search summary)

## UNVERIFIED
- Exact 26D SCM task names and offering/area for shifts, workday patterns, schedules (only Manage Facility Schedules, from 26C/25B); whether separate "Manage Shifts/Workday Patterns/Schedules" SCM tasks exist.
- Any REST resource for schedules/shifts/workday patterns (none found in the pieces of the 26D SCM list that were readable; list is huge and only partly scanned).
- Whether ScheduleId in 26D org REST is still required; the org REST facts are from 22D-24A pages.
- REST resource for descriptive/extensible/key flexfield definitions or a deploy API (none found; treat Deploy as UI-only).
- ESS job path/name of Synchronize Flexfields with Business Objects; any other deploy-related ESS job.
- Setup Task CSV support for flexfield/value set/schedule tasks.
- Deployment status values; Locator KFF code `MTLL` (from SaaS data dictionary snippet) and structure details in 26D; Item EFF details in 26D PDF; Stock Locator segment behaviour in Fusion.
- Whether REST describe needs cache refresh after deploy (no official statement; practical advice: re-describe, run sync process, sign-out only matters for the UI).
