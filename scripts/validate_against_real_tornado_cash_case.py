# File: scripts/validate_against_real_tornado_cash_case.py
"""
Script de validação manual (NÃO faz parte da suíte automatizada de
pytest — é executado avulso, documentando que o motor foi testado contra
um caso real, não só contra dado sintético).

Como rodar:
    python scripts/validate_against_real_tornado_cash_case.py

Validação manual com DADO REAL (não mock sintético).

Os dados abaixo foram capturados ao vivo via Blockscout MCP contra o pool de
1.000 USDC do Tornado Cash (0xd96f2B1c14Db8458374d9Aca76E26c3D18364307),
endereço sancionado pela OFAC. Foram convertidos para o formato exato que a
API do Etherscan retorna (campos: from, to, value, contractAddress,
timeStamp, hash) e injetados diretamente no etherscan_client real via
monkeypatch — ou seja, isso executa o código de produção
(backend/tracing.py) sem alteração nenhuma, só substituindo a origem do
dado de rede por uma captura real.
"""
import os
from datetime import datetime
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///./real_world_test.db"
os.environ["SECRET_KEY"] = "real-world-test"
os.environ["EMAIL_ALERTS_ENABLED"] = "false"
os.environ["WEBHOOK_ALERTS_ENABLED"] = "false"

from backend import tracing  # noqa: E402
from backend.database import Base, SessionLocal, TraceEdge, TraceJob, TraceNode, engine  # noqa: E402

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
POOL = "0xd96f2b1c14db8458374d9aca76e26c3d18364307"  # Tornado Cash: 1,000 USDC (OFAC)
RELAYER = "0xaaaaa27ea9ffab81f4735e6b766af985d0c88c61"
CLEAN_ADDR = "0xd6112038202e6a4ab50ecc4487c499d5298c4faa"


def _ts(iso: str) -> str:
    return str(int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()))


def _tok(from_addr, to_addr, value_units_6dec, tx_hash, iso_ts):
    return {
        "from": from_addr,
        "to": to_addr,
        "value": str(value_units_6dec),
        "contractAddress": USDC,
        "hash": tx_hash,
        "timeStamp": _ts(iso_ts),
    }


# === Hop 0 -> 1: retiradas reais do pool sancionado (capturadas via Blockscout) ===
POOL_WITHDRAWALS = [
    _tok(POOL, "0x4858d03b2092fa311fa282debaec1ee3416ad8f2", 1_000_000, "0xb80aee9a", "2026-06-26T09:57:47"),
    _tok(POOL, "0x25fd4d79fb402bcb603f83c1d27b4ac21e123508", 99_000_000, "0xb80aee9a", "2026-06-26T09:57:47"),
    _tok(POOL, RELAYER, 4_379_668, "0x69e679f2", "2026-06-23T17:25:59"),
    _tok(POOL, CLEAN_ADDR, 95_620_332, "0x69e679f2", "2026-06-23T17:25:59"),
    _tok(POOL, RELAYER, 4_363_247, "0x5a0bfc34", "2026-06-23T17:22:23"),
    _tok(POOL, CLEAN_ADDR, 95_636_753, "0x5a0bfc34", "2026-06-23T17:22:23"),
    _tok(POOL, RELAYER, 4_391_431, "0xb9336518", "2026-06-23T17:21:47"),
    _tok(POOL, CLEAN_ADDR, 95_608_569, "0xb9336518", "2026-06-23T17:21:47"),
]

# === Hop 1 -> 2: pra onde o relayer e o "endereço limpo" mandaram o dinheiro ===
RELAYER_OUTFLOW = [
    _tok(RELAYER, "0x66a9893cc07d91d95644aedd05d03f95e1dba8af", 8_169_715, "0x4a38c2f4", "2026-06-23T11:42:11"),
]
CLEAN_ADDR_OUTFLOW = [
    _tok(CLEAN_ADDR, "0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5", 2_700_000_000, "0xedb464fe", "2026-06-25T17:21:23"),
    _tok(CLEAN_ADDR, "0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5", 282_000_000, "0x3209bf26", "2026-06-25T17:19:47"),
    _tok(CLEAN_ADDR, "0xe3478b0bb1a5084567c319096437924948be1964", 851_513, "0x9cf0bd21", "2026-06-23T17:27:47"),
    _tok(CLEAN_ADDR, "0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5", 280_000_000, "0x58c15523", "2026-06-23T17:27:47"),
    _tok(CLEAN_ADDR, "0xe3478b0bb1a5084567c319096437924948be1964", 698_188, "0xf34630d2", "2026-06-23T17:27:11"),
]

TOKEN_DATA = {
    POOL: POOL_WITHDRAWALS,
    RELAYER: RELAYER_OUTFLOW,
    CLEAN_ADDR: CLEAN_ADDR_OUTFLOW,
}


def fake_token_transactions(address, chain_id, **kwargs):
    return TOKEN_DATA.get(address, [])


db = SessionLocal()
job = TraceJob(
    requested_by="hill_validacao_real",
    target_address=POOL,
    chain="ethereum",
    max_hops=2,
    case_reference="Validacao com dado real - Tornado Cash USDC pool (OFAC)",
    status="pending",
)
db.add(job)
db.commit()
db.refresh(job)
job_id = job.id
db.close()

with patch("backend.tracing.etherscan_client.get_normal_transactions", return_value=[]), patch(
    "backend.tracing.etherscan_client.get_token_transactions", side_effect=fake_token_transactions
):
    tracing.run_trace(job_id)

db = SessionLocal()
job = db.query(TraceJob).filter(TraceJob.id == job_id).first()
nodes = db.query(TraceNode).filter(TraceNode.job_id == job_id).order_by(TraceNode.depth).all()
edges = db.query(TraceEdge).filter(TraceEdge.job_id == job_id).order_by(TraceEdge.depth).all()
db.close()

print(f"\n=== Job {job_id} | status={job.status} | erro={job.error_message} ===\n")
print(f"Nós encontrados: {len(nodes)}")
for n in nodes:
    marker = " (ALVO/SANCIONADO)" if n.is_target else ""
    print(f"  [hop {n.depth}] {n.address}{marker}")

print(f"\nArestas encontradas: {len(edges)}")
for e in edges:
    print(f"  [hop {e.depth}] {e.from_address[:10]}... -> {e.to_address[:10]}...  {e.amount:.4f} {e.token_symbol}")
