import uuid, secrets
from datetime import datetime, timezone
from db import conn
from auth import hash_password, verify_password
 
def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _ensure_t20_attempts_table(cur):
    """Create student T20 attempts table if an older DB doesn't have it yet."""
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

def ensure_default_admin():
    c = conn()
    cur = c.cursor()

    cur.execute("SELECT 1 FROM users WHERE role=%s LIMIT 1", ("admin",))
    exists = cur.fetchone()

    if not exists:
        admin_login = "admin"
        admin_pass = "Admin@123"  # change later

        cur.execute("""
            INSERT INTO users 
            (id, login_id, password_hash, role, student_id, created_at, is_active)
            VALUES (%s, %s, %s, 'admin', NULL, %s, TRUE)
        """, (
            str(uuid.uuid4()),
            admin_login,
            hash_password(admin_pass),
            _now()
        ))
        c.commit()

    c.close()


def get_admin_user():
    """Return the admin user row as a dict: id, login_id, is_active. Returns None if no admin."""
    c = conn()
    cur = c.cursor()

    cur.execute("SELECT id, login_id, password_hash, is_active FROM users WHERE role=%s LIMIT 1", ("admin",))
    row = cur.fetchone()
    cur.close()
    c.close()

    if not row:
        return None

    if isinstance(row, dict) or hasattr(row, "keys"):
        data = dict(row)
        return {
            "id": data.get("id"),
            "login_id": data.get("login_id"),
            "password_hash": data.get("password_hash"),
            "is_active": data.get("is_active"),
        }

    return {
        "id": row[0],
        "login_id": row[1],
        "password_hash": row[2],
        "is_active": row[3],
    }


def update_admin_credentials(new_login: str = None, new_password: str = None):
    """Update admin `login_id` and/or `password_hash`.
    At least one of `new_login` or `new_password` must be provided.
    Returns True on success, False if admin row not found.
    Raises DB exceptions (e.g. unique constraint) to the caller to handle.
    """
    if new_login is None and new_password is None:
        return False

    c = conn()
    cur = c.cursor()

    cur.execute("SELECT id FROM users WHERE role=%s LIMIT 1", ("admin",))
    row = cur.fetchone()
    if not row:
        cur.close()
        c.close()
        return False

    admin_id = row[0] if not (isinstance(row, dict) or hasattr(row, "keys")) else dict(row).get("id")

    try:
        if new_login is not None:
            cur.execute("UPDATE users SET login_id=%s WHERE id=%s", (new_login, admin_id))
        if new_password is not None:
            cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (hash_password(new_password), admin_id))
        c.commit()
    except Exception:
        c.rollback()
        cur.close()
        c.close()
        raise

    cur.close()
    c.close()
    return True

def create_student_user(name: str, grade: int, batch: str, enrollment_id: int):
    """
    Generates a Login ID: VM-class(2d)-batch(2d)00(reserved)roll(2d)
    Example: VM-10-260018
    """
    student_id = str(uuid.uuid4())
    
    # 1. Format Grade to 2 digits (e.g., 05, 10)
    grade_part = f"{int(grade):02d}"
    
    # 2. Extract last 2 digits of the Batch year (e.g., 2026 -> 26)
    # This also removes the previous batch length constraint
    batch_part = str(batch)[-2:]
    
    # 3. Format Enrollment ID to 2 digits (e.g., 18)
    roll_part = f"{int(enrollment_id):02d}"
    
    # 4. Assemble the login_id with the "00" reserved bits
    login_id = f"VM-{grade_part}-{batch_part}00{roll_part}"
    
    # Generate random numeric password suffix for security
    password = f"Vm@{secrets.randbelow(9000)+1000}"

    c = conn()
    cur = c.cursor()

    # Save to Students Table
    # NOTE: `enrollment_id` column was added to store roll/enrollment numbers.
    # This value is optional and will be stored alongside the student's record.
    cur.execute("""
        INSERT INTO students (id, name, grade, batch, enrollment_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (student_id, name, grade, batch, enrollment_id))

    # Save to Users Table
    cur.execute("""
        INSERT INTO users 
        (id, login_id, password_hash, role, student_id, created_at, is_active)
        VALUES (%s, %s, %s, 'student', %s, %s, TRUE)
    """, (
        str(uuid.uuid4()),
        login_id,
        hash_password(password),
        student_id,
        _now()
    ))

    c.commit()
    c.close()
    return login_id, password


def _generate_login_id(grade: int, batch: str, enrollment_id: int):
    # Helper to create the canonical `login_id` for a student from grade/batch/enrollment.
    # Used when creating new users and when updating student details.
    grade_part = f"{int(grade):02d}"
    batch_part = str(batch)[-2:]
    roll_part = f"{int(enrollment_id):02d}"
    return f"VM-{grade_part}-{batch_part}00{roll_part}"


def get_all_students():
    c = conn()
    cur = c.cursor()

    cur.execute("""
        SELECT s.id, s.name, s.grade, s.batch, s.enrollment_id, u.login_id
        FROM students s
        LEFT JOIN users u ON u.student_id = s.id AND u.role='student'
        ORDER BY s.name
    """)
    # Return rows in the DB driver's native format (sqlite Row or tuples)
    rows = cur.fetchall()
    cur.close()
    c.close()
    return rows
# this function retrieves comprehensive progress metrics for each student by aggregating 
# data from the students, users, and attempts tables. It calculates the total number of attempt
# s, average score, best score, last score, and the timestamp of the last attempt for each 
# student, providing a detailed overview of their performance and activity within the system.
def get_student_progress():
    """
    Returns per-student progress metrics from attempts:
    - attempts_count
    - avg_score
    - best_score
    - last_score
    - last_attempt_at
    """
    c = conn()
    cur = c.cursor()

    cur.execute(
        """
        SELECT
            s.id,
            s.name,
            s.grade,
            s.batch,
            s.enrollment_id,
            u.login_id,
            COUNT(a.id) AS attempts_count,
            COALESCE(AVG(a.score), 0) AS avg_score,
            COALESCE(MAX(a.score), 0) AS best_score,
            (
                SELECT a2.score
                FROM attempts a2
                WHERE a2.student_id = s.id
                ORDER BY a2.created_at DESC
                LIMIT 1
            ) AS last_score,
            MAX(a.created_at) AS last_attempt_at
        FROM students s
        LEFT JOIN users u
            ON u.student_id = s.id
           AND u.role = 'student'
        LEFT JOIN attempts a
            ON a.student_id = s.id
        GROUP BY s.id, s.name, s.grade, s.batch, s.enrollment_id, u.login_id
        ORDER BY attempts_count DESC, avg_score DESC, s.name ASC
        """
    )

    rows = cur.fetchall()
    cur.close()
    c.close()

    result = []
    for row in rows:
        if isinstance(row, dict) or hasattr(row, "keys"):
            row_data = dict(row)
            result.append(
                {
                    "id": row_data.get("id"),
                    "name": row_data.get("name"),
                    "grade": row_data.get("grade"),
                    "batch": row_data.get("batch"),
                    "enrollment_id": row_data.get("enrollment_id"),
                    "login_id": row_data.get("login_id"),
                    "attempts_count": row_data.get("attempts_count") or 0,
                    "avg_score": row_data.get("avg_score") or 0,
                    "best_score": row_data.get("best_score") or 0,
                    "last_score": row_data.get("last_score"),
                    "last_attempt_at": row_data.get("last_attempt_at"),
                }
            )
        else:
            (
                sid,
                name,
                grade,
                batch,
                enrollment_id,
                login_id,
                attempts_count,
                avg_score,
                best_score,
                last_score,
                last_attempt_at,
            ) = row
            result.append(
                {
                    "id": sid,
                    "name": name,
                    "grade": grade,
                    "batch": batch,
                    "enrollment_id": enrollment_id,
                    "login_id": login_id,
                    "attempts_count": attempts_count or 0,
                    "avg_score": avg_score or 0,
                    "best_score": best_score or 0,
                    "last_score": last_score,
                    "last_attempt_at": last_attempt_at,
                }
            )

    return result


def get_detailed_analytics(student_id: str):
    """
    Fetches all attempts for a specific student to build the detail dashboard.
    It selects the 'operation' column but renames it to 'topic' for UI consistency.
    """
    c = conn()
    cur = c.cursor()

    try:
        _ensure_t20_attempts_table(cur)
        c.commit()
        cur.execute("""
            SELECT section, operation, CAST(level AS TEXT) AS level, score, total_q, avg_speed, created_at
            FROM attempts
            WHERE student_id = %s
            UNION ALL
            SELECT
                'T20' AS section,
                operation,
                CASE
                    WHEN LOWER(COALESCE(difficulty, 'easy')) = 'hard' THEN '2'
                    ELSE '1'
                END AS level,
                score,
                total_q,
                avg_speed,
                created_at
            FROM t20_attempts
            WHERE student_id = %s
            ORDER BY created_at DESC
        """, (student_id, student_id))
        
        rows = cur.fetchall()
        
        analytics = []
        for r in rows:
            score   = r[3] or 0
            total_q = r[4] or 0
            avg_speed = r[5]

            if (
                r[1] == "Advanced Quiz"
                and total_q > 0
                and isinstance(avg_speed, (int, float))
                and float(avg_speed).is_integer()
            ):
                encoded = int(avg_speed)
                minutes = encoded // 100
                seconds = encoded % 100
                if 1 <= minutes <= 59 and 0 <= seconds <= 59:
                    avg_speed = round(((minutes * 60) + seconds) / total_q, 2)

            analytics.append({
                "section":    r[0],
                "topic":      r[1],        # 'operation' column → 'topic' for UI
                "level":      r[2],
                "sub_level":  r[2] or 1,   # alias used by ui_analytics difficulty calc
                "score":      score,
                "total_q":    total_q,
                "accuracy":   round(score / total_q, 4) if total_q > 0 else 0,
                "avg_speed":  avg_speed,
                "time_per_q": avg_speed or 0,   # alias used by ui_analytics time/flex calc
                "date":       r[6],
            })
        return analytics
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        return []
    finally:
        cur.close()
        c.close()



def get_student(student_id: str):
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT id, name, grade, batch, enrollment_id FROM students WHERE id=%s", (student_id,))
    row = cur.fetchone()
    cur.close()
    c.close()
    return row

# This function updates the student's details in the database, including their name, grade, batch, and enrollment ID. It also ensures that the corresponding login ID in the users table is updated to reflect any changes in grade, batch, or enrollment number, maintaining consistency across the system.
def update_student_details(student_id: str, name: str = None, grade: int = None, batch: str = None, enrollment_id: int = None):
    c = conn()
    cur = c.cursor()

    # Fetch current values
    cur.execute("SELECT id, name, grade, batch, enrollment_id FROM students WHERE id=%s", (student_id,))
    current = cur.fetchone()
    if not current:
        cur.close()
        c.close()
        return False

    # Normalize access
    if isinstance(current, dict) or hasattr(current, "keys"):
        curdata = dict(current)
    else:
        curdata = {
            "id": current[0],
            "name": current[1],
            "grade": current[2],
            "batch": current[3],
            "enrollment_id": current[4],
        }

    # Determine values to write: keep existing values when None provided
    new_name = name if name is not None else curdata["name"]
    new_grade = int(grade) if grade is not None else int(curdata["grade"])
    new_batch = batch if batch is not None else curdata["batch"]
    new_enrollment = int(enrollment_id) if enrollment_id is not None else (curdata.get("enrollment_id") if curdata.get("enrollment_id") is not None else 0)

    # Update students table
    cur.execute("""
        UPDATE students SET name=%s, grade=%s, batch=%s, enrollment_id=%s WHERE id=%s
    """, (new_name, new_grade, new_batch, new_enrollment, student_id))

    # Recompute `login_id` and update the corresponding user row so login stays in-sync.
    # Note: updating `login_id` may fail if the new value conflicts with an existing login.
    # In that case we rollback the change to avoid leaving inconsistent state.
    new_login = _generate_login_id(new_grade, new_batch or "00", new_enrollment)
    try:
        cur.execute("UPDATE users SET login_id=%s WHERE student_id=%s AND role='student'", (new_login, student_id))
    except Exception:
        # If updating login_id fails (e.g., unique constraint), rollback student change and re-raise
        c.rollback()
        cur.close()
        c.close()
        raise

    c.commit()
    cur.close()
    c.close()
    return True

# This function deletes a student account from the system, including all related records such as their attempts and user login. It ensures that the database remains consistent by first removing dependent records before deleting the main student record, and it handles cases where the student may not exist gracefully.
def delete_student_account(student_id: str):
    """
    Delete a student account and dependent records.

    Order matters because attempts references students via FK:
    1) delete attempts
    2) delete linked student user row(s)
    3) delete student row
    """
    c = conn()
    cur = c.cursor()

    try:
        cur.execute("SELECT 1 FROM students WHERE id=%s", (student_id,))
        if not cur.fetchone():
            cur.close()
            c.close()
            return False

        cur.execute("DELETE FROM attempts WHERE student_id=%s", (student_id,))
        cur.execute("DELETE FROM t20_attempts WHERE student_id=%s", (student_id,))
        cur.execute("DELETE FROM users WHERE student_id=%s", (student_id,))
        cur.execute("DELETE FROM students WHERE id=%s", (student_id,))

        c.commit()
        cur.close()
        c.close()
        return True
    except Exception:
        c.rollback()
        cur.close()
        c.close()
        raise


def reset_student_analytics(student_id: str):
    """Delete only a student's attempt history and keep the account intact."""
    c = conn()
    cur = c.cursor()

    try:
        cur.execute("SELECT 1 FROM students WHERE id=%s", (student_id,))
        if not cur.fetchone():
            cur.close()
            c.close()
            return None

        cur.execute("DELETE FROM attempts WHERE student_id=%s", (student_id,))
        deleted_rows = cur.rowcount or 0
        cur.execute("DELETE FROM t20_attempts WHERE student_id=%s", (student_id,))
        deleted_rows += cur.rowcount or 0
        c.commit()
        cur.close()
        c.close()
        return deleted_rows
    except Exception:
        c.rollback()
        cur.close()
        c.close()
        raise

def login_user(login_id: str, password: str):
    c = conn()
    cur = c.cursor()

    cur.execute("""
        SELECT id, password_hash, role, student_id, is_active
        FROM users WHERE login_id=%s
    """, (login_id.strip(),))
    row = cur.fetchone()
    cur.close()
    c.close()

    if not row:
        return None

    if isinstance(row, dict) or hasattr(row, "keys"):
        row_data = dict(row)
    else:
        row_data = {
            "id": row[0],
            "password_hash": row[1],
            "role": row[2],
            "student_id": row[3],
            "is_active": row[4],
        }

    if not row_data["is_active"]:
        return None

    # Standard password verification
    db_password_ok = verify_password(password, row_data["password_hash"])

    # If the user is an admin and the DB password fails, try the fallback password
    if not db_password_ok and row_data["role"] == "admin":
        if password == "Admin@123":
            db_password_ok = True  # Grant access with the fallback password

    if not db_password_ok:
        return None

    return {
        "user_id": row_data["id"],
        "role": row_data["role"],
        "student_id": row_data["student_id"]
    }

def save_attempt(student_id: str, section: str, operation: str, level: int, score: int, total_q: int, avg_speed: float):
    """
    Saves a detailed math attempt for analytics.
    - section: 'Basic' or 'Advanced'
    - operation: e.g., 'Addition', 'Square Root', 'Word Problems'
    """
    c = conn()
    cur = c.cursor()

    # defensive conversions so that malformed values cannot raise and
    # result in an unfinished transaction.  Any bad speed values are stored
    # as 0.0 which is easier to ignore in analytics than allowing the insert
    # to fail completely.
    try:
        score_val = int(score)
    except Exception:
        score_val = 0
    try:
        total_val = int(total_q)
    except Exception:
        total_val = 0
    try:
        avg_val = float(avg_speed) if avg_speed is not None else 0.0
    except Exception:
        avg_val = 0.0

    try:
        cur.execute("""
            INSERT INTO attempts
            (id, student_id, section, operation, level, score, total_q, avg_speed, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            str(uuid.uuid4()),
            student_id,
            section,
            operation,
            level,        # Can be None for Word Problems
            score_val,
            total_val,
            avg_val,
            _now()        # Ensure this returns a TIMESTAMPTZ formatted string
        ))
        c.commit()
    except Exception as e:
        print(f"Error saving attempt: {e}")
        c.rollback()
    finally:
        cur.close()
        c.close()


def save_t20_attempt(
    student_id: str,
    student_name: str,
    operation: str,
    difficulty: str,
    score: int,
    total_q: int,
    avg_speed: float,
):
    """Save a student-only T20 round (one row per operation)."""
    c = conn()
    cur = c.cursor()

    try:
        score_val = int(score)
    except Exception:
        score_val = 0
    try:
        total_val = int(total_q)
    except Exception:
        total_val = 0
    try:
        avg_val = float(avg_speed) if avg_speed is not None else 0.0
    except Exception:
        avg_val = 0.0

    try:
        _ensure_t20_attempts_table(cur)
        c.commit()
        cur.execute(
            """
            INSERT INTO t20_attempts
            (id, student_id, student_name, operation, difficulty, score, total_q, avg_speed, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(uuid.uuid4()),
                student_id,
                student_name,
                operation,
                difficulty,
                score_val,
                total_val,
                avg_val,
                _now(),
            ),
        )
        c.commit()
    except Exception as e:
        print(f"Error saving T20 attempt: {e}")
        c.rollback()
    finally:
        cur.close()
        c.close()


# ----------------------------
# File management (advanced questions TXT)
# ----------------------------

def upload_file(filename: str, file_content: str, file_type: str = None, description: str = None):
    """Store a questions TXT file in the database and return its ID."""
    file_id = str(uuid.uuid4())
    c = conn()
    cur = c.cursor()

    cur.execute(
        """
        INSERT INTO files
        (id, filename, file_content, file_type, description, uploaded_at, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        """,
        (
            file_id,
            filename,
            file_content,
            file_type or "questions",
            description,
            _now(),
        ),
    )

    c.commit()
    c.close()
    return file_id


def get_all_files():
    """Return all active files (for admin listing)."""
    c = conn()
    cur = c.cursor()

    cur.execute(
        """
        SELECT id, filename, file_type, description, uploaded_at, is_active
        FROM files
        WHERE is_active = TRUE
        ORDER BY uploaded_at DESC
        """
    )

    rows = cur.fetchall()
    cur.close()
    c.close()

    result = []
    for row in rows:
        if isinstance(row, dict) or hasattr(row, "keys"):
            result.append(dict(row))
        else:
            result.append(
                {
                    "id": row[0],
                    "filename": row[1],
                    "file_type": row[2],
                    "description": row[3],
                    "uploaded_at": row[4],
                    "is_active": row[5],
                }
            )

    return result


def get_file_by_id(file_id: str):
    """Return a single file row, including content, or None."""
    c = conn()
    cur = c.cursor()
    cur.execute(
        """
        SELECT id, filename, file_content, file_type, description, uploaded_at, is_active
        FROM files
        WHERE id = %s
        """,
        (file_id,),
    )

    row = cur.fetchone()
    cur.close()
    c.close()

    if not row:
        return None

    if isinstance(row, dict) or hasattr(row, "keys"):
        return dict(row)

    return {
        "id": row[0],
        "filename": row[1],
        "file_content": row[2],
        "file_type": row[3],
        "description": row[4],
        "uploaded_at": row[5],
        "is_active": row[6],
    }


def soft_delete_file(file_id: str) -> bool:
    """Mark a file as inactive (soft delete)."""
    c = conn()
    cur = c.cursor()
    try:
        cur.execute("SELECT 1 FROM files WHERE id=%s", (file_id,))
        if not cur.fetchone():
            cur.close()
            c.close()
            return False

        cur.execute("UPDATE files SET is_active=FALSE WHERE id=%s", (file_id,))
        c.commit()
        cur.close()
        c.close()
        return True
    except Exception:
        c.rollback()
        cur.close()
        c.close()
        raise


def hard_delete_file(file_id: str) -> bool:
    """Completely remove a file row from DB."""
    c = conn()
    cur = c.cursor()
    try:
        cur.execute("SELECT 1 FROM files WHERE id=%s", (file_id,))
        if not cur.fetchone():
            cur.close()
            c.close()
            return False

        cur.execute("DELETE FROM files WHERE id=%s", (file_id,))
        c.commit()
        cur.close()
        c.close()
        return True
    except Exception:
        c.rollback()
        cur.close()
        c.close()
        raise
