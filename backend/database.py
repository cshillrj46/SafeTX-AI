# File: backend/database.py

from sqlalchemy import Boolean, create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

from backend.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class TransactionRecord(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, index=True, nullable=False)
    recipient = Column(String, index=True, nullable=False)
    amount_eth = Column(Float, nullable=False)
    risk = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ReclassificationLog(Base):
    __tablename__ = "reclassifications"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, index=True, nullable=False)
    old_risk = Column(String, nullable=False)
    new_risk = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    reclassified_by = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class TraceJob(Base):
    __tablename__ = "trace_jobs"

    id = Column(Integer, primary_key=True, index=True)
    requested_by = Column(String, nullable=False)
    target_address = Column(String, index=True, nullable=False)
    chain = Column(String, nullable=False, default="ethereum")
    max_hops = Column(Integer, nullable=False, default=2)
    case_reference = Column(String, nullable=True)
    since_timestamp = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending|running|completed|failed
    was_truncated = Column(Boolean, nullable=False, default=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class TraceNode(Base):
    __tablename__ = "trace_nodes"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True, nullable=False)
    address = Column(String, index=True, nullable=False)
    depth = Column(Integer, nullable=False, default=0)
    is_target = Column(Boolean, nullable=False, default=False)
    # Heurística comportamental (não depende de lista externa): marcado
    # quando o endereço tem fan-out de saída acima de TRACE_HUB_FANOUT_THRESHOLD
    # — tratado como infraestrutura compartilhada, expansão interrompida ali.
    is_likely_hub = Column(Boolean, nullable=False, default=False)
    # Campos de enriquecimento — ainda não preenchidos na Fase 1 (BFS puro),
    # reservados para a fase de cruzamento com sanctions list / exchanges.
    label = Column(String, nullable=True)
    is_sanctioned = Column(Boolean, nullable=False, default=False)
    is_known_exchange = Column(Boolean, nullable=False, default=False)


class TraceEdge(Base):
    __tablename__ = "trace_edges"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True, nullable=False)
    tx_hash = Column(String, index=True, nullable=False)
    from_address = Column(String, index=True, nullable=False)
    to_address = Column(String, index=True, nullable=False)
    # Quantia já convertida pra unidade humana (ETH para nativo, ou a
    # quantidade de token já dividida pelos decimais corretos).
    amount = Column(Float, nullable=False)
    # None/NULL = transferência de ETH nativo. Caso contrário, símbolo da
    # stablecoin (USDT/USDC/DAI) — ver STABLECOIN_CONTRACTS em config.py.
    token_symbol = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    depth = Column(Integer, nullable=False, default=0)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency do FastAPI: abre uma sessão por request e GARANTE o fechamento
    no final (inclusive em caso de exceção), evitando o vazamento de conexões
    que existia antes (sessões abertas com SessionLocal() e nunca fechadas).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        