"""Read-only smoke test: one GET per functional area, tells which role/privilege is missing on 401/403."""
from __future__ import annotations

from .client import HCM, FusionError, get_client

# (area, path, params, role that grants it) — role codes: knowledge/access-and-roles.md
CHECKS: list[tuple[str, str, dict, str]] = [
    ("Business units", "finBusinessUnitsLOV", {"limit": 1}, "Application Implementation Consultant (ORA_ASM_APPLICATION_IMPLEMENTATION_CONSULTANT_JOB)"),
    ("Locations", f"{HCM}/locationsV2", {"limit": 1}, "Human Resource Specialist / Application Implementation Consultant (location privileges)"),
    ("Suppliers", "suppliers", {"limit": 1}, "Supplier Administrator / Supplier Manager"),
    ("Procurement agents", "procurementAgents", {"limit": 1}, "Procurement Application Administrator (ORA_PO_PROCUREMENT_APPLICATION_ADMIN_JOB)"),
    ("Requisitions", "purchaseRequisitions", {"limit": 1}, "Procurement Requester / Buyer + requisitioning BU data access"),
    ("Purchase orders", "purchaseOrders", {"limit": 1}, "Buyer (ORA_PO_BUYER_JOB) + procurement agent record for the BU"),
    ("Draft purchase orders", "draftPurchaseOrders", {"limit": 1}, "Buyer (ORA_PO_BUYER_JOB) + procurement agent record for the BU"),
    ("Inventory organizations", "inventoryOrganizations", {"limit": 1}, "Inventory Manager (ORA_INV_INVENTORY_MANAGER_JOB) + inventory org data access"),
    ("Items", "itemsV2", {"limit": 1}, "Product Manager / Inventory Manager (item read privileges)"),
    ("Units of measure", "unitsOfMeasure", {"limit": 1}, "Inventory Manager / Application Implementation Consultant"),
    ("FSM setup CSV", "setupTaskCSVExports", {"limit": 1}, "Application Implementation Consultant (setup export/import privileges)"),
    ("ERP integrations / ESS", "erpintegrations", {"finder": "ESSJobStatusRF;requestId=1"}, "Integration Specialist (ORA_FND_INTEGRATION_SPECIALIST_JOB)"),
    ("Users (SCIM)", "/hcmRestApi/scim/Users", {"count": 1}, "IT Security Manager (only needed for user/role tasks)"),
]


def smoke_test() -> dict:
    """Run one read-only GET per area against the active environment and report access per area."""
    client = get_client()
    rows = []
    for area, path, params, role in CHECKS:
        try:
            client.request("GET", path, params=params, retries=1)
            rows.append({"area": area, "result": "OK"})
        except FusionError as e:
            if e.status in (401, 403):
                verdict = "AUTH FAILED (check credentials)" if e.status == 401 else "MISSING PRIVILEGE"
                rows.append({"area": area, "result": verdict, "status": e.status, "needs": role})
            elif e.status == 400:
                # authorized; only this probe's query/finder was rejected
                rows.append({"area": area, "result": f"REACHABLE (HTTP 400: {e.message[:120]})"})
            elif e.status == 404:
                rows.append({"area": area, "result": "NOT FOUND (resource name differs on this release? check rest_describe)"})
            else:
                rows.append({"area": area, "result": f"ERROR HTTP {e.status}: {e.message[:200]}"})
        except Exception as e:  # network / config problems
            rows.append({"area": area, "result": f"ERROR {type(e).__name__}: {e}"})
    ok = sum(r["result"] == "OK" for r in rows)
    return {"env": client.info(), "passed": f"{ok}/{len(rows)}", "checks": rows}
