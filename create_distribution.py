#!/usr/bin/env python3
"""
Library Management System - Distribution Package Generator
Isse deployment package bna deta hai
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def create_distribution_package():
    """Create distribution package for sharing"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dist_folder = f"LibraryApp_{timestamp}"
    
    # Create folder structure
    Path(dist_folder).mkdir(exist_ok=True)
    Path(f"{dist_folder}/app").mkdir(exist_ok=True)
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║   Creating Distribution Package: {dist_folder}
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # 1. Copy .exe
    if Path("dist/LibrarySystem.exe").exists():
        shutil.copy("dist/LibrarySystem.exe", f"{dist_folder}/app/LibrarySystem.exe")
        print("✅ Copied: LibrarySystem.exe")
    
    # 2. Create .env template
    env_template = """# Library Management System - Configuration
# 
# ⚠️ SETUP INSTRUCTIONS:
# 1. Replace DB_HOST with server machine IP
# 2. Keep DB_PORT, DB_NAME, DB_USER same
# 3. Update DB_PASSWORD if needed
# 4. Save this file in same folder as LibrarySystem.exe

# DATABASE CONNECTION (Update this)
DB_HOST=192.168.0.103          # Change to server machine IP
DB_PORT=5432
DB_NAME=library_db
DB_USER=postgres
DB_PASSWORD=system

# API KEY (Keep same)
GOOGLE_BOOKS_API_KEY=AIzaSyBJyYCWvvikhEfhjfWDUGFqZn1MJwmzKMo
"""
    
    with open(f"{dist_folder}/app/.env", "w", encoding="utf-8") as f:
        f.write(env_template)
    print("✅ Created: .env template")
    
    # 3. Create SETUP.txt instructions
    setup_instructions = """╔════════════════════════════════════════════════════════════╗
║     Library Management System - SETUP INSTRUCTIONS        ║
║                   (For User/Other Machine)                ║
╚════════════════════════════════════════════════════════════╝

📦 WHAT YOU RECEIVED:
├── LibrarySystem.exe     (Main app - just double-click to run)
└── .env                  (Configuration - MUST set up correctly)

🔧 SETUP STEPS (IMPORTANT):

1️⃣ DO NOT modify LibrarySystem.exe
   → Just leave it as is

2️⃣ MODIFY .env file:
   → Open .env with Notepad
   → Update DB_HOST = [Server Machine IP]
   
   Example:
   If server machine IP is 192.168.0.103, then:
   
   DB_HOST=192.168.0.103
   DB_PORT=5432
   DB_NAME=library_db
   DB_USER=postgres
   DB_PASSWORD=system
   
   → Save file (Ctrl+S)

3️⃣ RUN APPLICATION:
   → Double-click LibrarySystem.exe
   → Login credentials:
      • Admin: admin / admin123
      • Librarian: librarian / lib123
      • Student: Use enrollment number / password

✅ TROUBLESHOOTING:

Problem: "Cannot connect to database"
→ Check .env DB_HOST IP is correct
→ Ensure server machine PostgreSQL is running
→ Check firewall allows port 5432

Problem: "ModuleNotFoundError"
→ Reinstall: pip install -r requirements.txt
→ Then run: python library_system.py

Problem: "Wrong password/login fails"
→ Enter correct credentials (check admin credentials with sender)

📞 NEED HELP?
→ Contact: [Server Admin]
→ Check DB_HOST setting first

╚════════════════════════════════════════════════════════════╝
"""
    
    with open(f"{dist_folder}/SETUP.txt", "w", encoding="utf-8") as f:
        f.write(setup_instructions)
    print("✅ Created: SETUP.txt")
    
    # 4. Create test connection script
    test_script = """#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import psycopg2

print("Testing database connection...\\n")

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
    
    print("✅ Database Connection SUCCESS!\\n")
    print(f"📊 Database Stats:")
    print(f"   Users: {users}")
    print(f"   Books: {books}")
    print(f"   Active Issues: {issues}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection FAILED: {e}")
    print("\\nCheck .env file settings!")
"""
    
    with open(f"{dist_folder}/test_connection.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    print("✅ Created: test_connection.py")
    
    # 5. Create SERVER SETUP guide
    server_setup = """╔════════════════════════════════════════════════════════════╗
║   Library Management System - SERVER SETUP GUIDE         ║
║             (For Machine Hosting Database)               ║
╚════════════════════════════════════════════════════════════╝

Your machine will be the DATABASE SERVER that other users connect to.

🖥️ SERVER SETUP (Your Machine):

1️⃣ PostgreSQL Configuration:
   
   a) PostgreSQL.conf file खुले:
      Windows: 
      C:\\Program Files\\PostgreSQL\\16\\data\\postgresql.conf
      
   b) ढूंड़ो "listen_addresses" और बदलो:
      From: listen_addresses = 'localhost'
      To:   listen_addresses = '*'
      
   c) Save करो और PostgreSQL restart करो

2️⃣ Firewall Allow करो (पोर्ट 5432):
   
   Windows Defender Firewall:
   → New Inbound Rule
   → Port: 5432
   → Allow connection
   → Apply to: Domain, Private, Public

3️⃣ PostgreSQL Credentials Verify करो:
   
   Username: postgres
   Password: system (or your password)
   Database: library_db
   
   Test करो:
   psql -U postgres -h localhost -d library_db

4️⃣ Share Your IP with Others:
   
   Command लगाओ:
   ipconfig /all
   
   IPv4 Address note करो (e.g., 192.168.0.103)
   
   यही IP सभी को दो जो app use करेंगे

5️⃣ Verify Connection:
   
   दूसरे machine से:
   psql -U postgres -h <YOUR_IP> -d library_db -c "SELECT COUNT(*) FROM users;"
   
   यदि काम करता है तो ✅ All set!

🔐 SECURITY TIPS:

⚠️ Production के लिए:
- Strong password set करो DB के लिए
- Firewall को सिर्फ trusted IPs से allow करो
- Regular backups لیں
- .env file को git में commit न करो

🚀 NEXT STEPS:

1. Above steps follow करो
2. अपना IP दूसरों को दो
3. दूसरे लोग .env में यह IP डालें
4. सब successfully connect हो जाएंगे!

╚════════════════════════════════════════════════════════════╝
"""
    
    with open(f"{dist_folder}/SERVER_SETUP.txt", "w", encoding="utf-8") as f:
        f.write(server_setup)
    print("✅ Created: SERVER_SETUP.txt")
    
    # 6. Create requirements.txt
    requirements = """psycopg2-binary==2.9.9
python-dotenv==1.0.0
"""
    with open(f"{dist_folder}/requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements)
    print("✅ Created: requirements.txt")
    
    # Summary
    print(f"""
╔════════════════════════════════════════════════════════════╗
✅ DISTRIBUTION PACKAGE READY!
╚════════════════════════════════════════════════════════════╝

📁 Folder: {dist_folder}/

📋 Contents:
├── SETUP.txt              ← दूसरे को दो (सेटअप के लिए)
├── SERVER_SETUP.txt       ← अपने लिए (server setup करने के लिए)
├── app/
│   ├── LibrarySystem.exe  ← Main app
│   └── .env               ← Configuration template
└── requirements.txt

🎯 NEXT STEPS:

1. SERVER SETUP (अपने machine पर):
   → SERVER_SETUP.txt पढ़ो
   → PostgreSQL configure करो
   → Firewall open करो
   
2. DISTRIBUTION (दूसरे को):
   → Entire folder "{dist_folder}/" को दूसरे को दो
   → या zip करके send करो
   → वह SETUP.txt पढ़ेगा और configure करेगा

✨ Common setup time: 5-10 minutes
""")
    
    print(f"\n📂 Ready to distribute: {os.path.abspath(dist_folder)}/")
    return dist_folder

if __name__ == "__main__":
    create_distribution_package()
