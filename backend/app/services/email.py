import logging
from pathlib import Path

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "emails" / "templates"


class EmailService:
    def send(
        self,
        *,
        to: str,
        subject: str,
        template: str,
        context: dict,
    ) -> None:
        """Send email. Currently logs to stdout (real SMTP wired up in Plan 6)."""
        logger.info(
            "Email to=%s subject=%s template=%s context=%s",
            to,
            subject,
            template,
            context,
        )


email_service = EmailService()
