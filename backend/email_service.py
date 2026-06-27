# File: backend/email_service.py
"""
Envio de alertas por e-mail.

As credenciais NÃO ficam mais hardcoded aqui — vêm de variáveis de ambiente
(backend/config.py). Antes, este arquivo continha um Gmail App Password real
em texto puro, commitado em um repositório público. Se você está vendo este
comentário, revogue qualquer senha de app antiga em
https://myaccount.google.com/apppasswords antes de gerar uma nova.
"""
import logging
import smtplib
from email.message import EmailMessage

from backend.config import EMAIL_ALERTS_ENABLED, GMAIL_PASS, GMAIL_USER

logger = logging.getLogger("safetx.email")


def send_email_alert(recipient_email: str, subject: str, content: str) -> bool:
    if not EMAIL_ALERTS_ENABLED:
        logger.warning(
            "Alerta de e-mail não enviado: GMAIL_USER/GMAIL_APP_PASSWORD não "
            "configurados (ou EMAIL_ALERTS_ENABLED=false) em .env."
        )
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = recipient_email
    msg.set_content(content)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        logger.info("E-mail de alerta enviado para %s", recipient_email)
        return True
    except Exception:
        logger.exception("Falha ao enviar e-mail de alerta")
        return False
