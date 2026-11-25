"""User / role administration: find roles, read a user's roles, add/remove roles (SCIM), grant data access.
knowledge/users-roles.md, bu-data-access.md, access-and-roles.md. Needs IT Security Manager on the agent user."""
from __future__ import annotations

import datetime as dt
import json

from .client import ROOT, FusionError, get_client
from .generic import write

SCIM = "/hcmRestApi/scim"


def _safe(value: str) -> str:
    if '"' in value:
        raise ValueError('value must not contain a double quote')
    return value.strip()


def _user(user_name: str) -> dict:
    res = get_client().request("GET", f"{SCIM}/Users", params={"filter": f'userName eq "{_safe(user_name)}"'})
    users = res.get("Resources") or []
    if not users:
        raise LookupError(f"user {user_name!r} not found")
    return users[0]


def _role_id(code: str) -> dict | None:
    res = get_client().request("GET", f"{SCIM}/Roles",
                               params={"filter": f'name eq "{_safe(code)}"', "attributes": "id,name,displayName"})
    return (res.get("Resources") or [None])[0]


def find_role(text: str, limit: int = 25) -> dict:
    """Search roles by part of the code or display name, e.g. 'Inventory', 'ORA_PO_', 'Cost Accountant'.
    Returns code (name), displayName and SCIM id. Works for any role (job, abstract, data, custom)."""
    t = _safe(text)
    try:
        res = get_client().request("GET", f"{SCIM}/Roles", params={
            "filter": f'name co "{t}" or displayName co "{t}"', "attributes": "id,name,displayName", "count": limit})
    except FusionError as e:
        return e.to_dict()
    return {"count": len(res.get("Resources") or []),
            "roles": [{"code": r.get("name"), "name": r.get("displayName"), "id": r.get("id")} for r in res.get("Resources") or []]}


def user_roles(user_name: str, filter_text: str = "") -> dict:
    """List a user's roles (code + name). filter_text keeps only roles whose code/name contains it (case-insensitive)."""
    try:
        u = _user(user_name)
    except (FusionError, LookupError) as e:
        return e.to_dict() if isinstance(e, FusionError) else {"error": True, "message": str(e)}
    roles = [{"code": r.get("value"), "name": r.get("displayName")} for r in u.get("roles") or []]
    if filter_text:
        f = filter_text.lower()
        roles = [r for r in roles if f in (r["code"] or "").lower() or f in (r["name"] or "").lower()]
    return {"user": u.get("userName"), "user_id": u.get("id"), "active": u.get("active"),
            "total_roles": len(u.get("roles") or []), "roles": roles}


def assign_roles(user_name: str, role_codes: list[str], remove: bool = False, dry_run: bool = True,
                 confirm_prod: str = "") -> dict:
    """Add (or remove=True: revoke) roles for ANY user via SCIM PATCH /Roles/{id} members ADD|REMOVE.
    HIGH-IMPACT: show the before/after and get the user's confirmation first. Roles the user already has (add) or
    does not have (remove) are skipped. A live run backs up the user's current roles to backups/<date>/ first and
    re-reads the user afterwards. Data access (BU / inventory org / cost org) is separate: grant_data_access."""
    try:
        u = _user(user_name)
    except (FusionError, LookupError) as e:
        return e.to_dict() if isinstance(e, FusionError) else {"error": True, "message": str(e)}
    have = {r.get("value") for r in u.get("roles") or []}
    op = "REMOVE" if remove else "ADD"
    plan, skipped, unknown = [], [], []
    for code in dict.fromkeys(c.strip() for c in role_codes if c.strip()):
        if (code in have) != remove:
            skipped.append(code)
            continue
        role = _role_id(code)
        if role is None:
            unknown.append(code)
        else:
            plan.append(role)
    out: dict = {"user": u["userName"], "operation": op, "skipped": skipped, "unknown_codes": unknown,
                 "to_change": [{"code": r["name"], "name": r.get("displayName")} for r in plan]}
    if dry_run or not plan:
        return {"dry_run": dry_run, **out}
    backup = ROOT / "backups" / f"{dt.date.today():%Y-%m-%d}" / f"security-{u['userName']}-roles-before-{dt.datetime.now():%H%M%S}.json"
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text(json.dumps({"pod": get_client().base, "user": u["userName"], "id": u["id"],
                                  "roles": sorted(have)}, indent=1), encoding="utf-8")
    results = []
    for r in plan:
        res = write(f"scim_role_{op.lower()}", "PATCH", f"{SCIM}/Roles/{r['id']}",
                    {"members": [{"value": u["id"], "operation": op}]}, dry_run=False, confirm_prod=confirm_prod,
                    validate=False)
        results.append({"code": r["name"], "result": "OK" if res.get("ok") else f"ERROR {res.get('status')}: {res.get('message', '')[:200]}"})
    now = {r.get("value") for r in _user(user_name).get("roles") or []}
    out.update(backup=str(backup), results=results,
               verified=all((r["name"] in now) != remove for r in plan), roles_before=len(have), roles_after=len(now))
    return out


def grant_data_access(user_name: str, role_code: str, security_context: str, values: list[str],
                      dry_run: bool = True, confirm_prod: str = "") -> dict:
    """Give a user's role data access (REST dataSecurities POST, one row per value). The role must already be
    assigned. security_context as stored on the pod: 'Business unit' (value = BU name), 'Inventory organization'
    (value = org code), 'Reference data set', 'Cost organization'… Revoke later with
    rest_update('dataSecurities/<UserRoleDataAssignmentId>', {'ActiveFlag': False})."""
    rows = []
    for v in values:
        res = write("data_access_add", "POST", "dataSecurities",
                    {"UserName": user_name, "RoleCommonName": role_code, "SecurityContext": security_context,
                     "SecurityContextValue": v}, dry_run=dry_run, confirm_prod=confirm_prod, validate=False)
        rows.append({"value": v, "result": "dry_run" if res.get("dry_run") else
                     ("OK" if res.get("ok") else f"ERROR {res.get('status')}: {res.get('message', '')[:200]}"),
                     "id": (res.get("ids") or {}).get("UserRoleDataAssignmentId")})
    return {"user": user_name, "role": role_code, "context": security_context, "rows": rows}


# REST resource -> (roles that grant it, data-access context it usually also needs). From knowledge/access-and-roles.md.
# shortcut: best-known mapping per resource; if a 403 survives the grant, use find_role + the area's knowledge file.
_INV = ["ORA_INV_INVENTORY_MANAGER_JOB"]
_BUY = ["ORA_PO_BUYER_JOB"]
ROLE_MAP: dict[str, tuple[list[str], str]] = {
    **{r: (["ORA_POZ_SUPPLIER_MANAGER_ABSTRACT", "ORA_POZ_SUPPLIER_ADMINISTRATOR_ABSTRACT"], "Business unit")
       for r in ("suppliers", "supplierNumbering", "supplierOptions", "procurementApprovedSupplierListEntries")},
    "procurementAgents": (["ORA_PO_PROCUREMENT_MANAGER_JOB", "ORA_PO_PROCUREMENT_APPLICATION_ADMIN_JOB"], "Business unit"),
    **{r: (["ORA_PO_PROCUREMENT_APPLICATION_ADMIN_JOB"], "") for r in ("purchasingDocumentStyles", "purchasingLineTypes")},
    **{r: (["ORA_POR_PROCUREMENT_REQUESTER_ABSTRACT"], "Business unit") for r in ("purchaseRequisitions",)},
    **{r: (_BUY, "Business unit") for r in ("requisitionProcessingRequests", "draftPurchaseOrders", "purchaseOrders",
                                            "draftPurchaseAgreements", "purchaseAgreements", "purchaseAgreementImportRequests")},
    **{r: (["ORA_INV_WAREHOUSE_MANAGER_JOB"], "Inventory organization")
       for r in ("receivingReceiptRequests", "receivingReceiptExpectedShipmentLines")},
    **{r: (_INV, "Inventory organization") for r in (
        "inventoryOrganizations", "subinventories", "inventoryTransactions", "inventoryStagedTransactions",
        "onhandQuantityDetails", "interOrganizationParameters", "interSubinventoryParameters", "unitsOfMeasure",
        "unitOfMeasureClasses", "cycleCountDefinitions", "cycleCountTransactions", "physicalInventories",
        "subinventoryItems", "supplyRequests", "transferOrders")},
    **{r: (["ORA_EGI_PRODUCT_DATA_STEWARD_JOB"], "") for r in ("itemsV2", "itemBatches", "itemCatalogs", "itemCategories")},
    **{r: (["ORA_WSH_SHIPPING_MANAGER_JOB"], "Inventory organization") for r in (
        "carriers", "shippingParameters", "releaseRules", "pickWaves", "pickTransactions", "shipmentLines",
        "shipmentLineChangeRequests", "shipmentTransactionRequests")},
    **{r: (["ORA_CST_COST_ACCOUNTANT_JOB"], "Cost organization")
       for r in ("standardCosts", "itemCosts", "costScenarios", "costScenariosV2", "costAdjustments")},
    **{r: (["ORA_DOO_ORDER_MANAGER_JOB"], "Business unit") for r in ("salesOrdersForOrderHub", "salesOrderActionRequests")},
    "supplierNegotiations": (["ORA_PON_CATEGORY_MANAGER_JOB"], "Business unit"),
    "erpintegrations": (["ORA_FND_INTEGRATION_SPECIALIST_JOB"], ""),
    **{r: (["ORA_ASM_APPLICATION_IMPLEMENTATION_CONSULTANT_JOB", "ORA_ASM_FUNCTIONAL_SETUPS_USER_ABSTRACT"], "")
       for r in ("setupTasks", "setupTaskCSVExports", "setupTaskCSVImports", "setupOfferingCSVExports", "setupOfferingCSVImports")},
    "locationsV2": (["ORA_PER_HUMAN_RESOURCE_SPECIALIST_JOB"], ""),
    **{r: (["ORA_FND_IT_SECURITY_MANAGER_JOB"], "") for r in ("dataSecurities", "Users", "Roles", "userAccounts")},
}


def ensure_access(resource_path: str, dry_run: bool = True, confirm_prod: str = "") -> dict:
    """Self-heal a 403: find the roles that grant `resource_path` (e.g. 'suppliers/1/child/sites',
    '/hcmRestApi/resources/11.13.18.05/locationsV2', 'carriers') and add the missing ones to the AGENT'S OWN user
    (the profile's ORACLE_USERNAME). Add-only. dry_run=True shows what is missing. Also returns the data-access
    context the role usually needs (grant it with grant_data_access for the BU / org of the current job).
    Needs IT Security Manager on the agent user. Follow the self-grant rule in CLAUDE.md before a live run."""
    segs = [s for s in resource_path.split("?")[0].strip("/").split("/") if s]
    if "scim" in segs:  # /hcmRestApi/scim/Users -> Users
        key = segs[segs.index("scim") + 1]
    elif "resources" in segs:  # .../resources/11.13.18.05/<root>/...
        key = segs[segs.index("resources") + 2]
    else:  # relative fscm path: root resource is the first segment
        key = segs[0]
    if key not in ROLE_MAP:
        return {"resource": key, "known": False,
                "hint": "No mapping. Use find_role + knowledge/access-and-roles.md (or the area file) to pick the role, "
                        "then assign_roles(<agent user>, [...])."}
    roles, context = ROLE_MAP[key]
    me = get_client().info().get("user") or ""
    current = user_roles(me)
    if current.get("error"):
        return {"resource": key, "error": True, "message": f"cannot read roles of {me!r}", "detail": current}
    have = {r["code"] for r in current["roles"]}
    missing = [r for r in roles if r not in have]
    out = {"resource": key, "agent_user": me, "roles_needed": roles, "missing": missing,
           "data_access_context": context or None}
    if not missing:
        out["hint"] = ("Roles already present. If still 403: data access is missing"
                       + (f" (grant_data_access with context '{context}')" if context else "")
                       + ", the user is not a procurement agent on the BU, or Fusion has not refreshed the session yet "
                         "(retry after a minute).")
        return out
    if dry_run:
        return {"dry_run": True, **out}
    return {**out, "grant": assign_roles(me, missing, dry_run=False, confirm_prod=confirm_prod)}


TOOLS = [find_role, user_roles, assign_roles, grant_data_access, ensure_access]
