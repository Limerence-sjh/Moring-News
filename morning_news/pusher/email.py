"""Email pusher for Morning News fallback notifications.

Uses SMTP SSL to send HTML-formatted email messages as a fallback push channel
when Server酱 is unavailable or rate-limited.
"""

import html
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from morning_news.models import Message

logger = logging.getLogger(__name__)


class EmailPusher:
    """Push notifications via email (SMTP SSL).

    Args:
        config: Dict with 'smtp_host', 'smtp_port', 'from', 'password', 'to'.
    """

    def __init__(self, config: dict):
        """Initialize email pusher with SMTP configuration.

        Args:
            config: SMTP configuration dict.
        """
        self.smtp_host = config.get("smtp_host", "")
        self.smtp_port = config.get("smtp_port", 465)
        self.from_addr = config.get("from", "")
        self.password = config.get("password", "")
        self.to_addr = config.get("to", "")

    def push(self, message: Message) -> bool:
        """Push a message via email.

        Args:
            message: Message to push.

        Returns:
            True if email sent successfully, False if send failed or config is empty.
        """
        if not self.smtp_host or not self.from_addr or not self.to_addr:
            return False

        try:
            msg = self._create_email(message)

            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as smtp:
                smtp.login(self.from_addr, self.password)
                smtp.sendmail(self.from_addr, self.to_addr, msg.as_string())

            return True

        except smtplib.SMTPException:
            return False
        except Exception as e:
            logger.exception(f"Unexpected error in email push: {e}")
            return False

    def _create_email(self, message: Message) -> MIMEMultipart:
        """Create a MIME email object from a Message.

        Args:
            message: Message to convert to email format.

        Returns:
            MIMEMultipart email object with HTML content.
        """
        email_msg = MIMEMultipart("alternative")
        email_msg["Subject"] = f"Morning News | {message.title}"
        email_msg["From"] = self.from_addr
        email_msg["To"] = self.to_addr

        text_part = MIMEText(message.content, "plain", "utf-8")

        html_content = """
<html>
<head><style>
body { font-family: sans-serif; padding: 20px; }
.source { color: #666; font-size: 12px; }
.content { white-space: pre-wrap; }
</style></head>
<body>
<p class="source">来源: {source} | 级别: {level}</p>
<h2>{title}</h2>
<div class="content">{content}</div>
</body>
</html>
""".format(source=html.escape(message.source), level=html.escape(message.level), title=html.escape(message.title), content=html.escape(message.content))
        html_part = MIMEText(html_content, "html", "utf-8")

        email_msg.attach(text_part)
        email_msg.attach(html_part)

        return email_msg