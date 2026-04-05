#!/usr/bin/env python3
"""
Library Management System - Web Version (Flask)
Simple website instead of desktop app
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from datetime import datetime
import hashlib
import os
import re
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
CORS(app)


FEMALE_NAME_HINTS = {
    'aarti', 'aisha', 'akanksha', 'akriti', 'alisha', 'ananya', 'anjali', 'ankita',
    'anshika', 'archana', 'arti', 'bhavna', 'deepti', 'diksha', 'divya', 'gauri',
    'kajal', 'karishma', 'kavita', 'khushi', 'kriti', 'mansi', 'megha', 'muskan',
    'neha', 'nikita', 'nisha', 'palak', 'payal', 'pooja', 'pragya', 'prerna',
    'priyanka', 'rani', 'rashmi', 'riya', 'sakshi', 'saloni', 'shivani', 'shreya',
    'simran', 'sonal', 'supriya', 'swati', 'tanvi', 'vaishali'
}


def infer_avatar_gender(full_name=None, username=None, explicit_gender=None):
    gender_value = str(explicit_gender or '').strip().lower()
    if gender_value in {'f', 'female', 'girl', 'woman'}:
        return 'female'
    if gender_value in {'m', 'male', 'boy', 'man'}:
        return 'male'

    source_text = f"{full_name or ''} {username or ''}".strip().lower()
    if not source_text:
        return 'male'

    name_tokens = [token for token in re.split(r'[^a-z]+', source_text) if token]
    for token in name_tokens:
        if token in FEMALE_NAME_HINTS:
            return 'female'

    return 'male'


def decorate_rows_with_avatar(rows, name_key='full_name', username_key='username', gender_key='gender'):
    decorated = []
    for row in rows:
        item = dict(row)
        username_value = item.get(username_key) if username_key else None
        item['avatar_gender'] = infer_avatar_gender(
            item.get(name_key),
            username_value,
            item.get(gender_key)
        )
        decorated.append(item)
    return decorated


def current_user_view():
    user_view = dict(session)
    user_view['avatar_gender'] = infer_avatar_gender(
        user_view.get('full_name'),
        user_view.get('username'),
        user_view.get('gender')
    )
    return user_view


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def staff_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get('role') not in ['admin', 'librarian']:
            return redirect(url_for('dashboard'))
        return fn(*args, **kwargs)
    return wrapper


def rows_to_dicts(rows):
    return [dict(r) for r in rows]


def log_activity(action, details):
    if 'user_id' not in session:
        return
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO activity_log (user_id, action, details) VALUES (%s, %s, %s)",
            (session['user_id'], action, details),
        )
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()

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
        
        # Stored passwords are SHA-256 hashes in users.password
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", 
               (username, password_hash))
        user = cur.fetchone()
        
        if user:
            user_gender = user['gender'] if 'gender' in user.keys() else None
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            session['avatar_gender'] = infer_avatar_gender(user['full_name'], user['username'], user_gender)
            
            cur.close()
            conn.close()
            log_activity('login', 'User logged in successfully')
            
            return redirect(url_for('dashboard'))
        
        cur.close()
        conn.close()
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

# DASHBOARD
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get stats
    cur.execute("SELECT COUNT(*) as total FROM users WHERE role='student'")
    total_students = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM books")
    total_books = cur.fetchone()['total']

    cur.execute("SELECT COALESCE(SUM(total_copies), 0) as total FROM books")
    total_copies = cur.fetchone()['total']
    
    cur.execute("SELECT COALESCE(SUM(available_copies), 0) as total FROM books")
    available_books = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM issue_records WHERE status='issued'")
    issued_books = cur.fetchone()['total']
    
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', 
                          students=total_students,
                          books=total_books,
                          total_copies=total_copies,
                          available=available_books,
                          issued=issued_books,
                          user=current_user_view())

# SEARCH BOOKS
@app.route('/api/search-books')
@login_required
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
    
    books = rows_to_dicts(cur.fetchall())
    cur.close()
    conn.close()
    
    return jsonify(books)

# SEARCH USERS (Admin only)
@app.route('/api/search-users')
@login_required
@staff_required
def search_users():
    query = request.args.get('q', '')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cur.execute("""
        SELECT user_id, full_name, email, phone, username AS enrollment_number
        FROM users 
        WHERE role='student' AND (full_name ILIKE %s OR username ILIKE %s)
        ORDER BY user_id DESC
        LIMIT 25
    """, (f'%{query}%', f'%{query}%'))
    
    users = rows_to_dicts(cur.fetchall())
    users = decorate_rows_with_avatar(users, username_key='enrollment_number')
    cur.close()
    conn.close()
    
    return jsonify(users)


@app.route('/my-books')
@login_required
def my_books():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    is_staff_view = session.get('role') in ['admin', 'librarian']
    if is_staff_view:
        cur.execute(
            """
            SELECT
                i.issue_id,
                u.full_name,
                u.username,
                u.role,
                b.title,
                b.author,
                i.issue_date,
                i.due_date,
                i.return_date,
                i.status
            FROM issue_records i
            JOIN books b ON b.book_id = i.book_id
            JOIN users u ON u.user_id = i.user_id
            ORDER BY i.issue_id DESC
            LIMIT 300
            """
        )
    else:
        cur.execute(
            """
            SELECT i.issue_id, b.title, b.author, i.issue_date, i.due_date, i.return_date, i.status
            FROM issue_records i
            JOIN books b ON b.book_id = i.book_id
            WHERE i.user_id = %s
            ORDER BY i.issue_id DESC
            LIMIT 100
            """,
            (session['user_id'],),
        )

    records = decorate_rows_with_avatar(cur.fetchall())
    cur.close()
    conn.close()
    return render_template('my_books.html', records=records, user=current_user_view(), is_staff_view=is_staff_view)


@app.route('/manage-users')
@login_required
@staff_required
def manage_users():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        """
        SELECT user_id, full_name, username, email, phone, role
        FROM users
        ORDER BY user_id DESC
        LIMIT 200
        """
    )
    users = decorate_rows_with_avatar(cur.fetchall())
    cur.close()
    conn.close()
    return render_template('manage_users.html', users=users, user=current_user_view())


@app.route('/issued-books')
@login_required
@staff_required
def issued_books():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(
        """
        SELECT i.issue_id, u.full_name, u.username, u.role, b.title, i.issue_date, i.due_date
        FROM issue_records i
        JOIN users u ON u.user_id = i.user_id
        JOIN books b ON b.book_id = i.book_id
        WHERE i.status = 'issued'
        ORDER BY i.issue_id DESC
        LIMIT 300
        """
    )
    records = decorate_rows_with_avatar(cur.fetchall())
    cur.close()
    conn.close()
    return render_template('issued_books.html', records=records, user=current_user_view())


@app.route('/reports')
@login_required
@staff_required
def reports():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT COUNT(*) AS c FROM users WHERE role='student'")
    students = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM books")
    books = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM issue_records WHERE status='issued'")
    active_issues = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM issue_records WHERE status='returned'")
    returned = cur.fetchone()['c']
    cur.execute("SELECT COALESCE(SUM(fine_amount), 0) AS total_fine FROM issue_records")
    total_fine = cur.fetchone()['total_fine']
    cur.close()
    conn.close()

    return render_template(
        'reports.html',
        students=students,
        books=books,
        active_issues=active_issues,
        returned=returned,
        total_fine=total_fine,
        user=current_user_view(),
    )


@app.route('/activity-log')
@login_required
@staff_required
def activity_log():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    records = []
    try:
        cur.execute(
            """
            SELECT a.log_id, a.action, a.details, a.timestamp, u.full_name, u.role
            FROM activity_log a
            LEFT JOIN users u ON u.user_id = a.user_id
            ORDER BY a.log_id DESC
            LIMIT 200
            """
        )
        records = cur.fetchall()
    except Exception:
        records = []
    finally:
        cur.close()
        conn.close()

    records = decorate_rows_with_avatar(records, username_key=None)
    return render_template('activity_log.html', records=records, user=current_user_view())


@app.route('/add-book', methods=['GET', 'POST'])
@login_required
@staff_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        isbn = request.form.get('isbn', '').strip() or None
        total_copies = int(request.form.get('total_copies', '1') or 1)

        if not title or not author:
            flash('Title and Author are required.', 'error')
            return render_template('add_book.html', user=current_user_view())

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO books (isbn, title, author, category, total_copies, available_copies)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (isbn, title, author, category, total_copies, total_copies),
            )
            conn.commit()
            log_activity('add_book', f'Added book: {title}')
            flash('Book added successfully.', 'success')
            return redirect(url_for('add_book'))
        except Exception as e:
            conn.rollback()
            flash(f'Failed to add book: {e}', 'error')
        finally:
            cur.close()
            conn.close()

    return render_template('add_book.html', user=current_user_view())

# ISSUE BOOK
@app.route('/issue-book', methods=['GET', 'POST'])
@login_required
@staff_required
def issue_book():
    if request.method == 'POST':
        user_input = request.form.get('user_id', '').strip()
        book_input = request.form.get('book_id', '').strip()
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            if user_input.isdigit():
                cur.execute("SELECT user_id FROM users WHERE user_id=%s", (int(user_input),))
            else:
                cur.execute("SELECT user_id FROM users WHERE username=%s", (user_input,))
            user_row = cur.fetchone()

            if not user_row:
                raise ValueError('User not found. Use valid user ID or username.')

            if book_input.isdigit():
                cur.execute("SELECT book_id, available_copies FROM books WHERE book_id=%s", (int(book_input),))
            else:
                cur.execute("SELECT book_id, available_copies FROM books WHERE isbn=%s", (book_input,))
            book_row = cur.fetchone()

            if not book_row:
                raise ValueError('Book not found. Use valid book ID or ISBN.')

            if int(book_row['available_copies']) <= 0:
                raise ValueError('No available copies for this book.')

            # Create issue record
            cur.execute("""
                INSERT INTO issue_records (user_id, book_id, issue_date, due_date, status)
                VALUES (%s, %s, CURRENT_DATE, CURRENT_DATE + INTERVAL '14 days', 'issued')
            """, (user_row['user_id'], book_row['book_id']))
            
            # Update book stock
            cur.execute("""
                UPDATE books SET available_copies = available_copies - 1 
                WHERE book_id = %s AND available_copies > 0
            """, (book_row['book_id'],))
            
            conn.commit()
            log_activity('issue_book', f"Issued book_id={book_row['book_id']} to user_id={user_row['user_id']}")
            cur.close()
            conn.close()
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            return render_template('issue_book.html', error=str(e), user=current_user_view())

    return render_template('issue_book.html', user=current_user_view())

# RETURN BOOK
@app.route('/return-book', methods=['GET', 'POST'])
@login_required
@staff_required
def return_book():
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
                log_activity('return_book', f'Returned issue_id={issue_id}')
            
            cur.close()
            conn.close()
            return redirect(url_for('dashboard'))
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            return render_template('return_book.html', error=str(e), user=current_user_view())

    return render_template('return_book.html', user=current_user_view())

# LOGOUT
@app.route('/logout')
@login_required
def logout():
    log_activity('logout', 'User logged out')
    session.clear()
    return redirect(url_for('login'))

# ERROR HANDLER
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
