import secrets
import string
import uuid
from datetime import datetime, timezone

from db import (
    DEFAULT_ADMIN_LOGIN,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_STUDENT_LOGIN,
    DEFAULT_STUDENT_NAME,
    DEFAULT_STUDENT_PASSWORD,
    conn,
    ensure_default_admin_user,
    ensure_default_student_user,
    get_connection,
    hash_password,
    verify_password,
)


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _generate_temp_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _row_to_dict(row):
    return dict(row) if row else None


def _build_user_payload(row, *, login_id_override=None, name_override=None):
    if not row:
        return None

    payload = {
        "user_id": row["id"],
        "role": row["role"],
        "student_id": row["student_id"],
        "login_id": login_id_override or row["login_id"],
    }

    if name_override is not None:
        payload["name"] = name_override

    return payload


def ensure_default_admin():
    admin_id = ensure_default_admin_user()
    ensure_default_student_user()
    return admin_id


def ensure_default_student():
    return ensure_default_student_user()


def _generate_login_id(grade, batch, enrollment_id):
    grade_part = f"{int(grade):02d}"
    batch_part = str(batch or "00")[-2:].zfill(2)
    roll_part = f"{int(enrollment_id):02d}"
    return f"VM-{grade_part}-{batch_part}00{roll_part}"


def create_student_user(name, grade, batch, enrollment_id):
    student_id = str(uuid.uuid4())
    normalized_batch = batch or "00"
    login_id = _generate_login_id(grade, normalized_batch, enrollment_id)
    temp_password = _generate_temp_password()

    with get_connection() as connection:
        existing_user = connection.execute(
            "SELECT id FROM users WHERE login_id = ? LIMIT 1",
            (login_id,),
        ).fetchone()
        if existing_user:
            raise ValueError(
                f"Login ID already exists for this student pattern: {login_id}"
            )

        connection.execute(
            """
            INSERT INTO students (id, name, grade, batch, enrollment_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_id, name, int(grade), normalized_batch, int(enrollment_id)),
        )

        connection.execute(
            """
            INSERT INTO users (
                id, login_id, role, student_id, created_at, is_active, password_hash
            )
            VALUES (?, ?, 'student', ?, ?, 1, ?)
            """,
            (
                str(uuid.uuid4()),
                login_id,
                student_id,
                _now(),
                hash_password(temp_password),
            ),
        )
        connection.commit()

    return login_id, temp_password


def get_all_students():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                s.id,
                s.name,
                s.grade,
                s.batch,
                s.enrollment_id,
                u.login_id
            FROM students s
            LEFT JOIN users u
                ON u.student_id = s.id
               AND u.role = 'student'
            ORDER BY s.name
            """
        ).fetchall()
    return [dict(row) for row in rows]


def update_student_details(student_id, name=None, grade=None, batch=None, enrollment_id=None):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, name, grade, batch, enrollment_id FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()

        if not row:
            return False

        current = dict(row)
        new_name = name if name is not None and name != "" else current["name"]
        new_grade = grade if grade is not None else current["grade"]
        new_batch = batch if batch is not None and batch != "" else current["batch"]
        new_enrollment = (
            enrollment_id if enrollment_id is not None else current["enrollment_id"]
        )

        connection.execute(
            """
            UPDATE students
            SET name = ?, grade = ?, batch = ?, enrollment_id = ?
            WHERE id = ?
            """,
            (new_name, new_grade, new_batch, new_enrollment, student_id),
        )

        new_login = _generate_login_id(new_grade, new_batch or "00", new_enrollment)
        connection.execute(
            """
            UPDATE users
            SET login_id = ?
            WHERE student_id = ? AND role = 'student'
            """,
            (new_login, student_id),
        )
        connection.commit()
        return True


def delete_student_account(student_id):
    with get_connection() as connection:
        connection.execute("DELETE FROM attempts WHERE student_id = ?", (student_id,))
        connection.execute("DELETE FROM t20_attempts WHERE student_id = ?", (student_id,))
        connection.execute("DELETE FROM users WHERE student_id = ?", (student_id,))
        result = connection.execute("DELETE FROM students WHERE id = ?", (student_id,))
        connection.commit()
        return result.rowcount > 0


def login_user(login_id, password=None):
    login_id = (login_id or "").strip()
    password = password or ""

    if not login_id or not password:
        return None

    if login_id == DEFAULT_ADMIN_LOGIN and password == DEFAULT_ADMIN_PASSWORD:
        ensure_default_admin()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, login_id, role, student_id, is_active
                FROM users
                WHERE role = 'admin'
                LIMIT 1
                """
            ).fetchone()
        if row and row["is_active"]:
            return _build_user_payload(
                row,
                login_id_override=DEFAULT_ADMIN_LOGIN,
            )
        return {
            "role": "admin",
            "login_id": DEFAULT_ADMIN_LOGIN,
            "student_id": None,
        }

    if login_id == DEFAULT_STUDENT_LOGIN and password == DEFAULT_STUDENT_PASSWORD:
        student_id = ensure_default_student()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT u.id, u.login_id, u.role, u.student_id, u.is_active, s.name
                FROM users u
                LEFT JOIN students s ON s.id = u.student_id
                WHERE u.login_id = ?
                LIMIT 1
                """,
                (DEFAULT_STUDENT_LOGIN,),
            ).fetchone()
        if row and row["is_active"]:
            return _build_user_payload(
                row,
                login_id_override=DEFAULT_STUDENT_LOGIN,
                name_override=row["name"] or DEFAULT_STUDENT_NAME,
            )
        return {
            "role": "student",
            "login_id": DEFAULT_STUDENT_LOGIN,
            "student_id": student_id,
            "name": DEFAULT_STUDENT_NAME,
        }

    try:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, login_id, role, student_id, is_active, password_hash
                FROM users
                WHERE login_id = ?
                LIMIT 1
                """,
                (login_id,),
            ).fetchone()
            if not row or not row["is_active"]:
                return None
            if not verify_password(password, row["password_hash"]):
                return None
            return _build_user_payload(row)
    except Exception:
        return None


def save_attempt(student_id, section, operation, level, score, total_q, avg_speed):
    if not student_id:
        raise ValueError("Cannot save attempt without a student_id.")

    with get_connection() as connection:
        student_row = connection.execute(
            "SELECT id FROM students WHERE id = ? LIMIT 1",
            (student_id,),
        ).fetchone()
        if not student_row:
            raise ValueError(f"Student not found for attempt save: {student_id}")

        connection.execute(
            """
            INSERT INTO attempts
            (id, student_id, section, operation, level, score, total_q, avg_speed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                student_id,
                section,
                operation,
                level,
                int(score or 0),
                int(total_q or 0),
                float(avg_speed or 0),
                _now(),
            ),
        )
        connection.commit()
        return True


def save_t20_attempt(student_id, student_name, operation, difficulty, score, total_q, avg_speed):
    if not student_id:
        print("Cannot save T20 attempt: missing student_id")
        return False

    try:
        with get_connection() as connection:
            student_row = connection.execute(
                "SELECT id FROM students WHERE id = ? LIMIT 1",
                (student_id,),
            ).fetchone()
            if not student_row:
                raise ValueError(f"Student not found for T20 attempt save: {student_id}")

            connection.execute(
                """
                INSERT INTO t20_attempts (
                    id, student_id, student_name, operation,
                    difficulty, score, total_q, avg_speed, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    student_id,
                    student_name,
                    operation,
                    difficulty,
                    int(score or 0),
                    int(total_q or 0),
                    float(avg_speed or 0),
                    _now(),
                ),
            )
            connection.commit()
            return True
    except Exception as exc:
        print(f"Error saving T20 attempt: {exc}")
        return False


def get_student_progress():
    with get_connection() as connection:
        rows = connection.execute(
            """
            WITH combined_attempts AS (
                SELECT
                    student_id,
                    score,
                    created_at
                FROM attempts
                UNION ALL
                SELECT
                    student_id,
                    score,
                    created_at
                FROM t20_attempts
            )
            SELECT
                s.id,
                s.name,
                s.grade,
                s.batch,
                s.enrollment_id,
                u.login_id,
                COUNT(ca.student_id) AS attempts_count,
                COALESCE(AVG(ca.score), 0) AS avg_score,
                COALESCE(MAX(ca.score), 0) AS best_score,
                (
                    SELECT ca2.score
                    FROM combined_attempts ca2
                    WHERE ca2.student_id = s.id
                    ORDER BY ca2.created_at DESC
                    LIMIT 1
                ) AS last_score,
                (
                    SELECT ca3.created_at
                    FROM combined_attempts ca3
                    WHERE ca3.student_id = s.id
                    ORDER BY ca3.created_at DESC
                    LIMIT 1
                ) AS last_attempt_at
            FROM students s
            LEFT JOIN users u
                ON u.student_id = s.id
               AND u.role = 'student'
            LEFT JOIN combined_attempts ca
                ON ca.student_id = s.id
            GROUP BY s.id, s.name, s.grade, s.batch, s.enrollment_id, u.login_id
            ORDER BY attempts_count DESC, s.name ASC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def upload_file(filename, content, file_type=None, description=None):
    file_id = str(uuid.uuid4())
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO files
            (id, filename, file_content, file_type, description, uploaded_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (
                file_id,
                filename,
                content,
                file_type,
                description,
                _now(),
            ),
        )
        connection.commit()
    return file_id


def get_all_files():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, filename, file_type, description, uploaded_at
            FROM files
            WHERE is_active = 1
            """
        ).fetchall()
    return [dict(row) for row in rows]


def soft_delete_file(file_id):
    with get_connection() as connection:
        connection.execute("UPDATE files SET is_active = 0 WHERE id = ?", (file_id,))
        connection.commit()
    return True


def get_detailed_analytics(student_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                section,
                operation,
                level,
                score,
                total_q,
                avg_speed,
                created_at
            FROM attempts
            WHERE student_id = ?
            UNION ALL
            SELECT
                'T20' AS section,
                operation,
                CASE
                    WHEN LOWER(COALESCE(difficulty, '')) = 'hard' THEN 2
                    ELSE 1
                END AS level,
                score,
                total_q,
                avg_speed,
                created_at
            FROM t20_attempts
            WHERE student_id = ?
            ORDER BY created_at DESC
            """,
            (student_id, student_id),
        ).fetchall()

    analytics = []
    for row in rows:
        analytics.append(
            {
                "section": row["section"],
                "topic": row["operation"],
                "level": row["level"],
                "sub_level": row["level"],
                "score": row["score"],
                "total_q": row["total_q"],
                "accuracy": round(row["score"] / row["total_q"], 4) if row["total_q"] else 0,
                "avg_speed": row["avg_speed"],
                "time_per_q": row["avg_speed"],
                "date": row["created_at"],
            }
        )

    return analytics


def reset_student_analytics(student_id):
    with get_connection() as connection:
        deleted_attempts = connection.execute(
            "DELETE FROM attempts WHERE student_id = ?",
            (student_id,),
        ).rowcount
        deleted_t20 = connection.execute(
            "DELETE FROM t20_attempts WHERE student_id = ?",
            (student_id,),
        ).rowcount
        connection.commit()
    return deleted_attempts + deleted_t20


def get_admin_user():
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, login_id, is_active
            FROM users
            WHERE role = 'admin'
            LIMIT 1
            """
        ).fetchone()
    return _row_to_dict(row)


def get_student(student_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, grade, batch, enrollment_id
            FROM students
            WHERE id = ?
            """,
            (student_id,),
        ).fetchone()
    return _row_to_dict(row)


def update_admin_credentials(new_login=None, new_password=None):
    if new_login is None and new_password is None:
        return False

    with get_connection() as connection:
        row = connection.execute(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()
        if not row:
            return False

        updates = []
        params = []

        if new_login is not None:
            updates.append("login_id = ?")
            params.append(new_login)

        if new_password is not None:
            updates.append("password_hash = ?")
            params.append(hash_password(new_password))

        if not updates:
            return False

        params.append(row["id"])
        connection.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        connection.commit()
        return True


def get_file_by_id(file_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, filename, file_content, file_type, description, uploaded_at, is_active
            FROM files
            WHERE id = ?
            """,
            (file_id,),
        ).fetchone()
    return _row_to_dict(row)


def hard_delete_file(file_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM files WHERE id = ?",
            (file_id,),
        ).fetchone()
        if not row:
            return False

        connection.execute("DELETE FROM files WHERE id = ?", (file_id,))
        connection.commit()
        return True
