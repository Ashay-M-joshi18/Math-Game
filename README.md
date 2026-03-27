# Bubble Burst

Bubble Burst is a desktop-based educational math game designed to help students practice and improve their arithmetic skills in a fun and engaging way. It features a simple interface for students and a separate admin tool for user management.

## Tech Stack

- **Language:** Python 3
- **GUI:** `tkinter` for the application shell and `pygame` for the game interface.
- **Database:** Supports PostgreSQL (`psycopg2`) and MySQL (`pymysql`).
- **Analytics:** `matplotlib` for visualizing student progress.

## Features

- **Game Modes:** Multiple difficulty levels (Easy, Intermediate, Expert) and speeds (Rapid, Blitz, Bullet).
- **Math Operations:** Covers addition, subtraction, multiplication, division, squares, cubes, and roots.
- **Student Tracking:** Records game attempts and provides performance analytics.
- **Admin CLI:** A command-line interface for managing student accounts.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd bubble-burst-py
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment:**
    Create a `.env` file in the project root to store your database connection details. Use the `.env.example` file as a template.
    ```
    DB_TYPE=postgresql
    DB_HOST=localhost
    DB_PORT=5432
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_NAME=bubble_burst
    ```

5.  **Initialize the database:**
    The application will create the necessary tables on its first run.

## Usage

-   **Run the main application:**
    ```bash
    python main/main.py
    ```
-   **Run the Admin CLI:**
    ```bash
    python main/admin_cli.py
    ```
