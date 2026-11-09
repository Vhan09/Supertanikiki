import sqlite3
from pathlib import Path
from typing import Iterable


DB_FILE = Path(__file__).resolve().parents[1] / "data" / "supertani.db"


def get_connection() -> sqlite3.Connection:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_inventory_db() -> None:
    with get_connection() as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_produk TEXT UNIQUE NOT NULL,
            nama_produk TEXT NOT NULL,
            kategori TEXT DEFAULT '', satuan TEXT DEFAULT '',
            stok_awal REAL DEFAULT 0, harga_beli REAL DEFAULT 0,
            harga_satuan REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL, kode_produk TEXT NOT NULL,
            jenis TEXT NOT NULL CHECK (jenis IN ('MASUK', 'KELUAR')),
            jumlah REAL NOT NULL CHECK (jumlah > 0), gudang TEXT DEFAULT '',
            referensi TEXT DEFAULT '', keterangan TEXT DEFAULT '',
            FOREIGN KEY (kode_produk) REFERENCES products(kode_produk)
        );
        """)


def list_products() -> list[dict]:
    initialize_inventory_db()
    with get_connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM products ORDER BY nama_produk")]


def list_movements() -> list[dict]:
    initialize_inventory_db()
    with get_connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM stock_movements ORDER BY tanggal DESC, id DESC")]


def get_inventory() -> list[dict]:
    products = list_products()
    totals: dict[str, dict[str, float]] = {}
    for movement in list_movements():
        code = movement["kode_produk"]
        totals.setdefault(code, {"MASUK": 0, "KELUAR": 0})
        totals[code][movement["jenis"]] += float(movement["jumlah"])

    inventory = []
    for product in products:
        movement = totals.get(product["kode_produk"], {"MASUK": 0, "KELUAR": 0})
        item = dict(product)
        item["stok"] = float(product["stok_awal"]) + movement["MASUK"] - movement["KELUAR"]
        item["barang_masuk"] = movement["MASUK"]
        item["barang_keluar"] = movement["KELUAR"]
        inventory.append(item)
    return inventory


def upsert_products(rows: Iterable[dict]) -> tuple[int, int]:
    initialize_inventory_db()
    added = updated = 0
    with get_connection() as connection:
        for row in rows:
            code = str(row.get("kode_produk", row.get("id", ""))).strip()
            name = str(row.get("nama_produk", "")).strip()
            if not code or not name:
                continue
            values = (
                str(row.get("kategori", "")).strip(),
                str(row.get("satuan", "")).strip(),
                float(row.get("stok_awal", row.get("stok", 0)) or 0),
                float(row.get("harga_beli", 0) or 0),
                float(row.get("harga_satuan", row.get("harga_jual", 0)) or 0),
            )
            existing = connection.execute("SELECT id FROM products WHERE kode_produk=?", (code,)).fetchone()
            if existing:
                connection.execute("""UPDATE products SET nama_produk=?, kategori=?, satuan=?, stok_awal=?,
                harga_beli=?, harga_satuan=? WHERE kode_produk=?""", (name, *values, code))
                updated += 1
            else:
                connection.execute("""INSERT INTO products
                (kode_produk, nama_produk, kategori, satuan, stok_awal, harga_beli, harga_satuan)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (code, name, *values))
                added += 1
    return added, updated


def add_movement(row: dict) -> None:
    initialize_inventory_db()
    code = str(row["kode_produk"]).strip()
    kind = str(row["jenis"]).strip().upper()
    amount = float(row["jumlah"])
    if kind not in ("MASUK", "KELUAR"):
        raise ValueError("Jenis barang harus MASUK atau KELUAR")
    if amount <= 0:
        raise ValueError("Jumlah harus lebih besar dari nol")
    with get_connection() as connection:
        if not connection.execute("SELECT 1 FROM products WHERE kode_produk=?", (code,)).fetchone():
            raise ValueError(f"Kode produk '{code}' tidak ditemukan")
        if kind == "KELUAR":
            inventory = {item["kode_produk"]: item["stok"] for item in get_inventory()}
            if inventory.get(code, 0) < amount:
                raise ValueError(f"Stok {code} tidak cukup")
        connection.execute("""INSERT INTO stock_movements
        (tanggal, kode_produk, jenis, jumlah, gudang, referensi, keterangan)
        VALUES (?, ?, ?, ?, ?, ?, ?)""", (
            str(row["tanggal"]), code, kind, amount, str(row.get("gudang", "")),
            str(row.get("referensi", "")), str(row.get("keterangan", ""))))


def import_movements(rows: Iterable[dict]) -> tuple[int, list[str]]:
    added = 0
    errors = []
    for row in rows:
        try:
            add_movement(row)
            added += 1
        except Exception as exc:
            errors.append(str(exc))
    return added, errors


def delete_movement(movement_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM stock_movements WHERE id=?", (movement_id,))


def replace_products(rows: Iterable[dict]) -> int:
    initialize_inventory_db()
    rows = list(rows)
    with get_connection() as connection:
        connection.execute("DELETE FROM stock_movements")
        connection.execute("DELETE FROM products")
    upsert_products(rows)
    return len(rows)


def seed_sample_products() -> None:
    if list_products():
        return
    upsert_products([
        {"kode_produk": "PRD-UREA", "nama_produk": "Pupuk Urea Non-Subsidi", "kategori": "Urea", "satuan": "Sak (50kg)", "stok_awal": 150, "harga_beli": 110000, "harga_satuan": 125000},
        {"kode_produk": "PRD-NPK", "nama_produk": "Pupuk NPK Mutiara 16-16-16", "kategori": "NPK", "satuan": "Sak (50kg)", "stok_awal": 85, "harga_beli": 135000, "harga_satuan": 150000},
        {"kode_produk": "PRD-ORGANIK", "nama_produk": "Pupuk Organik Granul", "kategori": "Organik", "satuan": "Karung", "stok_awal": 200, "harga_beli": 35000, "harga_satuan": 45000},
    ])
