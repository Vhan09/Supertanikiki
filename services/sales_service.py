"""Persistence helpers for distributor orders."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


DB_FILE = Path(__file__).resolve().parents[1] / "data" / "supertani.db"


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_sales_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS distributor_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nomor_surat TEXT NOT NULL DEFAULT '',
                nama_perusahaan TEXT NOT NULL,
                npwp TEXT NOT NULL DEFAULT '',
                no_rekening TEXT NOT NULL DEFAULT '',
                alamat TEXT NOT NULL DEFAULT '',
                kab_prov TEXT NOT NULL DEFAULT '',
                box INTEGER NOT NULL DEFAULT 0 CHECK (box >= 0),
                karton INTEGER NOT NULL DEFAULT 0 CHECK (karton >= 0)
            )
            """
        )


def list_distributor_orders() -> list[dict]:
    initialize_sales_db()
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM distributor_orders ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def add_distributor_order(order: dict) -> None:
    initialize_sales_db()
    company = str(order.get("nama_perusahaan", "")).strip()
    if not company:
        raise ValueError("Nama perusahaan wajib diisi.")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO distributor_orders
                (nomor_surat, nama_perusahaan, npwp, no_rekening, alamat, kab_prov, box, karton)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(order.get("nomor_surat", "")).strip(),
                company,
                str(order.get("npwp", "")).strip(),
                str(order.get("no_rekening", "")).strip(),
                str(order.get("alamat", "")).strip(),
                str(order.get("kab_prov", "")).strip(),
                int(order.get("box", 0)),
                int(order.get("karton", 0)),
            ),
        )


def delete_distributor_order(order_id: int) -> None:
    initialize_sales_db()
    with get_connection() as connection:
        connection.execute("DELETE FROM distributor_orders WHERE id = ?", (order_id,))
