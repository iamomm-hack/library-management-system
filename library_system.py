"""
Advanced Library Management System
Features: Multi-user roles, GUI, Database, Fine calculation, Reports, Search filters
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import psycopg2
from datetime import datetime, timedelta
import json
import hashlib
import random
import string

class LibraryDatabase:
    """Handle all database operations"""
    
    def __init__(self, host="localhost", port=5432, database="library_db", user="postgres", password="system"):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.init_database()
    
    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
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
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    book_id SERIAL PRIMARY KEY,
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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS issue_records (
                    issue_id SERIAL PRIMARY KEY,
                    book_id INTEGER,
                    user_id INTEGER,
                    issue_date DATE NOT NULL,
                    due_date DATE NOT NULL,
                    return_date DATE,
                    fine_amount REAL DEFAULT 0,
                    fine_paid BOOLEAN DEFAULT false,
                    status TEXT DEFAULT 'issued',
                    FOREIGN KEY (book_id) REFERENCES books (book_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id SERIAL PRIMARY KEY,
                    book_id INTEGER,
                    user_id INTEGER,
                    reservation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (book_id) REFERENCES books (book_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    log_id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            cursor.execute("SELECT * FROM users WHERE role='admin'")
            if not cursor.fetchone():
                admin_password = self.hash_password("admin123")
                cursor.execute('''
                    INSERT INTO users (username, password, role, full_name, email)
                    VALUES (%s, %s, %s, %s, %s)
                ''', ("admin", admin_password, "admin", "System Administrator", "admin@library.com"))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Database initialization error: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def log_activity(self, user_id, action, details):
        """Log user activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO activity_log (user_id, action, details)
                VALUES (%s, %s, %s)
            ''', (user_id, action, details))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


class LibraryManagementSystem:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Library Management System")
        self.root.geometry("1200x700")
        self.colors = {
            'app_bg': "#0f172a",
            'surface': "#111827",
            'surface_soft': "#1f2937",
            'panel': "#f8fafc",
            'text_light': "#e2e8f0",
            'text_dark': "#0f172a",
            'muted': "#94a3b8",
            'accent': "#2563eb",
            'accent_hover': "#1d4ed8",
            'success': "#10b981",
            'success_hover': "#059669",
            'danger': "#ef4444",
            'danger_hover': "#dc2626",
            'warning': "#f59e0b",
            'neutral': "#64748b",
            'input_bg': "#ffffff",
            'border': "#cbd5e1",
            'table_header': "#e2e8f0",
            'table_row': "#ffffff",
            'table_selected': "#dbeafe",
            'page_bg': "#f1f5f9"
        }
        self.root.configure(bg=self.colors['app_bg'])
        self.setup_modern_styles()
        
        self.db = LibraryDatabase(
            host="localhost",
            port=5432,
            database="library_db",
            user="postgres",
            password="system"
        )
        self.current_user = None
        
        self.fine_per_day = 5.0
        
        self.show_login()

    def setup_modern_styles(self):
        """Configure modern ttk styles"""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Modern.TCombobox",
            fieldbackground=self.colors['input_bg'],
            background=self.colors['input_bg'],
            foreground=self.colors['text_dark'],
            bordercolor=self.colors['border'],
            arrowcolor=self.colors['text_dark'],
            relief="flat",
            padding=5
        )
        style.map(
            "Modern.TCombobox",
            fieldbackground=[('readonly', self.colors['input_bg'])],
            background=[('readonly', self.colors['input_bg'])],
            foreground=[('readonly', self.colors['text_dark'])]
        )

        style.configure(
            "Modern.Treeview",
            background=self.colors['table_row'],
            fieldbackground=self.colors['table_row'],
            foreground=self.colors['text_dark'],
            bordercolor=self.colors['border'],
            rowheight=30,
            relief="flat"
        )
        style.map("Modern.Treeview", background=[('selected', self.colors['table_selected'])])

        style.configure(
            "Modern.Treeview.Heading",
            background=self.colors['table_header'],
            foreground=self.colors['text_dark'],
            borderwidth=0,
            relief="flat",
            font=("Segoe UI", 10, "bold")
        )

        style.configure(
            "Modern.Vertical.TScrollbar",
            background=self.colors['surface_soft'],
            troughcolor=self.colors['table_header'],
            bordercolor=self.colors['table_header'],
            arrowcolor=self.colors['text_dark'],
            relief="flat"
        )
        style.map(
            "Modern.Vertical.TScrollbar",
            background=[('active', self.colors['surface'])]
        )

        style.configure(
            "Modern.Horizontal.TScrollbar",
            background=self.colors['surface_soft'],
            troughcolor=self.colors['table_header'],
            bordercolor=self.colors['table_header'],
            arrowcolor=self.colors['text_dark'],
            relief="flat"
        )
        style.map(
            "Modern.Horizontal.TScrollbar",
            background=[('active', self.colors['surface'])]
        )

    def create_modern_button(self, parent, text, command, variant="primary", font=("Segoe UI", 11, "bold"),
                             padx=24, pady=10, anchor="center"):
        """Create consistently styled button"""
        palette = {
            'primary': (self.colors['accent'], self.colors['accent_hover']),
            'success': (self.colors['success'], self.colors['success_hover']),
            'danger': (self.colors['danger'], self.colors['danger_hover']),
            'neutral': (self.colors['neutral'], "#475569"),
            'warning': (self.colors['warning'], "#d97706")
        }
        bg, active_bg = palette.get(variant, palette['primary'])
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=font,
            bg=bg,
            fg="white",
            activebackground=active_bg,
            activeforeground="white",
            relief="flat",
            borderwidth=0,
            padx=padx,
            pady=pady,
            cursor="hand2",
            anchor=anchor
        )

    def create_modern_entry(self, parent, width=30, show=None, font=("Segoe UI", 11)):
        """Create consistently styled entry"""
        entry = tk.Entry(
            parent,
            width=width,
            font=font,
            show=show,
            bg=self.colors['input_bg'],
            fg=self.colors['text_dark'],
            insertbackground=self.colors['text_dark'],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            highlightcolor=self.colors['accent']
        )
        return entry
    
    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_login(self):
        """Display login screen"""
        self.clear_window()
        self.root.configure(bg=self.colors['app_bg'])
        
        login_frame = tk.Frame(self.root, bg=self.colors['surface'], padx=45, pady=45)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        title = tk.Label(login_frame, text="📚 Library Management System", 
                font=("Segoe UI", 24, "bold"), bg=self.colors['surface'], fg=self.colors['text_light'])
        title.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        tk.Label(login_frame, text="Username:", font=("Segoe UI", 11), 
            bg=self.colors['surface'], fg=self.colors['text_light']).grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.username_entry = self.create_modern_entry(login_frame, width=28, font=("Segoe UI", 11))
        self.username_entry.grid(row=1, column=1, pady=10)
        
        tk.Label(login_frame, text="Password:", font=("Segoe UI", 11), 
            bg=self.colors['surface'], fg=self.colors['text_light']).grid(row=2, column=0, sticky="e", padx=10, pady=10)
        self.password_entry = self.create_modern_entry(login_frame, width=28, show="*", font=("Segoe UI", 11))
        self.password_entry.grid(row=2, column=1, pady=10)
        
        login_btn = self.create_modern_button(login_frame, "Login", self.login, variant="success",
                              font=("Segoe UI", 11, "bold"), padx=34, pady=10)
        login_btn.grid(row=3, column=0, columnspan=2, pady=20)
        
        register_btn = self.create_modern_button(login_frame, "Register New Student", self.show_register,
                             variant="primary", font=("Segoe UI", 10), padx=22, pady=8)
        register_btn.grid(row=4, column=0, columnspan=2)
        
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
            WHERE username=%s AND password=%s
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
        self.root.configure(bg=self.colors['app_bg'])
        
        reg_frame = tk.Frame(self.root, bg=self.colors['surface'], padx=45, pady=35)
        reg_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(reg_frame, text="Student Registration", font=("Segoe UI", 20, "bold"),
            bg=self.colors['surface'], fg=self.colors['text_light']).grid(row=0, column=0, columnspan=2, pady=20)
        
        fields = [
            ("Username:", "username"),
            ("Password:", "password"),
            ("Full Name:", "full_name"),
            ("Email:", "email"),
            ("Phone:", "phone")
        ]
        
        self.reg_entries = {}
        
        for idx, (label, key) in enumerate(fields, start=1):
            tk.Label(reg_frame, text=label, font=("Segoe UI", 10), 
                    bg=self.colors['surface'], fg=self.colors['text_light']).grid(row=idx, column=0, sticky="e", padx=10, pady=8)
            entry = self.create_modern_entry(reg_frame, width=32, show="*" if key == "password" else None)
            entry.grid(row=idx, column=1, pady=8)
            self.reg_entries[key] = entry
        
        btn_frame = tk.Frame(reg_frame, bg=self.colors['surface'])
        btn_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
        
        self.create_modern_button(btn_frame, "Register", self.register_student, variant="success",
                                  font=("Segoe UI", 10, "bold"), padx=20, pady=8).pack(side="left", padx=5)
        
        self.create_modern_button(btn_frame, "Back to Login", self.show_login, variant="neutral",
                                  font=("Segoe UI", 10), padx=20, pady=8).pack(side="left", padx=5)
    
    def register_student(self):
        """Register a new student"""
        data = {k: v.get().strip() for k, v in self.reg_entries.items()}
        
        if not all(data.values()):
            messagebox.showerror("Error", "All fields are required")
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            hashed_password = self.db.hash_password(data['password'])
            cursor.execute('''
                INSERT INTO users (username, password, role, full_name, email, phone)
                VALUES (%s, %s, %s, %s, %s, %s)
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
        self.root.configure(bg=self.colors['app_bg'])
        
        header = tk.Frame(self.root, bg=self.colors['surface'], height=80)
        header.pack(fill="x")
        
        tk.Label(header, text=f"Welcome, {self.current_user['full_name']} ({self.current_user['role'].upper()})",
            font=("Segoe UI", 15, "bold"), bg=self.colors['surface'], fg=self.colors['text_light']).pack(side="left", padx=20, pady=20)
        
        self.create_modern_button(header, "Logout", self.logout, variant="danger",
                      font=("Segoe UI", 10), padx=20, pady=7).pack(side="right", padx=20)
        
        content = tk.Frame(self.root, bg=self.colors['page_bg'])
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        menu_frame = tk.Frame(content, bg=self.colors['surface_soft'], width=250)
        menu_frame.pack(side="left", fill="y", padx=(0, 20))
        
        tk.Label(menu_frame, text="📋 Menu", font=("Segoe UI", 14, "bold"),
            bg=self.colors['surface_soft'], fg=self.colors['text_light'], pady=15).pack(fill="x")
        
        menu_options = self.get_menu_options()
        
        for option, command in menu_options:
            btn = tk.Button(menu_frame, text=option, font=("Arial", 11),
                           bg=self.colors['surface'], fg=self.colors['text_light'], activebackground=self.colors['accent'],
                           activeforeground="white", relief="flat", anchor="w",
                           padx=20, pady=12, command=command, borderwidth=0, cursor="hand2")
            btn.pack(fill="x", pady=2)
        
        self.content_area = tk.Frame(content, bg=self.colors['page_bg'])
        self.content_area.pack(side="right", fill="both", expand=True)
        
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
                ("📚 Issued Books", self.show_issued_books),
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
        
        tk.Label(self.content_area, text="📊 Dashboard", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)
        
        stats_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        stats_frame.pack(fill="both", expand=True, padx=20)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
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
        
        stats = [
            ("📚 Total Books", total_books, "#2563eb"),
            ("📖 Total Copies", total_copies, "#7c3aed"),
            ("✅ Available", available, "#10b981"),
            ("📤 Issued", currently_issued, "#f59e0b"),
            ("👥 Students", total_students, "#0ea5e9"),
        ]
        
        for idx, (label, value, color) in enumerate(stats):
            card = tk.Frame(stats_frame, bg=color, relief="raised", bd=2)
            card.grid(row=idx//3, column=idx%3, padx=15, pady=15, sticky="nsew")
            
            tk.Label(card, text=str(value), font=("Segoe UI", 28, "bold"),
                    bg=color, fg="white").pack(pady=(20, 5))
            tk.Label(card, text=label, font=("Segoe UI", 11),
                    bg=color, fg="white").pack(pady=(0, 20))
            
            stats_frame.grid_columnconfigure(idx%3, weight=1)
        
        if self.current_user['role'] in ['admin', 'librarian']:
            recent_frame = tk.LabelFrame(self.content_area, text="Recent Issues", 
                                        font=("Segoe UI", 11, "bold"), bg=self.colors['panel'],
                                        fg=self.colors['text_dark'], padx=10, pady=10)
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
                    tk.Label(recent_frame, text=text, font=("Segoe UI", 10),
                        bg=self.colors['panel'], fg=self.colors['text_dark'], anchor="w").pack(fill="x", pady=2)
    
    def show_search_books(self):
        """Display book search interface"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="🔍 Search Books", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)
        
        search_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        search_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(search_frame, text="Search by:", font=("Segoe UI", 11),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).grid(row=0, column=0, padx=5)
        
        self.search_by = ttk.Combobox(search_frame, values=["Title", "Author", "ISBN", "Category"],
                         state="readonly", width=12, style="Modern.TCombobox")
        self.search_by.set("Title")
        self.search_by.grid(row=0, column=1, padx=5)
        
        self.search_entry = self.create_modern_entry(search_frame, width=32)
        self.search_entry.grid(row=0, column=2, padx=5)
        
        self.create_modern_button(search_frame, "Search", self.search_books,
                      variant="primary", font=("Segoe UI", 10, "bold"),
                      padx=18, pady=7).grid(row=0, column=3, padx=5)
        
        self.create_modern_button(search_frame, "Show All", lambda: self.search_books(show_all=True),
                      variant="neutral", font=("Segoe UI", 10),
                      padx=16, pady=7).grid(row=0, column=4, padx=5)
        
        table_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        v_scroll = ttk.Scrollbar(table_frame, style="Modern.Vertical.TScrollbar")
        v_scroll.pack(side="right", fill="y")
        
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", style="Modern.Horizontal.TScrollbar")
        h_scroll.pack(side="bottom", fill="x")
        
        columns = ("ID", "ISBN", "Title", "Author", "Category", "Year", "Available", "Location")
        self.search_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                       yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set,
                                       style="Modern.Treeview")
        
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=100)
        
        self.search_tree.column("Title", width=200)
        self.search_tree.column("Author", width=150)
        
        self.search_tree.pack(fill="both", expand=True, padx=(0, 6), pady=(0, 6))
        
        v_scroll.config(command=self.search_tree.yview)
        h_scroll.config(command=self.search_tree.xview)
        
        self.search_entry.bind('<Return>', lambda e: self.search_books())
    
    def search_books(self, show_all=False):
        """Search books in database"""
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if show_all:
            cursor.execute("SELECT * FROM books ORDER BY title")
        else:
            search_term = f"%{self.search_entry.get().strip()}%"
            search_field = self.search_by.get().lower()
            
            query = f"SELECT * FROM books WHERE {search_field} ILIKE %s ORDER BY title"
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
        
        tk.Label(self.content_area, text="📖 My Issued Books", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)
        
        table_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Book Title", "Author", "Issue Date", "Due Date", "Fine", "Status")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15, style="Modern.Treeview")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.column("Book Title", width=250)
        
        scrollbar = ttk.Scrollbar(table_frame, command=tree.yview, style="Modern.Vertical.TScrollbar")
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True, padx=(0, 6), pady=(0, 6))
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.title, b.author, i.issue_date, i.due_date, i.fine_amount, i.status
            FROM issue_records i
            JOIN books b ON i.book_id = b.book_id
            WHERE i.user_id = %s AND i.status = 'issued'
            ORDER BY i.issue_date DESC
        ''', (self.current_user['user_id'],))
        
        records = cursor.fetchall()
        conn.close()
        
        for record in records:
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
        
        tk.Label(self.content_area, text="➕ Add New Book", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)
        
        form_frame = tk.Frame(self.content_area, bg=self.colors['panel'], padx=24, pady=24)
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
            tk.Label(form_frame, text=label, font=("Segoe UI", 10),
                    bg=self.colors['panel'], fg=self.colors['text_dark']).grid(
                row=idx, column=0, sticky="e", padx=10, pady=8)
            
            if key == "description":
                entry = tk.Text(
                    form_frame,
                    font=("Segoe UI", 11),
                    width=35,
                    height=4,
                    bg=self.colors['input_bg'],
                    fg=self.colors['text_dark'],
                    insertbackground=self.colors['text_dark'],
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=self.colors['border'],
                    highlightcolor=self.colors['accent']
                )
            else:
                entry = self.create_modern_entry(form_frame, width=37)
            
            entry.grid(row=idx, column=1, pady=8)
            self.book_entries[key] = entry
        
        self.create_modern_button(self.content_area, "Add Book", self.add_book,
                                  variant="success", font=("Segoe UI", 11, "bold"),
                                  padx=30, pady=10).pack(pady=20)
    
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        
        tk.Label(self.content_area, text="📤 Issue Book", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)
        
        form_frame = tk.Frame(self.content_area, bg=self.colors['panel'], padx=24, pady=24)
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Student Username:", font=("Segoe UI", 10),
            bg=self.colors['panel'], fg=self.colors['text_dark']).grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.issue_username = self.create_modern_entry(form_frame, width=32)
        self.issue_username.grid(row=0, column=1, pady=10)
        
        tk.Label(form_frame, text="Book ISBN/ID:", font=("Segoe UI", 10),
            bg=self.colors['panel'], fg=self.colors['text_dark']).grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.issue_book_id = self.create_modern_entry(form_frame, width=32)
        self.issue_book_id.grid(row=1, column=1, pady=10)
        
        tk.Label(form_frame, text="Issue Days:", font=("Segoe UI", 10),
            bg=self.colors['panel'], fg=self.colors['text_dark']).grid(row=2, column=0, sticky="e", padx=10, pady=10)
        self.issue_days = tk.Spinbox(
            form_frame,
            from_=1,
            to=30,
            font=("Segoe UI", 11),
            width=30,
            bg=self.colors['input_bg'],
            fg=self.colors['text_dark'],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            highlightcolor=self.colors['accent']
        )
        self.issue_days.delete(0, "end")
        self.issue_days.insert(0, "14")
        self.issue_days.grid(row=2, column=1, pady=10)
        
        self.create_modern_button(self.content_area, "Issue Book", self.issue_book,
                      variant="primary", font=("Segoe UI", 11, "bold"),
                      padx=30, pady=10).pack(pady=20)
    
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
        
        cursor.execute("SELECT user_id, full_name FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        
        if not user:
            messagebox.showerror("Error", "Student not found")
            conn.close()
            return
        
        cursor.execute('''
            SELECT book_id, title, available_copies FROM books 
            WHERE book_id=%s OR isbn=%s
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
        
        issue_date = datetime.now().date()
        due_date = issue_date + timedelta(days=days)
        
        cursor.execute('''
            INSERT INTO issue_records (book_id, user_id, issue_date, due_date, status)
            VALUES (%s, %s, %s, %s, %s)
        ''', (book[0], user[0], issue_date, due_date, 'issued'))
        
        cursor.execute('''
            UPDATE books SET available_copies = available_copies - 1
            WHERE book_id = %s
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
        
        tk.Label(self.content_area, text="📥 Return Book", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)
        
        form_frame = tk.Frame(self.content_area, bg=self.colors['panel'], padx=20, pady=20)
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Issue ID:", font=("Segoe UI", 10),
            bg=self.colors['panel'], fg=self.colors['text_dark']).grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.return_issue_id = self.create_modern_entry(form_frame, width=32)
        self.return_issue_id.grid(row=0, column=1, pady=10)
        
        self.create_modern_button(self.content_area, "Return Book", self.return_book,
                      variant="success", font=("Segoe UI", 11, "bold"),
                      padx=30, pady=10).pack(pady=20)
        
        tk.Label(self.content_area, text="Pending Returns:", font=("Segoe UI", 14, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=(30, 10))
        
        table_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Issue ID", "Book", "Student", "Issue Date", "Due Date", "Days Overdue", "Fine")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10, style="Modern.Treeview")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.column("Book", width=200)
        tree.pack(fill="both", expand=True)
        
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
        
        cursor.execute('''
            SELECT i.issue_id, i.book_id, i.due_date, b.title, u.full_name
            FROM issue_records i
            JOIN books b ON i.book_id = b.book_id
            JOIN users u ON i.user_id = u.user_id
            WHERE i.issue_id = %s AND i.status = 'issued'
        ''', (issue_id,))
        
        record = cursor.fetchone()
        
        if not record:
            messagebox.showerror("Error", "Invalid Issue ID or already returned")
            conn.close()
            return
        
        due_date = datetime.strptime(record[2], "%Y-%m-%d")
        days_overdue = max(0, (datetime.now() - due_date).days)
        fine = days_overdue * self.fine_per_day
        
        return_date = datetime.now().date()
        cursor.execute('''
            UPDATE issue_records 
            SET return_date = %s, fine_amount = %s, status = 'returned'
            WHERE issue_id = %s
        ''', (return_date, fine, issue_id))
        
        cursor.execute('''
            UPDATE books SET available_copies = available_copies + 1
            WHERE book_id = %s
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
        
        tk.Label(self.content_area, text="🎫 Reserve a Book", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)
        
        tk.Label(self.content_area, text="Books Currently Unavailable:", 
            font=("Segoe UI", 11), bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=10)
        
        table_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Book ID", "Title", "Author", "Total", "Available")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15, style="Modern.Treeview")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        tree.column("Title", width=300)
        tree.pack(fill="both", expand=True)
        
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
        
        btn_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        btn_frame.pack(pady=20)
        
        tk.Label(btn_frame, text="Book ID:", font=("Segoe UI", 10),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(side="left", padx=5)
        self.reserve_book_id = self.create_modern_entry(btn_frame, width=18)
        self.reserve_book_id.pack(side="left", padx=5)
        
        self.create_modern_button(btn_frame, "Reserve", self.reserve_book,
                      variant="warning", font=("Segoe UI", 10, "bold"),
                      padx=18, pady=8).pack(side="left", padx=5)
    
    def reserve_book(self):
        """Reserve a book"""
        book_id = self.reserve_book_id.get().strip()
        
        if not book_id:
            messagebox.showerror("Error", "Please enter Book ID")
            return
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT book_id, title, available_copies FROM books
            WHERE book_id = %s
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
        
        cursor.execute('''
            SELECT * FROM reservations
            WHERE book_id = %s AND user_id = ? AND status = 'active'
        ''', (book_id, self.current_user['user_id']))
        
        if cursor.fetchone():
            messagebox.showinfo("Info", "You have already reserved this book")
            conn.close()
            return
        
        cursor.execute('''
            INSERT INTO reservations (book_id, user_id, status)
            VALUES (%s, %s, 'active')
        ''', (book_id, self.current_user['user_id']))
        
        conn.commit()
        conn.close()
        
        self.db.log_activity(self.current_user['user_id'], "RESERVE_BOOK",
                           f"Reserved book: {book[1]}")
        
        messagebox.showinfo("Success", f"Book '{book[1]}' reserved successfully!")
        self.show_reserve_book()
    
    def show_manage_users(self):
        """Show user management interface with search"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="👥 Manage Users", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)
        
        search_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        search_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(search_frame, text="Search:", bg=self.colors['page_bg'], 
                fg=self.colors['text_dark'], font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        
        search_entry = tk.Entry(search_frame, width=40, font=("Segoe UI", 10),
                               bg=self.colors['input_bg'], fg=self.colors['text_dark'])
        search_entry.pack(side="left", padx=5)
        
        table_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("ID", "Username", "Full Name", "Role", "Email", "Phone")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20, style="Modern.Treeview")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        tree.column("Full Name", width=200)
        tree.pack(fill="both", expand=True)
        
        def populate_users(search_term=""):
            """Populate tree with users, optionally filtered by search term"""
            tree.delete(*tree.get_children())
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if search_term:
                search_term = f"%{search_term}%"
                cursor.execute('''
                    SELECT user_id, username, full_name, role, email, phone FROM users 
                    WHERE username ILIKE %s OR full_name ILIKE %s OR email ILIKE %s OR phone ILIKE %s
                    ORDER BY full_name
                ''', (search_term, search_term, search_term, search_term))
            else:
                cursor.execute("SELECT user_id, username, full_name, role, email, phone FROM users ORDER BY full_name")
            
            users = cursor.fetchall()
            conn.close()
            
            for user in users:
                tree.insert("", "end", values=user)
            
            count_label.config(text=f"Total: {len(users)} user(s)")
        
        def on_search():
            """Handle search"""
            search_text = search_entry.get().strip()
            populate_users(search_text)
        
        def on_clear():
            """Clear search"""
            search_entry.delete(0, tk.END)
            populate_users()
        
        button_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        button_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Button(button_frame, text="🔍 Search", command=on_search,
                 bg=self.colors['accent'], fg="white", font=("Segoe UI", 10, "bold"),
                 padx=20, pady=5, relief="flat", cursor="hand2").pack(side="left", padx=5)
        
        tk.Button(button_frame, text="❌ Clear", command=on_clear,
                 bg=self.colors['muted'], fg="white", font=("Segoe UI", 10, "bold"),
                 padx=20, pady=5, relief="flat", cursor="hand2").pack(side="left", padx=5)
        
        count_label = tk.Label(button_frame, text="Total: 0 user(s)", 
                              bg=self.colors['page_bg'], fg=self.colors['text_dark'],
                              font=("Segoe UI", 10))
        count_label.pack(side="right", padx=10)
        
        search_entry.bind('<Return>', lambda e: on_search())
        
        populate_users()

    def show_issued_books(self):
        """Show all currently issued books for admin and librarian"""
        for widget in self.content_area.winfo_children():
            widget.destroy()

        tk.Label(self.content_area, text="📚 Issued Books", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)

        search_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        search_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(search_frame, text="Search:", bg=self.colors['page_bg'],
                 fg=self.colors['text_dark'], font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)

        search_entry = tk.Entry(search_frame, width=40, font=("Segoe UI", 10),
                               bg=self.colors['input_bg'], fg=self.colors['text_dark'])
        search_entry.pack(side="left", padx=5)

        count_label = tk.Label(search_frame, text="Total: 0 issued book(s)",
                              bg=self.colors['page_bg'], fg=self.colors['text_dark'],
                              font=("Segoe UI", 10, "bold"))
        count_label.pack(side="right", padx=10)

        table_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("Issue ID", "Student", "Student ID", "Book Title", "Category", "Issue Date", "Due Date", "Fine", "Status")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18, style="Modern.Treeview")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        tree.column("Book Title", width=240)
        tree.column("Student", width=180)
        tree.pack(fill="both", expand=True)

        def populate_issues(search_term=""):
            tree.delete(*tree.get_children())

            conn = self.db.get_connection()
            cursor = conn.cursor()

            base_query = '''
                SELECT i.issue_id, u.full_name, u.username, b.title, b.category,
                       i.issue_date, i.due_date, i.fine_amount, i.status
                FROM issue_records i
                JOIN users u ON i.user_id = u.user_id
                JOIN books b ON i.book_id = b.book_id
                WHERE i.status = 'issued'
            '''
            params = []

            if search_term:
                base_query += '''
                    AND (
                        u.full_name ILIKE %s OR
                        u.username ILIKE %s OR
                        b.title ILIKE %s OR
                        b.category ILIKE %s
                    )
                '''
                like_term = f"%{search_term}%"
                params = [like_term, like_term, like_term, like_term]

            base_query += " ORDER BY i.issue_date DESC, u.full_name ASC"
            cursor.execute(base_query, tuple(params))
            records = cursor.fetchall()
            conn.close()

            for record in records:
                issue_id, student_name, username, book_title, category, issue_date, due_date, fine_amount, status = record
                due_dt = datetime.strptime(str(due_date), "%Y-%m-%d")
                days_overdue = max(0, (datetime.now() - due_dt).days)
                fine = days_overdue * self.fine_per_day if days_overdue > 0 else float(fine_amount or 0)
                tree.insert("", "end", values=(
                    issue_id, student_name, username, book_title, category,
                    issue_date, due_date, f"₹{fine:.2f}", status
                ))

            count_label.config(text=f"Total: {len(records)} issued book(s)")

        def on_search():
            populate_issues(search_entry.get().strip())

        def on_clear():
            search_entry.delete(0, tk.END)
            populate_issues()

        button_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        button_frame.pack(fill="x", padx=20, pady=5)

        self.create_modern_button(button_frame, "Search", on_search,
                                  variant="primary", font=("Segoe UI", 10, "bold"),
                                  padx=18, pady=7).pack(side="left", padx=5)

        self.create_modern_button(button_frame, "Clear", on_clear,
                                  variant="neutral", font=("Segoe UI", 10),
                                  padx=16, pady=7).pack(side="left", padx=5)

        search_entry.bind('<Return>', lambda e: on_search())

        populate_issues()
    
    def show_reports(self):
        """Show various reports"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="📊 Reports & Analytics", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)
        
        reports_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        reports_frame.pack(fill="both", expand=True, padx=20)
        
        overdue_frame = tk.LabelFrame(reports_frame, text="⚠️ Overdue Books", 
                         font=("Segoe UI", 12, "bold"), bg=self.colors['panel'],
                         fg=self.colors['text_dark'], padx=10, pady=10)
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
                tk.Label(overdue_frame, text=text, font=("Segoe UI", 10), bg=self.colors['panel'],
                        fg="red", anchor="w").pack(fill="x", pady=2)
        else:
            tk.Label(overdue_frame, text="✅ No overdue books!", 
                    font=("Segoe UI", 10), bg=self.colors['panel'], fg="green").pack()
        
        popular_frame = tk.LabelFrame(reports_frame, text="🔥 Most Issued Books", 
                                     font=("Segoe UI", 12, "bold"), bg=self.colors['panel'],
                                     fg=self.colors['text_dark'], padx=10, pady=10)
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
            tk.Label(popular_frame, text=text, font=("Segoe UI", 10),
                bg=self.colors['panel'], fg=self.colors['text_dark'], anchor="w").pack(fill="x", pady=2)
        
        conn.close()
    
    def show_activity_log(self):
        """Show activity log"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        tk.Label(self.content_area, text="📜 Activity Log", font=("Segoe UI", 19, "bold"),
            bg=self.colors['page_bg'], fg=self.colors['text_dark']).pack(pady=20)
        
        table_frame = tk.Frame(self.content_area, bg=self.colors['page_bg'])
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = ttk.Scrollbar(table_frame, style="Modern.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        
        columns = ("ID", "User", "Action", "Details", "Timestamp")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                           yscrollcommand=scrollbar.set, height=25, style="Modern.Treeview")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.column("Details", width=300)
        tree.column("Timestamp", width=150)
        
        scrollbar.config(command=tree.yview)
        tree.pack(fill="both", expand=True, padx=(0, 6), pady=(0, 6))
        
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
