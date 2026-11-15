import json

import httpx
import pytest

from oracle_fusion_mcp import client, generic, smoke

from .conftest import HCM_URL, describe, make_client

SUP_DESC = describe("suppliers", [
    {"name": "SupplierId", "type": "integer", "updatable": False},
    {"name": "Supplier", "type": "string", "mandatory": True},
    "TaxOrganizationType", "BusinessRelationship",
], children={"sites": ["SupplierSite", "ProcurementBU"]})


def test_collection_of():
    assert generic.collection_of("suppliers") == "suppliers"
    assert generic.collection_of("suppliers/1") == "suppliers"
    assert generic.collection_of("suppliers/1/child/sites") == "suppliers/1/child/sites"
    assert generic.collection_of("suppliers/1/child/sites/2") == "suppliers/1/child/sites"
    assert generic.collection_of("/hcmRestApi/resources/11.13.18.05/locationsV2/9") == "/hcmRestApi/resources/11.13.18.05/locationsV2"
    assert generic.q_str("O'Brien") == "'O''Brien'"


def test_parse_error_codes(fusion):
    fusion.get("/suppliers").respond(400, json={"title": "Bad", "o:errorDetails": [
        {"detail": "POZ-2130403 You must provide a valid address.", "o:errorCode": "POZ-2130403"}]})
    out = generic.rest_get("suppliers")
    assert out["error"] and out["status"] == 400
    assert out["oracle_codes"] == ["POZ-2130403"]
    assert "valid address" in out["message"]


def test_pagination_and_links_stripped(fusion):
    fusion.get("/suppliers", params={"offset": "0"}).respond(
        200, json={"items": [{"SupplierId": 1, "links": [1]}], "hasMore": True})
    fusion.get("/suppliers", params={"offset": "1"}).respond(200, json={"items": [{"SupplierId": 2}], "hasMore": False})
    out = generic.rest_get("suppliers", limit=1, all_pages=True)
    assert out["count"] == 2 and out["items"][0] == {"SupplierId": 1}


def test_disconnect_blocks_calls_until_reconnect(fusion):
    client._state["mode"] = "auto"
    client.disconnect()
    with pytest.raises(RuntimeError, match="Agent is off"):
        client.get_client()
    assert client.get_mode() == "confirm"
    client.set_client(make_client())  # what switch_environment does after load_profile
    assert client.get_client().env_name == "TEST"


def test_scim_get_sends_no_adf_params(fusion, monkeypatch):
    seen = {}
    monkeypatch.setattr(client.get_client(), "request",
                        lambda m, p, params=None, **kw: seen.update(path=p, params=params) or {"Resources": []})
    generic.rest_get('/hcmRestApi/scim/Users?filter=userName eq "X"', limit=5)
    assert seen["path"] == "/hcmRestApi/scim/Users"
    assert seen["params"] == {"filter": 'userName eq "X"', "count": 5, "startIndex": 1}


def test_get_retries_503_but_post_not_retried_on_502(fusion):
    route = fusion.get("/suppliers").mock(side_effect=[httpx.Response(503), httpx.Response(200, json={"items": []})])
    assert generic.rest_get("suppliers")["items"] == []
    assert route.call_count == 2
    post = fusion.post("/suppliers").respond(502)
    with pytest.raises(client.FusionError):
        client.get_client().request("POST", "suppliers", json_body={})
    assert post.call_count == 1


def test_describe_summary(fusion):
    fusion.get("/suppliers/describe").respond(200, json=describe("suppliers", ["Supplier"], item_actions=["inactivate"]))
    out = generic.rest_describe("suppliers/123")
    assert out["resource"] == "suppliers"
    assert out["attributes"] == ["Supplier:string"]
    assert out["custom_actions"] == [{"name": "inactivate", "parameters": []}]


def test_create_dry_run_does_not_send(fusion):
    fusion.get("/suppliers/describe").respond(200, json=SUP_DESC)
    post = fusion.post("/suppliers").respond(201, json={})
    out = generic.rest_create("suppliers", {"Supplier": "Nile Trading", "sites": [{"SupplierSite": "CAIRO"}]})
    assert out["dry_run"] is True and out["url"].endswith("/suppliers")
    assert out["field_check"]["errors"] == []
    assert post.call_count == 0


def test_unknown_field_blocked_with_suggestion(fusion):
    fusion.get("/suppliers/describe").respond(200, json=SUP_DESC)
    out = generic.rest_create("suppliers", {"Suplier": "X", "sites": [{"SiteName": "A"}]})
    assert out["blocked"]
    assert any("Suplier" in e and "Supplier" in e for e in out["field_check"]["errors"])
    assert any(e.startswith("sites[0].SiteName") for e in out["field_check"]["errors"])


def test_create_executes_and_audits_without_secrets(fusion):
    fusion.get("/suppliers/describe").respond(200, json=describe("suppliers", ["Supplier", "BankAccountNumber"]))
    fusion.post("/suppliers").respond(201, json={"SupplierId": 77, "SupplierNumber": "1001", "links": []})
    out = generic.rest_create("suppliers", {"Supplier": "Nile", "BankAccountNumber": "EG12345"}, dry_run=False)
    assert out["ok"] and out["ids"] == {"SupplierId": 77, "SupplierNumber": "1001"}
    log = next(fusion.log_dir.glob("audit-*.jsonl")).read_text(encoding="utf-8")
    assert "EG12345" not in log and '"BankAccountNumber": "***"' in log
    assert json.loads(log.splitlines()[0])["ids"]["SupplierId"] == 77


def test_prod_guard(fusion):
    client.set_client(make_client("PROD"))
    fusion.get("/suppliers/describe").respond(200, json=SUP_DESC)
    post = fusion.post("/suppliers").respond(201, json={"SupplierId": 1})
    with pytest.raises(PermissionError):
        generic.rest_create("suppliers", {"Supplier": "X"}, dry_run=False)
    assert post.call_count == 0
    assert generic.rest_create("suppliers", {"Supplier": "X"}, dry_run=False, confirm_prod="CONFIRM PROD")["ok"]
    with pytest.raises(PermissionError):
        client.set_mode("auto")


def test_action_uses_adf_action_content_type(fusion):
    route = fusion.post("/draftPurchaseOrders/55/action/submit").respond(200, json={"result": "SUCCESS"})
    out = generic.rest_action("draftPurchaseOrders/55", "submit", dry_run=False)
    assert out["ok"]
    assert route.calls[0].request.headers["content-type"] == "application/vnd.oracle.adf.action+json"


def test_delete_refused_without_explicit_request(fusion):
    assert generic.rest_delete("suppliers/1", dry_run=False)["blocked"]


def test_update_warns_read_only(fusion):
    fusion.get("/suppliers/describe").respond(200, json=SUP_DESC)
    out = generic.rest_update("suppliers/5", {"SupplierId": 9})
    assert "read-only" in out["field_check"]["warnings"][0]


def test_batch_shape(fusion):
    route = fusion.post("/").respond(200, json={"parts": []})
    parts = [{"id": "1", "path": "/suppliers", "operation": "create", "payload": {"Supplier": "A"}}]
    assert generic.rest_batch(parts, dry_run=False)["ok"]
    assert route.calls[0].request.headers["content-type"] == "application/vnd.oracle.adf.batch+json"
    assert generic.rest_batch([{"id": "x"}])["blocked"]


def test_smoke_reports_missing_privilege(fusion):
    fusion.get("/suppliers").respond(403, text="Forbidden")
    fusion.get(f"{HCM_URL}/locationsV2").respond(401, text="Unauthorized")
    fusion.route(host="pod.example.com").respond(200, json={"items": []})  # everything else OK (first match wins)
    rows = {r["area"]: r for r in smoke.smoke_test()["checks"]}
    assert rows["Suppliers"]["result"] == "MISSING PRIVILEGE" and "Supplier" in rows["Suppliers"]["needs"]
    assert rows["Locations"]["result"].startswith("AUTH FAILED")
    assert rows["Purchase orders"]["result"] == "OK"


def test_describe_disk_cache_survives_restart(fusion):
    route = fusion.get("/suppliers/describe").respond(200, json=describe("suppliers", ["Supplier"]))
    generic.rest_describe("suppliers")
    generic._describe_cache.clear()  # simulate a new MCP server process
    assert generic.rest_describe("suppliers")["attributes"] == ["Supplier:string"]
    assert route.call_count == 1
    generic.rest_describe("suppliers", refresh=True)
    assert route.call_count == 2
