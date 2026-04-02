#!/usr/bin/env python3
"""
🎯 AUTOMATED SERVER SETUP SCRIPT
सब कुछ automatically करवा दो!
"""

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
    
    input("\n👉 ENTER दबाओ continue करने के लिए...")

def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         🚀 AUTOMATED SERVER SETUP SCRIPT 🚀               ║
    ║                                                            ║
    ║  सब कुछ automatic हो जाएगा! सिर्फ instructions पढ़ो     ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print("\n1️⃣ पहले अपना IP देख लो:\n")
    os.system("ipconfig /all | findstr /I \"IPv4\"")
    print("\n👉 ऊपर जो 192.168.x.x दिख रहा है वह तुम्हारा IP है!")
    print("   इसे कहीं लिख लो!\n")
    
    input("👉 ENTER दबाओ जब IP note कर लो...")
    
    # Step 2
    print("\n\n2️⃣ अब Firewall rule add करते हैं...")
    print("(यह Admin rights की जरूरत है)\n")
    
    input("👉 ENTER दबाओ... (अगर UAC prompt आए तो 'Yes' कहना!)")
    
    os.system("netsh advfirewall firewall add rule name=\"PostgreSQL\" dir=in action=allow protocol=tcp localport=5432 profile=any")
    
    print("\n✅ Firewall rule जोड़ दिया!")
    
    input("\n👉 ENTER दबाओ continue करने के लिए...")
    
    # Step 3
    print("\n\n3️⃣ PostgreSQL को network पर खोल रहे हैं...\n")
    
    config_file = r"C:\Program Files\PostgreSQL\16\data\postgresql.conf"
    
    # Check if file exists
    if os.path.exists(config_file):
        print(f"✅ Config file मिल गई: {config_file}\n")
        
        with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check if already changed
        if "listen_addresses = '*'" in content:
            print("✅ पहले से ही setup है (listen_addresses = '*')")
        else:
            # Update the file
            content = content.replace("listen_addresses = 'localhost'", "listen_addresses = '*'")
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ postgresql.conf update हो गया!")
            print("   (listen_addresses = 'localhost' → listen_addresses = '*')")
        
        input("\n👉 ENTER दबाओ PostgreSQL restart करने के लिए...")
        
        # Restart PostgreSQL
        print("\n4️⃣ PostgreSQL restart हो रहा है...\n")
        os.system("net stop postgresql-x64-16 >nul 2>&1")
        print("   Stopping...")
        
        import time
        time.sleep(3)
        
        os.system("net start postgresql-x64-16 >nul 2>&1")
        print("   Starting...")
        
        time.sleep(3)
        print("\n✅ PostgreSQL restart हो गया!")
        
    else:
        print(f"❌ File नहीं मिली: {config_file}")
        print("   PostgreSQL manually configure करो")
    
    input("\n👉 ENTER दबाओ test करने के लिए...")
    
    # Test
    print("\n\n5️⃣ अब test करते हैं कि database accessible है:\n")
    
    print("Command:")
    print('psql -U postgres -h localhost -d library_db -c "SELECT COUNT(*) FROM users;"\n')
    
    os.system('psql -U postgres -h localhost -d library_db -c "SELECT COUNT(*) FROM users;"')
    
    print("\nअगर ऊपर '665' दिख रहा है तो ✅ सब ठीक है!")
    
    input("\n👉 ENTER दबाओ...")
    
    # Summary
    print("""
╔════════════════════════════════════════════════════════════╗
✅ SERVER SETUP COMPLETE!
╚════════════════════════════════════════════════════════════╝

अब तुम्हें क्या करना है:

1. अपना IP note करो (ऊपर देखा था)
   Example: 192.168.0.103

2. ZIP बना दो:
   PowerShell में यह चलाओ:
   
   cd e:\\library-python
   Compress-Archive -Path "LibraryApp_20260402_221539" -DestinationPath "LibraryApp.zip" -Force

3. दूसरे को LibraryApp.zip दे दो

4. दूसरे को कहो:
   - ZIP extract करो
   - app/.env खोलो
   - DB_HOST = तुम्हारा IP लगा दो
   - LibrarySystem.exe run करो
   - Login करो

Done! ✅

╚════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled!")
        sys.exit(1)
