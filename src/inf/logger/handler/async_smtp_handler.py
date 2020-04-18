from asyncio import AbstractEventLoop
from email.message import EmailMessage
from typing import List, Optional

from aiologger.formatters.base import Formatter
from aiologger.handlers.base import Handler
from aiologger.records import LogRecord
from aiosmtplib import send


class AsyncSMTPHandler(Handler):
    def __init__(self,
                 level: str,
                 sender: str,
                 recipients: List[str],
                 subject: str,
                 username: str,
                 password: str,
                 hostname: str,
                 port: int,
                 use_tls: bool,
                 loop: Optional[AbstractEventLoop] = None,
                 formatter: Optional[Formatter] = None):
        super().__init__(loop=loop)
        if formatter:
            self.formatter = formatter
        self.level = level
        self._sender = sender
        self._recipients = ", ".join(recipients)
        self._subject = subject
        self._username = username
        self._password = password
        self._hostname = hostname
        self._port = port
        self._use_tls = use_tls

    async def emit(self, record: LogRecord) -> None:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = self._recipients
        message["Subject"] = self._subject
        message.set_content(self.formatter.format(record))

        await send(message=message,
                   hostname=self._hostname,
                   port=self._port,
                   username=self._username,
                   password=self._password,
                   use_tls=self._use_tls)

    async def close(self) -> None:
        pass
