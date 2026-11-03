"""Command line interface. Every printed line passes through `_clean` to hide the service key."""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from . import __version__
from .core import Diagnosis, check_key, diagnose, diagnose_exception

ENV = "DATAGO_SERVICE_KEY"
KEY_RE = re.compile(r"(?i)(servicekey=)([^&#\s\"']+)")
_secrets = set()


def mask(value):
    return value[:4] + "***" if len(value) > 4 else "***"


def _register(key):
    """Remember every common spelling of the key so it is hidden wherever it shows up."""
    k = key.strip().strip("\"'")
    if k:
        _secrets.update({k, urllib.parse.quote(k, safe=""), urllib.parse.unquote(k), urllib.parse.quote(k)})


def _clean(text):
    text = KEY_RE.sub(lambda m: m.group(1) + mask(urllib.parse.unquote(m.group(2))), text)
    for s in sorted(_secrets, key=len, reverse=True):
        if len(s) >= 8:
            text = text.replace(s, mask(s))
    return text


def out(text="", file=None):
    print(_clean(text), file=file or sys.stdout)


def render(d, status=None):
    head = "[%s] %s (layer=%s, %s)" % (d.code, d.cause, d.layer, "확정" if d.confidence == "confirmed" else "후보")
    if status:
        head = "HTTP %s  " % status + head
    lines = [head]
    if d.raw_msg:
        lines.append("  raw_msg: " + d.raw_msg)
    if d.candidates:
        lines.append("  가능한 원인(candidates):")
        lines += ["    - " + c for c in d.candidates]
    if d.fix:
        lines.append("  fix: " + d.fix)
    return "\n".join(lines)


def fetch(url, timeout=15):
    """One GET. Returns (status, headers, body). Raises on transport errors."""
    req = urllib.request.Request(url, headers={"User-Agent": "datago-doctor/" + __version__})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def _with_key(url, val):
    """Append serviceKey=<val> verbatim (the caller chooses the encoding form)."""
    url = KEY_RE.sub("", url).rstrip("?&")
    return url + ("&" if "?" in url else "?") + "serviceKey=" + val


def _step(label, url, results):
    out("\n== %s\n%s" % (label, url))
    expect = "json" if re.search(r"(?i)(_type|returnType|type)=json", url) else None
    try:
        status, headers, body = fetch(url)
        d = diagnose(status, headers, body, expect)
    except Exception as e:  # transport failure: classify, never show the raw exception text
        status, d = None, diagnose_exception(e)
    out(render(d, status))
    results.append({"url": _clean(url), "status": status, "diagnosis": d.to_dict()})
    return d


def cmd_check(args):
    url = args.url
    if not url.startswith(("http://", "https://")):
        out("URL 은 https:// 로 시작해야 합니다.", sys.stderr)
        return 2
    m = KEY_RE.search(url)
    if m:
        tried = m.group(2)
        _register(tried)
        out("경고: URL 에 serviceKey 가 들어 있습니다. 셸 기록에 키가 남으니 환경 변수 %s 사용을 권장합니다." % ENV, sys.stderr)
    else:
        key = os.environ.get(ENV, "").strip().strip("\"'")
        tried = key if "%" in key else urllib.parse.quote(key, safe="")
        if key:
            _register(key)
            url = _with_key(url, tried)
        else:
            out("경고: %s 가 없고 URL 에도 serviceKey 가 없어 키 없이 호출합니다." % ENV, sys.stderr)
    if url.startswith("http://"):
        out("http:// URL 은 키를 평문으로 보냅니다. https:// 를 사용하세요.", sys.stderr)
        if not args.allow_http:
            return 2
    results = []
    d = _step("1/3 요청", url, results)
    if d.layer == "http" and d.code in ("SSL_ERROR", "TIMEOUT", "NETWORK_ERROR") and url.startswith("https://"):
        if args.allow_http:
            d = _step("3/3 http 재시도 (--allow-http, 키가 평문으로 전송됨)", "http://" + url[8:], results)
        else:
            out("\nhttps 호출이 실패했습니다. 평문 http 로 키를 보내는 재시도는 --allow-http 가 있을 때만 합니다.")
    elif d.code == "30" and tried:
        alt = urllib.parse.unquote(tried)  # the other form: decoded key sent unescaped
        if alt != tried:
            _register(alt)
            d = _step("2/3 키 인코딩 형태를 바꿔 재시도", _with_key(url, alt), results)
            if d.code == "OK":
                out("\n키 인코딩 형태가 원인이었습니다: 위에서 성공한 형태를 사용하세요.")
    if args.json:
        print(_clean(json.dumps(results, ensure_ascii=False, indent=2)))
    return 0 if d.code == "OK" else 1


def cmd_explain(args):
    try:
        if args.file in (None, "-"):
            data = sys.stdin.buffer.read()
        else:
            with open(args.file, "rb") as f:
                data = f.read()
    except OSError as e:
        out("파일을 읽을 수 없습니다: %s" % e.strerror, sys.stderr)
        return 2
    d = diagnose(args.status, None, data)
    if args.json:
        print(_clean(json.dumps(d.to_dict(), ensure_ascii=False, indent=2)))
    else:
        out(render(d, args.status))
    return 0 if d.code == "OK" else 1


def cmd_key(args):
    key = os.environ.get(ENV)
    if key is None:
        out("환경 변수 %s 가 설정되어 있지 않습니다." % ENV, sys.stderr)
        return 2
    _register(key)
    findings = check_key(key)
    k = key.strip().strip("\"'")
    if args.json:
        print(_clean(json.dumps({"key": mask(k), "findings": [vars(f) for f in findings]}, ensure_ascii=False, indent=2)))
    else:
        out("key: %s (길이 %d)" % (mask(k), len(k)))
        for f in findings or ():
            out("  [%s] %s: %s" % (f.level, f.code, f.message))
        if not findings:
            out("  문제 없음")
    return 1 if any(f.level == "error" for f in findings) else 0


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, _clean(self.format_usage() + message) + "\n")


def build_parser():
    p = _Parser(prog="datago-doctor", description="data.go.kr OpenAPI 실패 응답 진단기")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="URL 을 최대 3회 호출해 진단")
    c.add_argument("url")
    c.add_argument("--allow-http", action="store_true", help="https 실패 시 평문 http 재시도 허용")
    c.add_argument("--json", action="store_true")
    c.set_defaults(fn=cmd_check)
    e = sub.add_parser("explain", help="받아 둔 응답 본문(파일 또는 -)을 진단, 네트워크 호출 없음")
    e.add_argument("file", nargs="?", default="-")
    e.add_argument("--status", type=int, default=None, help="응답의 HTTP 상태 코드")
    e.add_argument("--json", action="store_true")
    e.set_defaults(fn=cmd_explain)
    k = sub.add_parser("key", help="%s 환경 변수의 키 형태 점검" % ENV)
    k.add_argument("--json", action="store_true")
    k.set_defaults(fn=cmd_key)
    return p


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        return args.fn(args)
    except Exception as e:
        out("오류: %s: %s" % (type(e).__name__, e), sys.stderr)
        return 2
