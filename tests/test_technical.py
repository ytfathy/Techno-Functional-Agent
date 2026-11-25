"""Technical-consultant tools (BI Publisher, workflow) — mocked HTTP only."""
import base64
import json
import re

import httpx

from oracle_fusion_mcp import bi, workflow

from .conftest import BASE

BPM = f"{BASE}/bpm/api/4.0/tasks"
BIP = f"{BASE}{bi.REPORT_SVC}"


def _soap(inner: str, status: int = 200) -> httpx.Response:
    return httpx.Response(status, text=f'<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope"><env:Body>{inner}</env:Body></env:Envelope>',
                          headers={"content-type": "application/soap+xml"})


def test_run_report_csv_preview_masked(fusion, monkeypatch, tmp_path):
    monkeypatch.setattr(bi, "ROOT", tmp_path)
    csv_bytes = b"SUPPLIER,BANK_ACCOUNT_NUMBER\nNile,EG123\n"
    route = fusion.post(BIP).mock(return_value=_soap(
        f'<ns2:runReportResponse xmlns:ns2="{bi.PUB}"><ns2:runReportReturn><ns2:reportBytes>'
        f'{base64.b64encode(csv_bytes).decode()}</ns2:reportBytes></ns2:runReportReturn></ns2:runReportResponse>'))
    out = bi.bi_run_report("/Custom/AI/Sup.xdo", {"P_BU": "US1 Business Unit", "P_X": ["a", "b"]})
    sent = route.calls[0].request.content.decode()
    assert "<pub:reportAbsolutePath>/Custom/AI/Sup.xdo</pub:reportAbsolutePath>" in sent
    assert "<pub:name>P_X</pub:name><pub:values><pub:item>a</pub:item><pub:item>b</pub:item>" in sent
    assert route.calls[0].request.headers["content-type"].startswith("application/soap+xml")
    assert out["row_count"] == 1 and out["preview"] == [{"SUPPLIER": "Nile", "BANK_ACCOUNT_NUMBER": "***"}]
    saved = open(out["saved"], encoding="utf-8").read()
    assert "EG123" not in saved and "***" in saved  # saved file is masked too


def test_run_report_soap_fault(fusion):
    fusion.post(BIP).mock(return_value=_soap(
        "<env:Fault><env:Reason><env:Text>Report not found</env:Text></env:Reason></env:Fault>", 500))
    out = bi.bi_run_report("/Custom/missing.xdo")
    assert out["error"] and out["message"] == "Report not found"


def test_wf_tasks_validates_and_trims(fusion):
    assert workflow.wf_tasks(assignment="EVERYONE")["error"]
    route = fusion.get(BPM).respond(200, json={"items": [{"number": "200", "title": "Approve Requisition 1001",
                                                          "state": "ASSIGNED", "noise": "x"}], "hasMore": False})
    out = workflow.wf_tasks(assignment="admin", status="errored", keyword="1001")
    assert out["tasks"] == [{"number": "200", "title": "Approve Requisition 1001", "state": "ASSIGNED"}]
    assert route.calls[0].request.url.params["assignment"] == "ADMIN"


def test_wf_task_with_history(fusion):
    fusion.get(f"{BPM}/200").respond(200, json={"number": "200", "state": "ASSIGNED",
                                                "actionList": [{"actionId": "APPROVE"}, {"actionId": "REJECT"}]})
    fusion.get(f"{BPM}/200/history").respond(200, json={"items": [{"actionName": "ASSIGN", "userId": "MGR1"}]})
    out = workflow.wf_task("200")
    assert out["actions"] == ["APPROVE", "REJECT"] and out["history"][0]["userId"] == "MGR1"


def test_wf_task_action_dry_run_and_reassign(fusion):
    put = fusion.put(f"{BPM}/200").respond(200, json={"outcome": "APPROVE"})
    dry = workflow.wf_task_action("200", "approve", "ok")
    assert dry["dry_run"] and put.call_count == 0
    assert workflow.wf_task_action("200", "REASSIGN")["blocked"]
    live = workflow.wf_task_action("200", "REASSIGN", reassign_to_user="FIN_MGR", dry_run=False)
    assert live["ok"]
    assert json.loads(put.calls[0].request.content)["action"] == {"id": "REASSIGN", "assignees": [{"id": "FIN_MGR", "type": "USER"}]}


def test_soap_call_read_and_write_guards(fusion):
    from oracle_fusion_mcp import generic
    url = f"{BASE}/fscmService/PurchaseOrderServiceV2"
    route = fusion.post(url).mock(return_value=_soap("<ns:getPurchaseOrderResponse xmlns:ns='urn:x'><ns:result>ok</ns:result></ns:getPurchaseOrderResponse>"))
    env = lambda op: f'<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Body><t:{op} xmlns:t="urn:x"/></soap:Body></soap:Envelope>'
    read = generic.soap_call("/fscmService/PurchaseOrderServiceV2", env("getPurchaseOrder"), read_only=True)
    assert read["ok"] and "ok" in read["response_xml"] and route.call_count == 1
    assert generic.soap_call("/fscmService/PurchaseOrderServiceV2", env("cancelPurchaseOrder"), read_only=True)["blocked"]
    assert generic.soap_call("/fscmService/PurchaseOrderServiceV2", env("cancelPurchaseOrder"))["dry_run"]
    assert route.call_count == 1
    assert generic.soap_call("/x", "not xml")["error"]


def test_check_select_blocks_writes():
    assert bi.check_select("select 1 from dual; ") == "select 1 from dual"
    assert bi.check_select("WITH a AS (SELECT CREATED_BY, DELETE_FLAG FROM t) SELECT * FROM a")
    for bad in ["delete from po_headers_all", "select 1 from dual; drop table x", "begin null; end;",
                "select dbms_xmlgen.getxml('x') from dual", "update t set a=1", "select * into x from t"]:
        try:
            bi.check_select(bad)
            raise AssertionError(bad)
        except ValueError:
            pass


def test_bi_sql_runs_runner_and_masks(fusion, monkeypatch, tmp_path):
    monkeypatch.setattr(bi, "ROOT", tmp_path)
    inner = "<ROWSET><ROW><SEGMENT1>1001</SEGMENT1><IBAN>EG99</IBAN></ROW></ROWSET>"
    from xml.sax.saxutils import escape
    xml = f"<DATA_DS><G_1><RESULT_XML>{escape(inner)}</RESULT_XML></G_1></DATA_DS>".encode()
    route = fusion.post(BIP).mock(return_value=_soap(
        f'<ns2:runReportResponse xmlns:ns2="{bi.PUB}"><ns2:reportBytes>{base64.b64encode(xml).decode()}</ns2:reportBytes></ns2:runReportResponse>'))
    out = bi.bi_sql("select segment1, iban from po_headers_all", max_rows=10)
    assert out["preview"] == [{"SEGMENT1": "1001", "IBAN": "***"}]
    sent = route.calls[0].request.content.decode()
    b64 = re.search(r"<pub:item>([A-Za-z0-9+/=]+)</pub:item>", sent).group(1)
    assert base64.b64decode(b64).decode() == "SELECT * FROM (select segment1, iban from po_headers_all) WHERE ROWNUM <= 10"
    assert "/Custom/AI_SCM_AGENT/SQL_RUNNER.xdo" in sent
    assert bi.bi_sql("delete from x")["blocked"]


def test_catalog_list_and_deploy_guards(fusion, tmp_path):
    url = f"{BASE}{bi.CATALOG_SVC}"
    route = fusion.post(url).mock(return_value=httpx.Response(200, text=(
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"><soapenv:Body><r><item>'
        '<absolutePath>/Custom/AI/A.xdo</absolutePath><type>Report</type><displayName>A</displayName></item></r>'
        '</soapenv:Body></soapenv:Envelope>')))
    out = bi.bi_catalog_list("/Custom/AI")
    assert out["items"] == [{"absolutePath": "/Custom/AI/A.xdo", "type": "Report", "displayName": "A", "lastModified": None}]
    assert route.calls[0].request.headers["content-type"].startswith("text/xml")
    f = tmp_path / "a.xdoz"
    f.write_bytes(b"PK")
    dry = bi.bi_deploy_object(str(f), "/Custom/AI/A.xdo", "xdo")
    assert dry["dry_run"] and "pw" not in json.dumps(dry)
    assert bi.bi_deploy_object(str(f), "/Shared Folders/Procurement/A.xdo", "xdo")["blocked"]
    assert bi.bi_deploy_object(str(f), "/Custom/AI/A.xdo", "zip")["blocked"]
