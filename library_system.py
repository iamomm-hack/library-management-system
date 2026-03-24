"""
Advanced Library Management System
Features: Multi-user roles, GUI, Database, Fine calculation, Reports, Search filters
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime, timedelta
import json
import hashlib
import random
import string

class LibraryDatabase:
    """Handle all database operations"""
    
    def __init__(self, db_name="library.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table (Admin, Librarian, Student)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Books table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn TEXT UNIQUE,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT,
                publisher TEXT,
                year INTEGER,
                total_copies INTEGER DEFAULT 1,
                available_copies INTEGER DEFAULT 1,
                shelf_location TEXT,
                description TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Issue records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS issue_records (
                issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                user_id INTEGER,
                issue_date DATE NOT NULL,
                due_date DATE NOT NULL,
                return_date DATE,
                fine_amount REAL DEFAULT 0,
                fine_paid BOOLEAN DEFAULT 0,
                status TEXT DEFAULT 'issued',
                FOREIGN KEY (book_id) REFERENCES books (book_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Reservations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                user_id INTEGER,
                reservation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (book_id) REFERENCES books (book_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Activity log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Create default admin if not exists
        cursor.execute("SELECT * FROM users WHERE role='admin'")
        if not cursor.fetchone():
            admin_password = self.hash_password("admin123")
            cursor.execute('''
                INSERT INTO users (username, password, role, full_name, email)
                VALUES (?, ?, ?, ?, ?)
            ''', ("admin", admin_password, "admin", "System Administrator", "admin@library.com"))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def log_activity(self, user_id, action, details):
        """Log user activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activity_log (user_id, action, details)
            VALUES (?, ?, ?)
        ''', (user_id, action, details))
        conn.commit()
        conn.close()


class LibraryManagementSystem:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Library Management System")
        self.root.geometry("1200x700")
        self.root.configure(bg="#2c3e50")
        
        self.db = LibraryDatabase()
        self.current_user = None
        
        # Fine rate per day
        self.fine_per_day = 5.0
        
        # Show login screen
        self.show_login()
    
    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_login(self):
        """Display login screen"""
        self.clear_window()
        
        # Main frame
        login_frame = tk.Frame(self.root, bg="#34495e", padx=40, pady=40)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title
        title = tk.Label(login_frame, text="📚 Library Management System", 
                        font=("Arial", 24, "bold"), bg="#34495e", fg="#ecf0f1")
        title.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # Username
        tk.Label(login_frame, text="Username:", font=("Arial", 12), 
                bg="#34495e", fg="#ecf0f1").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.username_entry = tk.Entry(login_frame, font=("Arial", 12), width=25)
        self.username_entry.grid(row=1, column=1, pady=10)
        
        # Password
        tk.Label(login_frame, text="Password:", font=("Arial", 12), 
                bg="#34495e", fg="#ecf0f1").grid(row=2, column=0, sticky="e", padx=10, pady=10)
        self.password_entry = tk.Entry(login_frame, font=("Arial", 12), width=25, show="*")
        self.password_entry.grid(row=2, column=1, pady=10)
        
        # Login button
        login_btn = tk.Button(login_frame, text="Login", font=("Arial", 12, "bold"),
                             bg="#27ae60", fg="white", padx=30, pady=10,
                             command=self.login)
        login_btn.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Register button
        register_btn = tk.Button(login_frame, text="Register New Student", 
                                font=("Arial", 10), bg="#3498db", fg="white",
                                command=self.show_register)
        register_btn.grid(row=4, column=0, columnspan=2)
        
        # Bind Enter key
        self.password_entry.bind('<Return>', lambda e: self.login())
    
    def login(self):
        """Authenticate user"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        hashed_password = self.db.hash_password(password)
        cursor.execute('''
            SELECT user_id, username, role, full_name FROM users 
            WHERE username=? AND password=?
        ''', (username, hashed_password))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.current_user = {
                'user_id': user[0],
                'username': user[1],
                'role': user[2],
                'full_name': user[3]
            }
            self.db.log_activity(user[0], "LOGIN", f"User {username} logged in")
            self.show_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
    
    def show_register(self):
        """Show student registration form"""
        self.clear_window()
        
        reg_frame = tk.Frame(self.root, bg="#34495e", padx=40, pady=30)
        reg_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(reg_frame, text="Student Registration", font=("Arial", 20, "bold"),
                bg="#34495e", fg="#ecf0f1").grid(row=0, column=0, columnspan=2, pady=20)
        
        # Form fields
        fields = [
            ("Username:", "username"),
            ("Password:", "password"),
            ("Full Name:", "full_name"),
            ("Email:", "email"),
            ("Phone:", "phone")
        ]
        
        self.reg_entries = {}
        
        for idx, (label, key) in enumerate(fields, start=1):
            tk.Label(reg_frame, text=label, font=("Arial", 11), 
                    bg="#34495e", fg="#ecf0f1").grid(row=idx, column=0, sticky="e", padx=10, pady=8)
            entry = tk.Entry(reg_frame, font=("Arial", 11), width=30)
            if key == "password":
                entry.config(show="*")
            entry.grid(row=idx, column=1, pady=8)
            self.reg_entries[key] = entry
        
        # Buttons
        btn_frame = tk.Frame(reg_frame, bg="#34495e")
        btn_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="Register", font=("Arial", 11, "bold"),
                 bg="#27ae60", fg="white", padx=20, pady=8,
                 command=self.register_student).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Back to Login", font=("Arial", 11),
                 bg="#95a5a6", fg="white", padx=20, pady=8,
                 command=self.show_login).pack(side="left", padx=5)
    
    def register_student(self):
        """Register a new student"""
        data = {k: v.get().strip() for k, v in self.reg_entries.items()}
        
        # Validation
        if not all(data.values()):
            messagebox.showerror("Error", "All fields are required")
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            hashed_password = self.db.hash_password(data['password'])
            cursor.execute('''
                INSERT INTO users (username, password, role, full_name, email, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['username'], hashed_password, 'student', 
                  data['full_name'], data['email'], data['phone']))
            conn.commit()
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.show_login()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
        finally:
            conn.close()
    
    def show_dashboard(self):
        """Display main dashboard based on user role"""
        self.clear_window()
        
        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=80)
        header.pack(fill="x")
        
        tk.Label(header, text=f"Welcome, {self.current_user['full_name']} ({self.current_user['role'].upper()})",
                font=("Arial", 16, "bold"), bg="#2c3e50", fg="#ecf0f1").pack(side="left", padx=20, pady=20)
        
        tk.Button(header, text="Logout", font=("Arial", 11), bg="#e74c3c", fg="white",
                 command=self.logout).pack(side="right", padx=20)
        
        # Main content area
        content = tk.Frame(self.root, bg="#ecf0f1")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left sidebar - Menu
        menu_frame = tk.Frame(content, bg="#34495e", width=250)
        menu_frame.pack(side="left", fill="y", padx=(0, 20))
        
        tk.Label(menu_frame, text="📋 Menu", font=("Arial", 14, "bold"),
                bg="#34495e", fg="#ecf0f1", pady=15).pack(fill="x")
        
        # Menu options based on role
        menu_options = self.get_menu_options()
        
        for option, command in menu_options:
            btn = tk.Button(menu_frame, text=option, font=("Arial", 11),
                           bg="#2c3e50", fg="#ecf0f1", activebackground="#1abc9c",
                           activeforeground="white", relief="flat", anchor="w",
                           padx=20, pady=12, command=command)
            btn.pack(fill="x", pady=2)
        
        # Right content area
        self.content_area = tk.Frame(content, bg="white")
        self.content_area.pack(side="right", fill="both", expand=True)
        
        # Show default view
        self.show_home()
    
    def get_menu_options(self):
        """Get menu options based on user role"""
        common = [
            ("🏠 Home", self.show_home),
            ("🔍 Search Books", self.show_search_books),
            ("📖 My Books", self.show_my_books),
        ]
        
        if self.current_user['role'] in ['admin', 'librarian']:
            admin_options = [
                ("➕ Add Book", self.show_add_book),
                ("📤 Issue Book", self.show_issue_book),
                ("📥 Return Book", self.show_return_book),
                ("👥 Manage Users", self.show_manage_users),
                ("📊 Reports", self.show_reports),
                ("📜 Activity Log", self.show_activity_log),
            ]
            return common + admin_options
        else:
            return common + [("🎫 Reserve Book", self.show_reserve_book)]
    
    def logout(self):
        """Logout current user"""
        if self.current_user:
            self.db.log_activity(self.current_user['user_id'], "LOGOUT", 
                                f"User {self.current_user['username']} logged out")
        self.current_user = None
        self.show_login()
    
    def show_home(self):
        """Display home/dashboard statistics"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="📊 Dashboard", font=("Arial", 18, "bold"),
                bg="white").pack(pady=20)
        
        # Statistics cards
        stats_frame = tk.Frame(self.content_area, bg="white")
        stats_frame.pack(fill="both", expand=True, padx=20)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM books")
        total_books = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total_copies) FROM books")
        total_copies = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(available_copies) FROM books")
        available = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM issue_records WHERE status='issued'")
        currently_issued = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='student'")
        total_students = cursor.fetchone()[0]
        
        conn.close()
        
        # Create stat cards
        stats = [
            ("📚 Total Books", total_books, "#3498db"),
            ("📖 Total Copies", total_copies, "#9b59b6"),
            ("✅ Available", available, "#27ae60"),
            ("📤 Issued", currently_issued, "#e67e22"),
            ("👥 Students", total_students, "#1abc9c"),
        ]
        
        for idx, (label, value, color) in enumerate(stats):
            card = tk.Frame(stats_frame, bg=color, relief="raised", bd=2)
            card.grid(row=idx//3, column=idx%3, padx=15, pady=15, sticky="nsew")
            
            tk.Label(card, text=str(value), font=("Arial", 28, "bold"),
                    bg=color, fg="white").pack(pady=(20, 5))
            tk.Label(card, text=label, font=("Arial", 12),
                    bg=color, fg="white").pack(pady=(0, 20))
            
            stats_frame.grid_columnconfigure(idx%3, weight=1)
        
        # Recent activity (for admin/librarian)
        if self.current_user['role'] in ['admin', 'librarian']:
            recent_frame = tk.LabelFrame(self.content_area, text="Recent Issues", 
                                        font=("Arial", 12, "bold"), bg="white", padx=10, pady=10)
            recent_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.title, u.full_name, i.issue_date, i.due_date
                FROM issue_records i
                JOIN books b ON i.book_id = b.book_id
                JOIN users u ON i.user_id = u.user_id
                WHERE i.status = 'issued'
                ORDER BY i.issue_date DESC
                LIMIT 5
            ''')
            recent = cursor.fetchall()
            conn.close()
            
            if recent:
                for issue in recent:
                    text = f"📖 {issue[0]} | 👤 {issue[1]} | Issued: {issue[2]} | Due: {issue[3]}"
                    tk.Label(recent_frame, text=text, font=("Arial", 10),
                            bg="white", anchor="w").pack(fill="x", pady=2)
    
    def show_search_books(self):
        """Display book search interface"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="🔍 Search Books", font=("Arial", 18, "bold"),
                bg="white").pack(pady=20)
        
        # Search controls
        search_frame = tk.Frame(self.content_area, bg="white")
        search_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(search_frame, text="Search by:", font=("Arial", 11),
                bg="white").grid(row=0, column=0, padx=5)
        
        self.search_by = ttk.Combobox(search_frame, values=["Title", "Author", "ISBN", "Category"],
                                     state="readonly", width=12)
        self.search_by.set("Title")
        self.search_by.grid(row=0, column=1, padx=5)
        
        self.search_entry = tk.Entry(search_frame, font=("Arial", 11), width=30)
        self.search_entry.grid(row=0, column=2, padx=5)
        
        tk.Button(search_frame, text="Search", font=("Arial", 10, "bold"),
                 bg="#3498db", fg="white", command=self.search_books).grid(row=0, column=3, padx=5)
        
        tk.Button(search_frame, text="Show All", font=("Arial", 10),
                 bg="#95a5a6", fg="white", command=lambda: self.search_books(show_all=True)).grid(row=0, column=4, padx=5)
        
        # Results table
        table_frame = tk.Frame(self.content_area, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Scrollbars
        v_scroll = tk.Scrollbar(table_frame)
        v_scroll.pack(side="right", fill="y")
        
        h_scroll = tk.Scrollbar(table_frame, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")
        
        # Treeview
        columns = ("ID", "ISBN", "Title", "Author", "Category", "Year", "Available", "Location")
        self.search_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                       yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=100)
        
        self.search_tree.column("Title", width=200)
        self.search_tree.column("Author", width=150)
        
        self.search_tree.pack(fill="both", expand=True)
        
        v_scroll.config(command=self.search_tree.yview)
        h_scroll.config(command=self.search_tree.xview)
        
        # Bind Enter key
        self.search_entry.bind('<Return>', lambda e: self.search_books())
    
    def search_books(self, show_all=False):
        """Search books in database"""
        # Clear existing items
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if show_all:
            cursor.execute("SELECT * FROM books ORDER BY title")
        else:
            search_term = f"%{self.search_entry.get().strip()}%"
            search_field = self.search_by.get().lower()
            
            query = f"SELECT * FROM books WHERE {search_field} LIKE ? ORDER BY title"
            cursor.execute(query, (search_term,))
        
        books = cursor.fetchall()
        conn.close()
        
        for book in books:
            self.search_tree.insert("", "end", values=(
                book[0], book[1], book[2], book[3], book[4], book[6],
                f"{book[8]}/{book[7]}", book[9]
            ))
    
    def show_my_books(self):
        """Show books issued to current user"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="📖 My Issued Books", font=("Arial", 18, "bold"),
                bg="white").pack(pady=20)
        
        # Table
        table_frame = tk.Frame(self.content_area, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Book Title", "Author", "Issue Date", "Due Date", "Fine", "Status")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.column("Book Title", width=250)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(table_frame, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        
        # Fetch data
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.title, b.author, i.issue_date, i.due_date, i.fine_amount, i.status
            FROM issue_records i
            JOIN books b ON i.book_id = b.book_id
            WHERE i.user_id = ? AND i.status = 'issued'
            ORDER BY i.issue_date DESC
        ''', (self.current_user['user_id'],))
        
        records = cursor.fetchall()
        conn.close()
        
        for record in records:
            # Calculate fine if overdue
            due_date = datetime.strptime(record[3], "%Y-%m-%d")
            if datetime.now() > due_date:
                days_overdue = (datetime.now() - due_date).days
                fine = days_overdue * self.fine_per_day
            else:
                fine = 0
            
            tree.insert("", "end", values=(
                record[0], record[1], record[2], record[3],
                f"₹{fine:.2f}", record[5]
            ))
    
    def show_add_book(self):
        """Show add book form"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="➕ Add New Book", font=("Arial", 18, "bold"),
                bg="white").pack(pady=20)
        
        form_frame = tk.Frame(self.content_area, bg="white")
        form_frame.pack(pady=20)
        
        fields = [
            ("ISBN:", "isbn"),
            ("Title:", "title"),
            ("Author:", "author"),
            ("Category:", "category"),
            ("Publisher:", "publisher"),
            ("Year:", "year"),
            ("Total Copies:", "total_copies"),
            ("Shelf Location:", "shelf_location"),
            ("Description:", "description")
        ]
        
        self.book_entries = {}
        
        for idx, (label, key) in enumerate(fields):
            tk.Label(form_frame, text=label, font=("Arial", 11), bg="white").grid(
                row=idx, column=0, sticky="e", padx=10, pady=8)
            
            if key == "description":
                entry = tk.Text(form_frame, font=("Arial", 11), width=35, height=4)
            else:
                entry = tk.Entry(form_frame, font=("Arial", 11), width=35)
            
            entry.grid(row=idx, column=1, pady=8)
            self.book_entries[key] = entry
        
        tk.Button(self.content_area, text="Add Book", font=("Arial", 12, "bold"),
                 bg="#27ae60", fg="white", padx=30, pady=10,
                 command=self.add_book).pack(pady=20)
    
    def add_book(self):
        """Add book to database"""
        data = {}
        for key, widget in self.book_entries.items():
            if isinstance(widget, tk.Text):
                data[key] = widget.get("1.0", "end-1c").strip()
            else:
                data[key] = widget.get().strip()
        
        if not data['title'] or not data['author']:
            messagebox.showerror("Error", "Title and Author are required")
            return
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            total_copies = int(data['total_copies']) if data['total_copies'] else 1
            
            cursor.execute('''
                INSERT INTO books (isbn, title, author, category, publisher, year, 
                                 total_copies, available_copies, shelf_location, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data['isbn'], data['title'], data['author'], data['category'],
                  data['publisher'], data['year'], total_copies, total_copies,
                  data['shelf_location'], data['description']))
            
            conn.commit()
            conn.close()
            
            self.db.log_activity(self.current_user['user_id'], "ADD_BOOK",
                               f"Added book: {data['title']}")
            
            messagebox.showinfo("Success", "Book added successfully!")
            self.show_home()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add book: {str(e)}")
    
    def show_issue_book(self):
        """Show issue book interface"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="📤 Issue Book", font=("Arial", 18, "bold"),
                bg="white").pack(pady=20)
        
        form_frame = tk.Frame(self.content_area, bg="white")
        form_frame.pack(pady=20)
        
        # Student username
        tk.Label(form_frame, text="Student Username:", font=("Arial", 11),
                bg="white").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.issue_username = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.issue_username.grid(row=0, column=1, pady=10)
        
        # Book ISBN or ID
        tk.Label(form_frame, text="Book ISBN/ID:", font=("Arial", 11),
                bg="white").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.issue_book_id = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.issue_book_id.grid(row=1, column=1, pady=10)
        
        # Days
        tk.Label(form_frame, text="Issue Days:", font=("Arial", 11),
                bg="white").grid(row=2, column=0, sticky="e", padx=10, pady=10)
        self.issue_days = tk.Spinbox(form_frame, from_=1, to=30, font=("Arial", 11), width=28)
        self.issue_days.delete(0, "end")
        self.issue_days.insert(0, "14")
        self.issue_days.grid(row=2, column=1, pady=10)
        
        tk.Button(self.content_area, text="Issue Book", font=("Arial", 12, "bold"),
                 bg="#3498db", fg="white", padx=30, pady=10,
                 command=self.issue_book).pack(pady=20)
    
    def issue_book(self):
        """Issue a book to a student"""
        username = self.issue_username.get().strip()
        book_identifier = self.issue_book_id.get().strip()
        days = int(self.issue_days.get())
        
        if not username or not book_identifier:
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get user
        cursor.execute("SELECT user_id, full_name FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        
        if not user:
            messagebox.showerror("Error", "Student not found")
            conn.close()
            return
        
        # Get book
        cursor.execute('''
            SELECT book_id, title, available_copies FROM books 
            WHERE book_id=? OR isbn=?
        ''', (book_identifier, book_identifier))
        book = cursor.fetchone()
        
        if not book:
            messagebox.showerror("Error", "Book not found")
            conn.close()
            return
        
        if book[2] <= 0:
            messagebox.showerror("Error", "No copies available")
            conn.close()
            return
        
        # Issue the book
        issue_date = datetime.now().date()
        due_date = issue_date + timedelta(days=days)
        
        cursor.execute('''
            INSERT INTO issue_records (book_id, user_id, issue_date, due_date, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (book[0], user[0], issue_date, due_date, 'issued'))
        
        # Update available copies
        cursor.execute('''
            UPDATE books SET available_copies = available_copies - 1
            WHERE book_id = ?
        ''', (book[0],))
        
        conn.commit()
        conn.close()
        
        self.db.log_activity(self.current_user['user_id'], "ISSUE_BOOK",
                           f"Issued '{book[1]}' to {user[1]}")
        
        messagebox.showinfo("Success", 
                          f"Book '{book[1]}' issued to {user[1]}\nDue date: {due_date}")
        self.show_home()
    
    def show_return_book(self):
        """Show return book interface"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="📥 Return Book", font=("Arial", 18, "bold"),
                bg="white").pack(pady=20)
        
        form_frame = tk.Frame(self.content_area, bg="white")
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Issue ID:", font=("Arial", 11),
                bg="white").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.return_issue_id = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.return_issue_id.grid(row=0, column=1, pady=10)
        
        tk.Button(self.content_area, text="Return Book", font=("Arial", 12, "bold"),
                 bg="#27ae60", fg="white", padx=30, pady=10,
                 command=self.return_book).pack(pady=20)
        
        # Show pending returns
        tk.Label(self.content_area, text="Pending Returns:", font=("Arial", 14, "bold"),
                bg="white").pack(pady=(30, 10))
        
        table_frame = tk.Frame(self.content_area, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Issue ID", "Book", "Student", "Issue Date", "Due Date", "Days Overdue", "Fine")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.column("Book", width=200)
        tree.pack(fill="both", expand=True)
        
        # Fetch pending returns
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT i.issue_id, b.title, u.full_name, i.issue_date, i.due_date
            FROM issue_records i
            JOIN books b ON i.book_id = b.book_id
            JOIN users u ON i.user_id = u.user_id
            WHERE i.status = 'issued'
            ORDER BY i.due_date
        ''')
        
        records = cursor.fetchall()
        conn.close()
        
        for record in records:
            due_date = datetime.strptime(record[4], "%Y-%m-%d")
            days_overdue = max(0, (datetime.now() - due_date).days)
            fine = days_overdue * self.fine_per_day
            
            tree.insert("", "end", values=(
                record[0], record[1], record[2], record[3], record[4],
                days_overdue, f"₹{fine:.2f}"
            ))
    
    def return_book(self):
        """Process book return"""
        issue_id = self.return_issue_id.get().strip()
        
        if not issue_id:
            messagebox.showerror("Error", "Please enter Issue ID")
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get issue record
        cursor.execute('''
            SELECT i.issue_id, i.book_id, i.due_date, b.title, u.full_name
            FROM issue_records i
            JOIN books b ON i.book_id = b.book_id
            JOIN users u ON i.user_id = u.user_id
            WHERE i.issue_id = ? AND i.status = 'issued'
        ''', (issue_id,))
        
        record = cursor.fetchone()
        
        if not record:
            messagebox.showerror("Error", "Invalid Issue ID or already returned")
            conn.close()
            return
        
        # Calculate fine
        due_date = datetime.strptime(record[2], "%Y-%m-%d")
        days_overdue = max(0, (datetime.now() - due_date).days)
        fine = days_overdue * self.fine_per_day
        
        # Update record
        return_date = datetime.now().date()
        cursor.execute('''
            UPDATE issue_records 
            SET return_date = ?, fine_amount = ?, status = 'returned'
            WHERE issue_id = ?
        ''', (return_date, fine, issue_id))
        
        # Update available copies
        cursor.execute('''
            UPDATE books SET available_copies = available_copies + 1
            WHERE book_id = ?
        ''', (record[1],))
        
        conn.commit()
        conn.close()
        
        self.db.log_activity(self.current_user['user_id'], "RETURN_BOOK",
                           f"Returned '{record[3]}' from {record[4]}")
        
        msg = f"Book '{record[3]}' returned successfully!"
        if fine > 0:
            msg += f"\n\nFine: ₹{fine:.2f} ({days_overdue} days overdue)"
        
        messagebox.showinfo("Success", msg)
        self.show_return_book()
    
    def show_reserve_book(self):
        """Show book reservation interface for students"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="🎫 Reserve a Book", font=("Arial", 18, "bold"),
                bg="white").pack(pady=20)
        
        # Available books for reservation
        tk.Label(self.content_area, text="Books Currently Unavailable:", 
                font=("Arial", 12), bg="white").pack(pady=10)
        
        table_frame = tk.Frame(self.content_area, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Book ID", "Title", "Author", "Total", "Available")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        tree.column("Title", width=300)
        tree.pack(fill="both", expand=True)
        
        # Fetch books with no available copies
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT book_id, title, author, total_copies, available_copies
            FROM books
            WHERE available_copies = 0
            ORDER BY title
        ''')
        
        books = cursor.fetchall()
        conn.close()
        
        for book in books:
            tree.insert("", "end", values=book)
        
        # Reserve button
        btn_frame = tk.Frame(self.content_area, bg="white")
        btn_frame.pack(pady=20)
        
        tk.Label(btn_frame, text="Book ID:", font=("Arial", 11),
                bg="white").pack(side="left", padx=5)
        self.reserve_book_id = tk.Entry(btn_frame, font=("Arial", 11), width=15)
        self.reserve_book_id.pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Reserve", font=("Arial", 11, "bold"),
                 bg="#e67e22", fg="white", command=self.reserve_book).pack(side="left", padx=5)
    
    def reserve_book(self):
        """Reserve a book"""
        book_id = self.reserve_book_id.get().strip()
        
        if not book_id:
            messagebox.showerror("Error", "Please enter Book ID")
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if book exists and is unavailable
        cursor.execute('''
            SELECT book_id, title, available_copies FROM books
            WHERE book_id = ?
        ''', (book_id,))
        
        book = cursor.fetchone()
        
        if not book:
            messagebox.showerror("Error", "Book not found")
            conn.close()
            return
        
        if book[2] > 0:
            messagebox.showinfo("Info", "Book is available. You can issue it directly!")
            conn.close()
            return
        
        # Check if already reserved
        cursor.execute('''
            SELECT * FROM reservations
            WHERE book_id = ? AND user_id = ? AND status = 'active'
        ''', (book_id, self.current_user['user_id']))
        
        if cursor.fetchone():
            messagebox.showinfo("Info", "You have already reserved this book")
            conn.close()
            return
        
        # Create reservation
        cursor.execute('''
            INSERT INTO reservations (book_id, user_id, status)
            VALUES (?, ?, 'active')
        ''', (book_id, self.current_user['user_id']))
        
        conn.commit()
        conn.close()
        
        self.db.log_activity(self.current_user['user_id'], "RESERVE_BOOK",
                           f"Reserved book: {book[1]}")
        
        messagebox.showinfo("Success", f"Book '{book[1]}' reserved successfully!")
        self.show_reserve_book()
    
    def show_manage_users(self):
        """Show user management interface"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="👥 Manage Users", font=("Arial", 18, "bold"),
                bg="white").pack(pady=20)
        
        # Users table
        table_frame = tk.Frame(self.content_area, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("ID", "Username", "Full Name", "Role", "Email", "Phone")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        tree.column("Full Name", width=200)
        tree.pack(fill="both", expand=True)
        
        # Fetch users
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, full_name, role, email, phone FROM users")
        users = cursor.fetchall()
        conn.close()
        
        for user in users:
            tree.insert("", "end", values=user)
    
    def show_reports(self):
        """Show various reports"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="📊 Reports & Analytics", font=("Arial", 18, "bold"),
                bg="white").pack(pady=20)
        
        reports_frame = tk.Frame(self.content_area, bg="white")
        reports_frame.pack(fill="both", expand=True, padx=20)
        
        # Overdue books
        overdue_frame = tk.LabelFrame(reports_frame, text="⚠️ Overdue Books", 
                                     font=("Arial", 12, "bold"), bg="white", padx=10, pady=10)
        overdue_frame.pack(fill="x", pady=10)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.title, u.full_name, i.due_date
            FROM issue_records i
            JOIN books b ON i.book_id = b.book_id
            JOIN users u ON i.user_id = u.user_id
            WHERE i.status = 'issued' AND i.due_date < date('now')
            ORDER BY i.due_date
        ''')
        
        overdue = cursor.fetchall()
        
        if overdue:
            for item in overdue:
                days = (datetime.now() - datetime.strptime(item[2], "%Y-%m-%d")).days
                text = f"📖 {item[0]} | 👤 {item[1]} | {days} days overdue"
                tk.Label(overdue_frame, text=text, font=("Arial", 10), bg="white",
                        fg="red", anchor="w").pack(fill="x", pady=2)
        else:
            tk.Label(overdue_frame, text="✅ No overdue books!", 
                    font=("Arial", 10), bg="white", fg="green").pack()
        
        # Most issued books
        popular_frame = tk.LabelFrame(reports_frame, text="🔥 Most Issued Books", 
                                     font=("Arial", 12, "bold"), bg="white", padx=10, pady=10)
        popular_frame.pack(fill="x", pady=10)
        
        cursor.execute('''
            SELECT b.title, COUNT(*) as count
            FROM issue_records i
            JOIN books b ON i.book_id = b.book_id
            GROUP BY b.book_id
            ORDER BY count DESC
            LIMIT 5
        ''')
        
        popular = cursor.fetchall()
        
        for item in popular:
            text = f"📚 {item[0]} - Issued {item[1]} times"
            tk.Label(popular_frame, text=text, font=("Arial", 10),
                    bg="white", anchor="w").pack(fill="x", pady=2)
        
        conn.close()
    
    def show_activity_log(self):
        """Show activity log"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="📜 Activity Log", font=("Arial", 18, "bold"),
                bg="white").pack(pady=20)
        
        table_frame = tk.Frame(self.content_area, bg="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Treeview
        columns = ("ID", "User", "Action", "Details", "Timestamp")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                           yscrollcommand=scrollbar.set, height=25)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.column("Details", width=300)
        tree.column("Timestamp", width=150)
        
        scrollbar.config(command=tree.yview)
        tree.pack(fill="both", expand=True)
        
        # Fetch logs
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.log_id, u.username, l.action, l.details, l.timestamp
            FROM activity_log l
            JOIN users u ON l.user_id = u.user_id
            ORDER BY l.timestamp DESC
            LIMIT 100
        ''')
        
        logs = cursor.fetchall()
        conn.close()
        
        for log in logs:
            tree.insert("", "end", values=log)


def main():
    root = tk.Tk()
    app = LibraryManagementSystem(root)
    root.mainloop()


if __name__ == "__main__":
    main()
