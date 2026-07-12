import ssl

from sqlmodel import SQLModel, create_engine
from app.core.config import settings

# Correct connection string for asyncpg
DATABASE_URL = str(settings.DATABASE_URL)

# Use SSL for external databases (Supabase etc.) — skip for local Docker container
_sync_url = DATABASE_URL.replace("+asyncpg", "")
_connect_args = {}
if "supabase.co" in DATABASE_URL or "pooler.supabase.com" in DATABASE_URL:
    _connect_args["sslmode"] = "require"

# pool_pre_ping issues a cheap SELECT 1 before each checkout, so stale
# connections killed by Supabase's Supavisor idle timeout are transparently
# replaced instead of surfacing as "SSL connection has been closed unexpectedly".
# pool_recycle bounds connection age to 5 min as defense-in-depth.
# See Sentry ZABT-API-1D / 1G / 1Y.
engine = create_engine(
    _sync_url,
    echo=False,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
