import importlib.util
from pathlib import Path

import httpx
import pytest
import respx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("setup_env", ROOT / "scripts" / "setup_env.py")
setup_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_env)

POD = "https://pod.example.com"


@pytest.fixture
def root(tmp_path):
    (tmp_path / ".env.example").write_text((ROOT / ".env.example").read_text())
    return tmp_path


def test_save_creates_from_example(root):
    setup_env.save_profile(root, "test", POD + "/fscmUI/faces/x", "hcm_impl", "pw1")
    cfg = dotenv_values(root / ".env.test")
    assert cfg["ORACLE_BASE_URL"] == POD + "/fscmUI/faces/x"
    assert cfg["ORACLE_USERNAME"] == "hcm_impl" and cfg["ORACLE_PASSWORD"] == "pw1"
    assert cfg["ORACLE_ENV_NAME"] == "TEST" and cfg["ORACLE_AUTH_MODE"] == "basic"


def test_save_keeps_password_when_empty(root):
    setup_env.save_profile(root, "test", POD, "u1", "old#pw")
    setup_env.save_profile(root, "test", POD, "u2", "")
    cfg = dotenv_values(root / ".env.test")
    assert cfg["ORACLE_USERNAME"] == "u2" and cfg["ORACLE_PASSWORD"] == "old#pw"


@pytest.mark.parametrize("pw", ["a#b c", "it's", r"back\slash", r"x\'y", '"dq"'])
def test_password_round_trips(root, pw):
    setup_env.save_profile(root, "test", POD, "u1", pw)
    assert dotenv_values(root / ".env.test")["ORACLE_PASSWORD"] == pw


def test_save_rejects_http_url(root):
    setup_env.save_profile(root, "test", POD, "u1", "pw")
    before = (root / ".env.test").read_text()
    for bad in ("http://pod.example.com", "pod.example.com", ""):
        with pytest.raises(ValueError):
            setup_env.save_profile(root, "test", bad, "u1", "pw")
    with pytest.raises(ValueError):
        setup_env.save_profile(root, "../x", POD, "u1", "pw")
    assert (root / ".env.test").read_text() == before


def test_connection_reports_401(root):
    setup_env.save_profile(root, "test", POD, "u1", "bad")
    with respx.mock(assert_all_called=False) as r:
        r.get(url__startswith=POD).mock(return_value=httpx.Response(401, json={}))
        ok, msg = setup_env.test_connection(root, "test")
    assert not ok and "401" in msg


def test_connection_ok(root):
    setup_env.save_profile(root, "test", POD, "u1", "good")
    with respx.mock(assert_all_called=False) as r:
        r.get(url__startswith=POD).mock(return_value=httpx.Response(200, json={"items": [], "count": 0}))
        ok, msg = setup_env.test_connection(root, "test")
    assert ok and "u1" in msg


def test_password_never_in_page(root):
    setup_env.save_profile(root, "test", POD, "u1", "S3cret!")
    html = setup_env.render_form(root, "test", token="t", note="")
    assert "S3cret!" not in html and "u1" in html and POD in html
