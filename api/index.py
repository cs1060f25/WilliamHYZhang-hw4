"""Flask application exposing the HW4 county_data endpoint.

This file was drafted with assistance from GPT-4o (Harvard Sandbox) and
reviewed/modified manually to comply with the assignment specification.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, Tuple

from flask import Flask, jsonify, request


ALLOWED_MEASURE_NAMES = {
    "Violent crime rate",
    "Unemployment",
    "Children in poverty",
    "Diabetic screening",
    "Mammography screening",
    "Preventable hospital stays",
    "Uninsured",
    "Sexually transmitted infections",
    "Physical inactivity",
    "Adult obesity",
    "Premature Death",
    "Daily fine particulate matter",
}


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = BASE_DIR / "data.db"

DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", DEFAULT_DATABASE))


def get_db_connection() -> sqlite3.Connection:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"SQLite database not found at {DATABASE_PATH}. Did you run csv_to_sqlite.py?"
        )
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


app = Flask(__name__)


@app.get("/")
def health_check():
    return jsonify({"status": "ok", "endpoint": "/county_data"})


def validate_payload(payload: Dict[str, str]) -> Tuple[str, str]:
    zip_code = payload.get("zip")
    measure_name = payload.get("measure_name")

    if not zip_code or not measure_name:
        raise ValueError("Both 'zip' and 'measure_name' are required.")

    if not isinstance(zip_code, str) or not zip_code.isdigit() or len(zip_code) != 5:
        raise ValueError("ZIP code must be a 5-digit string.")

    if measure_name not in ALLOWED_MEASURE_NAMES:
        raise ValueError("measure_name is not one of the allowed values.")

    return zip_code, measure_name


def query_county_data(connection: sqlite3.Connection, zip_code: str, measure: str) -> Iterable[sqlite3.Row]:
    query = """
        SELECT
            chr.state,
            chr.county,
            chr.state_code,
            chr.county_code,
            chr.year_span,
            chr.measure_name,
            chr.measure_id,
            chr.numerator,
            chr.denominator,
            chr.raw_value,
            chr.confidence_interval_lower_bound,
            chr.confidence_interval_upper_bound,
            chr.data_release_year,
            chr.fipscode
        FROM county_health_rankings AS chr
        INNER JOIN zip_county AS z
            ON chr.county = z.county
            AND chr.state = z.state_abbreviation
        WHERE z.zip = ?
          AND chr.measure_name = ?
        ORDER BY chr.data_release_year
    """
    cursor = connection.execute(query, (zip_code, measure))
    return cursor.fetchall()


@app.post("/county_data")
def county_data():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON."}), 400

    payload = request.get_json(silent=True) or {}

    if payload.get("coffee") == "teapot":
        return jsonify({"error": "I'm a teapot."}), 418

    try:
        zip_code, measure_name = validate_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        connection = get_db_connection()
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 500

    with connection:
        rows = query_county_data(connection, zip_code, measure_name)

    if not rows:
        return jsonify({"error": "No data found for the provided zip/measure pair."}), 404

    result = [dict(row) for row in rows]
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

