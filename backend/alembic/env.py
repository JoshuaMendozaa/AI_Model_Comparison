import os
os.environ["ALEMBIC"] = "1"

import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make /app importable
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# ---- Import Base and ensure models are loaded so metadata is populated ----
from app.db_base import Base

# Auto-import all modules under app/models so model classes register on Base.metadata
import pkgutil, importlib
import app.models as models_pkg  # this is a package: backend/app/models/__init__.py should exist

for finder, name, ispkg in pkgutil.walk_packages(models_pkg.__path__, models_pkg.__name__ + "."):
    importlib.import_module(name)

target_metadata = Base.metadata

# ---- Alembic config ----
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

db_url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url") or ""
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
config.set_main_option("sqlalchemy.url", db_url)

def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
