"""Diagnose a failed data.go.kr OpenAPI response. Standard library only."""
import re
import socket
import ssl
import urllib.error
from dataclasses import asdict, dataclass, field

from .codes import CODES, MESSAGE_HINTS, OK_CODES

ISSUES_URL = "https://github.com/start-up-team-k/datago-doctor/issues"


@dataclass
class Diagnosis:
    code: str
    layer: str  # gateway | provider | http | html | unknown
    cause: str
    fix: str
    confidence: str  # confirmed | candidate
    raw_msg: str = ""
    candidates: list = field(default_factory=list)
    source: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Finding:
    level: str  # error | warn | info
    code: str
    message: str


def _text(body):
    if body is None:
        return ""
    if isinstance(body, str):
        return body
    try:
        return bytes(body).decode("utf-8")
    except UnicodeDecodeError:
        return bytes(body).decode("cp949", errors="replace")


def _field(text, name):
    """First value of an XML element or JSON key called `name`, else None."""
    m = re.search(r"<%s>\s*(.*?)\s*</%s>" % (name, name), text, re.S)
    if m:
        return m.group(1)
    m = re.search(r'"%s"\s*:\s*(?:"((?:[^"\\]|\\.)*)"|([^,}\s]+))' % name, text)
    if m:
        return m.group(1) if m.group(1) is not None else m.group(2)
    return None


def _from_entry(key, layer, raw_msg, extra=""):
    e = CODES[key]
    return Diagnosis(key, layer, e["cause"] + extra, e["fix"], e["confidence"],
                     raw_msg, list(e["candidates"]), e["source"])


def diagnose(status, headers, body, expect=None):
    """Diagnose one response. `expect="json"` if JSON was requested."""
    text = _text(body).strip()
    try:
        status = int(status or 0)
    except (TypeError, ValueError):
        status = 0
    ctype = ""
    for k, v in dict(headers or {}).items():
        if str(k).lower() == "content-type":
            ctype = str(v).lower()

    gw = _field(text, "returnReasonCode")
    code = gw if gw is not None else (_field(text, "resultCode") or _field(text, "CODE"))
    if code is not None:
        layer = "gateway" if gw is not None else "provider"
        msg = " / ".join(m for m in (
            _field(text, "errMsg"), _field(text, "returnAuthMsg"),
            _field(text, "resultMsg"), _field(text, "MESSAGE")) if m)
        if code in OK_CODES:
            return Diagnosis("OK", layer, "정상 응답", "", "confirmed", msg)
        key = code
        if key not in CODES or key == "99":
            up = msg.upper()
            key = next((c for s, c in MESSAGE_HINTS if s in up), key if key in CODES else None)
        extra = ""
        if expect == "json" and text.startswith("<"):
            extra = " (JSON 을 요청했지만 오류는 XML 로 옴: 오류 응답은 요청 형식과 무관할 수 있음)"
        if key is None:
            return Diagnosis(code, layer, "표에 없는 결과코드", "raw_msg 와 활용가이드의 오류코드표를 확인하고, "
                             "이 응답 본문(키 제거)을 이슈로 보내 주세요: " + ISSUES_URL, "candidate", msg)
        d = _from_entry(key, layer, msg, extra)
        d.code = code
        return d

    if status == 200 and re.search(r"<items|\"items\"|<body>|\"body\"", text):
        return Diagnosis("OK", "provider", "결과코드는 없지만 데이터처럼 보이는 응답", "", "candidate", "")

    low = text.lower()
    if "<html" in low or "<!doctype html" in low or "text/html" in ctype:
        key = "HTTP-%d" % status if "HTTP-%d" % status in CODES else "HTML_BODY"
        return _from_entry(key, "html", re.sub(r"<[^>]+>|\s+", " ", text).strip()[:120])
    for needle, st in (("unauthorized", 401), ("forbidden", 403), ("api not found", 404), ("not found", 404)):
        if text and len(text) < 200 and needle in low:
            return _from_entry("HTTP-%d" % st, "http", text)
    if status >= 400 and "HTTP-%d" % status in CODES:
        return _from_entry("HTTP-%d" % status, "http", text[:120])
    return Diagnosis("UNKNOWN", "unknown", "해석할 수 없는 응답",
                     "응답 본문(서비스키 제거)을 이슈로 보내 주세요: " + ISSUES_URL, "candidate", text[:120])


def diagnose_exception(exc):
    """Classify an exception raised before any response arrived (TLS, DNS, timeout)."""
    reason = getattr(exc, "reason", exc)
    if isinstance(reason, ssl.SSLError) or isinstance(exc, ssl.SSLError) or "CERTIFICATE_VERIFY" in str(exc):
        key = "SSL_ERROR"
    elif isinstance(reason, (socket.timeout, TimeoutError)):
        key = "TIMEOUT"
    else:
        key = "NETWORK_ERROR"
    return _from_entry(key, "http", type(reason).__name__)


def from_response(resp, expect=None):
    """Diagnose a requests / httpx response (duck-typed: status_code, headers, content)."""
    return diagnose(resp.status_code, resp.headers, resp.content, expect)


def check_key(key):
    """Static checks on a service key. Never prints or returns the key itself."""
    f = []
    if not key or not key.strip():
        return [Finding("error", "EMPTY", "서비스키가 비어 있습니다.")]
    if key != key.strip():
        f.append(Finding("error", "WHITESPACE", "앞뒤에 공백/줄바꿈이 있습니다 (.env 복사 시 흔함). 제거하세요."))
    k = key.strip()
    if re.search(r"\s", k):
        f.append(Finding("error", "INNER_WHITESPACE", "키 중간에 공백/줄바꿈이 섞여 있습니다."))
    if k[:1] in "\"'" or k[-1:] in "\"'":
        f.append(Finding("error", "QUOTES", "따옴표가 키에 포함되어 있습니다. 따옴표를 제거하세요."))
    if k.lower().startswith("servicekey="):
        f.append(Finding("error", "PREFIX", "'serviceKey=' 접두어까지 키로 복사되었습니다."))
    if not k.isascii():
        f.append(Finding("error", "NON_ASCII", "ASCII 가 아닌 문자가 있습니다 (잘못 복사됨)."))
    if "%25" in k:
        f.append(Finding("error", "DOUBLE_ENCODED", "이중 인코딩(%25)된 키입니다. 인코딩 키를 한 번 더 인코딩한 결과일 수 있습니다."))
    elif re.search(r"%(2B|2F|3D)", k, re.I):
        f.append(Finding("info", "ENCODED", "인코딩된 키 형태입니다. URL 문자열에 그대로 붙이세요; requests params= 로 넘기면 이중 인코딩됩니다."))
    elif re.search(r"[+/=]", k):
        f.append(Finding("info", "DECODED", "디코딩된 키 형태입니다. requests params= 로 넘기면 자동 인코딩됩니다; URL 에 직접 붙일 때는 인코딩하세요."))
    n = len(k.strip("\"'"))
    if not 40 <= n <= 120:
        f.append(Finding("warn", "LENGTH", "키 길이(%d)가 일반적인 범위(40~120자)를 벗어납니다. 일부만 복사했는지 확인하세요." % n))
    return f
