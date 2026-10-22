from contextlib import contextmanager
from typing import Iterator

from flask import Flask
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base


def initialize_database(app: Flask) -> None:
    database_url = app.config["DATABASE_URL"]
    engine_options = {"future": True}
    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            engine_options["poolclass"] = StaticPool

    engine = create_engine(database_url, **engine_options)

    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(connection, _connection_record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    Base.metadata.create_all(engine)
    app.extensions["celebrai_engine"] = engine
    app.extensions["celebrai_session_factory"] = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )


@contextmanager
def session_scope(app: Flask) -> Iterator[Session]:
    session_factory = app.extensions["celebrai_session_factory"]
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def dispose_database(engine: Engine) -> None:
    """Close a database engine, primarily for short-lived test apps."""
    engine.dispose()
