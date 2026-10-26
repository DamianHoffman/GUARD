import os
import psycopg2


def connect(user_env="ETL_USER", password_env="ETL_PASSWORD", default_user="guard_etl"):
    """Connection settings come from environment variables (see .env.example). No secrets in code."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "guard"),
        user=os.getenv(user_env, default_user),
        password=os.environ[password_env],
        application_name="guard-etl",
    )
