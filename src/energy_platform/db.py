
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# load local settings
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    # read required settings
    required = (
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    )

    settings = {key: os.getenv(key) for key in required}
    missing = [key for key, value in settings.items() if not value]

    if missing:
        raise ValueError(f"Missing database settings: {missing}")

    # connect to postgresql
    return psycopg.connect(
        host=settings["DB_HOST"],
        port=int(settings["DB_PORT"]),
        dbname=settings["DB_NAME"],
        user=settings["DB_USER"],
        password=settings["DB_PASSWORD"],
        options="-c timezone=UTC",
        connect_timeout=10,
    )
