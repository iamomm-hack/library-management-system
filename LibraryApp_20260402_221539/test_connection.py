#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import psycopg2

print("Testing database connection...\n")

load_dotenv()
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users;")
    users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM books;")
    books = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM issue_records WHERE status='issued';")
    issues = cursor.fetchone()[0]
    
    print("✅ Database Connection SUCCESS!\n")
    print(f"📊 Database Stats:")
    print(f"   Users: {users}")
    print(f"   Books: {books}")
    print(f"   Active Issues: {issues}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection FAILED: {e}")
    print("\nCheck .env file settings!")
