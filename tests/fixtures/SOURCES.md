# Fixture sources

Every fixture is the response body stored verbatim (HTTP status and Content-Type are in `manifest.json`).
Fixtures named `synthetic_*` are hand-written and are NOT counted as evidence.

## Live calls (data.go.kr gateway, 2026-11-03 KST)

Made with `curl` against `https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/`, one call per fixture (8 calls total), only with the obviously fake key `INVALID`. No real key was used.

| Fixture | HTTP | Request (base URL `https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/` unless noted) | Time (KST) |
|---|---|---|---|
| live_badkey.xml | 403 | `getRTMSDataSvcAptTrade?LAWD_CD=11110&DEAL_YMD=202510&serviceKey=INVALID` | 2026-11-03 17:15:46 KST |
| live_badop.xml | 400 | `noSuchOperation?LAWD_CD=11110&DEAL_YMD=202510&serviceKey=INVALID` | 2026-11-03 17:15:46 KST |
| live_badsvc.xml | 400 | `../NoSuchService/getX?serviceKey=INVALID` | 2026-11-03 17:15:47 KST |
| live_encbad.xml | 403 | `getRTMSDataSvcAptTrade?LAWD_CD=11110&DEAL_YMD=202510&serviceKey=INVALID%253D%253D` | 2026-11-03 17:15:47 KST |
| live_http.xml | 403 | `(http://) getRTMSDataSvcAptTrade?LAWD_CD=11110&DEAL_YMD=202510&serviceKey=INVALID` | 2026-11-03 17:15:47 KST |
| live_json.json | 403 | `getRTMSDataSvcAptTrade?LAWD_CD=11110&DEAL_YMD=202510&serviceKey=INVALID&_type=json` | 2026-11-03 17:15:47 KST |
| live_nokey.xml | 401 | `getRTMSDataSvcAptTrade?LAWD_CD=11110&DEAL_YMD=202510` | 2026-11-03 17:15:46 KST |
| live_noparams.xml | 403 | `getRTMSDataSvcAptTrade?serviceKey=INVALID` | 2026-11-03 17:15:47 KST |

## Public issues (verbatim response bodies quoted in the issue)

| Fixture | Source |
|---|---|
| issue_pdr2_99.xml | https://github.com/WooilJeong/PublicDataReader/issues/2 (status not stated in the issue; 200 assumed) |
| issue_pharmacy8_401_key_null.xml | https://github.com/atomo-ai-dev/pharmacy-now/issues/8 |
| issue_pharmacy8_403_not_registered.xml | https://github.com/atomo-ai-dev/pharmacy-now/issues/8 |

## kpubdata (MIT, Copyright (c) 2025 Yeongseon Choe)

Copied from https://github.com/kpubdata-lab/kpubdata (commit 9635fba6bf1e8c95aaa1d17581e57e309363d683), directory `tests/fixtures/datago/`, under the MIT license. We did not verify whether kpubdata captured these from live calls; HTTP status is not known.

| Fixture | Original path |
|---|---|
| kpubdata_gateway_key_not_registered.xml | tests/fixtures/datago/error_gateway_key_not_registered.xml |
| kpubdata_gateway_quota_exceeded.xml | tests/fixtures/datago/error_gateway_quota_exceeded.xml |
| kpubdata_gateway_unregistered_ip.xml | tests/fixtures/datago/error_gateway_unregistered_ip.xml |
| kpubdata_invalid_request_10.json | tests/fixtures/datago/error_invalid_request_10.json |
| kpubdata_rate_limit_22.json | tests/fixtures/datago/error_rate_limit_22.json |
| kpubdata_service_unavailable_01.json | tests/fixtures/datago/error_service_unavailable_01.json |
| kpubdata_xml_auth_30.xml | tests/fixtures/datago/error_xml_auth_30.xml |

## Official documents

None yet. No code meaning is marked `confirmed` from an official document; see `datago_doctor/codes.py`.

## Synthetic (hand-written, not evidence)

| Fixture | Why |
|---|---|
| synthetic_garbage.txt | Message seen by the user in PublicDataReader#77 (no response body in the issue) |
| synthetic_html_502.html | typical HTTP/proxy error shape or success shape for tests |
| synthetic_html_504.html | typical HTTP/proxy error shape or success shape for tests |
| synthetic_ok_json.json | typical HTTP/proxy error shape or success shape for tests |
| synthetic_ok_provider.xml | typical HTTP/proxy error shape or success shape for tests |
| synthetic_pdr66_99.xml | PublicDataReader#66 title only says SERVICE KEY IS NOT REGISTERED ERROR; body reconstructed in the shape of issue #2 |
| synthetic_text_api_not_found.txt | typical HTTP/proxy error shape or success shape for tests |
| synthetic_text_unauthorized.txt | typical HTTP/proxy error shape or success shape for tests |
