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

# === Etherscan (motor de rastreamento on-chain) ===
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_BASE_URL = "https://api.etherscan.io/v2/api"

# Chains suportadas na Fase 1 (só EVM via Etherscan v2). Mapeamento de nome
# amigável -> chainid exigido pela API v2 multi-chain.
SUPPORTED_CHAINS = {
    "ethereum": 1,
}

# Stablecoins rastreadas além do ETH nativo — validadas contra a rede real
# (endereço, símbolo e decimais confirmados via Blockscout antes de subir
# este código). BUSD foi deixada de fora de propósito: a Paxos descontinuou
# a emissão em 2024 e o volume residual hoje é irrelevante para investigação.
# Formato: chain -> {endereço do contrato (lowercase): (símbolo, decimais)}
STABLECOIN_CONTRACTS = {
    "ethereum": {
        "0xdac17f958d2ee523a2206206994597c13d831ec7": ("USDT", 6),
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": ("USDC", 6),
        "0x6b175474e89094c44da98b954eedeac495271d0f": ("DAI", 18),
    }
}

# Rate limit do tier free do Etherscan é 5 req/s — usamos margem de segurança.
ETHERSCAN_MAX_REQUESTS_PER_SECOND = float(os.getenv("ETHERSCAN_MAX_REQUESTS_PER_SECOND", "4"))

# A partir de 01/07/2026 o tier free do Etherscan limita a 1000 registros por
# página (antes eram 10000) — já nascemos compatíveis com o limite novo.
ETHERSCAN_PAGE_SIZE = int(os.getenv("ETHERSCAN_PAGE_SIZE", "1000"))

# Filtra transações de poeira (dust) que só poluiriam o grafo sem agregar
# sinal de investigação.
TRACE_MIN_VALUE_ETH = float(os.getenv("TRACE_MIN_VALUE_ETH", "0.001"))

# Limites de segurança do BFS, para não deixar uma investigação rodar
# indefinidamente nem estourar custo de API contra um hub com milhões de tx
# (ex: hot wallet de exchange grande).
TRACE_MAX_HOPS_ALLOWED = int(os.getenv("TRACE_MAX_HOPS_ALLOWED", "4"))
TRACE_MAX_NODES = int(os.getenv("TRACE_MAX_NODES", "150"))
TRACE_MAX_TXS_PER_ADDRESS = int(os.getenv("TRACE_MAX_TXS_PER_ADDRESS", "1000"))

# Detecção comportamental de hub: se um endereço tem mais saídas relevantes
# do que isso, tratamos como infraestrutura compartilhada (DEX, bridge,
# relayer) e PARAMOS de expandir a partir dele — continuamos registrando a
# aresta que levou até ali (mostra que o dinheiro passou por lá), mas não
# decompomos "todo mundo que já usou aquele contrato". Validado contra caso
# real: um endereço comum, em 2 hops, frequentemente toca um contrato de
# bridge/relay usado por milhares de pessoas, e sem essa guarda o grafo
# explode mesmo quando o endereço investigado é individual.
TRACE_HUB_FANOUT_THRESHOLD = int(os.getenv("TRACE_HUB_FANOUT_THRESHOLD", "40"))