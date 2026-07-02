import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from security import check_security
import json
from backend.license_manager import verify_license_key
# =========================================================
# KHÓA BẢN QUYỀN VÒNG NGOÀI (Thêm đoạn này vào)
# =========================================================
current_key = ""
if os.path.exists("license.json"):
    try:
        with open("license.json", "r") as f:
            current_key = json.load(f).get("product_key", "")
    except:
        pass

status = verify_license_key(current_key)
if not status["valid"]:
    st.error("🔒 Ứng dụng chưa được kích hoạt hoặc bản quyền đã hết hạn!")
    st.warning("⚠️ Vui lòng chuyển sang trang **Bản quyền** ở thanh menu bên cạnh để nhập mã kích hoạt mới nhằm tiếp tục sử dụng.")
    st.stop() # LỆNH TỐI QUAN TRỌNG: Dừng toàn bộ code phía dưới, không cho render các Tab tiện ích
# =========================================================
# Gọi hàm kiểm tra ngay đầu trang!
check_security()

st.title("🚀 HỆ THỐNG QUẢN TRỊ & XỬ LÝ HỒ SƠ THÔNG MINH")

st.divider()

st.markdown("""
Chào mừng bạn đến với ứng dụng tự động hóa nội bộ.

### Hướng dẫn nhanh

- Sử dụng menu bên trái để chuyển đổi chức năng.
- Hệ thống chạy offline.
- Không giới hạn lượt sử dụng.
- Toàn bộ dữ liệu được xử lý nội bộ.
""")