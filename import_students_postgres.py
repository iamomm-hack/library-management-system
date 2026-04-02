"""
Import students from an Excel file into PostgreSQL users table.

Expected Excel columns (case-insensitive):
- username
- full_name
- email (optional)
- phone (optional)
- password (optional; defaults to DEFAULT_STUDENT_PASSWORD)

Usage (PowerShell/cmd):
python import_students_postgres.py --excel "students.xlsx" --host localhost --port 5432 --db library_db --user postgres --password your_password
"""

import argparse
import hashlib
import sys
import re

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

DEFAULT_STUDENT_PASSWORD = "student123"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize incoming headers so small naming differences do not break import.
    normalized = {col: col.strip().lower() for col in df.columns}
    df = df.rename(columns=normalized)

    aliases = {
        "name": "full_name",
        "student_name": "full_name",
        "student name": "full_name",
        "mail": "email",
        "mobile": "phone",
        "contact": "phone",
        "user_name": "username",
        "enrollment number": "enrollment_number",
        "registration no": "registration_no",
        "registration number": "registration_no",
    }

    for source, target in aliases.items():
        if source in df.columns and target not in df.columns:
            df[target] = df[source]

    return df


def _detect_header_row(sheet_df: pd.DataFrame) -> int:
    detected_header_row = 0
    for idx in range(min(len(sheet_df), 15)):
        values = [str(v).strip().lower() for v in sheet_df.iloc[idx].tolist() if str(v).strip() and str(v).strip().lower() != "nan"]
        joined = " ".join(values)
        if (
            "name" in values
            or "enrollment number" in joined
            or "registration no" in joined
            or "registration number" in joined
            or "sl.no" in joined
        ):
            detected_header_row = idx
            break
    return detected_header_row


def load_excel_with_detected_header(excel_path: str) -> pd.DataFrame:
    # Merge all sheets because student lists are often split by sections.
    workbook = pd.ExcelFile(excel_path)
    frames = []

    for sheet in workbook.sheet_names:
        preview = pd.read_excel(excel_path, sheet_name=sheet, header=None)
        header_row = _detect_header_row(preview)
        sheet_df = pd.read_excel(excel_path, sheet_name=sheet, header=header_row)
        sheet_df["source_sheet"] = sheet
        frames.append(sheet_df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def build_username(row: pd.Series) -> str:
    direct_username = str(row.get("username", "")).strip()
    if direct_username and direct_username.lower() != "nan":
        return direct_username

    enrollment = str(row.get("enrollment_number", "")).strip()
    if enrollment and enrollment.lower() != "nan":
        return enrollment

    registration = str(row.get("registration_no", "")).strip()
    if registration and registration.lower() != "nan":
        return registration

    full_name = str(row.get("full_name", "")).strip().lower()
    if not full_name or full_name == "nan":
        return ""

    slug = re.sub(r"[^a-z0-9]+", "_", full_name).strip("_")
    if not slug:
        return ""

    return f"{slug}_std"


def validate_columns(df: pd.DataFrame) -> None:
    required = {"full_name"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in Excel: {', '.join(sorted(missing))}")


def create_users_table_if_missing(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    conn.commit()


def prepare_rows(df: pd.DataFrame):
    rows = []
    for _, row in df.iterrows():
        username = build_username(row)
        full_name = str(row.get("full_name", "")).strip()

        if not username or not full_name:
            continue

        email = row.get("email")
        phone = row.get("phone")
        raw_password = row.get("password")

        password_value = (
            str(raw_password).strip()
            if raw_password is not None and str(raw_password).strip() and str(raw_password).strip().lower() != "nan"
            else DEFAULT_STUDENT_PASSWORD
        )

        rows.append(
            (
                username,
                hash_password(password_value),
                "student",
                full_name,
                None if pd.isna(email) else str(email).strip(),
                None if pd.isna(phone) else str(phone).strip(),
            )
        )

    return rows


def upsert_students(conn, rows):
    if not rows:
        return 0

    query = """
        INSERT INTO users (username, password, role, full_name, email, phone)
        VALUES %s
        ON CONFLICT (username)
        DO UPDATE SET
            password = EXCLUDED.password,
            role = 'student',
            full_name = EXCLUDED.full_name,
            email = EXCLUDED.email,
            phone = EXCLUDED.phone
    """

    with conn.cursor() as cur:
        execute_values(cur, query, rows)
    conn.commit()
    return len(rows)


def parse_args():
    parser = argparse.ArgumentParser(description="Import students from Excel into PostgreSQL")
    parser.add_argument("--excel", required=True, help="Path to students Excel file (.xlsx/.xls)")
    parser.add_argument("--host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=5432, help="PostgreSQL port")
    parser.add_argument("--db", required=True, help="PostgreSQL database name")
    parser.add_argument("--user", required=True, help="PostgreSQL username")
    parser.add_argument("--password", required=True, help="PostgreSQL password")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        df = load_excel_with_detected_header(args.excel)
        df = normalize_columns(df)
        validate_columns(df)

        rows = prepare_rows(df)

        conn = psycopg2.connect(
            host=args.host,
            port=args.port,
            dbname=args.db,
            user=args.user,
            password=args.password,
        )

        try:
            create_users_table_if_missing(conn)
            count = upsert_students(conn, rows)
            print(f"Imported/updated {count} student records successfully.")
            print(f"Default password for rows without password: {DEFAULT_STUDENT_PASSWORD}")
        finally:
            conn.close()

    except Exception as exc:
        print(f"Import failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
