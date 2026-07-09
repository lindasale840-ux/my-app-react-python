# run_app.py
import os
import sys
import time
import threading
import webbrowser
import signal
import subprocess
import urllib.request
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

def start_auto_shutdown_monitor():
    """
    GIẢI PHÁP AN TOÀN: Kiểm tra cổng kết nối mạng bằng urllib tiêu chuẩn.
    Nếu người dùng tắt trình duyệt, server sẽ ngắt kết nối thực tế -> Kích hoạt tự hủy.
    """
    # Chờ 10 giây để người dùng mở hẳn tab trình duyệt đầu tiên lên thành công
    time.sleep(10)
    
    consecutive_failures = 0
    while True:
        time.sleep(4)  # Cứ mỗi 4 giây kiểm tra tình trạng app một lần
        try:
            # Gửi một request cực nhẹ đến trang chủ của App ngầm
            with urllib.request.urlopen("http://localhost:8501", timeout=2) as response:
                if response.status == 200:
                    consecutive_failures = 0  # Kết nối bình thường -> Reset bộ đếm lỗi
        except Exception:
            # Nếu không thể kết nối đến cổng (Trình duyệt đóng hoặc sập)
            consecutive_failures += 1
            
        # Nếu mất kết nối liên tiếp 3 lần (khoảng 12 giây), khẳng định người dùng đã tắt hoàn toàn
        if consecutive_failures >= 3:
            print("🛑 [TỰ ĐỘNG TẮT] Trình duyệt đã đóng. Tiến hành giải phóng bộ nhớ và tắt Task Manager...")
            if getattr(sys, 'frozen', False):
                sys.stdout.close()
            # Ra lệnh cho hệ điều hành diệt dứt điểm tiến trình ngầm này
            os.kill(os.getpid(), signal.SIGTERM)
            sys.exit(0)

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
    
    # Khởi chạy luồng phụ mở trình duyệt tự động
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Khởi chạy luồng phụ giám sát sự sống của cổng 8501 bằng thư viện hệ thống
    threading.Thread(target=start_auto_shutdown_monitor, daemon=True).start()
    
    # Kích hoạt máy chủ Streamlit gốc
    sys.exit(stcli.main())