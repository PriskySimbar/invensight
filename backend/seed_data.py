"""
InvenSight AI — seed data ke Neon PostgreSQL.

Men-drop tabel lama (jika ada), membuat schema warehouse, lalu mengisi data sintetis.
Jalankan dari folder backend:  python seed_data.py
"""

from __future__ import annotations

import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Seed tetap agar hasil bisa direproduksi saat debugging (tetap di-drop & diisi ulang).
RANDOM_SEED = 42

WAREHOUSE_COUNT = 10
PRODUCT_COUNT = 100
INVENTORY_COUNT = 500
TRANSACTION_COUNT = 10_000

# Batch VALUES — di Neon pooler, cursor.executemany() = 1 round-trip per baris (sangat lambat).
TXN_BATCH_SIZE = 2_000

# --- Katalog master (data sintetis yang terasa operasional, bukan lorem ipsum) ---

WAREHOUSES = [
    ("WH-JKT-01", "DC Jakarta Utara", "Jakarta", "DKI Jakarta", "Jl. Cakung Cilincing Raya No. 12"),
    ("WH-SBY-01", "DC Surabaya Timur", "Surabaya", "Jawa Timur", "Jl. Rungkut Industri III No. 8"),
    ("WH-BDG-01", "DC Bandung Barat", "Bandung", "Jawa Barat", "Jl. Soekarno-Hatta No. 456"),
    ("WH-MDN-01", "DC Medan Belawan", "Medan", "Sumatera Utara", "Jl. Pelabuhan Belawan No. 21"),
    ("WH-SMG-01", "DC Semarang Kaligawe", "Semarang", "Jawa Tengah", "Jl. Kaligawe Raya Km. 5"),
    ("WH-MKS-01", "DC Makassar Tamalanrea", "Makassar", "Sulawesi Selatan", "Jl. Perintis Kemerdekaan Km. 10"),
    ("WH-PLB-01", "DC Palembang Ilir", "Palembang", "Sumatera Selatan", "Jl. Soekarno Hatta No. 88"),
    ("WH-DPS-01", "DC Denpasar Bypass", "Denpasar", "Bali", "Jl. Bypass Ngurah Rai No. 33"),
    ("WH-YGY-01", "DC Yogyakarta Godean", "Yogyakarta", "DI Yogyakarta", "Jl. Godean Km. 7 No. 15"),
    ("WH-BPN-01", "DC Balikpapan Kariangau", "Balikpapan", "Kalimantan Timur", "Jl. Kariangau Industrial No. 9"),
]

ELEKTRONIK_ITEMS = [
    ("Laptop 14 inci i5", 8_990_000),
    ("Laptop 15 inci i7", 14_500_000),
    ("Monitor 24 inci IPS", 2_150_000),
    ("Monitor 27 inci 144Hz", 3_450_000),
    ("Keyboard mekanikal RGB", 890_000),
    ("Mouse wireless ergonomis", 275_000),
    ("Headset USB noise-cancel", 1_250_000),
    ("Webcam 1080p", 420_000),
    ("SSD NVMe 512GB", 780_000),
    ("SSD NVMe 1TB", 1_350_000),
    ("HDD 2TB", 890_000),
    ("RAM DDR4 16GB", 650_000),
    ("Power bank 20000mAh", 310_000),
    ("Charger GaN 65W", 245_000),
    ("Kabel USB-C 2m", 65_000),
    ("Hub USB-C 7-in-1", 390_000),
    ("Printer laser A4", 2_850_000),
    ("Scanner dokumen ADF", 3_200_000),
    ("Proyektor portable Full HD", 4_750_000),
    ("Switch network 24-port", 1_890_000),
    ("Access point Wi-Fi 6", 1_150_000),
    ("UPS 1500VA", 2_400_000),
    ("CCTV IP dome 4MP", 980_000),
    ("NVR 8 channel", 2_650_000),
    ("Smartphone Android 128GB", 3_499_000),
    ("Tablet 10 inci", 4_199_000),
    ("Speaker Bluetooth conference", 1_750_000),
    ("Microphone USB podcast", 560_000),
    ("Label printer thermal", 1_280_000),
    ("Barcode scanner 2D", 740_000),
    ("POS terminal Android", 3_850_000),
    ("Kalkulator desktop 12 digit", 185_000),
    ("Lampu meja LED USB", 95_000),
    ("Kipas USB mini", 79_000),
    ("Adaptor HDMI ke VGA", 55_000),
    ("Kartu memori 128GB", 210_000),
    ("Flashdisk 64GB", 89_000),
    ("Flashdisk 128GB", 145_000),
    ("Mousepad XL", 49_000),
    ("Docking station USB-C", 1_650_000),
    ("Toner printer hitam", 420_000),
    ("Toner printer warna", 680_000),
    ("Drum unit printer", 890_000),
    ("Kabel LAN Cat6 305m", 1_150_000),
    ("Patch cord Cat6 3m", 28_000),
    ("Rak server 12U", 3_900_000),
    ("PDU 8 socket", 540_000),
    ("Kamera webcam 4K", 1_890_000),
    ("Tablet drawing 8 inci", 2_250_000),
    ("Smartwatch enterprise", 1_499_000),
]

ATK_ITEMS = [
    ("Kertas A4 70gsm (rim)", 52_000),
    ("Kertas A4 80gsm (rim)", 61_000),
    ("Kertas HVS F4 70gsm (rim)", 55_000),
    ("Pulpen gel 0.5mm (lusin)", 36_000),
    ("Pulpen ballpoint 0.7mm (lusin)", 24_000),
    ("Pensil 2B (lusin)", 18_000),
    ("Spidol whiteboard hitam", 12_500),
    ("Spidol whiteboard warna (set)", 45_000),
    ("Highlighter (set 4)", 22_000),
    ("Penghapus karet (pack 20)", 28_000),
    ("Rautan meja", 35_000),
    ("Penggaris 30cm", 6_500),
    ("Map folder plastik (pack 12)", 42_000),
    ("Ordner A4", 28_000),
    ("Stopmap folio (pack 50)", 75_000),
    ("Amplop coklat A4 (pack 100)", 48_000),
    ("Stapler heavy duty", 85_000),
    ("Isi stapler no.10 (box)", 8_500),
    ("Isi stapler 24/6 (box)", 9_500),
    ("Paper clip 50mm (box)", 7_500),
    ("Binder clip 32mm (box)", 14_000),
    ("Binder clip 51mm (box)", 22_000),
    ("Lem stick 22g (pack 12)", 54_000),
    ("Lakban bening 48mm", 16_000),
    ("Lakban coklat packing", 18_000),
    ("Cutter besar", 19_000),
    ("Isi cutter (pack)", 11_000),
    ("Gunting kantor 8 inci", 21_000),
    ("Sticky notes 3x3 (pack 12)", 38_000),
    ("Index tab divider", 15_000),
    ("Buku tulis 58 lbr (pack 10)", 42_000),
    ("Buku folio bergaris", 14_500),
    ("Kertas stiker A4 (pack 50)", 65_000),
    ("Tinta stempel", 13_000),
    ("Stamp pad", 18_500),
    ("Klip kertas warna (box)", 9_000),
    ("ID card holder + tali", 8_500),
    ("Whiteboard 90x120cm", 385_000),
    ("Penghapus whiteboard", 17_000),
    ("Magnet whiteboard (set)", 24_000),
    ("Kertas foto A4 (pack 50)", 72_000),
    ("Amplop putih kecil (pack 100)", 22_000),
    ("Kertas buffalo A4 (pack 100)", 48_000),
    ("Cover jilid plastik (pack 100)", 55_000),
    ("Spiral binding 10mm (pack)", 32_000),
    ("Tinta printer botol 70ml", 89_000),
    ("Kertas thermal 80x80 (roll)", 21_000),
    ("Bubble wrap 50m", 95_000),
    ("Karton box 30x20x15 (pack 25)", 125_000),
    ("Strapping band PP", 68_000),
]


def load_database_url() -> str:
    """Baca DATABASE_URL dari backend/.env, terlepas dari working directory."""
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)

    url = os.getenv("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL tidak ditemukan di .env")
        sys.exit(1)
    return url


def random_datetime(start: datetime, end: datetime) -> datetime:
    """Ambil timestamp acak antara start dan end (inklusif)."""
    span = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, max(span, 1)))


def build_products() -> list[tuple[str, str, str, str, float]]:
    """
    100 SKU: 50 Elektronik + 50 ATK.
    Return: (sku, name, category, unit, unit_price)
    """
    products: list[tuple[str, str, str, str, float]] = []

    for i, (name, price) in enumerate(ELEKTRONIK_ITEMS, start=1):
        sku = f"ELC-{i:03d}"
        products.append((sku, name, "Elektronik", "pcs", float(price)))

    for i, (name, price) in enumerate(ATK_ITEMS, start=1):
        sku = f"ATK-{i:03d}"
        products.append((sku, name, "ATK", "pcs", float(price)))

    if len(products) != PRODUCT_COUNT:
        raise RuntimeError(f"Katalog produk harus {PRODUCT_COUNT}, dapat {len(products)}")
    return products


def terminate_stale_backends(cur: psycopg2.extensions.cursor) -> None:
    """Lepas session lain di database ini (sisa seed yang terputus) agar DROP/CREATE tidak deadlock."""
    try:
        cur.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = current_database()
              AND pid <> pg_backend_pid()
              AND backend_type = 'client backend'
            """
        )
        terminated = cur.rowcount
        if terminated:
            print(f"  session stale di-terminate: {terminated}", flush=True)
    except psycopg2.Error as exc:
        print(f"  skip terminate backend: {exc.pgerror or exc}", flush=True)


def _exec(cur: psycopg2.extensions.cursor, sql: str) -> None:
    """Satu statement per execute — lebih aman di Neon PgBouncer (pooler)."""
    cur.execute(sql)


def create_schema(cur: psycopg2.extensions.cursor) -> None:
    """Drop lalu buat 4 tabel + index. Urutan drop mundur mengikuti FK."""
    for table in ("transactions", "inventory", "products", "warehouses"):
        print(f"  DROP {table}", flush=True)
        _exec(cur, f"DROP TABLE IF EXISTS {table} CASCADE")

    print("  CREATE warehouses", flush=True)
    _exec(
        cur,
        """
        CREATE TABLE warehouses (
            id          SERIAL PRIMARY KEY,
            code        VARCHAR(20)  NOT NULL UNIQUE,
            name        VARCHAR(120) NOT NULL,
            city        VARCHAR(80)  NOT NULL,
            province    VARCHAR(80)  NOT NULL,
            address     TEXT         NOT NULL,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
        """,
    )
    _exec(
        cur,
        """
        CREATE TABLE products (
            id          SERIAL PRIMARY KEY,
            sku         VARCHAR(40)   NOT NULL UNIQUE,
            name        VARCHAR(160)  NOT NULL,
            category    VARCHAR(40)   NOT NULL
                        CHECK (category IN ('Elektronik', 'ATK')),
            unit        VARCHAR(20)   NOT NULL DEFAULT 'pcs',
            unit_price  NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
            created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
        )
        """,
    )
    _exec(
        cur,
        """
        CREATE TABLE inventory (
            id            SERIAL PRIMARY KEY,
            warehouse_id  INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
            product_id    INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            quantity      INTEGER NOT NULL CHECK (quantity >= 0),
            min_stock     INTEGER NOT NULL DEFAULT 10 CHECK (min_stock >= 0),
            last_updated  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (warehouse_id, product_id)
        )
        """,
    )
    _exec(
        cur,
        """
        CREATE TABLE transactions (
            id            SERIAL PRIMARY KEY,
            warehouse_id  INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
            product_id    INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
            txn_type      VARCHAR(8) NOT NULL CHECK (txn_type IN ('IN', 'OUT')),
            quantity      INTEGER NOT NULL CHECK (quantity > 0),
            unit_price    NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
            occurred_at   TIMESTAMPTZ NOT NULL,
            notes         TEXT,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )

    for sql in (
        "CREATE INDEX idx_inventory_warehouse ON inventory (warehouse_id)",
        "CREATE INDEX idx_inventory_product   ON inventory (product_id)",
        "CREATE INDEX idx_txn_occurred_at     ON transactions (occurred_at)",
        "CREATE INDEX idx_txn_warehouse       ON transactions (warehouse_id)",
        "CREATE INDEX idx_txn_product         ON transactions (product_id)",
        "CREATE INDEX idx_txn_type            ON transactions (txn_type)",
    ):
        _exec(cur, sql)


def seed_warehouses(cur: psycopg2.extensions.cursor) -> list[int]:
    rows = [(code, name, city, province, address) for code, name, city, province, address in WAREHOUSES]
    # Dataset kecil: executemany cukup. Dataset besar (transaksi) memakai execute_values.
    cur.executemany(
        """
        INSERT INTO warehouses (code, name, city, province, address)
        VALUES (%s, %s, %s, %s, %s)
        """,
        rows,
    )
    cur.execute("SELECT id FROM warehouses ORDER BY id")
    return [row[0] for row in cur.fetchall()]


def seed_products(cur: psycopg2.extensions.cursor) -> dict[int, float]:
    """Return mapping product_id -> unit_price untuk snapshot harga di transaksi."""
    cur.executemany(
        """
        INSERT INTO products (sku, name, category, unit, unit_price)
        VALUES (%s, %s, %s, %s, %s)
        """,
        build_products(),
    )
    cur.execute("SELECT id, unit_price FROM products ORDER BY id")
    return {row[0]: float(row[1]) for row in cur.fetchall()}


def seed_inventory(
    cur: psycopg2.extensions.cursor,
    warehouse_ids: list[int],
    product_ids: list[int],
) -> None:
    """500 kombinasi unik warehouse × product (bukan cartesian penuh)."""
    all_pairs = [(w, p) for w in warehouse_ids for p in product_ids]
    pairs = random.sample(all_pairs, INVENTORY_COUNT)

    rows = []
    for warehouse_id, product_id in pairs:
        quantity = random.randint(0, 800)
        # SKU elektronik biasanya safety stock lebih rendah (unit mahal).
        min_stock = random.choice([5, 10, 15, 20, 30, 50])
        rows.append((warehouse_id, product_id, quantity, min_stock))

    cur.executemany(
        """
        INSERT INTO inventory (warehouse_id, product_id, quantity, min_stock)
        VALUES (%s, %s, %s, %s)
        """,
        rows,
    )


def seed_transactions(
    cur: psycopg2.extensions.cursor,
    warehouse_ids: list[int],
    prices: dict[int, float],
) -> None:
    """10.000 mutasi IN/OUT dari 1 Jan 2023 sampai sekarang."""
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    end = datetime.now(timezone.utc)
    product_ids = list(prices.keys())
    notes_pool = [
        "Penerimaan PO supplier",
        "Transfer antar gudang",
        "Pengeluaran fulfillment",
        "Retur pelanggan",
        "Stock opname adjustment",
        "Kiriman cabang",
        None,
    ]

    rows: list[tuple] = []
    for i in range(TRANSACTION_COUNT):
        product_id = random.choice(product_ids)
        txn_type = random.choices(["IN", "OUT"], weights=[0.48, 0.52], k=1)[0]
        qty = random.randint(1, 80) if txn_type == "IN" else random.randint(1, 40)
        # Harga transaksi sedikit bervariasi di sekitar master price (±8%).
        base = prices[product_id]
        unit_price = round(base * random.uniform(0.92, 1.08), 2)
        rows.append(
            (
                random.choice(warehouse_ids),
                product_id,
                txn_type,
                qty,
                unit_price,
                random_datetime(start, end),
                random.choice(notes_pool),
            )
        )

        if len(rows) >= TXN_BATCH_SIZE or i == TRANSACTION_COUNT - 1:
            # Satu INSERT ... VALUES (...), (...) per batch — cepat di Neon pooler.
            execute_values(
                cur,
                """
                INSERT INTO transactions
                    (warehouse_id, product_id, txn_type, quantity, unit_price, occurred_at, notes)
                VALUES %s
                """,
                rows,
                page_size=TXN_BATCH_SIZE,
            )
            print(f"  transaksi terisi: {i + 1}/{TRANSACTION_COUNT}", flush=True)
            rows = []


def print_counts(cur: psycopg2.extensions.cursor) -> None:
    cur.execute(
        """
        SELECT 'warehouses' AS table_name, COUNT(*) FROM warehouses
        UNION ALL
        SELECT 'products', COUNT(*) FROM products
        UNION ALL
        SELECT 'inventory', COUNT(*) FROM inventory
        UNION ALL
        SELECT 'transactions', COUNT(*) FROM transactions
        ORDER BY 1
        """
    )
    print("\nRingkasan baris:")
    for name, count in cur.fetchall():
        print(f"  {name:14s} {count:,}")


def main() -> None:
    random.seed(RANDOM_SEED)
    database_url = load_database_url()

    print("Menghubungkan ke Neon PostgreSQL...", flush=True)
    conn = psycopg2.connect(database_url, connect_timeout=30)
    try:
        # DDL di Neon pooler (PgBouncer) harus autocommit; transaksi panjang mudah deadlock.
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SET lock_timeout = '60s'")
            cur.execute("SET statement_timeout = '120s'")
            print("Membuat ulang schema...", flush=True)
            terminate_stale_backends(cur)
            create_schema(cur)

        conn.autocommit = False
        with conn:
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = '300s'")
                print("Mengisi warehouses...", flush=True)
                warehouse_ids = seed_warehouses(cur)

                print("Mengisi products...", flush=True)
                prices = seed_products(cur)
                product_ids = list(prices.keys())

                print("Mengisi inventory...", flush=True)
                seed_inventory(cur, warehouse_ids, product_ids)

                print("Mengisi transactions (batch insert)...", flush=True)
                seed_transactions(cur, warehouse_ids, prices)

                print_counts(cur)
        print("\nSeed selesai.", flush=True)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
