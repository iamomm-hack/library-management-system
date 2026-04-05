"""
Import books from Google Books API into PostgreSQL library database
"""

import os
import requests
import psycopg2
import sys

def load_env_file(env_path=".env"):
    """Load key=value pairs from a local .env file if present."""
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_env_file()

GOOGLE_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "library_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "system")

def import_books_by_search(search_query, max_results=100):
    """Fetch books from Google Books API and import to database"""
    
    print(f"Searching for '{search_query}' on Google Books...")
    
    try:
        url = f"https://www.googleapis.com/books/v1/volumes"
        params = {
            'q': search_query,
            'maxResults': min(max_results, 40),
            'key': GOOGLE_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        if not items:
            print(f"No books found for '{search_query}'")
            return 0
        
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        
        imported_count = 0
        skipped_count = 0

        def build_book_key(item, vol_info):
            """Prefer ISBN, otherwise fall back to Google volume ID."""
            for identifier in vol_info.get('industryIdentifiers', []):
                identifier_type = identifier.get('type', '')
                identifier_value = identifier.get('identifier') or identifier.get('value')
                if identifier_type in ['ISBN_13', 'ISBN_10'] and identifier_value:
                    return identifier_value

            volume_id = item.get('id')
            if volume_id:
                return f"GB-{volume_id}"

            return None
        
        for item in items:
            try:
                vol_info = item.get('volumeInfo', {})

                isbn = build_book_key(item, vol_info)
                
                title = vol_info.get('title', 'Unknown Title')
                authors = vol_info.get('authors', ['Unknown Author'])
                author = ', '.join(authors)
                category = vol_info.get('categories', ['General'])[0]
                publisher = vol_info.get('publisher', 'Unknown')
                published_date = str(vol_info.get('publishedDate', '2000'))
                year_text = published_date[:4]
                year = int(year_text) if year_text.isdigit() else 2000
                description = vol_info.get('description', '')[:500]
                
                if not isbn:
                    skipped_count += 1
                    continue
                
                cursor.execute('''
                    INSERT INTO books (isbn, title, author, category, publisher, year, 
                                     total_copies, available_copies, description)
                    VALUES (%s, %s, %s, %s, %s, %s, 3, 3, %s)
                    ON CONFLICT (isbn) DO NOTHING
                ''', (isbn, title, author, category, publisher, int(year), description))
                
                imported_count += 1
                
                if imported_count % 10 == 0:
                    print(f"  Imported {imported_count} books...")
                
            except Exception as e:
                skipped_count += 1
                print(f"  ⚠ Skipped: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n✓ Import complete!")
        print(f"  Imported: {imported_count} books")
        print(f"  Skipped: {skipped_count} books")
        
        return imported_count
        
    except Exception as e:
        print(f"Error: {e}")
        return 0

def bulk_import_categories():
    """Import popular book categories"""
    
    categories = [
        ("DBMS", 25),
        ("Database Management System", 25),
        ("Automata Theory", 25),
        ("Theory of Computation", 25),
        ("Operating System", 25),
        ("Computer Networks", 25),
        ("Data Structures and Algorithms", 25),
        ("Algorithms", 25),
        ("Compiler Design", 20),
        ("Computer Organization and Architecture", 20),
        ("Digital Logic Design", 20),
        ("Software Engineering", 20),
        ("Object Oriented Programming", 20),
        ("Python Programming", 25),
        ("Java Programming", 25),
        ("Web Development", 25),
        ("React", 20),
        ("Node.js", 20),
        ("SQL", 20),
        ("MySQL", 20),
        ("Oracle Database", 20),
        ("Machine Learning", 25),
        ("Deep Learning", 20),
        ("Artificial Intelligence", 25),
        ("Natural Language Processing", 20),
        ("Cloud Computing", 20),
        ("Cyber Security", 20),
        ("Linux", 20),
        ("Networking", 20),
        ("Fiction", 25),
        ("Science", 20),
        ("Business", 20),
        ("Self-Help", 15),
    ]
    
    total_imported = 0
    
    for category, count in categories:
        print(f"\n{'='*60}")
        imported = import_books_by_search(category, count)
        total_imported += imported
    
    print(f"\n{'='*60}")
    print(f"✓ TOTAL IMPORTED: {total_imported} books")
    
    return total_imported

if __name__ == "__main__":
    
    if not GOOGLE_API_KEY:
        print("⚠ ERROR: Set GOOGLE_BOOKS_API_KEY in .env first!")
        print("\nSteps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create project → Enable Books API → Create API Key")
        print("3. Add GOOGLE_BOOKS_API_KEY=your_key in .env")
        sys.exit(1)
    
    print("Starting bulk import from Google Books API...")
    print(f"Target: library_db @ {DB_HOST}")
    
    total = bulk_import_categories()
    
    print(f"\n✓ Done! {total} books imported to library")
