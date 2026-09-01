"""
database.py
-----------
SQLite persistence layer for diagnostic history. Creates the database and
table automatically if they don't exist, and every function is defensive
against a missing/locked/corrupt database file.
"""

import sqlite3
from contextlib import contextmanager

import pandas as pd

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS diagnostic_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,               -- 'real' or 'demo'
    latency REAL,
    packet_loss REAL,
    network_usage REAL,
    active_connections INTEGER,
    cpu_usage REAL,
    network_errors INTEGER,
    is_anomaly INTEGER,
    anomaly_score REAL,
    problem TEXT,
    severity TEXT,
    confidence REAL,
    health_score REAL
);
"""


@contextmanager
def get_connection():
    """Context manager yielding a sqlite3 connection, always closed cleanly."""
    conn = None
    try:
        conn = sqlite3.connect(config.DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn is not None:
            conn.close()


def init_db():
    """Create the database file/table if they don't already exist. Safe to
    call on every app startup."""
    try:
        with get_connection() as conn:
            conn.execute(SCHEMA)
            conn.commit()
        return True
    except Exception as e:
        print(f"[database] init_db failed: {e}")
        return False


def insert_record(metrics: dict, diagnosis_result: dict) -> bool:
    """Persist one metrics+diagnosis snapshot. Returns True/False for success
    so the caller can show a warning without crashing the app."""
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO diagnostic_history (
                    timestamp, source, latency, packet_loss, network_usage,
                    active_connections, cpu_usage, network_errors,
                    is_anomaly, anomaly_score, problem, severity, confidence, health_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metrics.get("timestamp"),
                    metrics.get("source", "real"),
                    metrics.get("latency"),
                    metrics.get("packet_loss"),
                    metrics.get("network_usage"),
                    metrics.get("active_connections"),
                    metrics.get("cpu_usage"),
                    metrics.get("network_errors"),
                    int(bool(diagnosis_result.get("is_anomaly"))),
                    diagnosis_result.get("raw_anomaly_score"),
                    diagnosis_result.get("diagnosis"),
                    diagnosis_result.get("severity"),
                    diagnosis_result.get("confidence"),
                    diagnosis_result.get("health_score"),
                ),
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"[database] insert_record failed: {e}")
        return False


def fetch_history(limit: int = 200) -> pd.DataFrame:
    """Return the most recent `limit` records, oldest first (good for
    charting). Returns an empty DataFrame with the right columns if the DB
    is empty or unavailable, rather than raising."""
    columns = [
        "id", "timestamp", "source", "latency", "packet_loss", "network_usage",
        "active_connections", "cpu_usage", "network_errors", "is_anomaly",
        "anomaly_score", "problem", "severity", "confidence", "health_score",
    ]
    try:
        with get_connection() as conn:
            df = pd.read_sql_query(
                "SELECT * FROM diagnostic_history ORDER BY id DESC LIMIT ?",
                conn,
                params=(limit,),
            )
        if df.empty:
            return pd.DataFrame(columns=columns)
        df = df.sort_values("id").reset_index(drop=True)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df
    except Exception as e:
        print(f"[database] fetch_history failed: {e}")
        return pd.DataFrame(columns=columns)


def clear_history() -> bool:
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM diagnostic_history")
            conn.commit()
        return True
    except Exception as e:
        print(f"[database] clear_history failed: {e}")
        return False


def count_records() -> int:
    try:
        with get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) as c FROM diagnostic_history")
            return int(cur.fetchone()["c"])
    except Exception:
        return 0
