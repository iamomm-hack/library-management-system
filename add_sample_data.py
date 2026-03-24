"""
Sample Data Generator for Library Management System
Run this script to populate the database with demo data
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta
import random

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def populate_sample_data():
    """Populate database with sample books and users"""
    
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()
    
    print("🔄 Adding sample data to the database...")
    
    # Sample Students
    students = [
        ("om_kumar", "om123", "Om Kumar", "om@email.com", "9876543210"),
        ("mufti_armaan", "armaan123", "Mufti Armaan", "armaan@email.com", "9876543211"),
        ("satish_jalan", "satish123", "Satish Jalan", "satish@email.com", "9876543212"),
        ("sayan_roy", "sayan123", "Sayan Roy", "sayan@email.com", "9876543213"),
        ("sitanshu_bharti", "sitanshu123", "Sitanshu Bharti", "sitanshu@email.com", "9876543214"),
    ]
    
    print("\n👥 Adding sample students...")
    for username, password, name, email, phone in students:
        try:
            hashed_pwd = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password, role, full_name, email, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_pwd, 'student', name, email, phone))
            print(f"   ✓ Added: {name} (username: {username}, password: {password})")
        except sqlite3.IntegrityError:
            print(f"   ⚠ Skipped: {name} (already exists)")
    
    # Sample Librarian
    try:
        cursor.execute('''
            INSERT INTO users (username, password, role, full_name, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("librarian", hash_password("lib123"), 'librarian', 
              "Library Staff", "librarian@library.com", "9999999999"))
        print("\n📚 Added librarian (username: librarian, password: lib123)")
    except sqlite3.IntegrityError:
        print("\n⚠ Librarian already exists")
    
    # Sample Books
    books = [
        # Computer Science
        ("978-0132350884", "Clean Code", "Robert C. Martin", "Computer Science", 
         "Prentice Hall", 2008, 3, "CS-A1", "A handbook of agile software craftsmanship"),
        
        ("978-0201633610", "Design Patterns", "Gang of Four", "Computer Science",
         "Addison-Wesley", 1994, 2, "CS-A2", "Elements of reusable object-oriented software"),
        
        ("978-0134685991", "Effective Java", "Joshua Bloch", "Computer Science",
         "Addison-Wesley", 2018, 2, "CS-A3", "Best practices for Java programming"),
        
        ("978-0596007126", "Head First Design Patterns", "Eric Freeman", "Computer Science",
         "O'Reilly", 2004, 3, "CS-B1", "A brain-friendly guide to design patterns"),
        
        ("978-0135957059", "The Pragmatic Programmer", "David Thomas", "Computer Science",
         "Addison-Wesley", 2019, 2, "CS-B2", "Your journey to mastery"),
        
        # Data Science & AI
        ("978-1449369415", "Python for Data Analysis", "Wes McKinney", "Data Science",
         "O'Reilly", 2017, 4, "DS-A1", "Data wrangling with Pandas and NumPy"),
        
        ("978-1491952962", "Hands-On Machine Learning", "Aurélien Géron", "Data Science",
         "O'Reilly", 2019, 3, "DS-A2", "Machine learning with Scikit-Learn and TensorFlow"),
        
        ("978-0262033848", "Deep Learning", "Ian Goodfellow", "Data Science",
         "MIT Press", 2016, 2, "DS-A3", "Comprehensive deep learning textbook"),
        
        # Mathematics
        ("978-0073383095", "Discrete Mathematics", "Kenneth Rosen", "Mathematics",
         "McGraw-Hill", 2018, 3, "MATH-A1", "Applications in computer science"),
        
        ("978-0321774415", "Linear Algebra", "David Lay", "Mathematics",
         "Pearson", 2015, 2, "MATH-A2", "And its applications"),
        
        # Physics
        ("978-0321973610", "University Physics", "Young & Freedman", "Physics",
         "Pearson", 2019, 3, "PHY-A1", "With modern physics"),
        
        ("978-1292026558", "Fundamentals of Physics", "Halliday Resnick", "Physics",
         "Wiley", 2013, 2, "PHY-A2", "Extended edition"),
        
        # Fiction & Literature
        ("978-0547928227", "The Hobbit", "J.R.R. Tolkien", "Fiction",
         "Mariner Books", 2012, 4, "FIC-A1", "Classic fantasy adventure"),
        
        ("978-0618260274", "The Lord of the Rings", "J.R.R. Tolkien", "Fiction",
         "Mariner Books", 2005, 3, "FIC-A2", "Epic fantasy trilogy"),
        
        ("978-0061120084", "To Kill a Mockingbird", "Harper Lee", "Fiction",
         "Harper Perennial", 2006, 3, "FIC-B1", "American classic novel"),
        
        ("978-0451524935", "1984", "George Orwell", "Fiction",
         "Signet Classic", 1961, 4, "FIC-B2", "Dystopian social science fiction"),
        
        ("978-0743273565", "The Great Gatsby", "F. Scott Fitzgerald", "Fiction",
         "Scribner", 2004, 3, "FIC-C1", "American classic about the Jazz Age"),
        
        # Business & Economics
        ("978-0062316097", "Sapiens", "Yuval Noah Harari", "Non-Fiction",
         "Harper", 2015, 3, "BUS-A1", "A brief history of humankind"),
        
        ("978-0307886279", "Thinking, Fast and Slow", "Daniel Kahneman", "Psychology",
         "Farrar, Straus and Giroux", 2013, 2, "PSY-A1", "Psychology of decision making"),
        
        ("978-1476753836", "Atomic Habits", "James Clear", "Self-Help",
         "Avery", 2018, 5, "SELF-A1", "Build good habits and break bad ones"),
        
        # Web Development
        ("978-1491957660", "JavaScript: The Definitive Guide", "David Flanagan", "Computer Science",
         "O'Reilly", 2020, 3, "CS-C1", "Master the JavaScript language"),
        
        ("978-1617294136", "React in Action", "Mark Thomas", "Computer Science",
         "Manning", 2018, 2, "CS-C2", "Build web applications with React"),
        
        ("978-1491974827", "Learning React", "Alex Banks", "Computer Science",
         "O'Reilly", 2020, 3, "CS-C3", "Modern patterns for developing React apps"),
        
        # Database
        ("978-0596520823", "SQL and Relational Theory", "C.J. Date", "Computer Science",
         "O'Reilly", 2015, 2, "CS-D1", "Write accurate SQL code"),
        
        ("978-1449373320", "Designing Data-Intensive Applications", "Martin Kleppmann", "Computer Science",
         "O'Reilly", 2017, 2, "CS-D2", "Big data, scalability, and reliability"),
    ]
    
    print("\n📚 Adding sample books...")
    for book in books:
        try:
            if len(book) == 9:
                normalized_book = (
                    book[0],
                    book[1],
                    book[2],
                    book[3],
                    book[4],
                    book[5],
                    book[6],
                    book[6],
                    book[7],
                    book[8],
                )
            else:
                normalized_book = book

            cursor.execute('''
                INSERT INTO books (isbn, title, author, category, publisher, year, 
                                 total_copies, available_copies, shelf_location, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', normalized_book)
            print(f"   ✓ Added: {book[1]} by {book[2]}")
        except sqlite3.IntegrityError:
            print(f"   ⚠ Skipped: {book[1]} (already exists)")
    
    # Add some issue records for demo
    print("\n📤 Adding sample issue records...")
    
    # Get some book and user IDs
    cursor.execute("SELECT book_id FROM books LIMIT 5")
    book_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT user_id FROM users WHERE role='student' LIMIT 3")
    user_ids = [row[0] for row in cursor.fetchall()]
    
    if book_ids and user_ids:
        for i in range(min(3, len(book_ids), len(user_ids))):
            issue_date = datetime.now().date() - timedelta(days=random.randint(1, 10))
            due_date = issue_date + timedelta(days=14)
            
            cursor.execute('''
                INSERT INTO issue_records (book_id, user_id, issue_date, due_date, status)
                VALUES (?, ?, ?, ?, 'issued')
            ''', (book_ids[i], user_ids[i], issue_date, due_date))
            
            # Update available copies
            cursor.execute('''
                UPDATE books SET available_copies = available_copies - 1
                WHERE book_id = ?
            ''', (book_ids[i],))
            
            print(f"   ✓ Created issue record for book_id={book_ids[i]}, user_id={user_ids[i]}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Sample data added successfully!")
    print("\n📋 Sample Login Credentials:")
    print("=" * 50)
    print("Admin:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nLibrarian:")
    print("  Username: librarian")
    print("  Password: lib123")
    print("\nStudents:")
    print("  Username: om_kumar         | Password: om123")
    print("  Username: mufti_armaan     | Password: armaan123")
    print("  Username: satish_jalan     | Password: satish123")
    print("  Username: sayan_roy        | Password: sayan123")
    print("  Username: sitanshu_bharti  | Password: sitanshu123")
    print("=" * 50)
    print("\n🚀 Now run: python library_system.py")

if __name__ == "__main__":
    populate_sample_data()
