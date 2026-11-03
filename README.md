# datago-doctor

> Paste a failed data.go.kr OpenAPI response, from any SDK or plain `requests`, and get the cause and the fix. Zero dependencies.

This is an open-source project built by AI agents as an experiment run by start-up-team-k. Feedback and issues are welcome.

## Why

Calls to the Korea Public Data Portal (data.go.kr) OpenAPIs fail in confusing ways: the gateway answers with an XML error and HTTP 401/403 instead of 200, providers use their own `resultCode`, some SDKs hide the body and only raise "API request failed", and the same code (for example `30`) can mean several things. `datago-doctor` takes **one failed response** (status, headers, body) and says which layer failed (gateway / provider / http / html), what the likely cause is, and what to try.

It is **not** an SDK. It works on any API URL and any response body, whichever client produced it.

Existing alternatives, to be fair about them:

- [kpubdata](https://github.com/kpubdata-lab/kpubdata) (MIT) has `kpubdata probe`, which already classifies result codes, but for kpubdata's own dataset IDs.
- [kpublic](https://github.com/HyaC1107/kpublic) provides one exception class per result code inside its own client.
- [PublicDataReader](https://github.com/WooilJeong/PublicDataReader) is a data-fetching SDK; its failures are the main source of our test cases.

datago-doctor targets arbitrary URLs and arbitrary SDK response bodies instead.

## Install

Requires Python 3.9 or newer. Not on PyPI yet.

```bash
pip install git+https://github.com/start-up-team-k/datago-doctor
```

## Quick start

No key needed: explain a response that was already saved. From a clone of this repository:

```bash
git clone https://github.com/start-up-team-k/datago-doctor
cd datago-doctor
datago-doctor explain tests/fixtures/live_badkey.xml --status 403
datago-doctor explain tests/fixtures/issue_pdr2_99.xml
```

Pipe a body from any client (`-` reads stdin):

```bash
curl -s "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade?serviceKey=INVALID" | datago-doctor explain - --status 401
```

Use it from Python (works with `requests` and `httpx` responses):

```python
from datago_doctor import diagnose, from_response
d = from_response(resp)          # or diagnose(status, headers, body)
print(d.code, d.layer, d.cause, d.fix, d.confidence, d.candidates)
```

With a key (read from the environment, never from arguments):

```bash
export DATAGO_SERVICE_KEY="<your key>"
datago-doctor key                                  # static checks, no network
datago-doctor check "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade?LAWD_CD=11110&DEAL_YMD=202510"
```

`check` makes at most 3 requests (the URL; once more with the other key encoding only if the gateway says code 30; plain `http://` only if https failed at the transport level and you passed `--allow-http`). Every output masks the key (first 4 characters + `***`). Add `--json` for machine-readable output. Exit codes: 0 OK, 1 diagnosed failure, 2 usage error.

Example output:

```
HTTP 403  [30] 등록되지 않은 서비스키 (layer=gateway, 확정)
  raw_msg: SERVICE_KEY_IS_NOT_REGISTERED_ERROR / 등록되지 않은 서비스키
  가능한 원인(candidates):
    - 키 오타·공백·따옴표 혼입 또는 이중 인코딩(%25)
    - 인코딩 키/디코딩 키를 잘못 사용 (...)
    - 활용신청 직후 키 동기화 지연 (수 분~수 시간)
    ...
```

## Test

```bash
git clone https://github.com/start-up-team-k/datago-doctor
cd datago-doctor
python -m pip install ".[dev]"
python -m pytest
```

Tests use fixtures in `tests/fixtures/` (sources in `tests/fixtures/SOURCES.md`) and mock all network calls.

## Scope

- Does: diagnose one response (gateway XML/JSON, provider XML/JSON, XML when JSON was requested, plain-text and HTML errors, TLS/timeout failures); static checks of a service key; a tiny `check` command with a hard 3-request cap.
- Does not: fetch data, paginate, retry, parse successful payloads, or store anything. It does not publish to PyPI yet.

## Limitations

- Result-code meanings in `datago_doctor/codes.py` are `candidate` unless marked `confirmed`. Confirmed means the meaning is in the portal's official error-code docs (https://www.data.go.kr/tcs/dss/selectErrCodePopupView.do, the FAQ attachment at https://www.data.go.kr/bbs/faq/selectFaqView.do?bbsId=FAQ_0000000000000214) and, where possible, matched a live response: 10, 12, 22, 30, 31, 99. Still candidate: 20 (the portal uses it for both "no key" and "access denied"), 32 (missing from the current portal table), and the HTTP status / code returned when a valid key calls an API you have not applied for (401+20 vs 403+30 is unverified). A confirmed code can still list several possible causes (e.g. 30 covers typos, double encoding, sync delay and reissued keys). Fixing a meaning means editing one table.
- Fixtures: 8 come from live calls with an obviously fake key, 3 from public GitHub issues, 7 from kpubdata (MIT, see SOURCES.md; not verified as live captures), and some are synthetic. No official-document fixtures yet.
- No real key was available to the authors, so the "success" path and per-API result codes are only tested with synthetic bodies.
- Output text is Korean.
- python.org builds of Python on macOS may fail TLS verification until you run `Install Certificates.command` (datago-doctor reports this as `SSL_ERROR`; we hit it ourselves).

## 한국어 요약

공공데이터포털(data.go.kr) OpenAPI 호출이 실패했을 때, 어떤 SDK(PublicDataReader, kpubdata, requests 등)를 썼든 실패 응답 하나를 넣으면 실패 계층(gateway/provider/http/html), 원인, 해결책을 알려 주는 의존성 없는 도구입니다. SDK가 아닙니다. 키 없이도 `datago-doctor explain tests/fixtures/live_badkey.xml --status 403` 로 바로 해 볼 수 있고, `check` 는 요청을 최대 3회로 제한하며 모든 출력에서 서비스키를 마스킹합니다. 코드 10, 12, 22, 30, 31, 99는 포털 공식 문서로 확인했고, 20·32와 "활용신청 누락 시 응답"은 아직 "후보"로 표시합니다. 이 프로젝트는 AI 에이전트가 만든 실험 프로젝트입니다.

## License

MIT
