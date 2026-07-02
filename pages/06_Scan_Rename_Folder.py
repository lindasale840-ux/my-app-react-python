import streamlit as st
import tempfile
import shutil
import zipfile
from pathlib import Path
import os
import time

# Import cả 2 hàm xử lý của Tab 1 và Tab 2 độc lập từ Service của bạn
from services.scan_rename_service import run_scan_rename, run_auto_split_rename

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

st.title("📂 Hệ Thống Xử Lý PDF Scan Thông Minh")

st.markdown("""
Hỗ trợ đổi tên file lẻ hàng loạt hoặc tự động phân tách gói PDF tổng dựa vào mã GCN.
""")

st.markdown("---")

# Khởi tạo bộ đếm để reset uploader cho cả 2 tab
if "reset_counter_tab1" not in st.session_state:
    st.session_state.reset_counter_tab1 = 0
if "reset_counter_tab2" not in st.session_state:
    st.session_state.reset_counter_tab2 = 0

# Tạo cấu trúc 2 Tab
tab1, tab2 = st.tabs(["📄 Tab 1: Đổi tên file đã tách", "⚡ Tab 2: Tự động tách & Đổi tên (Nâng cao)"])

# Cấu hình danh mục kiểu đặt tên
naming_options = {
    "Mã quản lý": "ma_ql",
    "Số GCN": "so_gcn",
    "Tên thiết bị + Model": "ten_tb",
    "Tên thiết bị": "ten_khong_model",
    "Model": "model_khong_ten",
    "Mã xuất xưởng": "ma_xuat_xuong",
    "Tên + Mã xuất xưởng": "ten_ma_xuat_xuong",
    "Tên + Đặc trưng": "ten_dac_trung",
    "Tên + Model + NSX": "ten_model_nsx",
    "Tên + Model + Đặc trưng": "ten_model_dac_trung",
    "Tên + Mã quản lý": "ten_ma_ql",
    "Tên trước dấu / + Mã quản lý": "ten_truoc_slash_ma_ql",
    "Tên sau dấu / + Mã quản lý": "ten_sau_slash_ma_ql",
}

# ==============================================================================
# TAB 1: ĐỔI TÊN FILE ĐA TÁCH (GIỮ NGUYÊN 100% TOÀN BỘ LOGIC GỐC)
# ==============================================================================
with tab1:
    st.markdown("### OCR đổi tên hàng loạt các file PDF đã được chia nhỏ sẵn")
    
    uploaded_pdfs_t1 = st.file_uploader(
        label="Chọn các file PDF Scan lẻ",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"tab1_pdfs_{st.session_state.reset_counter_tab1}"
    )

    uploaded_excel_t1 = st.file_uploader(
        label="Chọn file Excel đối chiếu (Tab 1)",
        type=["xlsx", "xls"],
        key=f"tab1_excel_{st.session_state.reset_counter_tab1}"
    )

    selected_label_t1 = st.selectbox("Kiểu đặt tên (Tab 1)", options=list(naming_options.keys()), key="sb_t1")
    naming_type_t1 = naming_options[selected_label_t1]

    col_run_t1, col_reset_t1 = st.columns([3, 1])
    with col_reset_t1:
        if st.button("🗑️ Xóa sạch", key="btn_reset_t1", use_container_width=True):
            st.session_state.reset_counter_tab1 += 1
            st.rerun()
            
    with col_run_t1:
        run_t1 = st.button("🚀 Bắt đầu OCR & Đổi Tên", key="btn_run_t1", use_container_width=True, type="primary")

    if run_t1:
        if not uploaded_pdfs_t1 or not uploaded_excel_t1:
            st.error("⚠️ Vui lòng chọn đầy đủ file PDF và Excel.")
            st.stop()
        try:
            temp_folder = tempfile.mkdtemp()
            for pdf in uploaded_pdfs_t1:
                save_path = Path(temp_folder) / pdf.name
                with open(save_path, "wb") as f:
                    f.write(pdf.getvalue())

            excel_suffix = Path(uploaded_excel_t1.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=excel_suffix) as tmp_excel:
                tmp_excel.write(uploaded_excel_t1.getvalue())
                excel_path = tmp_excel.name

            with st.spinner(f"⏳ Đang OCR {len(uploaded_pdfs_t1)} file PDF..."):
                output_folder, msg = run_scan_rename(
                    folder_path=temp_folder, excel_path=excel_path, naming_type=naming_type_t1
                )
            st.success(msg)

            zip_path = Path(temp_folder) / "KetQua_DoiTen.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in Path(output_folder).rglob("*"):
                    if file_path.is_file():
                        zipf.write(file_path, arcname=file_path.relative_to(output_folder))

            with open(zip_path, "rb") as f:
                st.download_button("📥 Tải ZIP kết quả", data=f.read(), file_name="KetQua_DoiTen.zip", mime="application/zip", use_container_width=True)
        except Exception as e:
            st.exception(e)
        finally:
            try: shutil.rmtree(temp_folder)
            except: pass

# ==============================================================================
# TAB 2: TỰ ĐỘNG TÁCH & ĐỔI TÊN TỪ FILE TỔNG (PHIÊN BẢN NÂNG CAO)
# ==============================================================================
with tab2:
    st.markdown("### ⚡ Tự động nhận diện mã GCN ➡️ Tách bộ PDF ➡️ Đổi tên thành phẩm")
    st.info("💡 Điểm ưu việt: Bạn chỉ cần up 1 file PDF tổng lớn. Hệ thống tự gom các trang có mã GCN giống nhau và tự động LỌC BỎ các trang trống kết thúc hồ sơ.")

    uploaded_pdf_t2 = st.file_uploader(
        label="Chọn file PDF Tổng chưa tách",
        type=["pdf"],
        accept_multiple_files=False, # Chỉ cần nạp 1 file tổng lớn
        key=f"tab2_pdfs_{st.session_state.reset_counter_tab2}"
    )

    uploaded_excel_t2 = st.file_uploader(
        label="Chọn file Excel đối chiếu (Tab 2)",
        type=["xlsx", "xls"],
        key=f"tab2_excel_{st.session_state.reset_counter_tab2}"
    )

    selected_label_t2 = st.selectbox("Kiểu đặt tên (Tab 2)", options=list(naming_options.keys()), key="sb_t2")
    naming_type_t2 = naming_options[selected_label_t2]

    col_run_t2, col_reset_t2 = st.columns([3, 1])
    with col_reset_t2:
        if st.button("🗑️ Xóa sạch & Làm mới", key="btn_reset_t2", use_container_width=True):
            st.session_state.reset_counter_tab2 += 1
            st.rerun()

    with col_run_t2:
        run_t2 = st.button("⚡ Bắt đầu Tự động Tách & Đổi Tên", key="btn_run_t2", use_container_width=True, type="primary")

    if run_t2:
        if not uploaded_pdf_t2 or not uploaded_excel_t2:
            st.error("⚠️ Vui lòng chọn đầy đủ file PDF Tổng và file Excel đối chiếu.")
            st.stop()

        try:
            # Tạo thư mục làm việc tạm thời
            temp_dir = tempfile.mkdtemp()
            
            # Lưu file PDF tổng tạm thời
            pdf_total_path = Path(temp_dir) / uploaded_pdf_t2.name
            with open(pdf_total_path, "wb") as f:
                f.write(uploaded_pdf_t2.getvalue())
            
            # Lưu file Excel tạm thời
            excel_suffix = Path(uploaded_excel_t2.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=excel_suffix) as tmp_excel:
                tmp_excel.write(uploaded_excel_t2.getvalue())
                excel_path = tmp_excel.name

            # Thực thi gọi xuống hàm xử lý Tab 2 ở Backend
            with st.spinner("⏳ Hệ thống đang quét OCR từng trang và tự động phân nhóm GCN..."):
                zip_buffer, msg = run_auto_split_rename(
                    pdf_total_path=str(pdf_total_path),
                    excel_path=excel_path,
                    naming_type=naming_type_t2
                )
            
            if zip_buffer:
                st.success(msg)

                # 🔥 ĐOẠN ĐÃ ĐƯỢC CHỈNH SỬA: Không nén lại, không đọc file từ ổ cứng, 
                # Ăn trực tiếp luồng dữ liệu nhị phân (.getvalue()) từ bộ nhớ RAM sang nút tải
                st.download_button(
                    label="📥 Tải ZIP thành phẩm (Tab 2)",
                    data=zip_buffer.getvalue(),  # Lấy trực tiếp dữ liệu byte từ luồng bộ nhớ RAM
                    file_name=f"KetQua_Auto_Split_Rename_{int(time.time())}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
            else:
                st.error("⚠️ Có lỗi xảy ra trong quá trình tạo file ZIP từ Backend.")

        except Exception as e:
            st.exception(e)
        finally:
            # Dọn dẹp các file nhị phân tạm thời một cách an toàn
            try: 
                import shutil
                shutil.rmtree(temp_dir)
            except: 
                pass
            try:
                os.unlink(excel_path)
            except:
                pass