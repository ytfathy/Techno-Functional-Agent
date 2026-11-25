"""User/role administration tools — mocked SCIM + dataSecurities."""
import json

import httpx

from oracle_fusion_mcp import security

from .conftest import BASE

USERS = f"{BASE}/hcmRestApi/scim/Users"
ROLES = f"{BASE}/hcmRestApi/scim/Roles"
ROLE_IDS = {"ORA_INV_INVENTORY_MANAGER_JOB": "R1", "ORA_PO_BUYER_JOB": "R2"}


def _user(roles):
    return httpx.Response(200, json={"Resources": [{"id": "U1", "userName": "HCM", "active": True,
                                                    "roles": [{"value": r, "displayName": r} for r in roles]}]})


def _roles(request):
    flt = request.url.params["filter"]
    if flt.startswith("name eq"):
        code = flt.split('"')[1]
        found = [{"id": ROLE_IDS[code], "name": code, "displayName": code}] if code in ROLE_IDS else []
        return httpx.Response(200, json={"Resources": found})
    return httpx.Response(200, json={"Resources": [{"id": "R1", "name": "ORA_INV_INVENTORY_MANAGER_JOB",
                                                    "displayName": "Inventory Manager"}]})


def test_find_role(fusion):
    route = fusion.get(ROLES).mock(side_effect=_roles)
    out = security.find_role("Inventory")
    assert out["roles"][0]["code"] == "ORA_INV_INVENTORY_MANAGER_JOB"
    assert route.calls[0].request.url.params["filter"] == 'name co "Inventory" or displayName co "Inventory"'


def test_user_roles_filter(fusion):
    fusion.get(USERS).mock(return_value=_user(["ORA_PO_BUYER_JOB", "ORA_PER_EMPLOYEE_ABSTRACT"]))
    out = security.user_roles("HCM", filter_text="buyer")
    assert out["total_roles"] == 2 and out["roles"] == [{"code": "ORA_PO_BUYER_JOB", "name": "ORA_PO_BUYER_JOB"}]


def test_assign_roles_dry_run_skips_held_and_unknown(fusion):
    fusion.get(USERS).mock(return_value=_user(["ORA_PO_BUYER_JOB"]))
    fusion.get(ROLES).mock(side_effect=_roles)
    patch = fusion.patch(url__startswith=ROLES).respond(204)
    out = security.assign_roles("HCM", ["ORA_PO_BUYER_JOB", "ORA_INV_INVENTORY_MANAGER_JOB", "ORA_NOPE"])
    assert out["dry_run"] and out["skipped"] == ["ORA_PO_BUYER_JOB"] and out["unknown_codes"] == ["ORA_NOPE"]
    assert [r["code"] for r in out["to_change"]] == ["ORA_INV_INVENTORY_MANAGER_JOB"]
    assert patch.call_count == 0


def test_assign_roles_live_backs_up_and_verifies(fusion, monkeypatch, tmp_path):
    monkeypatch.setattr(security, "ROOT", tmp_path)
    fusion.get(USERS).mock(side_effect=[_user([]), _user(["ORA_INV_INVENTORY_MANAGER_JOB"])])
    fusion.get(ROLES).mock(side_effect=_roles)
    patch = fusion.patch(f"{ROLES}/R1").respond(204)
    out = security.assign_roles("HCM", ["ORA_INV_INVENTORY_MANAGER_JOB"], dry_run=False)
    assert out["results"] == [{"code": "ORA_INV_INVENTORY_MANAGER_JOB", "result": "OK"}] and out["verified"]
    assert json.loads(patch.calls[0].request.content) == {"members": [{"value": "U1", "operation": "ADD"}]}
    assert json.loads(open(out["backup"], encoding="utf-8").read())["roles"] == []


def test_remove_role(fusion, monkeypatch, tmp_path):
    monkeypatch.setattr(security, "ROOT", tmp_path)
    fusion.get(USERS).mock(side_effect=[_user(["ORA_PO_BUYER_JOB"]), _user([])])
    fusion.get(ROLES).mock(side_effect=_roles)
    patch = fusion.patch(f"{ROLES}/R2").respond(204)
    out = security.assign_roles("HCM", ["ORA_PO_BUYER_JOB", "ORA_INV_INVENTORY_MANAGER_JOB"], remove=True, dry_run=False)
    assert out["skipped"] == ["ORA_INV_INVENTORY_MANAGER_JOB"] and out["verified"]
    assert json.loads(patch.calls[0].request.content)["members"][0]["operation"] == "REMOVE"


def test_grant_data_access_rows(fusion):
    post = fusion.post("/dataSecurities").respond(201, json={"UserRoleDataAssignmentId": 7})
    out = security.grant_data_access("HCM", "ORA_PO_BUYER_JOB", "Business unit", ["US1 Business Unit"], dry_run=False)
    assert out["rows"] == [{"value": "US1 Business Unit", "result": "OK", "id": 7}]
    assert json.loads(post.calls[0].request.content)["RoleCommonName"] == "ORA_PO_BUYER_JOB"


def test_user_not_found(fusion):
    fusion.get(USERS).respond(200, json={"Resources": []})
    assert security.assign_roles("NOBODY", ["X"])["error"]


def test_ensure_access_maps_child_path_and_lists_missing(fusion):
    fusion.get(USERS).mock(return_value=_user(["ORA_POZ_SUPPLIER_MANAGER_ABSTRACT"]))
    out = security.ensure_access("suppliers/1/child/sites")
    assert out["dry_run"] and out["resource"] == "suppliers" and out["agent_user"] == "AI_SCM_AGENT"
    assert out["missing"] == ["ORA_POZ_SUPPLIER_ADMINISTRATOR_ABSTRACT"] and out["data_access_context"] == "Business unit"


def test_ensure_access_live_grants_only_missing(fusion, monkeypatch):
    fusion.get(USERS).mock(return_value=_user([]))
    calls = []
    monkeypatch.setattr(security, "assign_roles", lambda u, codes, **kw: calls.append((u, codes, kw)) or {"verified": True})
    out = security.ensure_access("/hcmRestApi/resources/11.13.18.05/locationsV2/9", dry_run=False)
    assert calls == [("AI_SCM_AGENT", ["ORA_PER_HUMAN_RESOURCE_SPECIALIST_JOB"], {"dry_run": False, "confirm_prod": ""})]
    assert out["grant"]["verified"]


def test_ensure_access_unknown_and_already_present(fusion):
    assert security.ensure_access("someNewResource")["known"] is False
    fusion.get(USERS).mock(return_value=_user(["ORA_FND_INTEGRATION_SPECIALIST_JOB"]))
    out = security.ensure_access("erpintegrations")
    assert out["missing"] == [] and "data access" in out["hint"]
