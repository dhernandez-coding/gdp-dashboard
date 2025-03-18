@echo off
echo Starting SQL Data Export...

:: Define the SQL Server name
set SQLSERVER=RLGOKC-DB01

:: Define the output folder
set EXPORT_PATH="C:\Users\v_rroberson\Report RLG\gdp-dashboard\data"

:: Export rpt.vMatters
echo Exporting vMatters...
bcp "SELECT * FROM DW.rpt.vMatters" queryout %EXPORT_PATH%\vMatters.csv -c -t, -T -S %SQLSERVER%

:: Export RevShareNewLogic
echo Exporting RevShareNewLogic...
bcp "SELECT * FROM DW.dbo.RevShareNewLogic" queryout %EXPORT_PATH%\RevShareNewLogic.csv -c -t, -T -S %SQLSERVER%

:: Export vBillableHoursStaff
echo Exporting vBillableHoursStaff...
bcp "SELECT * FROM DW.dbo.vBillableHoursStaff" queryout %EXPORT_PATH%\vBillableHoursStaff.csv -c -t, -T -S %SQLSERVER%

echo Export completed!
exit /b 0
