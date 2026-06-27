# File: backend/main.py
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend import tracing
from backend.ai_model import predict_risk
from backend.auth import router as auth_router
from backend.auth import get_current_user
from backend.config import (
    ALERT_RECIPIENT_EMAIL,
    CORS_ORIGINS,
    HIGH_RISK_AMOUNT_THRESHOLD_ETH,
    SUPPORTED_CHAINS,
    TRACE_MAX_HOPS_ALLOWED,
)
from backend.database import (
    ReclassificationLog,
    TraceEdge,
    TraceJob,
    TraceNode,
    TransactionRecord,
    User,
    get_db,
    init_db,
)
from backend.email_service import send_email_alert
from backend.webhook import send_webhook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("safetx.main")

app = FastAPI(title="SafeTX-AI")
init_db()

# === CORS Setup (origens configuráveis via .env, ver CORS_ORIGINS) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


# === Risk Level Enum ===
class RiskLevel(str, Enum):
    safe = "safe"
    suspicious = "suspicious"
    high_risk = "high-risk"


# === Input Model ===
class TransactionInput(BaseModel):
    sender: str
    recipient: str
    amount_eth: float


# === Analyze Transaction ===
@app.post("/analyze", response_model=RiskLevel)
def analyze_transaction(
    tx: TransactionInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.debug("Analisando transação com regra + IA (usuário=%s)", current_user.username)

    # 1. Regra fixa
    if tx.amount_eth > HIGH_RISK_AMOUNT_THRESHOLD_ETH:
        risk = RiskLevel.high_risk
        logger.debug("Valor acima do limiar. Classificado como: %s", risk)
    else:
        # 2. Modelo IA
        predicted = predict_risk(tx.sender, tx.recipient, tx.amount_eth)
        predicted = (predicted or "").strip().lower()
        logger.debug("IA previu: %s", predicted)

        valid_values = {rl.value for rl in RiskLevel}
        if predicted not in valid_values:
            logger.warning("Previsão inválida/ausente da IA ('%s'). Usando 'suspicious'.", predicted)
            risk = RiskLevel.suspicious
        else:
            risk = RiskLevel(predicted)

    # 3. Gravar no banco
    tx_record = TransactionRecord(
        sender=tx.sender,
        recipient=tx.recipient,
        amount_eth=tx.amount_eth,
        risk=risk,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(tx_record)
    db.commit()

    # 4. Notificações
    if risk == RiskLevel.high_risk and ALERT_RECIPIENT_EMAIL:
        send_webhook(
            {
                "sender": tx.sender,
                "recipient": tx.recipient,
                "amount_eth": tx.amount_eth,
                "risk": risk,
            }
        )

        send_email_alert(
            recipient_email=ALERT_RECIPIENT_EMAIL,
            subject="🚨 SafeTX Alert: High-Risk Transaction Detected",
            content=(
                f"A high-risk transaction was detected:\n\n"
                f"Sender: {tx.sender}\n"
                f"Recipient: {tx.recipient}\n"
                f"Amount (ETH): {tx.amount_eth}\n"
                f"Risk Level: {risk}"
            ),
        )

    return risk


# === Get Transaction History (com paginação real) ===
@app.get("/history")
def get_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(TransactionRecord).order_by(TransactionRecord.id)
    total = query.count()
    records = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": [
            {
                "id": r.id,
                "sender": r.sender,
                "recipient": r.recipient,
                "amount_eth": r.amount_eth,
                "risk": r.risk,
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else "N/A",
            }
            for r in records
        ],
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": (total + limit - 1) // limit if total else 0,
    }


# === Manual Reclassification ===
class ReclassificationInput(BaseModel):
    new_risk: RiskLevel
    reason: str


@app.patch("/reclassify/{tx_id}")
def reclassify_transaction(
    tx_id: int,
    payload: ReclassificationInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = db.query(TransactionRecord).filter(TransactionRecord.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    log = ReclassificationLog(
        transaction_id=tx.id,
        old_risk=tx.risk,
        new_risk=payload.new_risk,
        reason=payload.reason,
        reclassified_by=current_user.username,
    )
    db.add(log)
    tx.risk = payload.new_risk
    db.commit()

    return {"status": "reclassified", "tx_id": tx.id}


# === Get Reclassification Logs ===
@app.get("/reclassifications")
def get_reclassifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = db.query(ReclassificationLog).all()
    return [
        {
            "id": r.id,
            "tx_id": r.transaction_id,
            "old_risk": r.old_risk,
            "new_risk": r.new_risk,
            "reason": r.reason,
            "reclassified_by": r.reclassified_by,
        }
        for r in logs
    ]


# === On-chain tracing (Fase 1: expansão BFS, sem enriquecimento/LLM ainda) ===
class TraceRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    max_hops: int = Field(default=2, ge=1, le=TRACE_MAX_HOPS_ALLOWED)
    case_reference: Optional[str] = None
    since: Optional[datetime] = None


@app.post("/trace", status_code=202)
def create_trace(
    payload: TraceRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.chain not in SUPPORTED_CHAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Chain '{payload.chain}' não suportada. Disponíveis: {list(SUPPORTED_CHAINS)}",
        )

    job = TraceJob(
        requested_by=current_user.username,
        target_address=payload.address,
        chain=payload.chain,
        max_hops=payload.max_hops,
        case_reference=payload.case_reference,
        since_timestamp=payload.since,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(tracing.run_trace, job.id)
    logger.info("Trace job %s aberto por %s para %s", job.id, current_user.username, payload.address)

    return {"job_id": job.id, "status": job.status}


@app.get("/trace/{job_id}")
def get_trace(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(TraceJob).filter(TraceJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Trace job not found")

    nodes = db.query(TraceNode).filter(TraceNode.job_id == job_id).all()
    edges = db.query(TraceEdge).filter(TraceEdge.job_id == job_id).all()
    flagged = [n for n in nodes if n.is_sanctioned or n.is_known_exchange]

    return {
        "job_id": job.id,
        "status": job.status,
        "target_address": job.target_address,
        "chain": job.chain,
        "max_hops": job.max_hops,
        "case_reference": job.case_reference,
        "error_message": job.error_message,
        "nodes_found": len(nodes),
        "flagged_entities": len(flagged),
        "nodes": [
            {
                "address": n.address,
                "depth": n.depth,
                "is_target": n.is_target,
                "label": n.label,
                "is_sanctioned": n.is_sanctioned,
                "is_known_exchange": n.is_known_exchange,
            }
            for n in nodes
        ],
        "edges": [
            {
                "tx_hash": e.tx_hash,
                "from": e.from_address,
                "to": e.to_address,
                "amount": e.amount,
                "token_symbol": e.token_symbol,
                "timestamp": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "depth": e.depth,
            }
            for e in edges
        ],
    }
