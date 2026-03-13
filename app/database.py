import os

import psycopg2
from psycopg2.extensions import connection as Connection

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/marmitaria",
)


def get_connection() -> Connection:
    return psycopg2.connect(DATABASE_URL)
