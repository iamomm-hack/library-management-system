"""
Give one additional book to students who still have no issued books.
"""

import os
from datetime import date, timedelta

import psycopg2

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "library_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "system")

EXCLUDED_NAMES = [
    "OM KUMAR",
    "MUFTI ARMAAN",
    "SATISH JALAN",
    "SAYAN ROY",
]


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT user_id, username, full_name
                FROM users
                WHERE role = 'student'
                  AND UPPER(full_name) NOT IN (%s, %s, %s, %s)
                  AND NOT EXISTS (
                      SELECT 1 FROM issue_records i WHERE i.user_id = users.user_id
                  )
                ORDER BY full_name, username
                """,
                tuple(EXCLUDED_NAMES),
            )
            students = cursor.fetchall()

            cursor.execute(
                """
                SELECT book_id, title, available_copies
                FROM books
                WHERE available_copies > 0
                ORDER BY available_copies DESC, title ASC
                """
            )
            books = cursor.fetchall()

        if not students:
            print("No students need top-up issues.")
            return

        if not books:
            print("No available books left for top-up.")
            return

        book_queue = []
        for book_id, title, available_copies in books:
            book_queue.extend([(book_id, title)] * int(available_copies))

        issue_date = date.today()
        due_date = issue_date + timedelta(days=14)
        issued = 0
        queue_index = 0

        for user_id, username, full_name in students:
            if queue_index >= len(book_queue):
                break

            book_id, title = book_queue[queue_index]
            queue_index += 1

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO issue_records (book_id, user_id, issue_date, due_date, status)
                    VALUES (%s, %s, %s, %s, 'issued')
                    """,
                    (book_id, user_id, issue_date, due_date),
                )
                cursor.execute(
                    """
                    UPDATE books
                    SET available_copies = available_copies - 1
                    WHERE book_id = %s
                    """,
                    (book_id,),
                )

            issued += 1

        conn.commit()
        print(f"✓ Top-up complete. Added {issued} issue records.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
