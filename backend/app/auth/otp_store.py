import secrets
import time

from cachetools import TTLCache

_OTP_TTL_SECONDS = 5 * 60
_RATE_LIMIT_TTL_SECONDS = 15 * 60
_RATE_LIMIT_MAX_ATTEMPTS = 3


class OtpStore:
    """Armazenamento de OTP em memória — TTL 5min, single-use, sem tabela dedicada."""

    def __init__(self) -> None:
        self._codes: TTLCache[str, str] = TTLCache(maxsize=1000, ttl=_OTP_TTL_SECONDS)
        self._rate_limit: TTLCache[str, list[float]] = TTLCache(maxsize=1000, ttl=_RATE_LIMIT_TTL_SECONDS)

    def can_request(self, email: str) -> bool:
        attempts = self._rate_limit.get(email, [])
        return len(attempts) < _RATE_LIMIT_MAX_ATTEMPTS

    def record_request(self, email: str) -> None:
        attempts = self._rate_limit.get(email, [])
        attempts.append(time.time())
        self._rate_limit[email] = attempts

    def generate(self, email: str) -> str:
        code = f"{secrets.randbelow(1_000_000):06d}"
        self._codes[email] = code
        return code

    def verify(self, email: str, code: str) -> bool:
        stored = self._codes.get(email)
        if stored is None:
            return False
        if not secrets.compare_digest(stored, code):
            return False
        del self._codes[email]
        return True


_otp_store = OtpStore()


def get_otp_store() -> OtpStore:
    return _otp_store
