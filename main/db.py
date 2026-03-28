import sqlite3
from pathlib import Path
from datetime import datetime
import uuid

# =========================================================
# CONFIG
# =========================================================
DB_PATH = Path(__file__).resolve().parent / "students.db"

# =========================================================
# CONNECTION (SAFE)
# =========================================================
def get_connection():
    """
    Create a SQLite connection with Row factory and timeout for concurrency.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys for attempt saving safety
    conn.execute("PRAGMA foreign_keys = ON")
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
        with get_connection() as c:
            cur = c.cursor()

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
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL
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

            c.commit()
        
        # After creating tables, ensure a Demo Student exists for hardcoded logins
        ensure_demo_student()
        
        print("✅ SQLite database and Demo Student initialized successfully.")
        return True

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

# =========================================================
# HARDCODED HELPER
# =========================================================
def ensure_demo_student():
    """
    Checks for 'Demo Student' in the database. 
    If missing, creates it so hardcoded logins can save attempts.
    """
    try:
        with get_connection() as c:
            cur = c.cursor()
            cur.execute("SELECT id FROM students WHERE name = ?", ("Demo Student",))
            row = cur.fetchone()
            
            if not row:
                demo_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO students (id, name, grade, batch, enrollment_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (demo_id, "Demo Student", 10, "HARDCODED", 999))
                c.commit()
                return demo_id
            return row['id']
    except Exception as e:
        print(f"❌ Failed to ensure demo student: {e}")
        return None

# =========================================================
# UTILITIES
# =========================================================
def get_current_timestamp() -> str:
    """Returns current ISO format timestamp."""
    return datetime.utcnow().isoformat()

def execute_query(query, params=(), fetch=False):
    """Safe query execution wrapper."""
    try:
        with get_connection() as c:
            cur = c.cursor()
            cur.execute(query, params)
            c.commit()
            return cur.fetchall() if fetch else None
    except sqlite3.Error as e:
        print(f"❌ Query error: {e}")
        return None

if __name__ == "__main__":
    init_db()