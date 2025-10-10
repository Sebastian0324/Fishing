import sqlite3
import hashlib
import datetime
from pathlib import Path
import email


DB_PATH = "Analysis/mail.db" # placeholder path to the SQLite database file


def init_db(db_path: str = DB_PATH):
    """Skapar tabellen om den inte redan finns."""
    con = sqlite3.connect(db_path)
    con.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY,
        eml BLOB NOT NULL,
        sha256 TEXT UNIQUE NOT NULL,
        size_bytes INTEGER NOT NULL,
        received_at TEXT,
        from_addr TEXT,
        subject TEXT
    );
    """)
    con.commit()
    con.close()


def store_eml(file_path: str, db_path: str = DB_PATH) -> int:
    """
    Läser en .eml-fil och sparar som BLOB i databasen.
    Returnerar email-id:t (nytt eller befintligt).
    """
    data = Path(file_path).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    msg = email.message_from_bytes(data)

    subject = msg.get("Subject")
    from_addr = msg.get("From")
    received_at = msg.get("Date") or datetime.datetime.now(datetime.timezone.utc).isoformat()

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")

    cur = con.cursor()
    cur.execute("SELECT id FROM emails WHERE sha256=?", (sha,))
    row = cur.fetchone()

    if row:
        email_id = row[0]  # redan finns
    else:
        cur.execute("""
        INSERT INTO emails (eml, sha256, size_bytes, received_at, from_addr, subject)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (sqlite3.Binary(data), sha, len(data), received_at, from_addr, subject))
        email_id = cur.lastrowid

    con.commit()
    con.close()
    if email_id is None:
        raise RuntimeError("Failed to store or retrieve email ID from database.")
    return int(email_id)


def fetch_eml(email_id: int, out_path: str, db_path: str = DB_PATH) -> bool:
    """
    Hämtar ett mail ur databasen (via id) och sparar det som .eml-fil.
    Returnerar True om exporten lyckades, annars False.
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("SELECT eml FROM emails WHERE id=?", (email_id,))
    row = cur.fetchone()
    con.close()

    if row:
        Path(out_path).write_bytes(row[0])
        return True
    else:
        return False
