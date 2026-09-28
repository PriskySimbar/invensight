"""
InvenSight AI — Self-Correcting SQL Agent (LangGraph).

Alur:
  generate_sql → execute_sql → (jika error & retry_count < 2) generate_sql
                             → (jika sukses / retry habis) format_response
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

load_dotenv(Path(__file__).resolve().parent / ".env")

# Default sesuai spek; override via GROQ_MODEL jika Groq sudah menarik model lama.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_ROWS = 150

# Skema harus sinkron dengan seed_data.py — LLM hanya boleh SELECT dari tabel ini.
DB_SCHEMA = """
Tabel warehouses (
  id SERIAL PK,
  code VARCHAR(20) UNIQUE,      -- contoh: WH-JKT-01
  name VARCHAR(120),            -- nama DC
  city VARCHAR(80),             -- kota Indonesia
  province VARCHAR(80),
  address TEXT,
  created_at TIMESTAMPTZ
)

Tabel products (
  id SERIAL PK,
  sku VARCHAR(40) UNIQUE,       -- ELC-xxx (Elektronik) atau ATK-xxx
  name VARCHAR(160),
  category VARCHAR(40),         -- 'Elektronik' | 'ATK'
  unit VARCHAR(20),             -- biasanya 'pcs'
  unit_price NUMERIC(12,2),     -- harga master IDR
  created_at TIMESTAMPTZ
)

Tabel inventory (
  id SERIAL PK,
  warehouse_id INT FK → warehouses.id,
  product_id INT FK → products.id,
  quantity INT,                 -- stok on-hand (>= 0)
  min_stock INT,                -- safety stock
  last_updated TIMESTAMPTZ,
  UNIQUE (warehouse_id, product_id)
)

Tabel transactions (
  id SERIAL PK,
  warehouse_id INT FK → warehouses.id,
  product_id INT FK → products.id,
  txn_type VARCHAR(8),          -- 'IN' | 'OUT'
  quantity INT,                 -- jumlah mutasi (> 0)
  unit_price NUMERIC(12,2),     -- harga pada saat transaksi
  occurred_at TIMESTAMPTZ,      -- 2023-01-01 s/d sekarang
  notes TEXT,
  created_at TIMESTAMPTZ
)
"""

_engine: Engine | None = None
_sql_llm: ChatGroq | None = None
_summary_llm: ChatGroq | None = None


class GraphState(TypedDict):
    question: str
    sql_query: str
    data: list[dict[str, Any]]
    error: str
    retry_count: int
    summary: str
    is_error: bool


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} tidak ditemukan di .env")
    return value


def _sqlalchemy_url(raw: str) -> str:
    """SQLAlchemy 2.1 memetakan postgresql:// ke psycopg3; kita memakai psycopg2."""
    if raw.startswith("postgresql+"):
        return raw
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg2://" + raw[len("postgresql://") :]
    if raw.startswith("postgres://"):
        return "postgresql+psycopg2://" + raw[len("postgres://") :]
    return raw


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            _sqlalchemy_url(_require_env("DATABASE_URL")),
            pool_pre_ping=True,
            pool_size=3,
            max_overflow=2,
        )
    return _engine


def get_sql_llm() -> ChatGroq:
    global _sql_llm
    if _sql_llm is None:
        _sql_llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=0,
            api_key=_require_env("GROQ_API_KEY"),
        )
    return _sql_llm


def get_summary_llm() -> ChatGroq:
    global _summary_llm
    if _summary_llm is None:
        _summary_llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=0.2,
            api_key=_require_env("GROQ_API_KEY"),
        )
    return _summary_llm


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _extract_sql(raw: str) -> str:
    """Ambil statement SQL dari output LLM (bisa terbungkus markdown)."""
    text_out = raw.strip()
    fenced = re.search(r"```(?:sql)?\s*([\s\S]*?)```", text_out, re.IGNORECASE)
    if fenced:
        text_out = fenced.group(1).strip()
    # Buang prefix "SQL:" jika ada.
    text_out = re.sub(r"^(sql\s*:)\s*", "", text_out, flags=re.IGNORECASE)
    return text_out.rstrip(";").strip() + ";"


def _is_read_only_select(sql: str) -> bool:
    """Tolak mutasi / multi-statement. Analytics agent hanya SELECT."""
    cleaned = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*[\s\S]*?\*/", "", cleaned).strip().rstrip(";").strip()
    if ";" in cleaned:
        return False
    return bool(re.match(r"^(with|select)\b", cleaned, re.IGNORECASE))


def generate_sql(state: GraphState) -> dict[str, Any]:
    """Node 1 — tulis / perbaiki query SELECT berdasarkan pertanyaan (+ error sebelumnya)."""
    previous_error = (state.get("error") or "").strip()
    retry_count = state.get("retry_count", 0)

    # Self-correction: setiap kali node ini dipanggil ulang karena error,
    # naikkan retry_count. Percobaan pertama tetap 0.
    if previous_error:
        retry_count += 1

    error_block = ""
    if previous_error:
        error_block = f"""
Query sebelumnya gagal dijalankan.
SQL sebelumnya:
{state.get("sql_query") or "(kosong)"}

Pesan error PostgreSQL:
{previous_error}

Perbaiki query-nya. Jangan ulangi kesalahan yang sama.
"""

    prompt = f"""Kamu adalah SQL analyst untuk warehouse InvenSight AI (PostgreSQL).

SKEMA:
{DB_SCHEMA}

ATURAN:
- Tulis SATU query PostgreSQL, read-only (SELECT atau WITH ... SELECT).
- Jangan INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/GRANT/COPY.
- Gunakan JOIN yang benar (inventory & transactions butuh warehouses/products).
- txn_type hanya 'IN' atau 'OUT'. category hanya 'Elektronik' atau 'ATK'.
- Untuk tren waktu gunakan occurred_at. Untuk stok saat ini gunakan inventory.quantity.
- LIMIT maksimal {MAX_ROWS} kecuali agregasi (COUNT/SUM/AVG) yang sudah merangkum.
- Jangan bungkus penjelasan. Output HANYA SQL.

Pertanyaan user:
{state["question"]}
{error_block}
"""

    response = get_sql_llm().invoke(prompt)
    sql = _extract_sql(str(response.content))

    return {
        "sql_query": sql,
        "retry_count": retry_count,
        "error": "",
        "is_error": False,
    }


def execute_sql(state: GraphState) -> dict[str, Any]:
    """Node 2 — jalankan SQL di Neon (transaksi READ ONLY)."""
    sql = (state.get("sql_query") or "").strip()
    if not sql:
        return {
            "data": [],
            "error": "LLM tidak menghasilkan SQL.",
            "is_error": True,
        }

    if not _is_read_only_select(sql):
        return {
            "data": [],
            "error": "Query ditolak: hanya SELECT/CTE read-only yang diizinkan.",
            "is_error": True,
        }

    try:
        with get_engine().connect() as conn:
            conn.execute(text("SET TRANSACTION READ ONLY"))
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows: list[dict[str, Any]] = []
            for raw_row in result.fetchmany(MAX_ROWS):
                rows.append(
                    {col: _to_jsonable(val) for col, val in zip(columns, raw_row)}
                )
            conn.rollback()
        return {"data": rows, "error": "", "is_error": False}
    except SQLAlchemyError as exc:
        # Error ini akan disuntikkan ke prompt generate_sql pada retry berikutnya.
        origin = getattr(exc, "orig", None)
        message = str(origin or exc)
        return {"data": [], "error": message, "is_error": True}


def format_response(state: GraphState) -> dict[str, Any]:
    """Node 3 — ubah hasil query (atau error final) menjadi ringkasan bahasa natural."""
    error = (state.get("error") or "").strip()
    if error:
        summary = (
            "Maaf, query tidak berhasil dijalankan setelah percobaan perbaikan. "
            f"Detail teknis: {error}"
        )
        return {"summary": summary, "is_error": True}

    payload = json.dumps(state.get("data") or [], ensure_ascii=False, default=str)
    prompt = f"""Kamu adalah analis gudang untuk manajer operasional Indonesia.
Jawab ringkas, profesional, dalam Bahasa Indonesia. Jangan mengarang angka di luar data.

Pertanyaan:
{state["question"]}

SQL yang dipakai:
{state.get("sql_query")}

Data (JSON, bisa terpotong LIMIT):
{payload[:8000]}

Format jawaban dengan markdown yang bersih:
- Gunakan **bold** untuk poin penting
- Gunakan bullet points untuk daftar
- Jangan gunakan asterisk untuk emphasis selain bold
- Jangan gunakan tanda kutip miring
- 1-3 paragraf: temuan utama, angka penting, dan (jika relevan) saran operasional singkat
"""
    response = get_summary_llm().invoke(prompt)
    return {"summary": str(response.content).strip(), "is_error": False}


def route_after_execute(state: GraphState) -> Literal["generate_sql", "format_response"]:
    """
    Conditional edge — self-correction loop.

    execute_sql baru saja jalan.
    - Ada ERROR dan retry_count < 2  → kembali ke generate_sql
      (error PostgreSQL + SQL lama ikut ke prompt agar LLM memperbaiki query).
    - Sukses, ATAU sudah 2 kali gagal (retry_count mencapai 2) → format_response.

    retry_count naik di generate_sql hanya saat node itu dipanggil ulang karena error.
    Alur maksimum: generate → execute → generate → execute → generate → execute → format.
    """
    has_error = bool((state.get("error") or "").strip())
    retry_count = state.get("retry_count", 0)

    if has_error and retry_count < 2:
        return "generate_sql"
    return "format_response"


def build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("generate_sql", generate_sql)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("format_response", format_response)

    workflow.set_entry_point("generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_conditional_edges(
        "execute_sql",
        route_after_execute,
        {
            "generate_sql": "generate_sql",
            "format_response": "format_response",
        },
    )
    workflow.add_edge("format_response", END)
    return workflow.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_analyze(question: str) -> dict[str, Any]:
    """Entry point untuk FastAPI."""
    initial: GraphState = {
        "question": question.strip(),
        "sql_query": "",
        "data": [],
        "error": "",
        "retry_count": 0,
        "summary": "",
        "is_error": False,
    }
    result = get_graph().invoke(initial)
    return {
        "sql_query": result.get("sql_query") or "",
        "data": result.get("data") or [],
        "summary": result.get("summary") or "",
        "is_error": bool(result.get("is_error")),
    }
