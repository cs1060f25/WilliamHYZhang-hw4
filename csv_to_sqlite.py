#!/usr/bin/env python3
"""Convert a CSV file into a SQLite database.

This script is generated with assistance from Cursor and gpt-5-codex. The
final implementation has been reviewed and adjusted manually.
"""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path
from typing import Iterable, Iterator, Sequence, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load a CSV file into a SQLite database."
    )
    parser.add_argument(
        "database",
        help="Path to the SQLite database file (created if missing)",
    )
    parser.add_argument(
        "csv_file",
        help="Path to the CSV file to import (must include a header row)",
    )
    return parser.parse_args()


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def sanitize_identifier(name: str) -> str:
    if not IDENTIFIER_PATTERN.match(name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return name


def normalize_table_name(csv_path: Path) -> str:
    """Return sanitized table name derived from CSV filename."""
    return sanitize_identifier(csv_path.stem)


def read_csv_header(csv_path: Path) -> Tuple[str, ...]:
    with csv_path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
    if not header:
        raise ValueError("CSV file must contain a header row")
    cleaned = [column.lstrip("\ufeff") for column in header]
    return tuple(sanitize_identifier(column) for column in cleaned)


def iter_csv_rows(reader: Iterable[Sequence[str]], expected_len: int) -> Iterator[Tuple[str, ...]]:
    for row in reader:
        if len(row) != expected_len:
            raise ValueError(f"CSV row length mismatch: {row}")
        yield tuple(row)


def ensure_table(cursor: sqlite3.Cursor, table: str, columns: Tuple[str, ...]) -> None:
    columns_sql = ", ".join(f"{col} TEXT" for col in columns)
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} ({columns_sql})")
    cursor.execute(f"DELETE FROM {table}")


def insert_rows(
    cursor: sqlite3.Cursor,
    table: str,
    columns: Tuple[str, ...],
    rows: Iterable[Tuple[str, ...]],
) -> None:
    placeholders = ", ".join("?" for _ in columns)
    column_list = ", ".join(columns)
    cursor.executemany(
        f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})",
        rows,
    )


def main() -> None:
    args = parse_args()
    db_path = Path(args.database)
    csv_path = Path(args.csv_file)

    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    columns = read_csv_header(csv_path)
    table = normalize_table_name(csv_path)

    with csv_path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header is None:
            raise ValueError("CSV file must contain a header row")
        sanitized_header = tuple(
            sanitize_identifier(column.lstrip("\ufeff")) for column in header
        )
        if sanitized_header != columns:
            raise ValueError("CSV header changed during read")

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            ensure_table(cursor, table, columns)
            row_iter = iter_csv_rows(reader, len(columns))
            insert_rows(cursor, table, columns, row_iter)
            connection.commit()


if __name__ == "__main__":
    main()

