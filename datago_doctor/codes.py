"""The single result-code table. Edit only this file to change what is reported.

Keys are data.go.kr gateway `returnReasonCode` / provider `resultCode` values
(as strings), plus `HTTP-<status>` and a few transport pseudo-codes.

Fields per entry:
  name        official-looking English name (as seen in responses)
  cause       primary meaning (Korean)
  fix         what to do (Korean)
  confidence  "confirmed" only if verified against an official document or a
              live response captured in tests/fixtures; otherwise "candidate"
  candidates  alternative causes shown when confidence is "candidate"
  source      URL (or fixture path) where the code/meaning was observed
"""

KP = "https://github.com/kpubdata-lab/kpubdata/tree/main/tests/fixtures/datago"
LIVE = "tests/fixtures/SOURCES.md (live call 2026-11-03)"
PDR = "https://github.com/WooilJeong/PublicDataReader/issues/2"
PHARM = "https://github.com/atomo-ai-dev/pharmacy-now/issues/8"
ABROAD = "https://github.com/pihet/abroad-to-korea/issues/18"

# Responses with these codes are healthy.
OK_CODES = ("00", "0000", "INFO-000")

# (substring of upper-cased message, code). Used when the code is missing or a
# generic 99 but the message names the problem (e.g. 99 + "SERVICE KEY IS NOT REGISTERED").
MESSAGE_HINTS = (
    ("NOT REGISTERED", "30"),
    ("NOT_REGISTERED", "30"),
    ("EXCEEDS", "22"),
    ("DEADLINE", "31"),
    ("UNREGISTERED_IP", "32"),
    ("NO MANDATORY", "11"),
    ("INVALID REQUEST PARAMETER", "10"),
)


def _e(name, cause, fix, confidence="candidate", candidates=(), source=KP):
    return dict(name=name, cause=cause, fix=fix, confidence=confidence,
                candidates=list(candidates), source=source)


CODES = {
    "01": _e("APPLICATION_ERROR", "제공기관 서버 내부 오류", "잠시 뒤 재시도. 계속되면 제공기관 문의."),
    "02": _e("DB_ERROR", "제공기관 DB 오류", "잠시 뒤 재시도. 계속되면 제공기관 문의."),
    "03": _e("NODATA_ERROR", "조회 결과 없음", "조회 조건(지역코드, 날짜 등)을 바꿔 보세요."),
    "04": _e("HTTP_ERROR", "제공기관 HTTP 오류", "잠시 뒤 재시도. 계속되면 제공기관 문의."),
    "05": _e("SERVICETIMEOUT_ERROR", "제공기관 서비스 연결 시간 초과", "잠시 뒤 재시도."),
    "10": _e("INVALID_REQUEST_PARAMETER_ERROR", "요청 파라미터 값이 잘못됨",
             "활용가이드 문서의 파라미터 이름·형식(날짜 형식, 코드값)을 확인하세요."),
    "11": _e("NO_MANDATORY_REQUEST_PARAMETERS_ERROR", "필수 파라미터 누락",
             "활용가이드의 필수 파라미터를 모두 넣었는지 확인하세요."),
    "12": _e("NO_OPENAPI_SERVICE_ERROR", "해당 오픈API 서비스가 없거나 폐기됨 (URL의 서비스/오퍼레이션 경로 오류)",
             "URL 경로(서비스명, 오퍼레이션명)와 대소문자를 활용가이드와 대조하세요.",
             "confirmed", source=LIVE),
    "20": _e("SERVICE_ACCESS_DENIED_ERROR", "서비스 접근 거부 (출처마다 원인이 다름)",
             "아래 후보를 순서대로 확인하세요.",
             candidates=["serviceKey 파라미터가 비었거나 이름이 틀림 (실호출: 키 없이 호출하면 SERVICE_KEY_IS_NULL + 20, HTTP 401)",
                         "해당 API에 활용신청을 하지 않았거나 승인 전",
                         "키는 유효하나 이 서비스 접근 권한이 없음"],
             source=PHARM),
    "21": _e("TEMPORARILY_DISABLE_THE_SERVICEKEY_ERROR", "서비스키가 일시적으로 비활성화됨", "포털 마이페이지에서 키 상태를 확인하고 재시도하세요."),
    "22": _e("LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR", "서비스 요청 제한 횟수 초과",
             "호출 수를 줄이거나 다음 날(일일 한도) 재시도. 운영계정 전환/한도 상향 신청 가능.",
             candidates=["일일 트래픽 한도 초과 (개발계정 보통 1,000건)", "초당/분당 호출 제한 초과"],
             source=KP),
    "30": _e("SERVICE_KEY_IS_NOT_REGISTERED_ERROR", "등록되지 않은 서비스키",
             "키를 포털 마이페이지 값과 비교하고, 인코딩/디코딩 키 형태를 바꿔 보세요. `datago-doctor key`로 키 형태를 점검하세요.",
             candidates=["키 오타·공백·따옴표 혼입 또는 이중 인코딩(%25)",
                         "인코딩 키/디코딩 키를 잘못 사용 (requests params=로 넘기면 인코딩 키가 이중 인코딩됨)",
                         "활용신청 직후 키 동기화 지연 (수 분~수 시간)",
                         "포털에서 키가 재발급되어 이전 키가 무효화됨",
                         "해당 API에 활용신청이 안 되어 있음"],
             source=ABROAD),
    "31": _e("DEADLINE_HAS_EXPIRED_ERROR", "활용기간 만료", "포털에서 활용기간 연장(재신청)을 하세요.", source=KP),
    "32": _e("UNREGISTERED_IP_ERROR", "등록되지 않은 IP에서 호출", "포털에 등록한 서버 IP에서 호출했는지 확인하거나 IP 등록을 갱신하세요.", source=KP),
    "33": _e("UNSIGNED_CALL_ERROR", "서명되지 않은 호출", "제공기관 가이드의 서명/인증 방식을 확인하세요."),
    "99": _e("UNKNOWN_ERROR", "알 수 없는 오류 (제공기관이 메시지로만 구분하기도 함)",
             "raw_msg 를 확인하세요. 메시지가 키 미등록이면 코드 30 항목을 참고하세요.", source=PDR),
    "HTTP-400": _e("BAD_REQUEST", "잘못된 요청 (URL 형식 또는 경로 오류)", "URL, 파라미터 인코딩, 경로를 확인하세요."),
    "HTTP-401": _e("UNAUTHORIZED", "인증 실패: 게이트웨이가 401 로 거절함",
                   "본문이 있으면 explain 으로 다시 진단하세요 (SDK 가 본문을 숨기는 경우가 많음).",
                   candidates=["serviceKey 누락", "활용신청 누락", "접근 거부"], source=PHARM),
    "HTTP-403": _e("FORBIDDEN", "접근 금지: 게이트웨이가 403 으로 거절함",
                   "본문이 있으면 explain 으로 다시 진단하세요.",
                   candidates=["등록되지 않은 키 (코드 30)", "활용신청 누락", "IP 제한"], source=PHARM),
    "HTTP-404": _e("NOT_FOUND", "경로를 찾을 수 없음 (API not found)", "서비스/오퍼레이션 URL 경로를 활용가이드와 대조하세요."),
    "HTTP-429": _e("TOO_MANY_REQUESTS", "요청 과다", "호출 간격을 늘리고 일일 한도를 확인하세요."),
    "HTTP-500": _e("SERVER_ERROR", "서버 내부 오류", "잠시 뒤 재시도."),
    "HTTP-502": _e("BAD_GATEWAY", "게이트웨이가 제공기관 서버에 연결하지 못함 (HTML 오류 페이지)", "잠시 뒤 재시도. 반복되면 제공기관 점검 공지를 확인하세요."),
    "HTTP-503": _e("SERVICE_UNAVAILABLE", "서비스 일시 중단/점검", "잠시 뒤 재시도. 점검 공지를 확인하세요."),
    "HTTP-504": _e("GATEWAY_TIMEOUT", "제공기관 서버 응답 시간 초과 (HTML 오류 페이지)", "잠시 뒤 재시도, 조회 범위를 줄여 보세요."),
    "HTML_BODY": _e("HTML_RESPONSE", "XML/JSON 대신 HTML 이 왔음 (점검, 프록시, 차단 페이지 가능)", "브라우저로 같은 URL을 열어 보거나 사내 프록시/방화벽을 확인하세요."),
    "SSL_ERROR": _e("SSL_ERROR", "TLS/인증서 검증 실패 (호출 전 단계, 서버 응답 없음)",
                    "CA 번들 갱신(pip install -U certifi, macOS 는 Install Certificates.command), 사내 프록시면 루트 CA 등록. verify=False 는 권장하지 않음.",
                    candidates=["사내 프록시/보안 장비의 인증서 가로채기", "오래된 CA 번들·OpenSSL", "서버 인증서 체인 문제(제공기관)"],
                    source="https://github.com/WooilJeong/PublicDataReader/issues/43"),
    "TIMEOUT": _e("TIMEOUT", "응답 시간 초과", "잠시 뒤 재시도하거나 timeout 을 늘리세요."),
    "NETWORK_ERROR": _e("NETWORK_ERROR", "네트워크 연결 실패 (DNS, 연결 거부 등)", "인터넷/프록시 설정과 URL 호스트를 확인하세요."),
}
