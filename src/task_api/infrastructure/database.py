"""SQLite engine, schema, and session factory."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Engine,
    Index,
    String,
    create_engine,
    select,
)
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator


class UtcDateTime(TypeDecorator[datetime]):
    """Store timezone-aware datetimes and always read them back as UTC."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


class TaskRecord(Base):
    """Relational representation of a task. This is not the domain model."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('low', 'medium', 'high')",
            name="ck_tasks_priority",
        ),
        CheckConstraint(
            "status IN ('open', 'completed')",
            name="ck_tasks_status",
        ),
        CheckConstraint("length(title) BETWEEN 1 AND 200", name="ck_tasks_title_length"),
        CheckConstraint("length(description) <= 2000", name="ck_tasks_description_length"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), nullable=False)


def prepare_sqlite_path(database_url: str) -> None:
    """Create the parent directory for a file-backed SQLite URL."""

    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        return
    database = url.database
    if database is None or database == ":memory:":
        return
    parent = Path(database).parent
    if parent != Path(""):
        parent.mkdir(parents=True, exist_ok=True)


def create_db_engine(database_url: str) -> Engine:
    """Create an engine. In-memory SQLite shares one connection across the pool."""

    url = make_url(database_url)
    connect_args: dict[str, Any] = {}
    engine_kwargs: dict[str, Any] = {}
    if url.drivername.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if url.database in (None, "", ":memory:"):
            engine_kwargs["poolclass"] = StaticPool
    return create_engine(database_url, connect_args=connect_args, **engine_kwargs)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_database(engine: Engine) -> None:
    """Create tables when they are missing.

    This reference project intentionally uses create_all instead of a migration
    tool. The schema is small and recreated in tests. A production service with
    existing data would replace this with versioned migrations.
    """

    Base.metadata.create_all(engine)


def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Yield a session and commit only when the caller finishes cleanly."""

    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def database_reachable(session: Session) -> bool:
    try:
        session.execute(select(1))
    except SQLAlchemyError:
        return False
    return True
