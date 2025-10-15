@echo off
echo ====================================
echo Building LeatherTek Product Manager
echo ====================================
echo.

pyinstaller --onefile --windowed --icon=leathertek.ico --name="LeatherTek-ProductManager" product_manager_complete.py

echo.
echo ====================================
echo Build Complete!
echo ====================================
echo.
echo The EXE file is located in the 'dist' folder
echo File: dist\LeatherTek-ProductManager.exe
echo.
pause
