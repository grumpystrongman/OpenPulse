from __future__ import annotations

from typing import Iterable

import clickhouse_connect
from tenacity import retry, stop_after_attempt, wait_fixed

from .settings import settings


@retry(stop=stop_after_attempt(10), wait=wait_fixed(2))
def get_clickhouse_client():
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_database,
    )


def insert_rows(table: str, rows: list[dict]) -> None:
    if not rows:
        return
    client = get_clickhouse_client()
    columns = list(rows[0].keys())
    data = [[row.get(col) for col in columns] for row in rows]
    client.insert(table=table, column_names=columns, data=data)


def query(sql: str) -> list[dict]:
    client = get_clickhouse_client()
    result = client.query(sql)
    return [dict(zip(result.column_names, row)) for row in result.result_rows]


def execute(sql: str) -> None:
    client = get_clickhouse_client()
    client.command(sql)


def bulk_execute(statements: Iterable[str]) -> None:
    client = get_clickhouse_client()
    for statement in statements:
        statement = statement.strip()
        if statement:
            client.command(statement)
