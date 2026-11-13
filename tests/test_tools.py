"""Shortcut, FSM, FBDI/ESS and bulk tools — mocked HTTP only."""
import base64
import io
import json
import zipfile

import httpx
from openpyxl import Workbook

from oracle_fusion_mcp import bulk, enterprise, fbdi, fsm, inventory, locations, procurement, suppliers

from .conftest import HCM_URL, describe

SUP = describe("suppliers", ["Supplier", "BusinessRelationshipCode", "TaxOrganizationTypeCode", "SupplierTypeCode",
                             "TaxpayerId", "TaxRegistrationNumber"],
               children={"sites": ["SupplierSite", "ProcurementBU", "SupplierAddressName", "SitePurposePurchasingFlag",
                                   "SitePurposePayFlag"]})


def test_create_supplier_dry_run_with_dup_check(fusion):
    fusion.get("/suppliers/describe").respond(200, json=SUP)
    dup = fusion.get("/suppliers").respond(200, json={"items": []})
    post = fusion.post("/suppliers").respond(201, json={})
    out = suppliers.create_supplier("Nile Trading", taxpayer_id="123")
    assert out["dry_run"] and out["payload"] == {"Supplier": "Nile Trading", "TaxpayerId": "123"}
    assert "TaxpayerId='123'" in dup.calls[0].request.url.params["q"]
    assert post.call_count == 0


def test_create_supplier_blocks_duplicate(fusion):
    fusion.get("/suppliers").respond(200, json={"items": [{"SupplierId": 1, "Supplier": "Nile Trading"}]})
    out = suppliers.create_supplier("Nile Trading")
    assert out["blocked"] and out["duplicates"][0]["SupplierId"] == 1


def test_create_supplier_site_path_and_fields(fusion):
    fusion.get("/suppliers/describe").respond(200, json=SUP)
    fusion.get("/suppliers/77/child/sites").respond(200, json={"items": []})
    post = fusion.post("/suppliers/77/child/sites").respond(201, json={"SupplierSiteId": 5})
    out = suppliers.create_supplier_site(77, "CAIRO", "Egypt Operations", "Cairo HQ", dry_run=False)
    assert out["ok"] and out["ids"] == {"SupplierSiteId": 5}
    sent = json.loads(post.calls[0].request.content)
    assert sent["ProcurementBU"] == "Egypt Operations" and sent["SupplierAddressName"] == "Cairo HQ"


def test_assign_site_defaults_bill_to_bu(fusion):
    fusion.get("/suppliers/describe").respond(200, json=describe("suppliers", ["Supplier"]))
    fusion.get("/suppliers/7/child/sites/8/child/assignments").respond(200, json={"items": []})
    out = suppliers.assign_site_to_bu(7, 8, "Egypt Operations")
    assert out["payload"] == {"ClientBU": "Egypt Operations", "BillToBU": "Egypt Operations"}


def test_procurement_agent_all_access_from_describe(fusion):
    fusion.get("/procurementAgents/describe").respond(200, json=describe("procurementAgents", [
        "AgentEmail", "ProcurementBU", "StatusCode", "ManageOrdersAllowedFlag", "AnalyzeSpendAllowedFlag",
        "AccessLevelToOtherAgentsOrders", "AccessLevelToOtherAgentsOrdersCode"]))
    fusion.get("/procurementAgents").respond(200, json={"items": []})
    out = procurement.create_procurement_agent("ahmed@x.com", "Egypt Operations")
    p = out["payload"]
    assert p["ManageOrdersAllowedFlag"] is True and p["AnalyzeSpendAllowedFlag"] is True
    assert p["AccessLevelToOtherAgentsOrdersCode"] == "FULL" and "AccessLevelToOtherAgentsOrders" not in p


def test_submit_purchase_order_action(fusion):
    route = fusion.post("/draftPurchaseOrders/300/action/submit").respond(200, json={"result": "SUCCESS"})
    assert procurement.submit_purchase_order(300, dry_run=False)["ok"]
    assert json.loads(route.calls[0].request.content) == {}


def test_create_location_resolves_set_id(fusion):
    fusion.get("/setIdSets").respond(200, json={"items": [{"SetId": 0, "SetCode": "COMMON"}]})
    fusion.get(f"{HCM_URL}/locationsV2/describe").respond(200, json=describe("locationsV2", [
        "SetCode", "SetId", "LocationCode", "LocationName", "EffectiveStartDate", "EffectiveEndDate", "ShipToSiteFlag",
        "ReceivingSiteFlag", "BillToSiteFlag", "OfficeSiteFlag"], children={"addresses": ["AddressLine1", "TownOrCity", "Country"]}))
    fusion.get(f"{HCM_URL}/locationsV2").respond(200, json={"items": []})
    out = locations.create_location("RUH-WH", "Riyadh Warehouse", "COMMON", "SA", "King Fahd Rd", "Riyadh", "2026-11-14")
    assert out["dry_run"] and out["payload"]["SetId"] == 0
    assert out["payload"]["addresses"] == [{"AddressLine1": "King Fahd Rd", "TownOrCity": "Riyadh", "Country": "SA"}]
    assert out["field_check"]["errors"] == []


def test_carrier_org_association_path(fusion):
    fusion.get("/carriers/describe").respond(200, json=describe("carriers", ["CarrierName"]))
    fusion.get("/carriers/9/child/shippingMethods/FS-AIR/child/organizationAssociations").respond(200, json={"items": []})
    out = inventory.enable_ship_method_on_org(9, "FS-AIR", "CAI")
    assert out["url"].endswith("/carriers/9/child/shippingMethods/FS-AIR/child/organizationAssociations")


def test_lookup_values_query(fusion):
    route = fusion.get("/standardLookupsLOV").respond(200, json={"items": [{"LookupCode": "AIR"}], "hasMore": False})
    assert enterprise.lookup_values("WSH_MODE_OF_TRANSPORT")["items"][0]["LookupCode"] == "AIR"
    assert route.calls[0].request.url.params["q"] == "LookupType='WSH_MODE_OF_TRANSPORT'"


def test_fsm_export_status_download(fusion, monkeypatch, tmp_path):
    monkeypatch.setattr(fsm, "ROOT", tmp_path)
    fusion.post("/setupTaskCSVExports").respond(201, json={"SetupTaskCSVExportProcess": [{"ProcessId": 42}]})
    base = "/setupTaskCSVExports/PER_MANAGE_LOCATIONS/child/SetupTaskCSVExportProcess/42"
    fusion.get(base).respond(200, json={"ProcessCompletedFlag": True})
    fusion.get(f"{base}/child/SetupTaskCSVExportProcessResult/42").respond(200, json={"StatusCode": "COMPLETED"})
    zipped = io.BytesIO()
    with zipfile.ZipFile(zipped, "w") as z:
        z.writestr("a.csv", "x")
    fusion.get(f"{base}/child/SetupTaskCSVExportProcessResult/42/enclosure/FileContent").respond(
        200, content=base64.b64encode(zipped.getvalue()))
    assert fsm.fsm_export("PER_MANAGE_LOCATIONS")["process_id"] == 42
    st = fsm.fsm_status("PER_MANAGE_LOCATIONS", 42)
    assert st["completed"] and st["result"]["StatusCode"] == "COMPLETED"
    saved = fsm.fsm_download("PER_MANAGE_LOCATIONS", 42)
    assert saved["saved"].endswith(".zip") and open(saved["saved"], "rb").read()[:2] == b"PK"


def test_fsm_import_dry_run(fusion, tmp_path):
    z = tmp_path / "x.zip"
    z.write_bytes(b"PK" + b"0" * 3000)
    post = fusion.post("/setupTaskCSVImports").respond(201, json={})
    out = fsm.fsm_import("PER_MANAGE_LOCATIONS", str(z))
    assert out["dry_run"] and post.call_count == 0
    assert "chars>" in out["payload"]["SetupTaskCSVImportProcess"][0]["FileContent"]


def _template(path):
    wb = Workbook()
    wb.active.title = "Instructions and CSV Generation"
    ws = wb.create_sheet("POZ_SUPPLIERS_INT")
    ws.append(["Supplier import"])
    ws.append([])
    ws.append(["*Import Action", "*Supplier Name", "Tax Registration Number"])
    wb.save(path)


def test_fbdi_build_zip_column_order(tmp_path, monkeypatch):
    monkeypatch.setattr(fbdi, "WORK", tmp_path / "work")
    t = tmp_path / "t.xlsx"
    _template(t)
    assert fbdi.fbdi_template_columns(str(t))["sheets"] == {"POZ_SUPPLIERS_INT": ["Import Action", "Supplier Name", "Tax Registration Number"]}
    out = fbdi.fbdi_build_zip(str(t), {"POZ_SUPPLIERS_INT": [{"Supplier Name": "Nile", "Import Action": "CREATE"}]}, "sup")
    with zipfile.ZipFile(out["zip"]) as z:
        assert z.read("PozSuppliersInt.csv").decode() == "CREATE,Nile,\n"
    bad = fbdi.fbdi_build_zip(str(t), {"POZ_SUPPLIERS_INT": [{"Suplier": "x"}]}, "bad")
    assert bad["blocked"]


def test_fbdi_import_dry_run_account(fusion, tmp_path):
    z = tmp_path / "s.zip"
    z.write_bytes(b"PK")
    out = fbdi.fbdi_import(str(z), "prc/supplier/import", "/oracle/apps/ess/prc/poz/supplierImport,ImportSuppliers", "NEW,N")
    assert out["dry_run"] and out["payload"]["DocumentAccount"] == "prc$/supplier$/import$"


def test_ess_status_parses_details(fusion):
    fusion.get("/erpintegrations").mock(side_effect=[
        httpx.Response(200, json={"items": [{"RequestStatus": "SUCCEEDED"}]}),
        httpx.Response(200, json={"items": [{"RequestStatus": json.dumps({"JOBS": {"STATUS": "SUCCEEDED"}})}]}),
    ])
    out = fbdi.ess_status(55)
    assert out["status"] == "SUCCEEDED" and out["jobs"]["JOBS"]["STATUS"] == "SUCCEEDED"


def test_bulk_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(bulk, "ROOT", tmp_path)
    src = tmp_path / "in.csv"
    src.write_text("Supplier,TaxpayerId\nNile,123\n,\n", encoding="utf-8")
    rows = bulk.bulk_read_file(str(src))
    assert rows["count"] == 1 and rows["rows"][0]["Supplier"] == "Nile"  # blank row skipped
    rep = bulk.bulk_write_report("suppliers load", [{"row": 2, "status": "OK", "BankAccountNumber": "EG1"}])
    assert rep["rows"] == 1 and "suppliers-load-" in rep["report"]
