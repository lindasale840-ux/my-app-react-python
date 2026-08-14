@echo off
chcp 65001 > nul
title PHẦN MỀM QUẢN LÝ GHÉP & ĐỔI TÊN HỒ SƠ PDF (PORT 5174)

echo ============================================================
echo   ĐANG KHỞI ĐỘNG BỘ CÔNG CỤ XỬ LÝ PDF (FASTAPI + REACT)
echo ============================================================
echo.

:: 1. Chạy Backend FastAPI (mở cửa sổ Terminal ngầm)
echo [1/2] Đang khởi động Backend FastAPI (Port 8000)...
start "PDF Tool Backend (FastAPI)" cmd /k "cd /d %~dp0backend && uvicorn main:app --reload --port 8000"

:: 2. Chạy Frontend React (Vite) trên Port 5174
echo [2/2] Đang khởi động Frontend Vite (Port 5174)...
start "PDF Tool Frontend (Vite)" cmd /k "cd /d %~dp0 && npx vite --port 5174 --host"

echo.
echo ============================================================
echo   KHỞI ĐỘNG HOÀN TẤT!
echo   Vui lòng chờ khoảng 3-5 giây để dịch vụ sẵn sàng.
echo   Trình duyệt sẽ tự động mở địa chỉ: http://localhost:5174
echo ============================================================
echo.

:: 3. Tự động mở trình duyệt web sau 4 giây
timeout /t 4 /nobreak > nul
start http://localhost:5174

exit