"""datago-doctor: explain failed data.go.kr OpenAPI responses."""
from .core import Diagnosis, Finding, check_key, diagnose, diagnose_exception, from_response

__all__ = ["Diagnosis", "Finding", "check_key", "diagnose", "diagnose_exception", "from_response"]
__version__ = "0.1.0"
