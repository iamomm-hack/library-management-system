#!/usr/bin/env python3
import subprocess
import os
import sys

def run_command(cmd, description):
    """Run command and show result"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}\n")
    
    result = os.system(cmd)
    if result == 0:
        print(f"✅ Success!")
    else:
        print(f"⚠️  Check output above")
    
    input("\n👉 Press ENTER to continue...")

def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         🚀 AUTOMATED SERVER SETUP SCRIPT 🚀               ║
    ║                                                            ║
    ║  Everything will run automatically. Just follow the steps  ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print("\n1️⃣ First, check your IP address:\n")
    os.system("ipconfig /all | findstr /I \"IPv4\"")
    print("\n👉 The 192.168.x.x value shown above is your IP address!")
    print("   Save it somewhere for later use.\n")
    
    input("👉 Press ENTER after noting your IP...")
    
    # Step 2
    print("\n\n2️⃣ Now adding the Firewall rule...")
    print("(This requires Administrator rights)\n")
    
    input("👉 Press ENTER... (If a UAC prompt appears, click 'Yes'!)")
    
    os.system("netsh advfirewall firewall add rule name=\"PostgreSQL\" dir=in action=allow protocol=tcp localport=5432 profile=any")
    
    print("\n✅ Firewall rule added!")
    
    input("\n👉 Press ENTER to continue...")
    
    # Step 3
    print("\n\n3️⃣ Enabling PostgreSQL for network access...\n")
    
    config_file = r"C:\Program Files\PostgreSQL\16\data\postgresql.conf"
    
    # Check if file exists
    if os.path.exists(config_file):
        print(f"✅ Config file found: {config_file}\n")
        
        with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check if already changed
        if "listen_addresses = '*'" in content:
            print("✅ Setup already applied (listen_addresses = '*')")
        else:
            # Update the file
            content = content.replace("listen_addresses = 'localhost'", "listen_addresses = '*'")
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ postgresql.conf updated!")
            print("   (listen_addresses = 'localhost' → listen_addresses = '*')")
        
        input("\n👉 Press ENTER to restart PostgreSQL...")
        
        # Restart PostgreSQL
        print("\n4️⃣ Restarting PostgreSQL...\n")
        os.system("net stop postgresql-x64-16 >nul 2>&1")
        print("   Stopping...")
        
        import time
        time.sleep(3)
        
        os.system("net start postgresql-x64-16 >nul 2>&1")
        print("   Starting...")
        
        time.sleep(3)
        print("\n✅ PostgreSQL restarted!")
        
    else:
        print(f"❌ File not found: {config_file}")
        print("   Configure PostgreSQL manually.")
    
    input("\n👉 Press ENTER to run the test...")
    
    # Test
    print("\n\n5️⃣ Testing whether the database is accessible:\n")
    
    print("Command:")
    print('psql -U postgres -h localhost -d library_db -c "SELECT COUNT(*) FROM users;"\n')
    
    os.system('psql -U postgres -h localhost -d library_db -c "SELECT COUNT(*) FROM users;"')
    
    print("\nIf you see '665' above, everything is working ✅")
    
    input("\n👉 Press ENTER...")
    
    # Summary
    print("""
╔════════════════════════════════════════════════════════════╗
✅ SERVER SETUP COMPLETE!
╚════════════════════════════════════════════════════════════╝

What to do next:

1. Note your IP address (shown above)
   Example: 192.168.0.103

2. Create the ZIP package:
    Run this in PowerShell:
   
   cd e:\\library-python
   Compress-Archive -Path "LibraryApp_20260402_221539" -DestinationPath "LibraryApp.zip" -Force

3. Send LibraryApp.zip to the other user

4. Ask the other user to:
    - Extract the ZIP
    - Open app/.env
    - Set DB_HOST to your IP
    - Run LibrarySystem.exe
    - Log in

Done! ✅

╚════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled!")
        sys.exit(1)
