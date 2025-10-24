import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from email import policy
from email.parser import BytesParser


DB_PATH = "Fish/db/mail.db" # placeholder path to the SQLite database file
SCHEMA_PATH = "Fish/db/schema.sql"          # peka på din schemafil


# -------- init --------
def init_db(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        con.executescript("PRAGMA foreign_keys = ON;")
        schema_sql = Path(schema_path).read_text(encoding="utf-8")
        con.executescript(schema_sql)
        con.commit()
    finally:
        con.close()

# -------- parse helpers --------
def _parse_eml_fields(eml_bytes: bytes):
    msg = BytesParser(policy=policy.default).parsebytes(eml_bytes)
    from_addr = msg.get("From") or ""
    date_header = msg.get("Date") or ""
    # försök normalisera Received_At: ta Date-headern om den finns, annars UTC now
    try:
        # låt SQLite få ISO8601 (YYYY-MM-DDTHH:MM:SSZ)
        received_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        if date_header:
            # vi lämnar headern rakt av in i Received_At (som TEXT) för enkelhet,
            # alternativt kan du använda email.utils.parsedate_to_datetime för att normalisera
            received_at = date_header
    except Exception:
        received_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    return from_addr, date_header or received_at


# -------- store --------
def store_eml_bytes(
    eml_bytes: bytes,
    user_id: int,
    tag: str | None = None,
    db_path: str = DB_PATH,
) -> int:
    """
    Lagrar ett .eml (bytes) i tabellen Email enligt schema.sql.
    Dedup-logik: om samma användare (User_ID) redan laddat upp samma SHA256,
    återanvänds samma Email_ID; annars skapas en ny rad.
    Returnerar Email_ID.
    """
    sha256 = hashlib.sha256(eml_bytes).hexdigest()
    size_bytes = len(eml_bytes)
    from_addr, received_at = _parse_eml_fields(eml_bytes)

    con = sqlite3.connect(db_path)
    try:
        con.execute("PRAGMA foreign_keys = ON;")
        cur = con.cursor()

        # Finns redan för denna user?
        cur.execute("""
            SELECT Email_ID
            FROM Email
            WHERE User_ID = ? AND SHA256 = ?
        """, (user_id, sha256))
        row = cur.fetchone()
        if row:
            email_id = int(row[0])
        else:
            cur.execute("""
                INSERT INTO Email (User_ID, eml_file, SHA256, Size_Bytes, Received_At, From_Addr, Tag)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                sqlite3.Binary(eml_bytes),
                sha256,
                size_bytes,
                received_at,
                from_addr,
                tag
            ))
            email_id = int(cur.lastrowid)

        # Säkerställ att Analysis-raden finns (Analyzed=0)
        cur.execute("SELECT Email_ID FROM Analysis WHERE Email_ID = ?", (email_id,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO Analysis (Email_ID, Score, Analyzed, Verdict, Details_json, Analyzed_At)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (email_id, None, 0, None, None, None))

        con.commit()
        return email_id
    finally:
        con.close()

# --- User helpers (anonymous uploader) ---
def get_or_create_user(username: str, db_path: str = DB_PATH) -> int:
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        # Se till att username finns (Password_Hash tomt/sentinel för systemkonton)
        cur.execute("""
            INSERT OR IGNORE INTO User (Username, Password_Hash)
            VALUES (?, ?)
        """, (username, "!!SYSTEM!!"))
        con.commit()

        cur.execute("SELECT User_ID FROM User WHERE Username = ?", (username,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("Failed to create or fetch user")
        return int(row[0])
    finally:
        con.close()

def get_anonymous_user_id(db_path: str = DB_PATH) -> int:
    return get_or_create_user("anonymous", db_path=db_path)


# -------- convenience: från fil --------
def store_eml_file(
    file_path: str,
    user_id: int,
    tag: str | None = None,
    db_path: str = DB_PATH,
) -> int:
    data = Path(file_path).read_bytes()
    return store_eml_bytes(data, user_id=user_id, tag=tag, db_path=db_path)
