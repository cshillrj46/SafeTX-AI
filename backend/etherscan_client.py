# File: backend/etherscan_client.py
"""
Cliente para a API v2 (multi-chain) do Etherscan.

V1 foi desativada em 2025-08-15 — todo acesso agora passa por uma única
base URL (ETHERSCAN_BASE_URL) com o parâmetro `chainid` selecionando a rede.
"""
import logging
import threading
import time
from typing import Any

import requests

from backend.config import (
    ETHERSCAN_API_KEY,
    ETHERSCAN_BASE_URL,
    ETHERSCAN_MAX_REQUESTS_PER_SECOND,
    ETHERSCAN_PAGE_SIZE,
)

logger = logging.getLogger("safetx.etherscan")


class EtherscanError(Exception):
    """Erro de configuração ou de resposta da API do Etherscan."""


class EtherscanRateLimiter:
    """
    Pacing simples para não estourar o limite de 5 req/s do tier free.
    Thread-safe porque o BFS pode, no futuro, paralelizar chamadas.
    """

    def __init__(self, max_per_second: float):
        self._min_interval = 1.0 / max_per_second if max_per_second > 0 else 0
        self._lock = threading.Lock()
        self._last_call = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call = time.monotonic()


_rate_limiter = EtherscanRateLimiter(ETHERSCAN_MAX_REQUESTS_PER_SECOND)


def _request(params: dict[str, Any], retries: int = 3) -> Any:
    if not ETHERSCAN_API_KEY:
        raise EtherscanError(
            "ETHERSCAN_API_KEY não configurada no .env. Gere uma chave grátis "
            "em https://etherscan.io/myapikey antes de usar o rastreamento."
        )

    params = {**params, "apikey": ETHERSCAN_API_KEY}

    for attempt in range(1, retries + 1):
        _rate_limiter.wait()
        try:
            response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            if attempt == retries:
                raise EtherscanError(f"Falha de rede ao chamar o Etherscan: {e}") from e
            logger.warning("Etherscan request falhou (tentativa %d/%d): %s", attempt, retries, e)
            time.sleep(1.5 * attempt)
            continue

        body = response.json()
        status = body.get("status")
        message = str(body.get("message", ""))

        # "No transactions found" não é erro — é um endereço sem histórico.
        if status == "0" and "No transactions found" in message:
            return []

        # Mensagens de rate limit do Etherscan vêm com status "0" também.
        if status == "0" and "rate limit" in message.lower():
            if attempt == retries:
                raise EtherscanError("Rate limit do Etherscan excedido mesmo após retries.")
            logger.warning("Rate limit do Etherscan atingido, aguardando antes de tentar novamente.")
            time.sleep(2.0 * attempt)
            continue

        if status == "0":
            raise EtherscanError(f"Etherscan retornou erro: {message}")

        return body.get("result", [])

    raise EtherscanError("Falha ao consultar o Etherscan após múltiplas tentativas.")


def get_normal_transactions(
    address: str,
    chain_id: int,
    start_block: int = 0,
    end_block: int = 99_999_999,
    sort: str = "asc",
) -> list[dict]:
    """
    Busca transações externas (normais, ETH nativo) de um endereço. Pagina
    automaticamente, respeitando o limite de página do tier free.
    """
    return _paginated_request(
        {
            "chainid": chain_id,
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": sort,
        }
    )


def get_token_transactions(
    address: str,
    chain_id: int,
    start_block: int = 0,
    end_block: int = 99_999_999,
    sort: str = "asc",
) -> list[dict]:
    """
    Busca transferências ERC-20 de um endereço (action=tokentx) — SEM filtro
    de contrato, pra gastar 1 chamada por endereço em vez de 1 por token.
    O filtro pela whitelist de stablecoins (config.STABLECOIN_CONTRACTS)
    acontece depois, em backend/tracing.py — isso também é o que naturalmente
    descarta ataques de dusting/airdrop-spam (tokens não rastreados nunca
    entram no grafo).
    """
    return _paginated_request(
        {
            "chainid": chain_id,
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": start_block,
            "endblock": end_block,
            "sort": sort,
        }
    )


def _paginated_request(base_params: dict[str, Any]) -> list[dict]:
    all_results: list[dict] = []
    page = 1

    while True:
        result = _request({**base_params, "page": page, "offset": ETHERSCAN_PAGE_SIZE})
        if not result:
            break

        all_results.extend(result)

        if len(result) < ETHERSCAN_PAGE_SIZE:
            break  # última página
        page += 1

        if page > 10:  # guarda-corpo: nunca mais que 10 páginas por endereço
            logger.warning(
                "Endereço %s tem histórico muito longo (%s), truncando paginação.",
                base_params.get("address"),
                base_params.get("action"),
            )
            break

    return all_results
