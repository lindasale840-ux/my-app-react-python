# run_app.py
import os
import sys
import time
import threading
import webbrowser
import signal
import streamlit.web.cli as stcli
from streamlit.web.server.server import Server
from tornado.ioloop import PeriodicCallback

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

def check_browser_connections():
    """Kiểm tra số lượng tab trình duyệt kết nối đến Server để tự hủy tiến trình"""
    try:
        server = Server.get_current()
        if server is not None:
            active_connections = len(server._browser_connections)
            
            # Nếu người dùng tắt hết toàn bộ tab hoặc đóng trình duyệt (số kết nối về 0)
            if active_connections == 0:
                print("🛑 [TỰ ĐỘNG TẮT] Không còn trình duyệt kết nối. Hệ thống đang tiến hành đóng hoàn toàn tiến trình chạy ngầm...")
                # Giải phóng file log trước khi thoát để tránh crash dữ liệu
                if getattr(sys, 'frozen', False):
                    sys.stdout.close()
                
                # Thực hiện kill dứt điểm tiến trình hiện tại trên Windows
                os.kill(os.getpid(), signal.SIGTERM)
                sys.exit(0)
    except Exception as e:
        pass

def start_auto_shutdown_monitor():
    """Đợi Streamlit Server khởi động xong rồi gắn bộ đếm chu kỳ kiểm tra kết nối"""
    try:
        # Chờ 6 giây để server lên luồng ổn định và người dùng mở được tab trình duyệt đầu tiên
        time.sleep(6) 
        server = Server.get_current()
        if server is not None:
            loop = server._ioloop
            # Cứ mỗi 3000ms (3 giây) chạy hàm kiểm tra kết nối 1 lần dựa trên vòng lặp ioloop của Tornado
            loop.add_callback(lambda: PeriodicCallback(check_browser_connections, 3000).start())
            print("🚀 [GIÁM SÁT THÀNH CÔNG] Đã kích hoạt chốt chặn tự hủy tự động khi tắt trình duyệt.")
    except Exception as e:
        print(f"⚠️ [GIÁM SÁT LỖI] Không thể kích hoạt bộ tự hủy: {e}")

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
    
    # 🔥 THÊM CHỐT CHẶN: Khởi chạy luồng phụ giám sát trạng thái tab trình duyệt
    threading.Thread(target=start_auto_shutdown_monitor, daemon=True).start()
    
    # Kích hoạt máy chủ Streamlit gốc
    sys.exit(stcli.main())