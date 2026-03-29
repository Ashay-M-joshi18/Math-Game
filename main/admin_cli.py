from db import init_db
from models import create_student_user, get_all_students, update_student_details


def prompt_int(prompt, default=None):
    value = input(prompt).strip()
    if value == "":
        return default
    return int(value)


def create_flow():
    print("=== Add Student (Admin) ===")

    name = input("Student Name: ").strip()
    grade = int(input("Grade (1-10): ").strip())
    batch = input("Batch (optional): ").strip() or None

    enrollment = input("Enrollment / Roll (optional): ").strip() or None
    enrollment = int(enrollment) if enrollment else None

    login_id, temp_password = create_student_user(
        name=name,
        grade=grade,
        batch=batch,
        enrollment_id=enrollment,
    )

    print("\nStudent created.")
    print("Login ID:", login_id)
    print("Password:", temp_password)
    print("Share these credentials with the student.\n")


def edit_flow():
    students = get_all_students()

    if not students:
        print("No students found.")
        return

    print("\nSelect a student to edit:\n")

    for index, student in enumerate(students, start=1):
        print(
            f"{index}. {student.get('name')} | Grade: {student.get('grade')} | "
            f"Batch: {student.get('batch')} | Roll: {student.get('enrollment_id')} | "
            f"Login: {student.get('login_id')}"
        )

    try:
        choice = int(input("\nEnter number: ").strip())
        if choice < 1 or choice > len(students):
            print("Invalid choice")
            return
    except ValueError:
        print("Invalid input")
        return

    selected = students[choice - 1]

    print("\nLeave blank to keep existing value.\n")

    new_name = input(f"Name [{selected.get('name')}]: ").strip() or None
    new_grade = prompt_int(f"Grade [{selected.get('grade')}]: ", default=None)
    new_batch = input(f"Batch [{selected.get('batch')}]: ").strip() or None
    new_enrollment = prompt_int(
        f"Enrollment / Roll [{selected.get('enrollment_id')}]: ",
        default=None,
    )

    success = update_student_details(
        selected.get("id"),
        name=new_name,
        grade=new_grade,
        batch=new_batch,
        enrollment_id=new_enrollment,
    )

    if success:
        print("Student updated successfully.")
    else:
        print("Failed to update student.")


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
