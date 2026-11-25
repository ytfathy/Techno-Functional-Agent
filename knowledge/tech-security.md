# Technical security (Security Console, custom roles, reports, audit, 403 troubleshooting)

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL (26D Securing Applications guide readable only via snippets and neighbouring-release pages)

## Business purpose
Build least-privilege custom job roles, keep user/role data in sync, report on access, audit changes, and diagnose "403 / not authorized" for users and integration accounts. See `users-roles.md` (SCIM/userAccounts) and `access-and-roles.md` (role codes) for the REST side.

## Where in Fusion (FSM)
- Security Console: Tools > Security Console. Tabs: Roles, Users, Analytics, Certificates, Administration (Role Status tab shows copy jobs).
- FSM task "Run User and Roles Synchronization Process" (Initial Users functional area) = Retrieve Latest LDAP Changes.
- Audit: Setup and Maintenance task "Manage Audit Policies"; Navigator > Tools > Audit Reports.
- Needed job role to administer: IT Security Manager `ORA_FND_IT_SECURITY_MANAGER_JOB`.

## Prerequisites & dependencies
- Import User and Role Application Security Data must have run (reports and Security Console visualizations read the Applications Security tables).
- Send Pending LDAP Requests daily; Import job start time after it completes.

## Key facts
| Topic | Fact |
|---|---|
| Copy role | Roles tab: search/graph > menu > Copy Role. Options: "Copy top role" (shallow, keeps links to original inherited roles, Oracle's default advice) or "Copy top role and inherited roles" (new copies of hierarchy, insulated from Oracle changes) |
| Naming | Default suffix name "Custom", code "_CUSTOM"; prefix/suffix configurable in Administration > Roles tab |
| Edit rules | Predefined roles: can add/modify/remove custom data security policies and users (job/abstract/discretionary); cannot change function security policies, Oracle data policies, or hierarchy. Custom/copied roles: anything editable |
| Users | Copied role does not inherit users of source; assign explicitly. Hierarchy changes only on the top copied role |
| Copy job | Monitor Administration > Role Status tab |
| Compare | Roles tab: compare two roles; Users: Compare Users (direct + inherited roles) |
| Analytics | Role Analytics: category counts, export to spreadsheet |
| Privileges | Assign only what is needed (subscription usage warning) |
| REST for roles | SCIM `/hcmRestApi/scim/Roles` and `/Users` (read; role assignment via Users PATCH), HCM `userAccounts` (see `users-roles.md`). NO documented REST/SCIM to create/copy a custom role or add privileges/policies found -> use Security Console (D) |
| Sync processes | `Retrieve Latest LDAP Changes`: once before implementation, then automatic; one instance at a time; notification option. `Import User and Role Application Security Data`: schedule Daily, Days Between Runs 1, after Send Pending LDAP. `Send Pending LDAP Requests`: sends bulk and future-dated requests; daily; once scheduled cannot be run on demand; for supplier users run with User Type = Party, Batch Size = A (see `error-codes.md`) |
| Role sync delay (26D readiness note) | After role change: Tools > Scheduled Processes > run Import User and Role Application Security Data, wait Succeeds, then Retrieve Latest LDAP Changes |
| Security Console warning | Administration > Synchronization Process Preferences: warning on Roles tab if Import not run within N hours |
| Reports | User Role Membership Report (CSV in zip: user, LDAP status, role code/name; slow for all users); User and Role Access Audit Report (XML; function privileges + data security policies for role/all roles/user/all users; based on Import data); Inactive Users Report; User Password Changes Audit Report (privilege `ASE_USER_PASSWORD_CHANGES_AUDIT_REPORT_PRIV`, in IT Security Manager) - report names from CX/HCM guides, run as scheduled processes/BI reports |
| Audit | Manage Audit Policies (privilege `FND_MANAGE_AUDIT_POLICIES_PRIV`): Configure Business Object Attributes > pick Product > objects > attributes > Save and Close > Audit Level = Auditing > Save and Close. Off by default; configure objects before enabling. Select parent with child. View: Navigator > Tools > Audit Reports, privilege `FND_VIEW_AUDIT_HISTORY_PRIV` (Internal Auditor job role). OTBI on audit data needs duty `FBI_SECURITY_TRANSACTION_ANALYSIS_DUTY` |
| Web-service privileges (SCM) | `PO_MANAGE_PURCHASE_ORDER_WEB_SERVICE_PRIV`, `PO_SEARCH_PURCHASE_ORDER_WEB_SERVICE_PRIV`, `POZ_MANAGE_SUPPLIER_BY_WEB_SERVICE_PRIV` |
| Sandbox privilege | `FND_ADMINISTER_SANDBOX_PRIV` |

## Troubleshooting 403 / privilege issues (procedure)
1. Identify user and exact resource/operation; read REST error body (code, e.g. FND-, POZ-, PO-).
2. Security Console > Users > user > roles (direct + inherited) or SCIM `GET /hcmRestApi/scim/Users?filter=userName eq "X"`.
3. Security Console > Roles > role > Function Security Policies: search privilege code (e.g. the web-service privilege from the service doc).
4. Run User and Role Access Audit Report for the user (needs Import job fresh) to list function + data policies.
5. Compare Users against a working user to find missing role.
6. Data issue (200 but empty / "no access"): check data security policies, BU assignment (`bu-data-access.md`), Procurement agent/BU access.
7. Just-assigned roles: run Import then Retrieve Latest LDAP Changes; users re-sign in.
8. Custom role copied from predefined may miss privileges added by Oracle in updates: compare with source role.
9. Integration accounts: OAuth/JWT user must hold the role itself (see `access-and-roles.md`).

## Common mistakes
- Looking for a REST endpoint to create roles (none documented).
- Editing function policies of predefined roles (not allowed) instead of copying.
- Forgetting to assign users to the copied role.
- Scheduling Send Pending LDAP Requests too early in implementation (can't run on demand afterwards).
- Reports empty because Import not run.
- Enabling audit before configuring business objects (audit stays inactive).

## Channel & exact technique
- Preferred channel: D for role creation/copy and data policies (no API found); A (SCIM) for user/role assignment and read; C-like ESS submit for sync processes (`ess_submit`, names above; job paths UNVERIFIED).
- A: `/hcmRestApi/scim/Users|Roles`, `/hcmRestApi/resources/11.13.18.05/userAccounts`.
- D: playbook `playbooks/` to create/copy role in Security Console (Copy Role > option > Basic Information > Function Security Policies > Data Security Policies > Role Hierarchy > Users > Summary and Impact Report > Submit).

## How to verify
Role appears on Roles tab, Role Status Completed; SCIM Roles filter by code; test user calls the previously failing resource.

## Sources
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/facsa/role-copying-or-editing.html — copy/edit rules, steps
- https://docs.oracle.com/en/cloud/saas/applications-common/26b/faser/configure-the-security-console.html — sync processes, console administration, role prefix/suffix
- https://docs.oracle.com/en/cloud/saas/readiness/erp/26d/fins26d/26D-fin-wn-f51477.htm — 26D role sync steps
- https://docs.oracle.com/en/cloud/saas/applications-common/25c/facia/set-up-auditing-for-oracle-fusion-applications.html — audit setup (25C)
- https://docs.oracle.com/en/cloud/saas/sales/oscus/user-role-membership-report.html — User Role Membership Report
- https://docs.oracle.com/en/cloud/saas/human-resources/ochus/enable-audit-for-oracle-platform-security-services.html — audit privileges (HCM)
- https://docs.oracle.com/en/cloud/saas/applications-common/26c/facsa/securing-applications.pdf and 26A PDF — Compare Users, Role Analytics, User and Role Access Audit Report (snippets only)

## UNVERIFIED
- Any REST/SCIM operation to create/copy roles or add privileges/data policies (none found).
- Exact ESS job definition paths/parameters for Import User and Role Application Security Data, Retrieve Latest LDAP Changes, Send Pending LDAP Requests.
- 26D report names for "Data Role and Security Profiles" reports (HCM) and exact location of User Password Changes Audit Report in 26D.
- Privilege to copy roles (IT Security Manager implied; specific privilege not named in the 26D page).
- Sign-in audit configuration for 26D (only HCM page seen).
- "Administer Security" style privilege names: not confirmed.
