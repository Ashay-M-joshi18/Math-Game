import sqlite3
from pathlib import Path
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================
DB_PATH = Path(__file__).resolve().parent / "students.db"


# =========================================================
# CONNECTION (SAFE)
# =========================================================
def get_connection():
    """
    Create a SQLite connection with safety settings.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def conn():
    return get_connection()

# =========================================================
# DATABASE INITIALIZATION
# =========================================================
def init_db() -> bool:
    """
    Initialize all required tables.
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()

            # ------------------ STUDENTS ------------------
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    grade INTEGER NOT NULL,
                    batch TEXT,
                    enrollment_id INTEGER
                )
            """)

            # ------------------ USERS ------------------
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    login_id TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    student_id TEXT,
                    created_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY(student_id) REFERENCES students(id)
                )
            """)

            # ------------------ ATTEMPTS ------------------
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attempts (
                    id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    section TEXT,
                    operation TEXT,
                    level INTEGER,
                    total_q INTEGER,
                    avg_speed REAL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
                )
            """)

            # ------------------ FILES ------------------
            cur.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_content TEXT NOT NULL,
                    file_type TEXT,
                    description TEXT,
                    uploaded_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
            """)

            # ------------------ T20 ATTEMPTS ------------------
            cur.execute("""
                CREATE TABLE IF NOT EXISTS t20_attempts (
                    id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    student_name TEXT,
                    operation TEXT NOT NULL,
                    difficulty TEXT,
                    score INTEGER NOT NULL,
                    total_q INTEGER NOT NULL,
                    avg_speed REAL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
                )
            """)

            conn.commit()

        print("✅ SQLite database initialized successfully.")
        return True

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False


# =========================================================
# SAFE QUERY EXECUTOR (IMPORTANT)
# =========================================================
def execute_query(query, params=(), fetch=False):
    """
    Execute a query safely.
    Prevents database locking issues.
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()

            if fetch:
                return cur.fetchall()

    except sqlite3.OperationalError as e:
        print(f"❌ Database error: {e}")


# =========================================================
# UTILITY FUNCTIONS
# =========================================================
def get_current_timestamp() -> str:
    """
    Returns current UTC timestamp.
    """
    return datetime.utcnow().isoformat()

# Redundate code for testing database connection and schema
if __name__ == "__main__":
    init_db()
    
    c = conn()
    cur = c.cursor()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print([dict(row) for row in cur.fetchall()])
    rows = cur.fetchall()
    for row in rows:
        print(len(row), row)
        id, name = row