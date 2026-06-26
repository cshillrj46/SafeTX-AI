# File: backend/config.py
"""
Configuração centralizada da aplicação.

Todas as credenciais e parâmetros sensíveis vêm de variáveis de ambiente
(carregadas de um arquivo .env em desenvolvimento). NUNCA hardcode segredos
neste arquivo ou em qualquer outro módulo.
"""
import os
import secrets
from dotenv import load_dotenv

load_dotenv()


def _get_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# === Banco de dados ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./safetx.db")

# === JWT / Autenticação ===
# Em produção, SECRET_KEY é obrigatória. Em desenvolvimento, geramos uma
# chave aleatória por processo (e avisamos) para não travar quem está só
# testando localmente sem configurar .env ainda.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    print(
        "[CONFIG] ⚠️  SECRET_KEY não definida em .env — usando uma chave "
        "temporária gerada para esta execução. Tokens emitidos agora serão "
        "invalidados ao reiniciar o servidor. Defina SECRET_KEY em produção."
    )

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# === E-mail (SMTP) ===
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")
ALERT_RECIPIENT_EMAIL = os.getenv("ALERT_RECIPIENT_EMAIL", GMAIL_USER)
EMAIL_ALERTS_ENABLED = _get_bool("EMAIL_ALERTS_ENABLED", True) and bool(GMAIL_USER and GMAIL_PASS)

# === Webhook ===
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:9000/alert")
WEBHOOK_ALERTS_ENABLED = _get_bool("WEBHOOK_ALERTS_ENABLED", True)

# === CORS ===
# Lista separada por vírgula em CORS_ORIGINS, ex: "http://localhost:5173,https://app.safetx.io"
_default_origins = "http://localhost:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

# === Regras de negócio ===
HIGH_RISK_AMOUNT_THRESHOLD_ETH = float(os.getenv("HIGH_RISK_AMOUNT_THRESHOLD_ETH", "25"))
