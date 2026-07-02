import streamlit as st
from services.smart_split_excel_service import run_smart_split_excel
from utils.file_helper import save_uploaded_file

from pathlib import Path

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


st.set_page_config(
    page_title="Tách PDF Theo Excel",
    layout="wide"
)

st.title("📊 TÁCH PDF THEO EXCEL")

st.markdown("""
Tách PDF tổng → Bóc mã GCN → Đối chiếu Excel → Đổi tên file tự động.
""")

st.markdown("---")

# =========================
# Upload PDF
# =========================

uploaded_pdf = st.file_uploader(
    label="📄 Chọn file PDF tổng",
    type=["pdf"]
)

# =========================
# Upload Excel
# =========================

uploaded_excel = st.file_uploader(
    label="📊 Chọn file Excel đối chiếu",
    type=["xlsx", "xls"]
)

# =========================
# Keyword
# =========================

keyword = st.text_input(
    label="🔍 Từ khóa nhận diện điểm cắt",
    value="GIẤY CHỨNG NHẬN HIỆU CHUẨN"
)

# =========================
# Naming options
# =========================

naming_options = {
    "Tên thiết bị + Model": "ten_tb",
    "Mã quản lý": "ma_ql"
}

selected_label = st.selectbox(
    label="📝 Kiểu đặt tên file",
    options=list(naming_options.keys())
)

naming_type = naming_options[selected_label]

st.markdown("---")

# =========================
# Run button
# =========================

if st.button("🚀 Tách PDF & Đối Chiếu Excel", use_container_width=True):

    if uploaded_pdf is None:
        st.error("⚠️ Vui lòng chọn file PDF.")
        st.stop()

    if uploaded_excel is None:
        st.error("⚠️ Vui lòng chọn file Excel.")
        st.stop()

    try:

        # =========================
        # Save PDF temp
        # =========================

        pdf_path = save_uploaded_file(uploaded_pdf)


        # =========================
        # Save Excel temp
        # =========================

        excel_suffix = Path(uploaded_excel.name).suffix

        excel_path = save_uploaded_file(uploaded_excel)

        # =========================
        # Execute
        # =========================

        with st.spinner("⏳ Đang tách PDF và đối chiếu Excel..."):

            zip_path, msg = run_smart_split_excel(
                pdf_path=pdf_path,
                excel_path=excel_path,
                keyword=keyword,
                naming_type=naming_type
            )

        # =========================
        # Result
        # =========================

        if zip_path and Path(zip_path).exists():

            st.success(msg)

            with open(zip_path, "rb") as f:

                st.download_button(
                    label="📥 Tải ZIP kết quả",
                    data=f.read(),
                    file_name=Path(zip_path).name,
                    mime="application/zip",
                    use_container_width=True
                )

        else:

            st.error(msg)

    except Exception as e:

        st.exception(e)