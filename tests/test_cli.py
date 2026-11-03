import io
import json
import pathlib
import ssl
import urllib.error

import pytest

from datago_doctor import check_key, cli, from_response

FX = pathlib.Path(__file__).parent / "fixtures"
KEY = "SECRETKEYabc123+/=zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
ENC = "SECRETKEYabc123%2B%2F%3Dzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
URL = "https://apis.data.go.kr/1613000/X/y?a=1"


class FakeResp:
    def __init__(self, status, body, ctype="application/xml"):
        self.status, self.body, self.headers = status, body, {"Content-Type": ctype}

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def patch_urlopen(monkeypatch, replies):
    """replies: list of (status, body) or exceptions, consumed in order. Returns the list of called URLs."""
    calls, it = [], iter(replies)

    def fake(req, timeout=None):
        calls.append(req.full_url)
        r = next(it)
        if isinstance(r, Exception):
            raise r
        status, body = r
        if status >= 400:
            raise urllib.error.HTTPError(req.full_url, status, "err", {"Content-Type": "application/xml"}, io.BytesIO(body))
        return FakeResp(status, body)

    monkeypatch.setattr("urllib.request.urlopen", fake)
    return calls


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    cli._secrets.clear()
    monkeypatch.delenv("DATAGO_SERVICE_KEY", raising=False)


def test_explain_file_exit_codes(capsys):
    assert cli.main(["explain", str(FX / "live_badkey.xml"), "--status", "403"]) == 1
    assert "[30]" in capsys.readouterr().out
    assert cli.main(["explain", str(FX / "synthetic_ok_provider.xml")]) == 0
    assert cli.main(["explain", str(FX / "no-such-file")]) == 2
    assert cli.main(["bogus"]) == 2


def test_explain_stdin_json(monkeypatch, capsys):
    class In:
        buffer = io.BytesIO((FX / "kpubdata_rate_limit_22.json").read_bytes())

    monkeypatch.setattr("sys.stdin", In)
    assert cli.main(["explain", "-", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["code"] == "22"


def test_check_masks_key_everywhere(monkeypatch, capsys):
    monkeypatch.setenv("DATAGO_SERVICE_KEY", KEY)
    # the server even echoes the key back: it must still be hidden
    body = (FX / "live_badkey.xml").read_bytes().replace(b"</cmmMsgHeader>", b"<echo>" + KEY.encode() + b"</echo></cmmMsgHeader>")
    calls = patch_urlopen(monkeypatch, [(403, body)] * 4)
    for extra in ([], ["--json"]):
        assert cli.main(["check", URL] + extra) == 1
        cap = capsys.readouterr()
        for stream in (cap.out, cap.err):
            for form in (KEY, ENC, KEY[4:]):
                assert form not in stream
        assert "SECR***" in cap.out
    assert len(calls) == 4  # 2 calls per check run (original + other encoding)
    assert "serviceKey=SECRETKEYabc123%2B%2F%3D" in calls[0]


def test_check_key_in_url_warns_and_masks(monkeypatch, capsys):
    calls = patch_urlopen(monkeypatch, [(200, (FX / "synthetic_ok_provider.xml").read_bytes())])
    assert cli.main(["check", URL + "&serviceKey=" + ENC]) == 0
    cap = capsys.readouterr()
    assert ENC not in cap.out + cap.err and "경고" in cap.err
    assert len(calls) == 1


def test_check_max_three_calls_and_http_needs_flag(monkeypatch, capsys):
    monkeypatch.setenv("DATAGO_SERVICE_KEY", KEY)
    err = urllib.error.URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))
    calls = patch_urlopen(monkeypatch, [err])
    assert cli.main(["check", URL]) == 1
    out = capsys.readouterr().out
    assert "SSL_ERROR" in out and "--allow-http" in out and len(calls) == 1
    calls = patch_urlopen(monkeypatch, [err, (200, (FX / "synthetic_ok_provider.xml").read_bytes())])
    assert cli.main(["check", URL, "--allow-http"]) == 0
    assert calls[1].startswith("http://") and len(calls) == 2


def test_check_alt_encoding_succeeds(monkeypatch, capsys):
    monkeypatch.setenv("DATAGO_SERVICE_KEY", KEY)
    calls = patch_urlopen(monkeypatch, [(403, (FX / "live_badkey.xml").read_bytes()), (200, (FX / "synthetic_ok_provider.xml").read_bytes())])
    assert cli.main(["check", URL]) == 0
    assert "%2B" in calls[0] and "%2B" not in calls[1]
    assert "인코딩 형태가 원인" in capsys.readouterr().out


def test_key_command_masks(monkeypatch, capsys):
    monkeypatch.setenv("DATAGO_SERVICE_KEY", '"' + ENC + ' "')
    assert cli.main(["key"]) == 1
    cap = capsys.readouterr()
    assert ENC not in cap.out + cap.err and "QUOTES" in cap.out
    monkeypatch.delenv("DATAGO_SERVICE_KEY")
    assert cli.main(["key"]) == 2


def test_check_key_findings():
    codes = lambda k: {f.code for f in check_key(k)}
    good = "a" * 64
    assert check_key(good) == []
    assert "DOUBLE_ENCODED" in codes("ab%252B" + good)
    assert "ENCODED" in codes(good + "%3D%3D") and "DECODED" in codes(good + "==")
    assert {"WHITESPACE", "QUOTES"} <= codes(' "' + good + '"\n')
    assert "INNER_WHITESPACE" in codes(good[:30] + "\n" + good[30:])
    assert "LENGTH" in codes("short") and "EMPTY" in codes("")
    assert "PREFIX" in codes("serviceKey=" + good)


def test_from_response_duck_typing():
    class R:
        status_code = 403
        headers = {"Content-Type": "application/xml"}
        content = (FX / "live_badkey.xml").read_bytes()

    assert from_response(R()).code == "30"


def test_module_entry_prints_korean_utf8():
    import subprocess
    import sys

    r = subprocess.run([sys.executable, "-m", "datago_doctor", "explain", str(FX / "live_badkey.xml"), "--status", "403"],
                       capture_output=True)
    assert r.returncode == 1
    assert "등록되지 않은 서비스키" in r.stdout.decode("utf-8")
