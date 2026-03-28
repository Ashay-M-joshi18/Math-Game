import uuid
from datetime import datetime, timezone
from db import conn , get_connection


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ----------------------------
# ADMIN
# ----------------------------

def ensure_default_admin():
    c = get_connection()
    cur = c.cursor()

    # 🔍 Check if admin already exists
    cur.execute("SELECT 1 FROM users WHERE role=? LIMIT 1", ("admin",))
    exists = cur.fetchone()

    if not exists:
        cur.execute("""
            INSERT INTO users 
            (id, login_id, role, student_id, created_at, is_active)
            VALUES (?, ?, 'admin', NULL, ?, 1)
        """, (
            str(uuid.uuid4()),
            "admin",
            _now()
        ))
        c.commit()  # ✅ IMPORTANT

    cur.close()
    c.close()


# ----------------------------
# STUDENTS
# ----------------------------

def _generate_login_id(grade, batch, enrollment_id):
    grade_part = f"{int(grade):02d}"
    batch_part = str(batch)[-2:]
    roll_part = f"{int(enrollment_id):02d}"
    return f"VM-{grade_part}-{batch_part}00{roll_part}"


def create_student_user(name, grade, batch, enrollment_id):
    student_id = str(uuid.uuid4())
    login_id = _generate_login_id(grade, batch, enrollment_id)

    c = conn()
    cur = c.cursor()

    cur.execute("""
        INSERT INTO students (id, name, grade, batch, enrollment_id)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, name, grade, batch, enrollment_id))

    cur.execute("""
        INSERT INTO users (id, login_id, role, student_id, created_at, is_active)
        VALUES (?, ?, 'student', ?, ?, 1)
    """, (
        str(uuid.uuid4()),
        login_id,
        student_id,
        _now()
    ))

    c.commit()
    c.close()

    return login_id


def get_all_students():
    c = conn()
    cur = c.cursor()

    cur.execute("""
        SELECT s.id, s.name, s.grade, s.batch, s.enrollment_id, u.login_id
        FROM students s
        LEFT JOIN users u ON u.student_id = s.id AND u.role='student'
        ORDER BY s.name
    """)

    rows = cur.fetchall()
    c.close()
    return rows


def update_student_details(student_id, name=None, grade=None, batch=None, enrollment_id=None):
    c = conn()
    cur = c.cursor()

    cur.execute("SELECT * FROM students WHERE id=?", (student_id,))
    row = cur.fetchone()

    if not row:
        c.close()
        return False

    data = dict(row)

    new_name = name if name else data["name"]
    new_grade = grade if grade else data["grade"]
    new_batch = batch if batch else data["batch"]
    new_enr = enrollment_id if enrollment_id else data["enrollment_id"]

    cur.execute("""
        UPDATE students
        SET name=?, grade=?, batch=?, enrollment_id=?
        WHERE id=?
    """, (new_name, new_grade, new_batch, new_enr, student_id))

    new_login = _generate_login_id(new_grade, new_batch, new_enr)

    cur.execute("""
        UPDATE users SET login_id=?
        WHERE student_id=? AND role='student'
    """, (new_login, student_id))

    c.commit()
    c.close()
    return True


def delete_student_account(student_id):
    c = conn()
    cur = c.cursor()

    cur.execute("DELETE FROM attempts WHERE student_id=?", (student_id,))
    cur.execute("DELETE FROM t20_attempts WHERE student_id=?", (student_id,))
    cur.execute("DELETE FROM users WHERE student_id=?", (student_id,))
    cur.execute("DELETE FROM students WHERE id=?", (student_id,))

    c.commit()
    c.close()
    return True


# ----------------------------
# LOGIN (NO PASSWORD)
# ----------------------------

def login_user(login_id, password=None):
    # 1. 🔐 HARDCODED MASTER CREDENTIALS CHECK
    # This checks the hardcoded values before even opening a database connection.
    
    if login_id == "admin" and password == "admin@123":
        return {
            "user_id": 0,           # Static ID for master admin
            "role": "admin",
            "student_id": None,
            "login_id": "admin"
        }

    if login_id == "student" and password == "student@123":
        return {
            "user_id": 1,           # Static ID for master student
            "role": "student",
            "student_id": 1,        # Ensure this matches your logic expectations
            "login_id": "student"
        }

    # 2. DATABASE FALLBACK
    # If the hardcoded check fails, proceed to check the SQLite database
    try:
        c = conn()
        cur = c.cursor()

        cur.execute("""
            SELECT id, role, student_id, is_active
            FROM users WHERE login_id=?
        """, (login_id.strip(),))

        row = cur.fetchone()
        c.close()

        if not row:
            return None

        # Convert row to dict if it's a sqlite3.Row object
        data = dict(row)

        if not data["is_active"]:
            return None

        return {
            "user_id": data["id"],
            "role": data["role"],
            "student_id": data["student_id"],
            "login_id": login_id
        }
    except Exception as e:
        print(f"Login database error: {e}")
        return None

# ----------------------------
# ATTEMPTS
# ----------------------------

def save_attempt(student_id, section, operation, level, score, total_q, avg_speed):
    c = conn()
    cur = c.cursor()

    cur.execute("""
        INSERT INTO attempts
        (id, student_id, section, operation, level, score, total_q, avg_speed, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        student_id,
        section,
        operation,
        level,
        int(score or 0),
        int(total_q or 0),
        float(avg_speed or 0),
        _now()
    ))

    c.commit()
    c.close()


def save_t20_attempt(student_id, student_name, operation, difficulty, score, total_q, avg_speed):
    c = conn()
    cur = c.cursor()

    cur.execute("""
        INSERT INTO t20_attempts
        (id, student_id, student_name, operation, difficulty, score, total_q, avg_speed, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        student_id,
        student_name,
        operation,
        difficulty,
        int(score or 0),
        int(total_q or 0),
        float(avg_speed or 0),
        _now()
    ))

    c.commit()
    c.close()


# ----------------------------
# ANALYTICS
# ----------------------------

def get_student_progress():
    c = conn()
    cur = c.cursor()

    cur.execute("""
        SELECT
            s.name,
            COUNT(a.id),
            COALESCE(AVG(a.score), 0),
            COALESCE(MAX(a.score), 0)
        FROM students s
        LEFT JOIN attempts a ON a.student_id = s.id
        GROUP BY s.id
        ORDER BY COUNT(a.id) DESC
    """)

    rows = cur.fetchall()
    c.close()

    return [
        {
            "name": r[0],
            "attempts": r[1],
            "avg_score": r[2],
            "best_score": r[3],
        }
        for r in rows
    ]


# ----------------------------
# FILE MANAGEMENT
# ----------------------------

def upload_file(filename, content, file_type=None, description=None):
    c = conn()
    cur = c.cursor()

    file_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO files
        (id, filename, file_content, file_type, description, uploaded_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (
        file_id,
        filename,
        content,
        file_type,
        description,
        _now()
    ))

    c.commit()
    c.close()

    return file_id


def get_all_files():
    c = conn()
    cur = c.cursor()

    cur.execute("""
        SELECT id, filename, file_type, description, uploaded_at
        FROM files WHERE is_active=1
    """)

    rows = cur.fetchall()
    c.close()

    return [dict(r) for r in rows]


def soft_delete_file(file_id):
    c = conn()
    cur = c.cursor()

    cur.execute("UPDATE files SET is_active=0 WHERE id=?", (file_id,))
    c.commit()
    c.close()
    return True

def get_detailed_analytics(student_id):
    c = conn()
    cur = c.cursor()

    cur.execute("""
        SELECT section, operation, level, score, total_q, avg_speed, created_at
        FROM attempts
        WHERE student_id=?
        ORDER BY created_at DESC
    """, (student_id,))

    rows = cur.fetchall()
    c.close()

    analytics = []
    for r in rows:
        analytics.append({
            "section": r[0],
            "topic": r[1],
            "level": r[2],
            "sub_level": r[2],
            "score": r[3],
            "total_q": r[4],
            "accuracy": round(r[3] / r[4], 4) if r[4] else 0,
            "avg_speed": r[5],
            "time_per_q": r[5],
            "date": r[6],
        })

    return analytics

def reset_student_analytics(student_id):
    c = conn()
    cur = c.cursor()

    cur.execute("DELETE FROM attempts WHERE student_id=?", (student_id,))
    deleted = cur.rowcount

    cur.execute("DELETE FROM t20_attempts WHERE student_id=?", (student_id,))
    deleted += cur.rowcount

    c.commit()
    c.close()

    return deleted

def get_admin_user():
    c = conn()
    cur = c.cursor()

    cur.execute("""
        SELECT id, login_id, is_active
        FROM users
        WHERE role='admin'
        LIMIT 1
    """)

    row = cur.fetchone()
    c.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "login_id": row["login_id"],
        "is_active": row["is_active"],
    }

def get_student(student_id):
    c = conn()
    cur = c.cursor()

    cur.execute("""
        SELECT id, name, grade, batch, enrollment_id
        FROM students
        WHERE id=?
    """, (student_id,))

    row = cur.fetchone()
    c.close()

    if not row:
        return None

    return dict(row)

def update_admin_credentials(new_login=None):
    if new_login is None:
        return False

    c = conn()
    cur = c.cursor()

    cur.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
    row = cur.fetchone()

    if not row:
        c.close()
        return False

    admin_id = row["id"]

    try:
        cur.execute("""
            UPDATE users SET login_id=?
            WHERE id=?
        """, (new_login, admin_id))

        c.commit()
        c.close()
        return True

    except Exception:
        c.rollback()
        c.close()
        raise

def get_file_by_id(file_id: str):
    """Return a single file row, including content, or None."""
    c = conn()
    cur = c.cursor()

    cur.execute(
        """
        SELECT id, filename, file_content, file_type, description, uploaded_at, is_active
        FROM files
        WHERE id = ?
        """,
        (file_id,),
    )

    row = cur.fetchone()
    cur.close()
    c.close()

    if not row:
        return None

    # If using sqlite3.Row (recommended)
    if hasattr(row, "keys"):
        return dict(row)

    # Fallback for tuple
    return {
        "id": row[0],
        "filename": row[1],
        "file_content": row[2],
        "file_type": row[3],
        "description": row[4],
        "uploaded_at": row[5],
        "is_active": row[6],
    }

def hard_delete_file(file_id: str) -> bool:
    """Completely remove a file row from DB."""
    c = conn()
    cur = c.cursor()

    try:
        # Check if file exists
        cur.execute("SELECT 1 FROM files WHERE id = ?", (file_id,))
        if not cur.fetchone():
            cur.close()
            c.close()
            return False

        # Delete the file
        cur.execute("DELETE FROM files WHERE id = ?", (file_id,))
        c.commit()

        cur.close()
        c.close()
        return True

    except Exception:
        c.rollback()
        cur.close()
        c.close()
        raise