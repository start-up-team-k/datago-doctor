"""Seven real-world symptoms found in public GitHub issues (evidence E-001..E-007)."""
import pathlib
import ssl
import urllib.error

from datago_doctor import diagnose, diagnose_exception

FX = pathlib.Path(__file__).parent / "fixtures"


def fx(name, status=None):
    return diagnose(status, {}, (FX / name).read_bytes())


def test_e001_publicdatareader_2_code_99_key_not_registered():
    """https://github.com/WooilJeong/PublicDataReader/issues/2
    resultCode 99 + "SERVICE KEY IS NOT REGISTERED ERROR." is read as the key-not-registered family."""
    d = fx("issue_pdr2_99.xml")
    assert d.code == "99" and d.layer == "provider"
    assert "등록되지 않은 서비스키" in d.cause
    assert any("재발급" in c for c in d.candidates)


def test_e002_publicdatareader_20_wrapper_hides_error_code():
    """https://github.com/WooilJeong/PublicDataReader/issues/20
    The wrapper prints only "[ERROR] Open API 호출 오류" and ends the batch. The raw response the
    wrapper swallowed (here a live gateway reply) is still diagnosable on its own."""
    d = fx("live_badkey.xml", 403)
    assert d.code == "30" and d.fix


def test_e003_publicdatareader_66_service_key_not_registered():
    """https://github.com/WooilJeong/PublicDataReader/issues/66
    Title only: "SERVICE KEY IS NOT REGISTERED ERROR" (body reconstructed, synthetic)."""
    d = fx("synthetic_pdr66_99.xml")
    assert "등록되지 않은 서비스키" in d.cause and d.confidence == "confirmed"


def test_e004_publicdatareader_77_only_generic_failure_message_visible():
    """https://github.com/WooilJeong/PublicDataReader/issues/77
    The user sees only "Exception: API 요청이 실패했습니다". That text is not a response, so it is
    reported unknown and the fix points to `explain`-style raw body reporting; the raw reply is diagnosable."""
    d = fx("synthetic_garbage.txt", 200)
    assert d.layer == "unknown" and "본문" in d.fix
    assert fx("issue_pharmacy8_403_not_registered.xml", 403).code == "30"


def test_e005_publicdatareader_43_ssl_failure_is_classified():
    """https://github.com/WooilJeong/PublicDataReader/issues/43
    SSL verification failures (answered upstream with verify=False) are classified as SSL_ERROR."""
    exc = urllib.error.URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))
    d = diagnose_exception(exc)
    assert d.code == "SSL_ERROR" and "verify=False" in d.fix


def test_e006_abroad_to_korea_18_all_apis_403_after_new_key():
    """https://github.com/pihet/abroad-to-korea/issues/18
    403 + returnReasonCode 30 on every API: sync delay after a new application and key reissue are candidates."""
    d = fx("kpubdata_gateway_key_not_registered.xml", 403)
    text = " ".join(d.candidates)
    assert d.code == "30" and d.confidence == "confirmed"
    assert "동기화" in text and "재발급" in text


def test_e007_pharmacy_now_8_401_403_codes_30_22_20():
    """https://github.com/atomo-ai-dev/pharmacy-now/issues/8
    HTTP 401/403 carry an XML body; codes 20 (key null), 30 (not registered) and 22 (quota) are told apart."""
    assert fx("issue_pharmacy8_401_key_null.xml", 401).code == "20"
    assert fx("issue_pharmacy8_403_not_registered.xml", 403).code == "30"
    assert fx("kpubdata_gateway_quota_exceeded.xml", 403).code == "22"
