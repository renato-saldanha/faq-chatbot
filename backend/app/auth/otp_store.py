import secrets
import time

from cachetools import TTLCache

_OTP_TTL_SECONDS = 5 * 60
_RATE_LIMIT_TTL_SECONDS = 15 * 60
_REQUEST_MAX_ATTEMPTS = 3
_VERIFY_MAX_ATTEMPTS = 5


class OtpStore:
    """Armazenamento de OTP em memória — TTL 5min, single-use, sem tabela dedicada.

    Dois rate limits independentes por e-mail: um para pedir código novo
    (evita spam de e-mail/SMS), outro para tentativas de verificação (evita
    brute-force do código de 6 dígitos dentro da janela de 5min de validade).
    """

    def __init__(self) -> None:
        self._codes: TTLCache[str, str] = TTLCache(maxsize=1000, ttl=_OTP_TTL_SECONDS)
        self._request_attempts: TTLCache[str, list[float]] = TTLCache(maxsize=1000, ttl=_RATE_LIMIT_TTL_SECONDS)
        self._verify_attempts: TTLCache[str, list[float]] = TTLCache(maxsize=1000, ttl=_RATE_LIMIT_TTL_SECONDS)

    def can_request(self, email: str) -> bool:
        attempts = self._request_attempts.get(email, [])
        return len(attempts) < _REQUEST_MAX_ATTEMPTS

    def record_request(self, email: str) -> None:
        attempts = self._request_attempts.get(email, [])
        attempts.append(time.time())
        self._request_attempts[email] = attempts

    def generate(self, email: str) -> str:
        code = f"{secrets.randbelow(1_000_000):06d}"
        self._codes[email] = code
        return code

    def can_verify(self, email: str) -> bool:
        attempts = self._verify_attempts.get(email, [])
        return len(attempts) < _VERIFY_MAX_ATTEMPTS

    def verify(self, email: str, code: str) -> bool:
        if not self.can_verify(email):
            return False

        attempts = self._verify_attempts.get(email, [])
        attempts.append(time.time())
        self._verify_attempts[email] = attempts

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
