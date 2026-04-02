#!/usr/bin/env python3
"""
Library Management System - Web Version (Flask)
Simple website instead of desktop app
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
CORS(app)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'library_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'system')
    )
    return conn

# HOME PAGE
@app.route('/')
def home():
    return redirect(url_for('login'))

# LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cur.execute("SELECT * FROM users WHERE username=%s AND password_hash=%s", 
                   (username, password_hash))
        user = cur.fetchone()
        
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            cur.close()
            conn.close()
            
            return redirect(url_for('dashboard'))
        
        cur.close()
        conn.close()
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get stats
    cur.execute("SELECT COUNT(*) as total FROM users WHERE role='student'")
    total_students = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM books")
    total_books = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM books WHERE available_copies > 0")
    available_books = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM issue_records WHERE status='issued'")
    issued_books = cur.fetchone()['total']
    
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', 
                          students=total_students,
                          books=total_books,
                          available=available_books,
                          issued=issued_books,
                          user=session)

# SEARCH BOOKS
@app.route('/api/search-books')
def search_books():
    query = request.args.get('q', '')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cur.execute("""
        SELECT book_id, title, author, category, isbn, available_copies 
        FROM books 
        WHERE title ILIKE %s OR author ILIKE %s OR isbn ILIKE %s
        LIMIT 20
    """, (f'%{query}%', f'%{query}%', f'%{query}%'))
    
    books = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify(books)

# SEARCH USERS (Admin only)
@app.route('/api/search-users')
def search_users():
    if session.get('role') not in ['admin', 'librarian']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    query = request.args.get('q', '')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cur.execute("""
        SELECT user_id, full_name, email, phone, enrollment_number 
        FROM users 
        WHERE full_name ILIKE %s OR enrollment_number ILIKE %s
        LIMIT 20
    """, (f'%{query}%', f'%{query}%'))
    
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify(users)

# ISSUE BOOK
@app.route('/issue-book', methods=['GET', 'POST'])
def issue_book():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['role'] not in ['admin', 'librarian']:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        book_id = request.form.get('book_id')
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Create issue record
            cur.execute("""
                INSERT INTO issue_records (user_id, book_id, issue_date, due_date, status)
                VALUES (%s, %s, CURRENT_DATE, CURRENT_DATE + INTERVAL '14 days', 'issued')
            """, (user_id, book_id))
            
            # Update book stock
            cur.execute("""
                UPDATE books SET available_copies = available_copies - 1 
                WHERE book_id = %s AND available_copies > 0
            """, (book_id,))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            return render_template('issue_book.html', error=str(e), user=session)
    
    return render_template('issue_book.html', user=session)

# RETURN BOOK
@app.route('/return-book', methods=['GET', 'POST'])
def return_book():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session['role'] not in ['admin', 'librarian']:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        issue_id = request.form.get('issue_id')
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Get issue record
            cur.execute("SELECT book_id FROM issue_records WHERE issue_id=%s", (issue_id,))
            issue = cur.fetchone()
            
            if issue:
                book_id = issue[0]
                
                # Mark as returned
                cur.execute("""
                    UPDATE issue_records 
                    SET status='returned', return_date=CURRENT_DATE 
                    WHERE issue_id=%s
                """, (issue_id,))
                
                # Update book stock
                cur.execute("""
                    UPDATE books SET available_copies = available_copies + 1 
                    WHERE book_id = %s
                """, (book_id,))
                
                conn.commit()
            
            cur.close()
            conn.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            return render_template('return_book.html', error=str(e), user=session)
    
    return render_template('return_book.html', user=session)

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ERROR HANDLER
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
