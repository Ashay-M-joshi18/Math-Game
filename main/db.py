import os
from pathlib import Path
from urllib.parse import urlsplit

import psycopg2
from psycopg2 import OperationalError

DEFAULT_SUPABASE_URI = (
    "postgresql://postgres:Valueyourminds%4026@"
    "db.zizeolqgtsbknyojphpj.supabase.co:5432/postgres"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_local_env() -> None:
    """Best-effort loader for .env files without adding dependencies."""
    for candidate in (
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / ".env.local",
        PROJECT_ROOT / "main" / ".env",
    ):
        if not candidate.exists():
            continue

        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue

            cleaned = value.strip().strip("'").strip('"')
            os.environ.setdefault(key, cleaned)


def _read_database_uri():
    for env_key in (
        "SUPABASE_POOLER_URI",
        "SUPABASE_URI",
        "DATABASE_URL",
        "POSTGRES_URL",
        "POSTGRES_PRISMA_URL",
    ):
        value = os.getenv(env_key)
        if value:
            return value, env_key

    return DEFAULT_SUPABASE_URI, "DEFAULT_SUPABASE_URI"


def _redacted_endpoint(uri: str) -> str:
    try:
        parsed = urlsplit(uri)
    except ValueError:
        return "<invalid uri>"

    if not parsed.scheme or not parsed.netloc:
        return "<invalid uri>"

    host = parsed.hostname or "<unknown-host>"
    port = parsed.port
    if port:
        return f"{parsed.scheme}://{host}:{port}{parsed.path or ''}"
    return f"{parsed.scheme}://{host}{parsed.path or ''}"


def _looks_like_direct_supabase_uri(uri: str) -> bool:
    try:
        parsed = urlsplit(uri)
    except ValueError:
        lowered = uri.lower()
        return "postgresql://" in lowered and "db." in lowered and ".supabase.co:5432" in lowered

    host = (parsed.hostname or "").lower()
    port = parsed.port or 5432
    return host.startswith("db.") and host.endswith(".supabase.co") and port == 5432


def _looks_like_placeholder_password(uri: str) -> bool:
    lowered = uri.lower()
    return any(
        marker in lowered
        for marker in ("your-password", "[your-password]", "<password>", "{password}")
    )


_load_local_env()
SUPABASE_URI, SUPABASE_URI_SOURCE = _read_database_uri()


def _read_connect_timeout() -> int:
    raw_timeout = os.getenv("DB_CONNECT_TIMEOUT", "4")
    try:
        timeout = int(raw_timeout)
        return timeout if timeout > 0 else 4
    except ValueError:
        return 4


DB_CONNECT_TIMEOUT = _read_connect_timeout()
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")


def conn(retries: int = 3, delay: float = 1.0):
    """Establishes a connection to the Supabase PostgreSQL database with retry."""
    import time
    last_err = None
    for attempt in range(retries):
        try:
            return psycopg2.connect(
                SUPABASE_URI,
                connect_timeout=DB_CONNECT_TIMEOUT,
                sslmode=DB_SSLMODE,
            )
        except OperationalError as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(delay)
    raise last_err


def init_db() -> bool:
    """Initializes database schema. Returns True on success, else False."""
    c = None
    cur = None

    try:
        c = conn()
        cur = c.cursor()

        # In PostgreSQL, ENUM types must be created separately.
        cur.execute("SELECT 1 FROM pg_type WHERE typname = 'user_role'")
        if cur.fetchone() is None:
            cur.execute("CREATE TYPE user_role AS ENUM ('admin', 'student');")

        # STUDENTS table.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                grade INT NOT NULL,
                batch VARCHAR(50)
            )
            """
        )
        cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS enrollment_id INT")

        # USERS table.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                login_id VARCHAR(50) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role user_role NOT NULL,
                student_id VARCHAR(36) REFERENCES students(id),
                created_at TIMESTAMPTZ NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id VARCHAR(36) PRIMARY KEY,
                student_id VARCHAR(36) NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                score INT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        # Add columns if they don't exist to upgrade old schemas
        cur.execute("ALTER TABLE attempts ADD COLUMN IF NOT EXISTS section VARCHAR(50)")
        cur.execute("ALTER TABLE attempts ADD COLUMN IF NOT EXISTS topic VARCHAR(50)")
        cur.execute("ALTER TABLE attempts ADD COLUMN IF NOT EXISTS operation VARCHAR(50)")
        cur.execute("ALTER TABLE attempts ADD COLUMN IF NOT EXISTS level INT")
        cur.execute("ALTER TABLE attempts ADD COLUMN IF NOT EXISTS total_q INT")
        cur.execute("ALTER TABLE attempts ADD COLUMN IF NOT EXISTS avg_speed FLOAT")

        # Drop legacy 'topic' column if it still exists (replaced by 'operation')
        cur.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name='attempts' AND column_name='topic';
            """
        )
        if cur.fetchone():
            # Backfill section from topic before dropping, so we don't lose info
            cur.execute("""
                UPDATE attempts
                SET section = CASE
                    WHEN topic IN ('Squares', 'Cubes', 'Sq Roots', 'Cube Roots', 'Word Problems')
                        THEN 'Advanced'
                    ELSE 'Basic'
                END
                WHERE section IS NULL AND topic IS NOT NULL;
            """)
            cur.execute("ALTER TABLE attempts DROP COLUMN topic")

        # Migrate any legacy "speed" strings into avg_speed before we drop the column.
        # Old versions stored the per‑question speed as a varchar (sometimes with an
        # "s" suffix) and the column was required.  After the switch to
        # avg_speed the old field became obsolete, but it remained in databases
        # which leads to NOT NULL violations when new inserts omit it entirely.
        #
        # We only run the migration if the column still exists; on subsequent
        # initialisation attempts the column will have been dropped and trying to
        # reference it raises an error (see the log messages seen by the user).
        cur.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name='attempts' AND column_name='speed';
            """
        )
        if cur.fetchone():
            # perform the copy and then remove the legacy field
            cur.execute(r"""
                UPDATE attempts
                SET avg_speed = CASE
                    WHEN speed ~ '^[0-9]+(\.[0-9]+)?$' THEN speed::float
                    WHEN speed LIKE '%s' THEN regexp_replace(speed,'[^0-9.]','','g')::float
                    ELSE NULL
                END
                WHERE avg_speed IS NULL AND speed IS NOT NULL;
            """)
            cur.execute("ALTER TABLE attempts DROP COLUMN speed")
        # if the column wasn't present we don't even attempt the migration; this
        # avoids the informational error floods seen during startup


        # One-time data migration: Backfill 'section' for old records (topic already dropped above)
        cur.execute("""
            UPDATE attempts
            SET section = 'Basic'
            WHERE section IS NULL;
        """)

        # Backfill total_q for old records where it was never stored.
        # Use score as a reasonable estimate (score <= total_q in most cases).
        # This prevents accuracy from showing 0.0 for legacy data.
        cur.execute("""
            UPDATE attempts
            SET total_q = score
            WHERE total_q IS NULL AND score IS NOT NULL AND score > 0;
        """)

        # FILES table (for storing uploaded advanced question files).
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id VARCHAR(36) PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_content TEXT NOT NULL,
                file_type VARCHAR(50),
                description TEXT,
                uploaded_at TIMESTAMPTZ NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            )
            """
        )

        # T20 attempts table (student-only): stores one row per operation round.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS t20_attempts (
                id VARCHAR(36) PRIMARY KEY,
                student_id VARCHAR(36) NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                student_name VARCHAR(100),
                operation VARCHAR(50) NOT NULL,
                difficulty VARCHAR(20),
                score INT NOT NULL,
                total_q INT NOT NULL,
                avg_speed FLOAT,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )

        c.commit()
        print("Database initialized successfully.")
        return True
    except OperationalError as e:
        print("Database connection failed during initialization.")
        print(f"URI source: {SUPABASE_URI_SOURCE}")
        print(f"Endpoint: {_redacted_endpoint(SUPABASE_URI)}")
        if _looks_like_placeholder_password(SUPABASE_URI):
            print(
                "Detected placeholder credentials in the DB URI. "
                "Replace them with real values and URL-encode special characters "
                "(for example, @ as %40)."
            )
        if _looks_like_direct_supabase_uri(SUPABASE_URI):
            print(
                "Detected direct Supabase endpoint (port 5432). "
                "This port is blocked on some networks/ISPs."
            )
            print(
                "Use the pooled connection URI (port 6543) from "
                "Supabase Dashboard > Project Settings > Database."
            )
            print("Set it via SUPABASE_POOLER_URI in a .env file or environment variable.")
        else:
            print(
                "Check network/firewall access to Supabase and verify DB credentials, "
                "sslmode, and hostname."
            )
        print(f"Details: {e}")
        return False
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        if cur is not None:
            cur.close()
        if c is not None:
            c.close()
