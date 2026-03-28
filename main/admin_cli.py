from db import init_db
from models import create_student_user, get_all_students, update_student_details


def prompt_int(prompt, default=None):
    v = input(prompt).strip()
    if v == "":
        return default
    return int(v)


# ----------------------------
# CREATE STUDENT
# ----------------------------

def create_flow():
    print("=== Add Student (Admin) ===")

    name = input("Student Name: ").strip()
    grade = int(input("Grade (1-10): ").strip())
    batch = input("Batch (optional): ").strip() or None

    enrollment = input("Enrollment / Roll (optional): ").strip() or None
    enrollment = int(enrollment) if enrollment else None

    login_id = create_student_user(
        name=name,
        grade=grade,
        batch=batch,
        enrollment_id=enrollment,
    )

    print("\n✅ Student created!")
    print("Login ID:", login_id)
    print("NOTE: Share this Login ID with student.\n")


# ----------------------------
# EDIT STUDENT
# ----------------------------

def edit_flow():
    students = get_all_students()

    if not students:
        print("No students found.")
        return

    print("\nSelect a student to edit:\n")

    for i, s in enumerate(students, start=1):
        if isinstance(s, dict) or hasattr(s, "keys"):
            sid = s.get("id")
            name = s.get("name")
            grade = s.get("grade")
            batch = s.get("batch")
            enr = s.get("enrollment_id")
            login = s.get("login_id")
        else:
            sid, name, grade, batch, enr, login = s

        print(f"{i}. {name} | Grade: {grade} | Batch: {batch} | Roll: {enr} | Login: {login}")

    try:
        choice = int(input("\nEnter number: ").strip())
        if choice < 1 or choice > len(students):
            print("Invalid choice")
            return
    except:
        print("Invalid input")
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

    print("\nLeave blank to keep existing value.\n")

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
        print("✅ Student updated successfully.")
    else:
        print("❌ Failed to update student.")


# ----------------------------
# MAIN MENU
# ----------------------------

def main():
    init_db()

    while True:
        print("\n=== Admin CLI ===")
        print("1) Create student")
        print("2) Edit student")
        print("3) Exit")

        choice = input("Choose action [1/2/3]: ").strip()

        if choice == "1":
            create_flow()
        elif choice == "2":
            edit_flow()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()