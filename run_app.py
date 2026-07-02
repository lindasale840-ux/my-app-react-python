# run_app.py
import os
import sys
import time
import threading
import webbrowser
import streamlit.web.cli as stcli

# 🔥 ĐÃ THÊM: Cấu hình ghi log tự động ra file khi ẩn Terminal
if getattr(sys, 'frozen', False):
    # Khi chạy file EXE, lấy thư mục chứa file EXE chính (C:\Program Files\PDF Smart App)
    log_dir = os.path.dirname(sys.executable)
    log_file = os.path.join(log_dir, "app_debug.log")
    
    # Điều hướng toàn bộ kết quả Terminal (print và error) vào file log
    sys.stdout = open(log_file, "w", encoding="utf-8", buffering=1)
    sys.stderr = sys.stdout

def open_browser():
    """Hàm chạy ngầm: Đợi 3 giây cho Server mở cổng rồi mới bật trình duyệt"""
    time.sleep(3)
    webbrowser.open("http://localhost:8501")

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS 
    else:
        base_path = os.path.dirname(__file__)
        
    app_path = os.path.join(base_path, "app.py")
    
    sys.argv = [
        "streamlit", 
        "run", 
        app_path, 
        "--global.developmentMode=false",
        "--server.headless=true",          
        "--server.port=8501"               
    ]
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Kích hoạt máy chủ Streamlit
    sys.exit(stcli.main())