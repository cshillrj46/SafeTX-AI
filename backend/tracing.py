# File: backend/tracing.py
"""
Motor de rastreamento on-chain (Fase 1, agora com stablecoins).

Expande, em BFS (busca em largura), o caminho de saída dos fundos a partir
de um endereço investigado — segue para ONDE o dinheiro foi, não de onde
veio. Considera tanto transferências de ETH nativo quanto de stablecoins
(USDT/USDC/DAI), porque validar contra dado real mostrou que a maior parte
do volume de uma hot wallet de exchange é movimentação de token, não de ETH
nativo — e USDT especificamente é o canal mais comum em golpe de
investimento. Tokens fora da whitelist (config.STABLECOIN_CONTRACTS) são
ignorados — o que também filtra naturalmente ataques de dusting/airdrop
spam (confirmado contra dado real: vimos um endereço despejando token
chamado literalmente "ETH" com saldo falso gigante em outro endereço).

Profundidade e volume de transações por endereço são limitados por
configuração para não deixar a investigação rodar indefinidamente nem
estourar o limite de chamadas da API gratuita. Endereços com fan-out de
saída muito alto (validado contra dado real: contratos de bridge/relay
compartilhados por milhares de usuários) são tratados como hub e não são
expandidos — a aresta que leva até eles é registrada, mas o motor não
decompõe quem mais usou aquele contrato.

Rotulagem (sanções, exchanges conhecidas) e a narrativa em PT-BR via LLM
são fases seguintes, ainda não implementadas aqui.
"""
import logging
from collections import deque
from datetime import datetime, timezone

from backend import etherscan_client
from backend.config import (
    STABLECOIN_CONTRACTS,
    SUPPORTED_CHAINS,
    TRACE_HUB_FANOUT_THRESHOLD,
    TRACE_MAX_NODES,
    TRACE_MAX_TXS_PER_ADDRESS,
    TRACE_MIN_VALUE_ETH,
)
from backend.database import SessionLocal, TraceEdge, TraceJob, TraceNode

logger = logging.getLogger("safetx.tracing")


def _to_units(value_str: str, decimals: int) -> float:
    return int(value_str) / (10**decimals)


def _is_relevant_outgoing(tx: dict, address: str) -> bool:
    if tx.get("from", "").lower() != address:
        return False  # só seguimos saída: de onde o dinheiro foi, não veio
    if tx.get("isError") == "1":
        return False  # transação revertida, sem transferência real
    if not tx.get("to"):
        return False  # contract creation: sem endereço de destino
    return True


def _collect_native_edges(address: str, chain_id: int, since_ts: datetime | None) -> list[dict]:
    txs = etherscan_client.get_normal_transactions(address, chain_id=chain_id)
    txs = txs[:TRACE_MAX_TXS_PER_ADDRESS]

    edges = []
    for tx in txs:
        if not _is_relevant_outgoing(tx, address):
            continue

        tx_time = datetime.fromtimestamp(int(tx["timeStamp"]), tz=timezone.utc)
        if since_ts and tx_time < since_ts.replace(tzinfo=timezone.utc):
            continue

        amount = _to_units(tx["value"], 18)
        if amount < TRACE_MIN_VALUE_ETH:
            continue

        edges.append(
            {
                "tx_hash": tx["hash"],
                "to": tx["to"].lower(),
                "amount": amount,
                "token_symbol": None,
                "timestamp": tx_time,
            }
        )
    return edges


def _collect_stablecoin_edges(
    address: str, chain_id: int, chain_name: str, since_ts: datetime | None
) -> list[dict]:
    whitelist = STABLECOIN_CONTRACTS.get(chain_name, {})
    if not whitelist:
        return []

    txs = etherscan_client.get_token_transactions(address, chain_id=chain_id)
    txs = txs[:TRACE_MAX_TXS_PER_ADDRESS]

    edges = []
    for tx in txs:
        if not _is_relevant_outgoing(tx, address):
            continue

        contract = tx.get("contractAddress", "").lower()
        if contract not in whitelist:
            continue  # fora da whitelist: ignora (também filtra dusting/spam)

        symbol, decimals = whitelist[contract]

        tx_time = datetime.fromtimestamp(int(tx["timeStamp"]), tz=timezone.utc)
        if since_ts and tx_time < since_ts.replace(tzinfo=timezone.utc):
            continue

        amount = _to_units(tx["value"], decimals)
        # Stablecoin: 1 unidade ~= 1 USD, então o limiar de poeira em ETH
        # não se aplica direto. Usamos um piso fixo baixo (1 unidade) só
        # pra cortar transferências de teste/poeira, não valor real.
        if amount < 1:
            continue

        edges.append(
            {
                "tx_hash": tx["hash"],
                "to": tx["to"].lower(),
                "amount": amount,
                "token_symbol": symbol,
                "timestamp": tx_time,
            }
        )
    return edges


def run_trace(job_id: int) -> None:
    """
    Executa o job de rastreamento. Pensado para rodar em background
    (FastAPI BackgroundTasks) — por isso abre sua própria sessão de banco em
    vez de reusar a sessão da requisição HTTP, que já pode ter sido fechada
    quando esta função roda.
    """
    db = SessionLocal()
    try:
        job = db.query(TraceJob).filter(TraceJob.id == job_id).first()
        if not job:
            logger.error("Trace job %s não encontrado.", job_id)
            return

        job.status = "running"
        db.commit()

        chain_id = SUPPORTED_CHAINS.get(job.chain)
        if chain_id is None:
            raise ValueError(f"Chain '{job.chain}' não suportada na Fase 1.")

        target = job.target_address.lower()
        visited = {target}
        nodes_created = 1

        target_node = TraceNode(job_id=job_id, address=target, depth=0, is_target=True)
        db.add(target_node)
        db.commit()
        nodes_by_address = {target: target_node}

        queue: deque[tuple[str, int]] = deque([(target, 0)])
        truncated = False

        while queue:
            address, depth = queue.popleft()
            if depth >= job.max_hops:
                continue
            if nodes_created >= TRACE_MAX_NODES:
                logger.warning("Job %s atingiu TRACE_MAX_NODES (%d), parando expansão.", job_id, TRACE_MAX_NODES)
                truncated = True
                break

            edges = _collect_native_edges(address, chain_id, job.since_timestamp)
            edges += _collect_stablecoin_edges(address, chain_id, job.chain, job.since_timestamp)

            is_hub = len(edges) > TRACE_HUB_FANOUT_THRESHOLD
            if is_hub:
                node = nodes_by_address.get(address)
                if node:
                    node.is_likely_hub = True
                logger.info(
                    "Endereço %s tratado como hub (%d saídas relevantes, limiar=%d) — "
                    "registrando arestas, mas não expandindo a partir dele.",
                    address,
                    len(edges),
                    TRACE_HUB_FANOUT_THRESHOLD,
                )

            for edge in edges:
                db.add(
                    TraceEdge(
                        job_id=job_id,
                        tx_hash=edge["tx_hash"],
                        from_address=address,
                        to_address=edge["to"],
                        amount=edge["amount"],
                        token_symbol=edge["token_symbol"],
                        timestamp=edge["timestamp"],
                        depth=depth,
                    )
                )

                if is_hub:
                    continue  # aresta registrada, mas não decompõe o hub

                if edge["to"] not in visited:
                    if nodes_created < TRACE_MAX_NODES:
                        visited.add(edge["to"])
                        nodes_created += 1
                        new_node = TraceNode(job_id=job_id, address=edge["to"], depth=depth + 1, is_target=False)
                        db.add(new_node)
                        nodes_by_address[edge["to"]] = new_node
                        queue.append((edge["to"], depth + 1))
                    else:
                        # Teto de nós atingido no meio da expansão: a aresta foi
                        # gravada (mostra que a transação existe), mas o destino
                        # não foi enfileirado pra continuar — o grafo é parcial.
                        truncated = True

            db.commit()

        job.status = "completed"
        job.was_truncated = truncated
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("Trace job %s concluído: %d nós, %d hops.", job_id, nodes_created, job.max_hops)

    except Exception as e:
        db.rollback()
        job = db.query(TraceJob).filter(TraceJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        logger.exception("Trace job %s falhou.", job_id)
    finally:
        db.close()
        