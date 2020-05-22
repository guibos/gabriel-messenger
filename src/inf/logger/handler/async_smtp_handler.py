import mimetypes
from asyncio import AbstractEventLoop
from email.message import EmailMessage
from typing import List, Optional

import aiofiles
import aiofiles.os
from aiologger.formatters.base import Formatter
from aiologger.handlers.base import Handler
from aiologger.records import LogRecord
from aiosmtplib import send

from src.ser.common.value_object.file_value_object import FileValueObject


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

        await self.attach_files(record=record, message=message)

        await send(message=message,
                   hostname=self._hostname,
                   port=self._port,
                   username=self._username,
                   password=self._password,
                   use_tls=self._use_tls)

    @staticmethod
    async def attach_files(record: LogRecord, message: EmailMessage):
        if 'files' not in record.args:
            return
        for file in record.args['files']:
            file: FileValueObject

            file_type, encoding = mimetypes.guess_type(file.path)
            if file_type is None or encoding is not None:
                file_type = 'application/octet-stream'
            maintype, subtype = file_type.split('/', 1)
            async with aiofiles.open(file.path, 'rb') as fp:
                message.add_attachment(await fp.read(),
                                       maintype=maintype,
                                       subtype=subtype,
                                       filename=file.filename)
            await aiofiles.os.remove(file.path)

    async def close(self) -> None:
        pass
