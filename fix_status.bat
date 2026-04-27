@echo off
echo ========================================
echo  Blood Request Status Fix Tool
echo ========================================
echo.

REM Try to find Python
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
    goto :run_script
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=py
    goto :run_script
)

REM Try common Python locations
if exist "C:\Python39\python.exe" (
    set PYTHON=C:\Python39\python.exe
    goto :run_script
)

if exist "C:\Python310\python.exe" (
    set PYTHON=C:\Python310\python.exe
    goto :run_script
)

if exist "C:\Python311\python.exe" (
    set PYTHON=C:\Python311\python.exe
    goto :run_script
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    goto :run_script
)

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
    goto :run_script
)

echo ERROR: Python not found!
echo.
echo Please install Python or add it to your PATH.
echo Download from: https://www.python.org/downloads/
echo.
pause
exit /b 1

:run_script
echo Running fix script...
echo.
%PYTHON% fix_request_status.py
echo.
echo ========================================
echo  Fix Complete!
echo ========================================
echo.
echo Now refresh your admin verification page:
echo http://localhost:8000/requests/admin/verify/
echo.
pause
