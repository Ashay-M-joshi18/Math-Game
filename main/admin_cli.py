from db import init_db
from models import create_student_user, get_all_students, update_student_details

# Admin CLI additions:
# - `create_flow` now accepts an optional `enrollment`/roll number when creating students
# - `edit_flow` lists existing students and allows editing name, grade, batch, and enrollment
#   The underlying `update_student_details` keeps the `users.login_id` in-sync.


def prompt_int(prompt, default=None):
    v = input(prompt).strip()
    if v == "":
        return default
    return int(v)


def create_flow():
    print("=== Add Student (Admin) ===")
    name = input("Student Name: ").strip()
    grade = int(input("Grade (1-10): ").strip())
    batch = input("Batch (optional): ").strip() or None
    # Optional enrollment/roll number for the student (stored in `students.enrollment_id`)
    enrollment = input("Enrollment / Roll (optional number): ").strip() or None
    enrollment = int(enrollment) if enrollment else None

    login_id, temp_password = create_student_user(
        name=name,
        grade=grade,
        batch=batch,
        enrollment_id=enrollment,
    )

    print("\n✅ Student created!")
    print("Login ID:", login_id)
    print("Temp Password:", temp_password)
    print("NOTE: Share this with student. Password is not stored in plain text.\n")


def edit_flow():
    # Fetch all students. Rows may be sqlite Row objects or plain tuples.
    students = get_all_students()
    if not students:
        print("No students found.")
        return

    print("Select a student to edit:")
    for i, s in enumerate(students, start=1):
        # rows can be sqlite Row or tuple (handle both shapes)
        if isinstance(s, dict) or hasattr(s, "keys"):
            login = s.get("login_id")
            sid = s.get("id")
            name = s.get("name")
            grade = s.get("grade")
            batch = s.get("batch")
            enr = s.get("enrollment_id")
        else:
            sid, name, grade, batch, enr, login = s

        # Display brief student info to help selection
        print(f"{i}. {name} | Grade: {grade} | Batch: {batch} | Roll: {enr} | Login: {login}")

    choice = int(input("Enter number: ").strip())
    if choice < 1 or choice > len(students):
        print("Invalid choice")
        return

    sel = students[choice - 1]
    if isinstance(sel, dict) or hasattr(sel, "keys"):
        sid = sel.get("id")
        cur_name = sel.get("name")
        cur_grade = sel.get("grade")
        cur_batch = sel.get("batch")
        cur_enr = sel.get("enrollment_id")
    else:
        sid, cur_name, cur_grade, cur_batch, cur_enr, _ = sel

    print("Leave blank to keep existing value.")
    new_name = input(f"Name [{cur_name}]: ").strip() or None
    new_grade = prompt_int(f"Grade [{cur_grade}]: ", default=None)
    new_batch = input(f"Batch [{cur_batch}]: ").strip() or None
    new_enr = prompt_int(f"Enrollment / Roll [{cur_enr}]: ", default=None)

    success = update_student_details(
        sid,
        name=new_name,
        grade=new_grade,
        batch=new_batch,
        enrollment_id=new_enr,
    )

    if success:
        # Inform admin that student record and associated login were updated
        print("✅ Student updated successfully.")
    else:
        print("Failed to update student. See logs for details.")


def main():
    init_db()
    print("Admin CLI")
    print("1) Create student")
    print("2) Edit student")
    choice = input("Choose action [1/2]: ").strip() or "1"
    if choice == "1":
        create_flow()
    else:
        edit_flow()


if __name__ == "__main__":
    main()