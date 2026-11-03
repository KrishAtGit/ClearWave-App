import logging 
from typing import Protocol

log = logging.getLogger(__name__)

class Mailer(Protocol):
    async def send_login_link(self, email:str, link:str) -> None: ...

class ConsoleMailer:
    async def send_login_link(self, email:str, link:str) -> None:
        log.warning("Sign-in lik for %s: %s", email, link)


        