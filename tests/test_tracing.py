# File: tests/test_tracing.py
from unittest.mock import patch

from backend import tracing
from backend.database import SessionLocal, TraceEdge, TraceJob, TraceNode

USDT_CONTRACT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
RANDOM_SPAM_TOKEN = "0x9999999999999999999999999999999999999999"


def _make_tx(from_addr, to_addr, value_wei, tx_hash, timestamp=1_700_000_000, is_error="0"):
    return {
        "from": from_addr,
        "to": to_addr,
        "value": str(value_wei),
        "hash": tx_hash,
        "timeStamp": str(timestamp),
        "isError": is_error,
    }


def _make_token_tx(from_addr, to_addr, value_units, contract, tx_hash, timestamp=1_700_000_000, is_error="0"):
    tx = _make_tx(from_addr, to_addr, value_units, tx_hash, timestamp, is_error)
    tx["contractAddress"] = contract
    return tx


def _make_job(db, **overrides):
    defaults = dict(
        requested_by="hill",
        target_address="0xaaa",
        chain="ethereum",
        max_hops=2,
        status="pending",
    )
    defaults.update(overrides)
    job = TraceJob(**defaults)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_trace_expands_two_hops(client, auth_headers):
    job = _make_job(SessionLocal())
    job_id = job.id

    # 0xaaa -> 0xbbb (hop 0->1) -> 0xccc (hop 1->2), só ETH nativo
    native_responses = {
        "0xaaa": [_make_tx("0xaaa", "0xbbb", 2 * 10**18, "0xtx1")],
        "0xbbb": [_make_tx("0xbbb", "0xccc", 1 * 10**18, "0xtx2")],
        "0xccc": [],
    }

    with patch(
        "backend.tracing.etherscan_client.get_normal_transactions",
        side_effect=lambda address, chain_id, **kw: native_responses.get(address, []),
    ), patch("backend.tracing.etherscan_client.get_token_transactions", return_value=[]):
        tracing.run_trace(job_id)

    db = SessionLocal()
    job = db.query(TraceJob).filter(TraceJob.id == job_id).first()
    nodes = db.query(TraceNode).filter(TraceNode.job_id == job_id).all()
    edges = db.query(TraceEdge).filter(TraceEdge.job_id == job_id).all()
    db.close()

    assert job.status == "completed"
    assert {n.address for n in nodes} == {"0xaaa", "0xbbb", "0xccc"}
    assert len(edges) == 2
    assert any(e.tx_hash == "0xtx1" and e.amount == 2 and e.token_symbol is None for e in edges)


def test_trace_ignores_dust_and_incoming_and_failed_tx(client, auth_headers):
    job = _make_job(SessionLocal(), max_hops=1)
    job_id = job.id

    txs = [
        _make_tx("0xaaa", "0xbbb", int(0.0001 * 10**18), "0xdust"),  # abaixo do mínimo
        _make_tx("0xzzz", "0xaaa", 5 * 10**18, "0xincoming"),  # entrada, não saída
        _make_tx("0xaaa", "0xccc", 3 * 10**18, "0xfailed", is_error="1"),  # revertida
        _make_tx("0xaaa", "0xddd", 2 * 10**18, "0xgood"),  # única válida
    ]

    with patch("backend.tracing.etherscan_client.get_normal_transactions", return_value=txs), patch(
        "backend.tracing.etherscan_client.get_token_transactions", return_value=[]
    ):
        tracing.run_trace(job_id)

    db = SessionLocal()
    edges = db.query(TraceEdge).filter(TraceEdge.job_id == job_id).all()
    db.close()

    assert len(edges) == 1
    assert edges[0].tx_hash == "0xgood"


def test_trace_follows_whitelisted_stablecoin(client, auth_headers):
    job = _make_job(SessionLocal(), max_hops=1)
    job_id = job.id

    # 1000 USDT (6 decimais) de 0xaaa pra 0xbbb
    token_txs = [_make_token_tx("0xaaa", "0xbbb", 1000 * 10**6, USDT_CONTRACT, "0xusdt1")]

    with patch("backend.tracing.etherscan_client.get_normal_transactions", return_value=[]), patch(
        "backend.tracing.etherscan_client.get_token_transactions", return_value=token_txs
    ):
        tracing.run_trace(job_id)

    db = SessionLocal()
    edges = db.query(TraceEdge).filter(TraceEdge.job_id == job_id).all()
    nodes = {n.address for n in db.query(TraceNode).filter(TraceNode.job_id == job_id).all()}
    db.close()

    assert len(edges) == 1
    assert edges[0].token_symbol == "USDT"
    assert edges[0].amount == 1000
    assert nodes == {"0xaaa", "0xbbb"}


def test_trace_ignores_non_whitelisted_token_dusting_spam(client, auth_headers):
    job = _make_job(SessionLocal(), max_hops=1)
    job_id = job.id

    # Token fora da whitelist, com valor absurdo (simula o ataque de dusting
    # com token chamado "ETH" e saldo gigante que vimos contra dado real)
    spam_txs = [_make_token_tx("0xaaa", "0xspam", 10**40, RANDOM_SPAM_TOKEN, "0xspamtx")]

    with patch("backend.tracing.etherscan_client.get_normal_transactions", return_value=[]), patch(
        "backend.tracing.etherscan_client.get_token_transactions", return_value=spam_txs
    ):
        tracing.run_trace(job_id)

    db = SessionLocal()
    edges = db.query(TraceEdge).filter(TraceEdge.job_id == job_id).all()
    nodes = {n.address for n in db.query(TraceNode).filter(TraceNode.job_id == job_id).all()}
    db.close()

    assert len(edges) == 0
    assert nodes == {"0xaaa"}  # 0xspam nunca entra no grafo


def test_trace_combines_native_and_stablecoin_edges(client, auth_headers):
    job = _make_job(SessionLocal(), max_hops=1)
    job_id = job.id

    native_txs = [_make_tx("0xaaa", "0xbbb", 1 * 10**18, "0xeth1")]
    token_txs = [_make_token_tx("0xaaa", "0xccc", 500 * 10**6, USDT_CONTRACT, "0xusdt1")]

    with patch("backend.tracing.etherscan_client.get_normal_transactions", return_value=native_txs), patch(
        "backend.tracing.etherscan_client.get_token_transactions", return_value=token_txs
    ):
        tracing.run_trace(job_id)

    db = SessionLocal()
    edges = db.query(TraceEdge).filter(TraceEdge.job_id == job_id).all()
    db.close()

    assert len(edges) == 2
    symbols = {e.token_symbol for e in edges}
    assert symbols == {None, "USDT"}


def test_trace_respects_max_hops(client, auth_headers):
    job = _make_job(SessionLocal(), max_hops=1)
    job_id = job.id

    native_responses = {
        "0xaaa": [_make_tx("0xaaa", "0xbbb", 1 * 10**18, "0xtx1")],
        "0xbbb": [_make_tx("0xbbb", "0xccc", 1 * 10**18, "0xtx2")],
    }

    with patch(
        "backend.tracing.etherscan_client.get_normal_transactions",
        side_effect=lambda address, chain_id, **kw: native_responses.get(address, []),
    ), patch("backend.tracing.etherscan_client.get_token_transactions", return_value=[]):
        tracing.run_trace(job_id)

    db = SessionLocal()
    nodes = {n.address for n in db.query(TraceNode).filter(TraceNode.job_id == job_id).all()}
    db.close()

    # Com max_hops=1, não deve chegar a expandir a partir de 0xbbb
    assert nodes == {"0xaaa", "0xbbb"}


def test_trace_marks_job_failed_on_unsupported_chain(client, auth_headers):
    job = _make_job(SessionLocal(), chain="bitcoin")  # ainda não suportado na Fase 1
    job_id = job.id

    tracing.run_trace(job_id)

    db = SessionLocal()
    job = db.query(TraceJob).filter(TraceJob.id == job_id).first()
    db.close()

    assert job.status == "failed"
    assert "não suportada" in job.error_message.lower() or "not supported" in job.error_message.lower()


def test_create_trace_endpoint_requires_auth(client):
    resp = client.post("/trace", json={"address": "0xaaa"})
    assert resp.status_code == 401


def test_create_trace_endpoint_rejects_unsupported_chain(client, auth_headers):
    resp = client.post("/trace", json={"address": "0xaaa", "chain": "solana"}, headers=auth_headers)
    assert resp.status_code == 400


def test_create_trace_and_get_trace_endpoint(client, auth_headers):
    with patch("backend.tracing.etherscan_client.get_normal_transactions", return_value=[]), patch(
        "backend.tracing.etherscan_client.get_token_transactions", return_value=[]
    ):
        resp = client.post(
            "/trace",
            json={"address": "0xaaa", "max_hops": 1, "case_reference": "Caso de teste"},
            headers=auth_headers,
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        status_resp = client.get(f"/trace/{job_id}", headers=auth_headers)
        assert status_resp.status_code == 200
        body = status_resp.json()
        assert body["target_address"] == "0xaaa"
        assert body["case_reference"] == "Caso de teste"
        assert body["nodes_found"] >= 1
