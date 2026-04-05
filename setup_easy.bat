@echo off

echo.
echo Preparing server...
echo.

echo Updating PostgreSQL config...
powershell -Command "(Get-Content 'C:\Program Files\PostgreSQL\16\data\postgresql.conf') -replace \"listen_addresses = 'localhost'\", \"listen_addresses = '*'\" | Set-Content 'C:\Program Files\PostgreSQL\16\data\postgresql.conf'"

echo Restarting PostgreSQL...
net stop postgresql-x64-16 >nul 2>&1
timeout /t 3 >nul
net start postgresql-x64-16 >nul 2>&1

echo Opening firewall...
netsh advfirewall firewall add rule name="PostgreSQL" dir=in action=allow protocol=tcp localport=5432 profile=any >nul 2>&1

echo.
echo ========================================
echo    SETUP COMPLETE!
echo ========================================
echo.
echo Your Server IP:
ipconfig | findstr "IPv4"
echo.
echo INSTRUCTIONS FOR OTHERS:
echo ------------------------------------
echo 1. Send them: LibraryApp.zip
echo 2. Send them: Your IP (above)
echo 3. They extract file
echo 4. They open: app\.env with Notepad
echo 5. Change: DB_HOST=YOUR_IP
echo 6. Save
echo 7. Run: LibrarySystem.exe
echo.
pause
