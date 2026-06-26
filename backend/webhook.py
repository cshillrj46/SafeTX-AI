# File: backend/webhook.py
import logging

import requests

from backend.config import WEBHOOK_ALERTS_ENABLED, WEBHOOK_URL

logger = logging.getLogger("safetx.webhook")


def send_webhook(payload: dict) -> bool:
    if not WEBHOOK_ALERTS_ENABLED:
        logger.info("Webhook desabilitado (WEBHOOK_ALERTS_ENABLED=false).")
        return False

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        logger.info("Webhook enviado. Status: %s", response.status_code)
        return response.ok
    except requests.RequestException:
        logger.exception("Falha ao enviar webhook para %s", WEBHOOK_URL)
        return False
