# Units of Measure (UOM classes, UOMs, conversions, usages)

> Release: 26D · Last researched: 2026-11-14 · Status: PARTIAL

## Business purpose
- Each UOM belongs to a **UOM class**, for example Quantity, Weight or Volume.
- Each class has one **base UOM**. Make it the smallest unit. All conversions go through the base UOM.
- Conversion types:
  - **Standard (intraclass)**: UOM to base UOM, the same for all items (Dozen = 12 Each).
  - **Item-specific intraclass**.
  - **Interclass**: between the base UOMs of two classes, usually item-specific (1 Each = 4 Pound).
  - **Lot-specific**: lot UOM conversions.
- **UOM usages**: default stocking UOM per org, item and subinventory. Needs the "Enable Units of Measure Usages" feature.
- UOMs must exist before items are created or imported.

## Where in Fusion (FSM)
- Task **Manage Units of Measure**, with sub-pages Manage UOM Standard Conversions and Manage UOM Interclass Conversions. Also task **Manage Units of Measure for Interclass Conversion** (the docs search it from Tasks > Search).
  - Offering/functional area for Manage Units of Measure: UNVERIFIED. Quick Setup (Facilities functional area) can create UOM classes.
- Offering Manufacturing and Supply Chain Materials Management, Functional area **Inventory Management**, Task **Manage Units of Measure Usages**. Needs the feature opt-in.

## Prerequisites & dependencies
- None for classes and UOMs.
- Depends on this: items (`PrimaryUOMValue`), transactions, supply requests (`UOMCode`), interorg distance UOM, shipping weight/volume classes.

## Key fields
| Field (UI label) | REST attribute | Meaning | Notes |
|---|---|---|---|
| Class Code | `unitOfMeasureClasses.ClassCode` (req) | max 10 | |
| Class Name | `ClassName` (req) | max 10 | |
| Base UOM Code / Name | `BaseUOMCode` (req, max 3) / `BaseUnitOfMeasure` (req, max 25) | the base unit is created with the class | |
| UOM Code | `unitsOfMeasure.UOMCode` (req) | max 3 | |
| UOM Name | `UOM` (req) | max 25 | |
| Class | `UOMClass` (req) | the class **ClassId** value; or send `UOMClassName` | the doc example uses `UOMClass: 3222` |
| Base unit | `BaseUnitFlag` (req) | | |
| Conversion | `StandardConversion` (req) | rate to the base unit | |
| Descriptions | `Description`, `UOMPluralDescription`, `UOMReciprocalDescription` | | |
| End Date | `DisableDate`, `StandardConversionEndDate` | | |
| Intraclass (item) | `intraclassConversions`: `IntraclassConversion`, `InventoryItemId`, `InverseConversionFlag`, `InverseConversionRate`, `IntraclassConversionEndDate` | | |
| Interclass | `interclassConversions`: `FromUOMClassId`, `FromUOMCode`, `ToUOMClassId`, `ToUOMCode`, `InterclassConversion`, `InventoryItemId` / `ItemNumber`, `InverseConversionFlag`, `InverseConversionRate` | | |

## Common mistakes
- Base UOM that is not the smallest unit.
- The UOM code is max 3 characters. Codes are case-sensitive in examples ("Ea" vs "EA"); case behaviour itself is UNVERIFIED.
- Quick Setup cannot touch UOM classes that already exist. They are disabled to avoid overwrite.

## Channel & exact technique
- Preferred channel: **A (REST)**.
- A:
  - Classes: `GET|POST /fscmRestApi/resources/11.13.18.05/unitOfMeasureClasses`; `GET|PATCH|DELETE .../unitOfMeasureClasses/{ClassCode}`. Children: `interclassConversions` (GET/POST/PATCH `{InterclassConversionId}`), `dff`, `unitOfMeasureDFF`.
  - UOMs: `GET|POST /unitsOfMeasure`; `GET|PATCH|DELETE /unitsOfMeasure/{UOMCode}`. Children: `intraclassConversions` (GET/POST/PATCH `{ConversionId}`), `translatedData` (GET/PATCH), `dff`.
  - Conversion calculator: `POST /unitOfMeasureConversions` with `FromUOM`, `ToUOM`, `FromQuantity`, `ItemId`, `PrecisionFlag`. It returns `ConversionFactor`, `ToQuantity`, `ReturnStatus`, `ReturnMessage`. It computes; it does not persist setup.
  - Read-only: `itemUnitOfMeasureConversions` (GET), `orderableUnitsOfMeasureLOV`.
  - Lot conversions: `lotUnitOfMeasureConversions` (GET/POST/PATCH), `generateLotUnitOfMeasureConversions`.
  - Usages: `unitOfMeasureUsages` (GET/POST/PATCH/DELETE `{UomUsageId}`).
  - UOM POST example (doc): `{"UOMCode":"EA","UOMClass":3222,"UOM":"Each","Description":"Each","UOMReciprocalDescription":"Per Unit","UOMPluralDescription":"Each","BaseUnitFlag":true,"StandardConversion":1}`
- D (UI): Manage Units of Measure.

## How to verify
- `GET unitsOfMeasure/{UOMCode}?expand=intraclassConversions`
- `GET unitOfMeasureClasses/{ClassCode}`
- Test with `POST unitOfMeasureConversions` (FromUOM / ToUOM).

## Sources
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-unitofmeasureclasses-post.html — class attributes
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-unitsofmeasure-post.html — UOM attributes, example
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-unitsofmeasure-uomcode-child-intraclassconversions-post.html — intraclass
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-unitofmeasureclasses-classcode-child-interclassconversions-post.html — interclass
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/op-unitofmeasureconversions-post.html — conversion calculator
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/fasrp/rest-endpoints.html — methods and children
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faicf/implementing-common-features-for-scm.pdf — ch. 36 Units of Measure, ch. 22 Quick Setup UOM FAQ, ch. 35 "Define Units of Measure"
- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26d/faims/implementing-manufacturing-and-supply-chain-materials-management.pdf — ch. 7 Dual UOM (Manage Units of Measure / Interclass / Standard Conversions pages), ch. 8 Manage Units of Measure Usages

## UNVERIFIED
- Offering/functional area of the Manage Units of Measure task in 26D.
- Whether `UOMClass` accepts the ClassCode string or only the numeric ClassId (the doc says "value of the ClassId attribute").
- FSM CSV support for UOM setup.
