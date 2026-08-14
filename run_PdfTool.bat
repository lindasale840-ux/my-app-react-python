@echo off
chcp 65001 > nul
title PHẦN MỀM QUẢN LÝ GHÉP & ĐỔI TÊN HỒ SƠ PDF (PORT 5174)

echo ============================================================
echo   ĐANG KHỞI ĐỘNG BỘ CÔNG CỤ XỬ LÝ PDF (FASTAPI + REACT)
echo ============================================================
echo.

:: 1. Chạy Backend FastAPI (File main.py ở thư mục gốc)
echo [1/2] Đang khởi động Backend FastAPI (Port 8000)...

:: Tự động kích hoạt venv nếu có
if exist "%~dp0venv\Scripts\activate.bat" call "%~dp0venv\Scripts\activate.bat"
if exist "%~dp0.venv\Scripts\activate.bat" call "%~dp0.venv\Scripts\activate.bat"

start "PDF Tool Backend" cmd /k "cd /d "%~dp0" && python -m uvicorn main:app --reload --port 8000"

:: 2. Chạy Frontend React (Chuyển hẳn vào thư mục frontend chứa index.html)
echo [2/2] Đang khởi động Frontend Vite (Port 5174)...
start "PDF Tool Frontend" cmd /k "cd /d "%~dp0frontend" && npx vite --port 5174 --host"

echo.
echo ============================================================
echo   KHỞI ĐỘNG HOÀN TẤT!
echo   Vui lòng chờ khoảng 3-5 giây để dịch vụ sẵn sàng.
echo ============================================================
echo.

:: 3. Tự động mở trình duyệt web sau 4 giây
timeout /t 4 /nobreak > nul
start http://localhost:5174

exit