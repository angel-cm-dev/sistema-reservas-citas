"""Verifica que la migración de Alembic crea el mismo esquema que los modelos."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.domain.models import Base

BACKEND = Path(__file__).resolve().parents[1]


def test_alembic_upgrade_and_downgrade(tmp_path):
    url = f"sqlite:///{(tmp_path / 'migr.db').as_posix()}"
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)

    command.upgrade(cfg, "head")
    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
    assert tables == set(Base.metadata.tables)
    for name, table in Base.metadata.tables.items():
        cols = {c["name"] for c in inspect(engine).get_columns(name)}
        assert cols == {c.name for c in table.columns}, name
    engine.dispose()

    command.downgrade(cfg, "base")
    engine = create_engine(url)
    assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    engine.dispose()
