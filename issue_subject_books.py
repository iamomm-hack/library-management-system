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

SUBJECT_PATTERNS = [
    "%DBMS%",
    "%DATABASE MANAGEMENT SYSTEM%",
    "%AUTOMATA%",
    "%THEORY OF COMPUTATION%",
    "%OPERATING SYSTEM%",
    "%COMPUTER NETWORKS%",
    "%DATA STRUCTURES AND ALGORITHMS%",
    "%ALGORITHMS%",
    "%COMPILER DESIGN%",
    "%COMPUTER ORGANIZATION%",
    "%ARCHITECTURE%",
    "%DIGITAL LOGIC%",
    "%SOFTWARE ENGINEERING%",
    "%OBJECT ORIENTED PROGRAMMING%",
    "%SQL%",
    "%MYSQL%",
    "%ORACLE DATABASE%",
    "%ARTIFICIAL INTELLIGENCE%",
    "%MACHINE LEARNING%",
    "%DEEP LEARNING%",
    "%NATURAL LANGUAGE PROCESSING%",
    "%LINUX%",
    "%NETWORKING%",
]

ALGORITHMS_PATTERNS = ["%ALGORITHMS%"]


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def fetch_students(conn):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id, username, full_name
            FROM users
            WHERE role = 'student'
              AND UPPER(full_name) NOT IN (%s, %s, %s, %s)
            ORDER BY full_name, username
            """,
            tuple(EXCLUDED_NAMES),
        )
        return cursor.fetchall()


def fetch_books(conn, patterns):
    with conn.cursor() as cursor:
        conditions = []
        params = []
        for pattern in patterns:
            conditions.append("(title ILIKE %s OR category ILIKE %s OR author ILIKE %s)")
            params.extend([pattern, pattern, pattern])

        where_clause = " OR ".join(conditions)

        cursor.execute(
            f"""
            SELECT book_id, title, available_copies
            FROM books
            WHERE available_copies > 0
              AND ({where_clause})
            ORDER BY available_copies DESC, title ASC
            """,
            tuple(params),
        )
        return cursor.fetchall()


def fetch_algorithms_books(conn):
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT book_id, title, available_copies
            FROM books
            WHERE available_copies > 0
              AND (
                title ILIKE %s OR category ILIKE %s OR author ILIKE %s
              )
            ORDER BY available_copies DESC, title ASC
            """,
            (ALGORITHMS_PATTERNS[0], ALGORITHMS_PATTERNS[0], ALGORITHMS_PATTERNS[0]),
        )
        return cursor.fetchall()


def build_book_queue(books):
    queue = []
    for book_id, title, available_copies in books:
        queue.extend([(book_id, title)] * int(available_copies))
    return queue


def issue_book(conn, user_id, book_id, issue_date, due_date):
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


def main():
    conn = get_connection()
    try:
        students = fetch_students(conn)
        subject_books = fetch_books(conn, SUBJECT_PATTERNS)
        algorithm_books = fetch_algorithms_books(conn)

        if not students:
            print("No students found to issue books.")
            return

        if not subject_books:
            print("No subject books found to issue.")
            return

        book_queue = build_book_queue(subject_books)
        if not book_queue:
            print("No available copies in subject books.")
            return

        issue_date = date.today()
        due_date = issue_date + timedelta(days=14)

        total_issued = 0
        queue_index = 0
        algorithms_assigned = False

        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM issue_records")
            if cursor.fetchone()[0] > 0:
                print("Issue records already exist. This script is designed for a fresh issue run.")
                return

        for idx, (user_id, username, full_name) in enumerate(students):
            books_to_issue = 2 if idx % 2 == 0 else 1
            assigned_books = []

            if full_name.upper() == "ANKIT SARKAR" and algorithm_books and not algorithms_assigned:
                alg_book_id, alg_title, _ = algorithm_books[0]
                issue_book(conn, user_id, alg_book_id, issue_date, due_date)
                total_issued += 1
                assigned_books.append(alg_title)
                algorithms_assigned = True
                if books_to_issue > 0:
                    books_to_issue -= 1

            while books_to_issue > 0 and queue_index < len(book_queue):
                book_id, title = book_queue[queue_index]
                queue_index += 1

                if title in assigned_books:
                    continue

                issue_book(conn, user_id, book_id, issue_date, due_date)
                total_issued += 1
                assigned_books.append(title)
                books_to_issue -= 1

            if idx % 50 == 0:
                conn.commit()
                print(f"Processed {idx + 1}/{len(students)} students, total issued={total_issued}")

        conn.commit()
        print(f"\n✓ Done. Total issue records created: {total_issued}")
        print("✓ Om Kumar, Mufti Armaan, Satish Jalan, Sayan Roy skipped")
        print("✓ Ankit Sarkar got an Algorithms-related book")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
