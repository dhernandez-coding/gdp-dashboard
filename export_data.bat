@echo off
echo Starting SQL Data Export Using Python...

:: Define Paths
set SCRIPT_DIR=C:\Users\v_rroberson\Report RLG\gdp-dashboard
set SCRIPT_FILE=ExportSQLPython.py
set FULL_SCRIPT_PATH="%SCRIPT_DIR%\%SCRIPT_FILE%"

:: Verify the Script Exists
if not exist %FULL_SCRIPT_PATH% (
    echo Error: Python script not found at %FULL_SCRIPT_PATH%
   
    exit /b 1
)

:: Navigate to the Script Directory
cd /d "%SCRIPT_DIR%" || (
    echo Error: Failed to navigate to script directory.

    exit /b 1
)

:: Run Python Script
python %SCRIPT_FILE%

:: Check Execution Status
if %errorlevel% neq 0 (
    echo Error: Python script execution failed.
   
    exit /b 1
)

echo ✅ SQL Data Export Completed Successfully!

exit /b 0
