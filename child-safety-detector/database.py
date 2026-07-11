"""
database.py
------------
Everything related to saving and reading scan results in SQLite.

PRIVACY NOTE:
We never store the actual screenshot image. We only store the
short text that was found on screen (needed to explain the alert
to the parent) plus the AI's classification. This keeps the app
lightweight and privacy-friendly, as required by the project brief.
"""

import sqlite3
from datetime import datetime

DB_NAME = "safety_data.db"


def get_connection():
    """Open a connection to our local SQLite database file."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def init_db():
    """Create the 'scans' table if it does not already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            extracted_text TEXT,
            category TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            reason TEXT,
            suggestion TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_scan(extracted_text, category, risk_level, risk_score, reason, suggestion):
    """Insert one scan result into the database and return its id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scans (timestamp, extracted_text, category, risk_level, risk_score, reason, suggestion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        extracted_text[:500],  # keep only a short snippet, not the whole screen
        category,
        risk_level,
        risk_score,
        reason,
        suggestion,
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_recent_scans(limit=25):
    """Return the most recent scans, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM scans ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats():
    """Return simple counts used by the dashboard summary cards."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM scans")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as c FROM scans WHERE risk_level = 'High'")
    high = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) as c FROM scans WHERE risk_level = 'Medium'")
    medium = cursor.fetchone()["c"]

    cursor.execute("SELECT COUNT(*) as c FROM scans WHERE risk_level = 'Safe'")
    safe = cursor.fetchone()["c"]

    conn.close()
    return {"total": total, "high": high, "medium": medium, "safe": safe}


def clear_all_scans():
    """Wipe all stored data -- used by the 'Clear Data' privacy button."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scans")
    conn.commit()
    conn.close()
