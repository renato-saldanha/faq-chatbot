import logging
import smtplib
from email.message import EmailMessage

from app.auth.jwt import create_session_token
from app.auth.otp_store import OtpStore
from app.config import Settings

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, otp_store: OtpStore, settings: Settings) -> None:
        self._otp_store = otp_store
        self._settings = settings

    async def request_otp(self, email: str) -> None:
        """Sempre "sucesso" do ponto de vista do chamador — anti-enumeração.

        Só gera/envia o OTP de fato quando o e-mail bate com ADMIN_EMAIL e o
        rate limit permite; resposta ao cliente é idêntica em qualquer caso.
        """
        if email.strip().lower() != self._settings.admin_email.strip().lower():
            return
        if not self._otp_store.can_request(email):
            return

        self._otp_store.record_request(email)
        code = self._otp_store.generate(email)
        self._send_email(email, code)

    def verify_otp(self, email: str, code: str) -> str | None:
        if email.strip().lower() != self._settings.admin_email.strip().lower():
            return None
        if not self._otp_store.verify(email, code):
            return None
        return create_session_token(email)

    def _send_email(self, email: str, code: str) -> None:
        if not self._settings.smtp_host:
            logger.warning("SMTP não configurado — OTP para %s: %s", email, code)
            return

        message = EmailMessage()
        message["Subject"] = "Seu código de acesso"
        message["From"] = self._settings.smtp_user or "no-reply@faq-chatbot.local"
        message["To"] = email
        message.set_content(f"Seu código de acesso é: {code}\n\nExpira em 5 minutos.")

        try:
            with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port) as smtp:
                smtp.starttls()
                if self._settings.smtp_user:
                    smtp.login(self._settings.smtp_user, self._settings.smtp_password)
                smtp.send_message(message)
        except Exception:
            logger.exception("Falha ao enviar OTP por e-mail")
