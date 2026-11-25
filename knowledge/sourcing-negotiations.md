# Sourcing: Negotiations (RFQ / RFI / Auction) lifecycle

> Release: 26D · Last researched: 2026-11-25 · Status: PARTIAL
> Setup of styles/templates/BU function is in `knowledge/negotiation-styles.md`. This file covers running a negotiation via REST and the roles.

## Business purpose
A negotiation (Request for Quote, Request for Information, Auction) lets a category manager invite suppliers, collect responses, score, and award to create POs / blanket agreements / contracts. Affects: category managers, buyers, suppliers, requesters (award can reference requisition lines), contracts.

## Where in Fusion (FSM)
- Offering **Procurement** > Functional area **Sourcing**: **Manage Negotiation Styles** (see negotiation-styles.md). Other Sourcing setup (Redwood in 26D): Manage Cost Factors, Manage Cost Factor Lists, Manage Sourcing Notifications, Manage Procurement Category Hierarchy. Not yet Redwood: Negotiation Styles, Line Attribute Lists, Supplier Negotiation Approval Rules, Supplier Negotiation Award Approval Rules.
- Sourcing BU settings: **Configure Procurement Business Function** (Sourcing tab: defaults for negotiation type, style, rank indicator, max requirement score; feature controls incl. negotiation and award approvals - 26D What's New). There is no separate "Configure Sourcing Business Function" task found. 26D Using Procurement lists "Define Sourcing Configuration" under Manage Supplier Negotiations (task list name; contents UNVERIFIED).
- Runtime work area: Procurement > Negotiations (Redwood sourcing pages need `ORA_PON_SOURCING_REDWOOD_ENABLED`).
- Scope: Procurement BU (`ProcurementBUId` required on create).

## Prerequisites & dependencies
1. Procurement BU with Sourcing/Procurement business function configured (`dependencies.md`: BU, Configure Procurement Business Function).
2. Negotiation style (and optionally template, attribute list, cost factors, terms and conditions, abstracts) - see negotiation-styles.md. Style needed for `NegotiationStyleId`/`NegotiationStyle`.
3. Active suppliers with sites/contacts (supplier flow) for invitation; supplier users with sourcing supplier roles to respond. Procurement agent for the BU (needed for awards creating POs: privileges `PO_CREATE_PURCHASE_ORDER_PRIV` / `PO_CREATE_PURCHASE_AGREEMENT_PRIV`).
4. Category manager user with Category Manager job role and access to the Procurement BU.
5. Approval rules (Supplier Negotiation Approval Rules / Award Approval Rules, BPM, UI-only) if approvals enabled.
Depends on this: POs, blanket agreements, contract terms created from award.

## Roles
- **Category Manager** job role, code `ORA_PON_CATEGORY_MANAGER_JOB` (25C page; 26B page shows name only). Duties include Negotiation Management, Negotiation Update, Negotiation Viewing, Negotiation Response Evaluation, Negotiation Award, Negotiation Contract Management, Sourcing Administration (templates, styles, attribute lists, cost factor lists), Sourcing Program Management, Seller Negotiation duties.
- **Sourcing Project Collaborator**: abstract role (26D security overview). Role code UNVERIFIED. Used to assign people to the negotiation collaboration team for scoring/evaluation.
- Privileges seen: `PON_CREATE_SUPPLIER_NEGOTIATION_PRIV`, `PON_COMPLETE_SUPPLIER_NEGOTIATION_AWARD_PRIV` (REST: FinalizeAward, notify award decision), `PON_MANAGE_SUPPLIER_NEGOTIATION_TEMPLATE_PRIV`. Others UNVERIFIED (25C/26B names only: Submit Supplier Negotiation, Award Supplier Negotiation, Score Supplier Negotiation Response, Disqualify..., Close/Extend...).

## Key fields (`supplierNegotiations` create body)
| Field (UI label) | REST attribute | Meaning | Notes / typical value |
|---|---|---|---|
| Procurement BU | `ProcurementBUId` (required, int64), `ProcurementBU` | Owning BU | only attribute marked required |
| Title | `NegotiationTitle` | max 80 | |
| Type | `NegotiationType` / `NegotiationTypeId` | RFQ / RFI / Auction | |
| Style | `NegotiationStyle` / `NegotiationStyleId` | Style | |
| Template | `NegotiationTemplate` | used with action CreateNegotiationFromTemplate | |
| Outcome | `Outcome`; award `CurrentOutcomeCode` = STANDARD, BLANKET, CONTRACT | PO type to create | |
| Currency | `Currency`, `CurrencyCode`, `PricePrecision` | | |
| Open / Close / Preview / Award-by | `OpenDate`, `CloseDate`, `PreviewDate`, `AwardByDate` (date-time); flags `OpenImmediatelyFlag`, `PreviewImmediatelyFlag` | | |
| Buyer | `Buyer`, `BuyerId` | negotiation owner | |
| Requisitioning BU | `RequisitioningBU`, `RequisitioningBUId` | | |
| Invite only | `RestrictToInvitedSuppliersFlag` | | |
| Multiple responses / revision | `AllowMultipleResponsesFlag`, `AllowResponseRevisionFlag`, `AllowAlternateLinesFlag`, `RequireFullQuantityFlag`, `RespondOnAllLinesFlag` | | |
| Approval | `NegApprovalEnabledFlag`, `ApprovalAmount` | | |
| Scoring | `EnableTeamScoringFlag`, `TeamScoringEnabledFlag`, `CompositeScoreEnabledFlag`, `EnableRequirementWeightsFlag`, `TwoStageEvaluationFlag`, `OverallRankingMethodCode`, `RankIndicatorCode` | | |
| Contract terms | `ContractTermsEnabledFlag`, `ContractTermsLayout` | | |
| Agreement | `AgreementAmount`, `AgreementStartDate`, `AgreementEndDate`, `MinimumReleaseAmount` | for BPA outcome | |
| Synopsis, intro text | `Synopsis`, `GeneralIntroductionText`, `CoverPageText` | | |
Doc caveats: a few booleans carry odd maxLength; `AutonomousAward` typed string. Test fields.

Child resources of `supplierNegotiations/{supplierNegotiationsUniqID}/child/`: `lines`, `suppliers`, `sections`, `collaborationTeamMembers`, `attachments`, `negotiationOwners`, `negotiationRecommendedSuppliers`, `scoringTeams`, `projects`, `projectTasks`, `internalCostFactors`, `lineDefaultAttributeGroups`, `responseCurrencies`, `negotiationActivities`, `negotiationVersions`, `submittedProcesses`, `publishNegotiationErrors`, `importLinesErrors`, `DFF`, `supplierDFF`, `surrogateShortListSuppliers`, `supplierActivities`, `templateUsages`, `threads`, `abstracts`, `awardAttachments`, others (see source).
Supplier invitation: `POST .../child/suppliers` body (all nullable): `SupplierId`, `Supplier`, `SupplierSiteId`, `SupplierSite`, `SupplierContactId`, `SupplierContact`, `NotifyAllSupplierContactsFlag`, `RequestedSupplier`, `RequestedSupplierId`, `RequestedSupplierContactId`, `AdditionalContactEmail`, `ResponseCurrencyCode`, `RestrictedLineAccess` (+ `supplierLineAccessRestrictions`). Doc example sends Supplier, SupplierId, SupplierSite, SupplierSiteId, SupplierContact, SupplierContactId, NotifyAllSupplierContactsFlag.

## Actions
`supplierNegotiations` (path `/fscmRestApi/resources/11.13.18.05/supplierNegotiations`):
- Collection actions: `CreateNegotiation`, `CreateNegotiationFromTemplate`, `AddCategoriesToGenerateRequirements`, `GenerateSupplierRecommendations` (not supported).
- Instance actions `.../{supplierNegotiationsUniqID}/action/`: **`ValidateAndPublishNegotiation`** (publish/open), **`NegotiationTimeManagementActions`** (cancel/close/extend/pause/resume), `CompleteNegotiation`, `CompleteStageOneNegotiation`, `ReopenStageOneNegotiation`, `CreateNewRound`, `CreateAmendment`, `DuplicateNegotiation`, `CopyNegotiationToTemplate`, `DeleteDraftNegotiation`, `DeleteCanceledNegotiation`, `UnlockDraft`, `UnlockSupplierNegotiation`, `UnsealSupplierNegotiation`, `lockSupplier`, `unlockSupplier`, `NotifyAdditionalSuppliers`, `ReassignOwner`, `GetSurrogateResponseList`, `openScoring`, `closeScoring`, `submitResponseScores`, `CalculateTeamScoringProgress`, `AddQuestions`, `AddQualificationAreas`, `AddProjectTasks`, `addContractTerms`, `GenerateNegotiationPdf`, `ImportLinesSpreadsheet`, `GenerateAddLinesSpreadsheet`, `ExportRequirementsSpreadsheet`, `ImportRequirementsSpreadsheet`, `RenumberLines`, `recordInternalActivity` (60 operations in total).
`supplierNegotiationResponses` (read/evaluate, GET all/one, PATCH): actions `DisqualifyResponse` (collection-level), `OverrideScore`, `ResetOverriddenScore`, `DownloadResponsePdf`, `ExportResponseSpreadsheet`, `initializeTeamMemberScoring`, `InitializeProcess`, `SubmitProcess`, `ClearProcess`. Children: Lines, Attachments, Sections, Purchasing Documents, Response Line Prices, Response Lines Rank Summaries, Scoring Attachments, Team Member Score Details. Responses are created by suppliers (or surrogate in UI), not via this resource.
`supplierNegotiationAwards` (key = `AuctionHeaderId`): GET all not supported; use `?finder=PrimaryKey;AuctionHeaderId=<id>` with `expand=lines,responses,recommendedResponses`. Actions `/{AuctionHeaderId}/action/`: `GenerateRecommendedAward`, `ApplyRecommendedAward`, `ApplyDefaultAward`, `ApplyKnockoutCriteria`, `AddNewSupplierItemInItemRelationship`, `ClearAward`, `FinalizeAward`, `ReopenAward`, `SubmitAwardForApproval` (body `Buyer`, `BuyerId`), `EditAndWithdrawAwardApproval`, `ShareAwardDecision`, `AwardActionsStatus`, `AwardSummaryAttributes`, `RecommendAwardSummaryAttributes`, `ExportAwardSpreadsheet`, `ImportAwardSpreadsheet`, `InitializeAwardProcess`. Action media type `application/vnd.oracle.adf.action+json`, body `{"parameters":{...}}` (string values). Award attributes: `AwardStatus`, `AwardApprovalStatus`, `AwardDate`, `CurrentOutcomeCode`, `Negotiation`, `NegotiationTitle`, `ProcurementBUId`.
Other: `supplierNegotiationsLOV`, `negotiationStatusesLOV`, `supplierNegotiationCostFactorListsLOV`, supplier negotiation templates resource (`supplierNegotiationTemplates`, seen only as cost factor child page in 26D search; ops UNVERIFIED), `bidderSellerNegotiations` (seller-side, forward auctions).

## Common mistakes
- Awarding before closing / without scoring complete; ValidateAndPublish not called, negotiation stays Draft.
- Posting `suppliers` and `lines` deep in the same create payload with errors; create header, then children.
- Using GET all on `supplierNegotiationAwards`.
- Invitee supplier without site/contact: no notification, supplier cannot respond.
- No procurement agent / purchase privileges for award-to-PO.
- Inactive template or style.
- Expect REST for style/template setup: none.

## Channel & exact technique
- Preferred channel: **A (REST)** for create / invite / publish / award. D (UI) only for setup (styles, templates, approval rules) and for supplier-side responses in test.
- A flow (rest_describe first on each resource):
  1. `POST supplierNegotiations` (or action `CreateNegotiationFromTemplate`) with `ProcurementBUId`, `NegotiationTitle`, `NegotiationType`, `NegotiationStyle`, dates, `Currency`.
  2. `POST .../child/lines`; `POST .../child/suppliers` (invite); optional `collaborationTeamMembers`, `sections`.
  3. `POST .../action/ValidateAndPublishNegotiation`.
  4. Wait until `CloseDate`; or `NegotiationTimeManagementActions`. Read `supplierNegotiationResponses` (`q=` by negotiation) and score.
  5. `supplierNegotiationAwards`: `GenerateRecommendedAward` / `ApplyRecommendedAward` -> `SubmitAwardForApproval` (if approvals) -> `FinalizeAward` -> `ShareAwardDecision`; PO created via the award's purchasing document flow (resource `Purchasing Documents` child of responses; staged document actions require PO privileges).
- B: UNVERIFIED (no CSV for runtime negotiations). Sourcing BU defaults: REST `procurementBusinessFunctions` (see negotiation-styles.md).
- C: none found for negotiations (Category Manager has "Upload data for Supplier Negotiation Import" duty; import template name UNVERIFIED).
- D: playbook not yet written (`playbooks/` none).

## How to verify
- `GET supplierNegotiations?q=NegotiationTitle='...'&fields=Negotiation,NegotiationTitle,ProcurementBUId` then check status via `negotiationStatusesLOV`/negotiation record.
- After award: `GET supplierNegotiationAwards?finder=PrimaryKey;AuctionHeaderId=...&fields=AuctionHeaderId,Negotiation,AwardStatus` and the resulting PO.

## Sources
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-supplier-negotiations.html - 60 operations, actions, child list
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliernegotiations-post.html - create body attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliernegotiations-suppliernegotiationsuniqid-child-suppliers-post.html - invitation body
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-supplier-negotiation-responses.html - response resource operations
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/api-supplier-negotiation-award-responses.html - 19 award operations
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliernegotiationawards-get.html - PrimaryKey finder, award attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliernegotiationawards-auctionheaderid-action-shareawarddecision-post.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliernegotiationawards-auctionheaderid-action-generaterecommendedaward-post.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/op-suppliernegotiationawards-auctionheaderid-action-submitawardforapproval-post.html
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/Roles_and_Privileges.html - `PON_COMPLETE_SUPPLIER_NEGOTIATION_AWARD_PRIV`, `PON_CREATE_SUPPLIER_NEGOTIATION_PRIV`
- https://docs.oracle.com/en/cloud/saas/procurement/26b/oapcm/Category_Manager_job_roles.html - Category Manager duties/privileges
- https://docs.oracle.com/en/cloud/saas/procurement/25c/faopb/Category-Manager-JR-132.html - `ORA_PON_CATEGORY_MANAGER_JOB` (25C, via search snippet)
- https://docs.oracle.com/en/cloud/saas/applications-common/26d/faser/overview-of-security-for-oracle-fusion-cloud-procurement.html - Sourcing Project Collaborator is an abstract role (snippet)
- https://docs.oracle.com/en/cloud/saas/readiness/scm/26d/proc26d/26D-procurement-wn-f49538.htm - Sourcing tab of procurement business function (snippet)
- https://docs.oracle.com/en/cloud/saas/procurement/26d/fapra/rest-endpoints.html - LOV resources, `bidderSellerNegotiations` (only first 200k chars scanned)

## UNVERIFIED
- Request body of CreateNegotiation / CreateNegotiationFromTemplate actions and of `lines` POST (not fetched; describe on pod).
- Minimum payload for a working RFQ (docs only mark `ProcurementBUId` required; style/type likely needed at runtime).
- Role code for Sourcing Project Collaborator; Category Manager code confirmed only for 25C.
- Privileges for Manage Negotiation Styles, scoring/close/extend operations.
- `supplierNegotiationTemplates` operations; template creation by REST (only CopyNegotiationToTemplate action seen).
- How the PO is created from the award (which resource/action; child `Purchasing Documents` of responses suggested); not read.
- ESS jobs related to negotiations; FBDI/import template for negotiations; Setup Task CSV for Sourcing tasks.
- Whether "Define Sourcing Configuration" is a real FSM task in 26D.
- Paths for `supplierNegotiationResponses` response creation by supplier (not a REST create here).
