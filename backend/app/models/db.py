from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..config import settings
from ..core import utcnow

engine = create_async_engine(settings.DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, default="")
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Guardian(Base):
    __tablename__ = "guardians"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    relation: Mapped[str] = mapped_column("relationship", String)
    role: Mapped[str] = mapped_column(String, default="primary")
    link_code: Mapped[str] = mapped_column(String, index=True)
    chat_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linked: Mapped[bool] = mapped_column(Boolean, default=False)


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    source: Mapped[str] = mapped_column(String, default="text")
    verdict: Mapped[str] = mapped_column(String)
    scam_type: Mapped[str] = mapped_column(String)
    language: Mapped[str] = mapped_column(String)
    result_json: Mapped[str] = mapped_column(Text)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    analysis_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    verdict: Mapped[str] = mapped_column(String)
    scam_type: Mapped[str] = mapped_column(String)
    risk_score: Mapped[int] = mapped_column(Integer)
    summary_json: Mapped[str] = mapped_column(Text)
    acked: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class BlocklistEntry(Base):
    __tablename__ = "blocklist"
    value: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, primary_key=True)
    reports: Mapped[int] = mapped_column(Integer, default=1)


class SimSession(Base):
    __tablename__ = "sim_sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    scenario: Mapped[str] = mapped_column(String)
    ui_lang: Mapped[str] = mapped_column(String, default="en")
    history_json: Mapped[str] = mapped_column(Text, default="[]")
    unsafe: Mapped[int] = mapped_column(Integer, default=0)
    neutral: Mapped[int] = mapped_column(Integer, default=0)
    turns: Mapped[int] = mapped_column(Integer, default=0)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String, index=True)
    label: Mapped[str] = mapped_column(String)  # what the user says it really was: scam | safe
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
