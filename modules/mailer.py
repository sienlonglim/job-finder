import os
import sys
import logging
import smtplib
from typing import Iterable, Optional

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
log = logging.getLogger()


class EmailServer:
    def __init__(
        self,
        host: str = 'smtp.gmail.com',
        port: int = 465
    ):
        self.host = host
        self.port = port
        self._email_address = os.environ['EMAIL']
        self._app_pass = os.environ['APP_PASS']
        self.smtp_server = smtplib.SMTP_SSL(self.host, self.port)
        self.smtp_server.login(
                user=self._email_address,
                password=self._app_pass
            )
        log.info('Email login successful')

    def _create_MIME_message(
        self,
        subject: str,
        recipients: Iterable[str],
        body: str,
    ) -> MIMEMultipart:
        message = MIMEMultipart()
        message['Subject'] = subject
        message['From'] = self._email_address
        message['To'] = ', '.join(recipients)

        # HTML body
        # html_part = MIMEText(body, 'html')
        # Normal body
        email_content = MIMEText(body)
        message.attach(payload=email_content)
        return message

    def _add_attachements(
        self,
        message: MIMEMultipart,
        attachments: Iterable[str]
    ) -> MIMEMultipart:
        if attachments is not None:
            for filepath in attachments:
                with open(filepath, 'rb') as file:
                    attachment_part = MIMEBase('application', 'octet-stream')
                    attachment_part.set_payload((file).read())
                encoders.encode_base64(attachment_part)
                attachment_part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(filepath)
                )
                message.attach(payload=attachment_part)
        return message

    def send_email(
        self,
        subject: str,
        body: str,
        recipients: Iterable[str],
        attachments: Optional[Iterable[str]] = None
    ) -> None:
        '''
        Sends an email with the given parameters
        Inputs:
            server: smtplib server object
            subject: str - subject of email
            body: str - body of the email, in html format
            recipients: list of str - email addresses to send to
            attachments: list of str - filepaths of attachments
        '''
        message = self._create_MIME_message(
            subject=subject,
            recipients=recipients,
            body=body
        )
        if attachments is not None:
            message = self._add_attachements(
                message=message,
                attachments=attachments
            )
        self.smtp_server.ehlo()
        self.smtp_server.sendmail(
            from_addr=self._email_address,
            to_addrs=recipients,
            msg=message.as_string()
        )
        print(f"Message sent to {recipients}!")
