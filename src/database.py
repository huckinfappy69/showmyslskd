import sqlite3
from pathlib import Path

def get_db_connection(db_path: Path):
    """Opens a connection to the SQLite database."""
    return sqlite3.connect(db_path)

def initialize_database(db_path: Path):
    """Ensures the UserTransfers table exists and creates necessary indexes."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS UserTransfers (
            Id TEXT PRIMARY KEY,
            Username TEXT NOT NULL,
            Artist TEXT NOT NULL,
            Filename TEXT NOT NULL,
            Size INTEGER NOT NULL,
            EndedAt TEXT NOT NULL,
            BytesTransferred INTEGER NOT NULL,
            AverageSpeed REAL NOT NULL,
            State TEXT NOT NULL
        );
    """)

    # ✅ Add indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_username ON UserTransfers (Username);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_endedat ON UserTransfers (EndedAt);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_artist ON UserTransfers (Artist);")

    conn.commit()
    conn.close()

def batch_insert_user_transfers(db_path: Path, transfers):
    """Inserts multiple transfer records in batch for better performance."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT INTO UserTransfers (Id, Username, Artist, Filename, Size, EndedAt, BytesTransferred, AverageSpeed, State)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, transfers)

    conn.commit()
    conn.close()

