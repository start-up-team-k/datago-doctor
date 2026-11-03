import json
import pathlib

import pytest

from datago_doctor import diagnose

FX = pathlib.Path(__file__).parent / "fixtures"
MAN = json.loads((FX / "manifest.json").read_text(encoding="utf-8"))

# fixture -> (code, layer)
EXPECT = {
    "live_nokey.xml": ("20", "gateway"),
    "live_badkey.xml": ("30", "gateway"),
    "live_badop.xml": ("12", "gateway"),
    "live_badsvc.xml": ("12", "gateway"),
    "live_http.xml": ("30", "gateway"),
    "live_json.json": ("30", "gateway"),
    "live_noparams.xml": ("30", "gateway"),
    "live_encbad.xml": ("30", "gateway"),
    "issue_pdr2_99.xml": ("99", "provider"),
    "issue_pharmacy8_401_key_null.xml": ("20", "gateway"),
    "issue_pharmacy8_403_not_registered.xml": ("30", "gateway"),
    "kpubdata_gateway_key_not_registered.xml": ("30", "gateway"),
    "kpubdata_gateway_quota_exceeded.xml": ("22", "gateway"),
    "kpubdata_gateway_unregistered_ip.xml": ("32", "gateway"),
    "kpubdata_xml_auth_30.xml": ("30", "provider"),
    "kpubdata_rate_limit_22.json": ("22", "provider"),
    "kpubdata_invalid_request_10.json": ("10", "provider"),
    "kpubdata_service_unavailable_01.json": ("01", "provider"),
    "synthetic_html_502.html": ("HTTP-502", "html"),
    "synthetic_html_504.html": ("HTTP-504", "html"),
    "synthetic_text_unauthorized.txt": ("HTTP-401", "http"),
    "synthetic_text_api_not_found.txt": ("HTTP-404", "http"),
    "synthetic_pdr66_99.xml": ("99", "provider"),
    "synthetic_ok_provider.xml": ("OK", "provider"),
    "synthetic_ok_json.json": ("OK", "provider"),
    "synthetic_garbage.txt": ("UNKNOWN", "unknown"),
}


def test_every_fixture_is_listed():
    assert set(EXPECT) == set(MAN)
    assert len([n for n in MAN if not n.startswith("synthetic")]) >= 10


@pytest.mark.parametrize("name", sorted(EXPECT))
@pytest.mark.parametrize("as_bytes", [True, False])
def test_fixture(name, as_bytes):
    raw = (FX / name).read_bytes()
    d = diagnose(MAN[name]["status"], {}, raw if as_bytes else raw.decode("utf-8"))
    assert (d.code, d.layer) == EXPECT[name]
    if d.code == "UNKNOWN":
        assert "issues" in d.fix
