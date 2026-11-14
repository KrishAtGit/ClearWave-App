import logging 
import html
from typing import Protocol
import httpx

log = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"

class MailError(Exception): 
    """Raised when an email could not be sent."""
class Mailer(Protocol):
    async def send_login_link(self, email:str, link:str) -> None: ...
    async def close(self) -> None: ...
class ConsoleMailer:
    async def send_login_link(self, email:str, link:str) -> None:
        log.warning("Sign-in link for %s: %s", email, link)

    async def close(self) -> None:
        pass

class ResendMailer:
    def __init__(self, api_key: str, sender: str, client: httpx.AsyncClient | None = None) -> None:
        self.sender = sender
        self.client = client or httpx.AsyncClient(timeout=10)
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def send_login_link(self, email: str, link: str) -> None:
        safe = html.escape(link)
        response = await self.client.post(
            RESEND_URL,
            headers=self.headers,
            json={
                "from" : self.sender,
                "to" : [email],
                "subject": "Your ClearWave sign-in link",
                "text" : f"Sign in to ClearWave using this link : {link}\n\nThis link works once and expires soon.",
                "html" : f'<p><a href="{safe}">Sign in to ClearWave</a></p>'
                          "<p> This link works once and expires soon. "
                          "If you didn't ask for it, ignore this email.</p>"
            },
        )
        if response.status_code >= 400:
            log.error("Resend rejected the email : %s", response.status_code)
            raise MailError("Could not send the sign-in email")
        
    async def close(self) -> None:
        await self.client.aclose()

