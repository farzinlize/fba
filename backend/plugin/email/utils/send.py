from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from aiosmtplib import SMTP
from anyio import open_file
from jinja2 import Template
from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.log import log
from backend.core.conf import settings
from backend.core.path_conf import PLUGIN_DIR
from backend.plugin.email.utils.dynamic_config import load_email_config
from backend.utils.timezone import timezone


async def render_message(subject: str, from_header: str, content: str | dict, template: str | None) -> bytes:
    """
    Render email content

    :param subject: Email subject
    :param from_header: Email sender
    :param content: Email content
    :param template: Email content template
    :return:
    """
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = from_header
    message['date'] = timezone.now().strftime('%a, %d %b %Y %H:%M:%S %z')

    if template:
        async with await open_file(PLUGIN_DIR / 'email' / 'templates' / template, encoding='utf-8') as f:
            html = Template(await f.read(), enable_async=True)
        mail_body = MIMEText(await html.render_async(**content), 'html', 'utf-8')
    else:
        mail_body = MIMEText(content, 'plain', 'utf-8')

    message.attach(mail_body)

    return message.as_bytes()


async def send_email(
    db: AsyncSession,
    recipients: str | list[str],
    subject: str,
    content: str | dict,
    template: str | None = None,
) -> None:
    """
    Send email

    :param db: Database session
    :param recipients: Email recipient
    :param subject: Email subject
    :param content: Email content
    :param template: Email content template
    :return:
    """
    await load_email_config(db)

    try:
        message = await render_message(subject, settings.EMAIL_USERNAME, content, template)
        smtp_client = SMTP(
            hostname=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            use_tls=settings.EMAIL_SSL,
        )
        async with smtp_client:
            await smtp_client.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            await smtp_client.sendmail(settings.EMAIL_USERNAME, recipients, message)
    except Exception as e:
        log.error(f'Failed to send email: {e}')
