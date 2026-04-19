@echo off
:: setup_scheduler.bat - Đăng ký Windows Task Scheduler để chạy main.py mỗi ngày lúc 8:00 sáng

SET TASK_NAME=ThebumpAutopost
SET PYTHON_PATH=python
SET SCRIPT_PATH=%~dp0main.py
SET WORK_DIR=%~dp0

echo Dang ky Task Scheduler: %TASK_NAME%
echo Script: %SCRIPT_PATH%
echo Chay luc: 08:00 hang ngay

schtasks /create /tn "%TASK_NAME%" /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" /sc daily /st 08:00 /sd 01/01/2024 /f /rl highest

if %errorlevel% == 0 (
    echo.
    echo [OK] Task da duoc dang ky thanh cong!
    echo      Ten task: %TASK_NAME%
    echo      Chay luc: 08:00 moi ngay
    echo.
    echo De xem task: schtasks /query /tn "%TASK_NAME%" /fo LIST
    echo De chay thu ngay: schtasks /run /tn "%TASK_NAME%"
    echo De xoa task:  schtasks /delete /tn "%TASK_NAME%" /f
) else (
    echo.
    echo [LOI] Khong the dang ky task. Hay chay file nay voi quyen Administrator.
)

pause
