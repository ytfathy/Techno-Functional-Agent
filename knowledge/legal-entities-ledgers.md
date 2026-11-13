# Legal Entities & Ledgers (read-only lookup)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
Legal entities (LE) and primary ledgers are needed as inputs when a BU gets a business function that creates financial transactions (Requisitioning, Receiving, Materials Management, Payables Invoicing, ...). The SCM agent only **reads** them to fill the Primary Ledger / Default Legal Entity fields; creating them is Financials scope.

## Where in Fusion (FSM)
- Legal entity: Functional area **Legal Structures**, task **Manage Legal Entity** (HDL referenced-objects table). Rapid impl: Manage Legal Addresses, Manage Legal Entities, Manage Legal Entity Registrations.
- Ledger: Define Accounting Configurations (Create a Primary Ledger, Specify Ledger Options, Assign Legal Entities and Balancing Segments).
- Rapid: "Create Chart of Accounts, Ledger, Legal Entities, and Business Units in Spreadsheet".

## Prerequisites & dependencies
- Ledger needs COA, calendar, currency. LE assigned to ledger via Assign Legal Entities and Balancing Segments.
- Used by: `business-units` (Assign Business Function → Financial Reporting: Primary Ledger, Default Legal Entity).

## Key fields
| Field (UI label) | REST attribute | Meaning | Notes |
|---|---|---|---|
| Legal Entity Name | `Name` (legalEntitiesLOV, 240) | | |
| (id) | `LegalEntityId` (int64) | | Matches `finBusinessUnitsLOV.LegalEntityId` (string there) |
| Legal Entity Identifier | `LegalEntityIdentifier` (30) | | |
| Start/End Date | `EffectiveFrom` / `EffectiveTo` | | |
| (party) | `PartyId` | | |
| Ledger Name | `Name` (ledgersLOV, 30) | | |
| (id) | `LedgerId` | | Matches `finBusinessUnitsLOV.PrimaryLedgerId` |
| Ledger category | `LedgerCategoryCode` | Primary / Secondary / ALC | Filter Primary for BU |
| Ledger type | `LedgerTypeCode` | Ledger / Ledger Set | |
| Currency | `CurrencyCode` | | |
| Calendar | `PeriodSetName`, `AccountedPeriodType` | | |
| COA | `ChartOfAccountsId` | | |

## Common mistakes
- Picking a secondary/ALC ledger or a ledger set as BU primary ledger — filter `LedgerCategoryCode` = primary and `LedgerTypeCode` = ledger (exact stored codes UNVERIFIED).
- Default LE not assigned to the chosen ledger — use `LedgerFinder` on legalEntitiesLOV.
- LOVs are data-security filtered: an empty result can mean missing access, not missing data.

## Channel & exact technique
- Preferred channel: **A (REST, read-only)**.
- `GET /fscmRestApi/resources/11.13.18.05/legalEntitiesLOV` — finders `KeywordFinder` (SearchTerm), `LedgerFinder` (LedgerId, SearchTerm), `PrimaryKey` (LegalEntityId). All attributes read-only.
- `GET /fscmRestApi/resources/11.13.18.05/ledgersLOV` — finders `KeywordFinder` (SearchTerm), `PrimaryKey` (LedgerId), `OpenPeriodLedgerFinder` and `EncumPeriodLedgerFinder` (BindAccessSetId, BindDefaultPeriodName, SearchTerm). All read-only.
- Example: `.../legalEntitiesLOV?finder=LedgerFinder;LedgerId=<id>&onlyData=true`
- Write: out of scope (Financials). No channel defined.

## How to verify
Compare IDs with `finBusinessUnitsLOV` (PrimaryLedgerId, LegalEntityId) after assigning business functions.

## Sources
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-legalentitieslov-get.html — legalEntitiesLOV path, finders, attributes
- https://docs.oracle.com/en/cloud/saas/financials/26d/farfa/op-ledgerslov-get.html — ledgersLOV path, finders, attributes
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/business-functions.html — functions needing ledger + LE
- https://docs.oracle.com/en/cloud/saas/human-resources/fahdl/how-you-define-referenced-objects.html — Legal Entity | Legal Structures | Manage Legal Entity
- https://docs.oracle.com/en/cloud/saas/procurement/26d/oapro/enterprise-structure-for-procurement-rapid-implementation.html — rapid impl tasks

## UNVERIFIED
- UNVERIFIED: Stored code values of `LedgerCategoryCode` (e.g. `PRIMARY`) and `LedgerTypeCode` (e.g. `L`) — doc gives only display meanings.
- UNVERIFIED: Whether ledgersLOV returns all ledgers or only those in the caller's data access sets.
- UNVERIFIED: Writable REST for legal entities/ledgers (not researched; out of scope).
