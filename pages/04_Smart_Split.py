import streamlit as st
import tempfile

from pathlib import Path

from services.smart_split_service import run_smart_split

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
# Gọi hàm kiểm tra ngay đầu trang!
check_security()

st.title("🧠 Tách PDF Thông Minh")

st.markdown("---")

uploaded_pdf = st.file_uploader(
    "Chọn file PDF",
    type=["pdf"]
)

keyword = st.text_input(
    "Từ khóa nhận diện điểm cắt",
    value="GIẤY CHỨNG NHẬN HIỆU CHUẨN"
)

naming_options = {
    "Mã quản lý": "ma_ql",
    "Số GCN": "so_gcn",
    "Tên thiết bị + Model": "ten_tb"
}

selected_label = st.selectbox(
    "Kiểu đặt tên",
    list(naming_options.keys())
)

naming_type = naming_options[selected_label]


if st.button("🚀 Bắt đầu tách"):

    if uploaded_pdf is None:
        st.error("Vui lòng chọn file PDF")
        st.stop()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as tmp:

        tmp.write(uploaded_pdf.getvalue())

        pdf_path = tmp.name

    with st.spinner("Đang xử lý PDF..."):

        zip_path, msg = run_smart_split(
            pdf_path=pdf_path,
            keyword=keyword,
            naming_type=naming_type
        )

    st.success(msg)

    if zip_path and Path(zip_path).exists():

        with open(zip_path, "rb") as f:

            st.download_button(
                label="📥 Tải ZIP kết quả",
                data=f.read(),
                file_name=Path(zip_path).name,
                mime="application/zip"
            )