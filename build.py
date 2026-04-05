#!/usr/bin/env python3
"""
Library Management System - Build Script
Isse run karo: python build.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Execute command with output"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}\n")
    
    result = os.system(cmd)
    if result != 0:
        print(f"❌ Failed: {description}")
        sys.exit(1)
    print(f"✅ Success: {description}")
    return True

def main():
    """Main build process"""
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         Library Management System - Build Tool             ║
    ║                                                            ║
    ║  Isse .exe file banayega jo aap distribution kar sakte ho ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    if not os.path.exists("library_system.py"):
        print("❌ Error: library_system.py not found!")
        sys.exit(1)
    
    run_command(
        "pip install -r requirements.txt",
        "1/3: Installing dependencies"
    )
    
    print("\n📦 Cleaning old build artifacts...")
    for folder in ["build", "dist", "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"   Removed: {folder}/")
    
    pyinstaller_cmd = (
        "pyinstaller "
        "--onefile "
        "--windowed "
        "--name LibrarySystem "
        "--console "
        "--add-data=.env:. "
        "library_system.py"
    )
    
    run_command(
        pyinstaller_cmd,
        "2/3: Building executable (.exe)"
    )
    
    exe_path = Path("dist/LibrarySystem.exe")
    if exe_path.exists():
        print("\n" + "="*60)
        print("✅ BUILD SUCCESSFUL!")
        print("="*60)
        print(f"\n📁 Output location: {exe_path.absolute()}")
        print(f"📊 File size: {exe_path.stat().st_size / (1024*1024):.2f} MB")
        
        print("\n" + "="*60)
        print("📋 DEPLOYMENT INSTRUCTIONS:")
        print("="*60)
        print("""
1. 'dist/LibrarySystem.exe' copy karo dusre machine par

2. .env file create karo (same folder mein):
   
   GOOGLE_BOOKS_API_KEY=AIzaSycr...
   DB_HOST=localhost              (or production server IP)
   DB_PORT=5432
   DB_NAME=library_db
   DB_USER=postgres
   DB_PASSWORD=system

3. LibrarySystem.exe double-click karo

4. Login: 
   - Admin: admin / admin123
   - Librarian: librarian / lib123
        """)
        
        print("="*60)
        print("✨ Ready for deployment!")
        print("="*60)
    else:
        print(f"❌ Error: .exe file not created at {exe_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
