import logging
import resend
from config import Config

logger = logging.getLogger(__name__)

resend.api_key = Config.RESEND_KEY

FROM_EMAIL = "digest@odapulse.com"

def send_digest(to_email, html_body, daily=True):
    if not Config.RESEND_KEY or Config.RESEND_KEY == "placeholder_get_from_resend":
        logger.warning("RESEND_KEY not configured, skipping email")
        return False
    try:
        period = "Daily" if daily else "Weekly"
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"OdaPulse {period} Digest",
            "html": html_body,
        }
        r = resend.Emails.send(params)
        logger.info(f"Email digest sent to {to_email}: {r.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
