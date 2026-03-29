import hashlib
import hmac
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent / "students.db"

DEFAULT_ADMIN_LOGIN = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_STUDENT_LOGIN = "student"
DEFAULT_STUDENT_PASSWORD = "student123"
DEFAULT_STUDENT_NAME = "Demo Student"
DEFAULT_STUDENT_GRADE = 10
DEFAULT_STUDENT_BATCH = "HARDCODED"
DEFAULT_STUDENT_ENROLLMENT = 999

_PASSWORD_ALGORITHM = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 310000
_PASSWORD_SALT_BYTES = 16


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_connection():
    """Create a SQLite connection configured for short-lived app operations."""
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def conn():
    return get_connection()


def hash_password(password):
    """Hash a password using PBKDF2 so SQLite stores only derived values."""
    if not password:
        raise ValueError("Password cannot be empty.")

    salt = secrets.token_hex(_PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PASSWORD_ITERATIONS,
    )
    return f"{_PASSWORD_ALGORITHM}${_PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password, stored_hash):
    if not password or not stored_hash:
        return False

    try:
        algorithm, iterations, salt, digest = stored_hash.split("$", 3)
        if algorithm != _PASSWORD_ALGORITHM:
            return False

        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate, digest)
    except (TypeError, ValueError):
        return False


def _table_columns(connection, table_name):
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _ensure_users_password_column(connection):
    if "password_hash" not in _table_columns(connection, "users"):
        connection.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")


def _ensure_indexes(connection):
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_attempts_student_id ON attempts(student_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_t20_attempts_student_id ON t20_attempts(student_id)"
    )


def _backfill_missing_password_hashes(connection):
    """Give legacy rows a deterministic initial password so old data keeps working."""
    rows = connection.execute(
        """
        SELECT id, login_id, role
        FROM users
        WHERE password_hash IS NULL OR TRIM(password_hash) = ''
        """
    ).fetchall()

    for row in rows:
        if row["role"] == "admin":
            initial_password = DEFAULT_ADMIN_PASSWORD
        elif row["login_id"] == DEFAULT_STUDENT_LOGIN:
            initial_password = DEFAULT_STUDENT_PASSWORD
        else:
            initial_password = row["login_id"]

        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(initial_password), row["id"]),
        )


def _ensure_default_student_record(connection):
    row = connection.execute(
        """
        SELECT id
        FROM students
        WHERE name = ? AND batch = ? AND enrollment_id = ?
        LIMIT 1
        """,
        (DEFAULT_STUDENT_NAME, DEFAULT_STUDENT_BATCH, DEFAULT_STUDENT_ENROLLMENT),
    ).fetchone()
    if row:
        return row["id"]

    student_id = str(uuid.uuid4())
    connection.execute(
        """
        INSERT INTO students (id, name, grade, batch, enrollment_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            student_id,
            DEFAULT_STUDENT_NAME,
            DEFAULT_STUDENT_GRADE,
            DEFAULT_STUDENT_BATCH,
            DEFAULT_STUDENT_ENROLLMENT,
        ),
    )
    return student_id


def _ensure_default_admin_user(connection):
    row = connection.execute(
        """
        SELECT id, password_hash, is_active
        FROM users
        WHERE role = 'admin'
        LIMIT 1
        """
    ).fetchone()

    if row:
        updates = []
        params = []

        if not row["password_hash"]:
            updates.append("password_hash = ?")
            params.append(hash_password(DEFAULT_ADMIN_PASSWORD))
        if not row["is_active"]:
            updates.append("is_active = 1")

        if updates:
            params.append(row["id"])
            connection.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                params,
            )
        return row["id"]

    admin_id = str(uuid.uuid4())
    connection.execute(
        """
        INSERT INTO users (id, login_id, role, student_id, created_at, is_active, password_hash)
        VALUES (?, ?, 'admin', NULL, ?, 1, ?)
        """,
        (
            admin_id,
            DEFAULT_ADMIN_LOGIN,
            _utc_now(),
            hash_password(DEFAULT_ADMIN_PASSWORD),
        ),
    )
    return admin_id


def _ensure_default_student_user(connection):
    student_id = _ensure_default_student_record(connection)
    row = connection.execute(
        """
        SELECT id, role, student_id, password_hash, is_active
        FROM users
        WHERE login_id = ?
        LIMIT 1
        """,
        (DEFAULT_STUDENT_LOGIN,),
    ).fetchone()

    if row:
        updates = []
        params = []

        if row["role"] != "student":
            updates.append("role = 'student'")
        if row["student_id"] != student_id:
            updates.append("student_id = ?")
            params.append(student_id)
        if not row["password_hash"]:
            updates.append("password_hash = ?")
            params.append(hash_password(DEFAULT_STUDENT_PASSWORD))
        if not row["is_active"]:
            updates.append("is_active = 1")

        if updates:
            params.append(row["id"])
            connection.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                params,
            )
        return student_id

    connection.execute(
        """
        INSERT INTO users (id, login_id, role, student_id, created_at, is_active, password_hash)
        VALUES (?, ?, 'student', ?, ?, 1, ?)
        """,
        (
            str(uuid.uuid4()),
            DEFAULT_STUDENT_LOGIN,
            student_id,
            _utc_now(),
            hash_password(DEFAULT_STUDENT_PASSWORD),
        ),
    )
    return student_id


def ensure_default_admin_user():
    with get_connection() as connection:
        admin_id = _ensure_default_admin_user(connection)
        connection.commit()
        return admin_id


def ensure_default_student_user():
    with get_connection() as connection:
        student_id = _ensure_default_student_user(connection)
        connection.commit()
        return student_id


def init_db():
    """Create tables, migrate missing columns, and seed default demo users."""
    try:
        with get_connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    grade INTEGER NOT NULL,
                    batch TEXT,
                    enrollment_id INTEGER
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    login_id TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    student_id TEXT,
                    created_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    password_hash TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL
                )
                """
            )

            connection.execute(
                """
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
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_content TEXT NOT NULL,
                    file_type TEXT,
                    description TEXT,
                    uploaded_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                )
                """
            )

            connection.execute(
                """
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
                """
            )

            _ensure_users_password_column(connection)
            _ensure_indexes(connection)
            _backfill_missing_password_hashes(connection)
            _ensure_default_admin_user(connection)
            _ensure_default_student_user(connection)
            connection.commit()

        print("SQLite database initialized successfully.")
        return True
    except sqlite3.Error as exc:
        print(f"Error initializing database: {exc}")
        return False


def ensure_demo_student():
    """Backward-compatible wrapper for older code paths."""
    return ensure_default_student_user()


def get_current_timestamp():
    return datetime.now(timezone.utc).isoformat()


def execute_query(query, params=(), fetch=False):
    try:
        with get_connection() as connection:
            cursor = connection.execute(query, params)
            rows = cursor.fetchall() if fetch else None
            connection.commit()
            return rows
    except sqlite3.Error as exc:
        print(f"Query error: {exc}")
        return None


if __name__ == "__main__":
    init_db()
