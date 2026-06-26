# File: backend/database.py

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
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
