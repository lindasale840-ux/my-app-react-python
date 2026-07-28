import streamlit as st
import tempfile
import os

from services.pdf_merge_by_name_service import run_merge_by_name

from services.pdf_merge_by_excel_service import run_merge_by_excel

import pandas as pd

from services.pdf_excel_compare_service import run_compare_pdf_excel

from services.pdf_group_duplicate_service import (
    run_group_duplicate_files
)
from services.fill_form_service import run_generate_forms

from services.pdf_rename_from_excel import rename_pdf_files

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

st.title(
    "📂 TỰ ĐỘNG HÓA HỒ SƠ"
)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "Ghép theo tên file",
        "Ghép theo Excel",
        "Đối chiếu PDF-Excel",
        "Gom hồ sơ trùng tên",
        "Tạo hồ sơ hàng loạt",
        "Đổ dữ liệu vào form mẫu Excel",
        "Đổi tên file pdf theo excel tương ứng"
    ]
)


with tab1:

    st.subheader(
        "📎 Ghép hồ sơ theo tên file"
    )

    uploaded_a = st.file_uploader(
        "Folder A",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge_a"
    )

    uploaded_b = st.file_uploader(
        "Folder B",
        type=["pdf"],
        accept_multiple_files=True,
        key="merge_b"
    )

    if uploaded_a:

        st.success(
            f"Folder A: {len(uploaded_a)} file"
        )

    if uploaded_b:

        st.success(
            f"Folder B: {len(uploaded_b)} file"
        )

    if st.button(
        "🚀 Ghép hồ sơ",
        key="merge_by_name"
    ):

        if not uploaded_a:

            st.error(
                "Chưa chọn Folder A"
            )

            st.stop()

        if not uploaded_b:

            st.error(
                "Chưa chọn Folder B"
            )

            st.stop()

        temp_a = []
        temp_b = []

        # ==================
        # Folder A
        # ==================

        for file in uploaded_a:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as tmp:

                tmp.write(file.getvalue())

                temp_a.append({
                    "name": file.name,
                    "path": tmp.name
                })

        # ==================
        # Folder B
        # ==================

        # ==================
        # Folder B
        # ==================

        for file in uploaded_b:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as tmp:

                tmp.write(file.getvalue())

                temp_b.append({
                    "name": file.name,
                    "path": tmp.name
                })

        with st.spinner(
            "Đang ghép hồ sơ..."
        ):

            zip_path, msg = run_merge_by_name(
                temp_a,
                temp_b
            )

        if zip_path:

            st.success(msg)

            with open(
                zip_path,
                "rb"
            ) as f:

                st.download_button(
                    "📥 Tải ZIP",
                    data=f.read(),
                    file_name="Merged_By_Name.zip",
                    mime="application/zip"
                )

        else:

            st.error(msg)
            
with tab2:

    st.subheader(
        "📊 Ghép hồ sơ theo Excel"
    )

    uploaded_a = st.file_uploader(
        "Folder PDF A",
        type=["pdf"],
        accept_multiple_files=True,
        key="excel_a"
    )

    uploaded_b = st.file_uploader(
        "Folder PDF B",
        type=["pdf"],
        accept_multiple_files=True,
        key="excel_b"
    )

    excel_file = st.file_uploader(
        "File Excel Mapping",
        type=["xlsx", "xls"],
        key="excel_map"
    )

    column_a = None
    column_b = None

    if excel_file:

        df_preview = pd.read_excel(
            excel_file,
            dtype=str
        ).fillna("")

        st.success(
            f"Excel có {len(df_preview)} dòng"
        )

        st.dataframe(
            df_preview.head(10),
            use_container_width=True
        )

        columns = list(
            df_preview.columns
        )

        col1, col2 = st.columns(2)

        with col1:

            column_a = st.selectbox(
                "Cột chứa File A",
                columns
            )

        with col2:

            column_b = st.selectbox(
                "Cột chứa File B",
                columns
            )

    if st.button(
        "🚀 Ghép theo Excel",
        key="merge_excel"
    ):

        if not uploaded_a:

            st.error(
                "Chưa chọn Folder A"
            )
            st.stop()

        if not uploaded_b:

            st.error(
                "Chưa chọn Folder B"
            )
            st.stop()

        if not excel_file:

            st.error(
                "Chưa chọn Excel"
            )
            st.stop()

        temp_a = []
        temp_b = []

        for file in uploaded_a:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as tmp:

                tmp.write(
                    file.getvalue()
                )

                temp_a.append(
                    {
                        "name": file.name,
                        "path": tmp.name
                    }
                )

        for file in uploaded_b:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as tmp:

                tmp.write(
                    file.getvalue()
                )

                temp_b.append(
                    {
                        "name": file.name,
                        "path": tmp.name
                    }
                )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".xlsx"
        ) as tmp_excel:

            tmp_excel.write(
                excel_file.getvalue()
            )

            excel_path = tmp_excel.name

        with st.spinner(
            "Đang ghép..."
        ):

            zip_path, msg = run_merge_by_excel(
                temp_a,
                temp_b,
                excel_path,
                column_a,
                column_b
            )

        if zip_path:

            st.success(msg)

            with open(
                zip_path,
                "rb"
            ) as f:

                st.download_button(
                    "📥 Tải ZIP",
                    data=f.read(),
                    file_name="Merge_By_Excel.zip",
                    mime="application/zip"
                )

        else:

            st.error(msg)    
            
with tab3:

    st.subheader(
        "📊 Đối chiếu PDF - Excel"
    )

    compare_type = st.selectbox(
        "Đối chiếu theo",
        [
            "GCN",
            "Số seri",
            "Mã quản lý",
            "Tên thiết bị",
            "Model"
        ]
    )

    uploaded_excel = st.file_uploader(
        "Chọn Excel",
        type=["xlsx"],
        key="compare_excel"
    )

    uploaded_pdfs = st.file_uploader(
        "Chọn PDF",
        type=["pdf"],
        accept_multiple_files=True,
        key="compare_pdf"
    )

    if st.button(
        "🚀 Đối chiếu",
        key="compare_btn"
    ):

        if not uploaded_excel:

            st.error(
                "Chưa chọn Excel"
            )

            st.stop()

        if not uploaded_pdfs:

            st.error(
                "Chưa chọn PDF"
            )

            st.stop()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".xlsx"
        ) as tmp:

            tmp.write(
                uploaded_excel.getvalue()
            )

            excel_path = tmp.name

        result, msg = run_compare_pdf_excel(
            uploaded_pdfs,
            excel_path,
            compare_type
        )

        if not result:

            st.error(msg)

            st.stop()

        # =====================
        # KPI
        # =====================

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Khớp",
            len(result["matched"])
        )

        c2.metric(
            "Thiếu PDF",
            len(result["missing_pdf"])
        )

        c3.metric(
            "Thiếu Excel",
            len(result["missing_excel"])
        )

        c4.metric(
            "Trùng PDF",
            len(result["duplicates"])
        )

        # =====================
        # Chi tiết
        # =====================

        with st.expander(
            "Thiếu PDF"
        ):

            st.write(
                result["missing_pdf"]
            )

        with st.expander(
            "Thiếu Excel"
        ):

            st.write(
                result["missing_excel"]
            )

        with st.expander(
            "Trùng PDF"
        ):

            st.write(
                result["duplicates"]
            )

        with open(
            result["report"],
            "rb"
        ) as f:

            st.download_button(

                "📥 Tải báo cáo Excel",

                data=f.read(),

                file_name="BaoCao_DoiChieu.xlsx",

                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            )
            
            
with tab4:

    st.subheader(
        "📂 Gom hồ sơ trùng tên"
    )

    st.info(
        """
        Ví dụ:

        MayDo.pdf
        MayDo_1.pdf
        MayDo_2.pdf

        =>

        MayDo/
        """
    )

    uploaded_files = st.file_uploader(
        "Chọn các PDF",
        type=["pdf"],
        accept_multiple_files=True,
        key="group_duplicate"
    )

    if uploaded_files:

        st.success(
            f"Đã chọn {len(uploaded_files)} file"
        )

    if st.button(
        "🚀 Gom hồ sơ",
        key="group_btn"
    ):

        if not uploaded_files:

            st.error(
                "Vui lòng chọn PDF"
            )

            st.stop()

        with st.spinner(
            "Đang gom hồ sơ..."
        ):

            zip_path, stats, msg = (
                run_group_duplicate_files(
                    uploaded_files
                )
            )

        if not zip_path:

            st.error(msg)

            st.stop()

        st.success(
            "Hoàn thành"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Thư mục tạo",
            stats[
                "total_groups"
            ]
        )

        c2.metric(
            "PDF xử lý",
            stats[
                "total_files"
            ]
        )

        c3.metric(
            "Nhóm lớn nhất",
            stats[
                "largest_count"
            ]
        )

        st.info(
            f"Nhóm lớn nhất: {stats['largest_group']}"
        )

        with open(
            zip_path,
            "rb"
        ) as f:

            st.download_button(
                "📥 Tải ZIP",
                data=f.read(),
                file_name="HoSo_Gom.zip",
                mime="application/zip"
            )  
            
with tab6:
    st.subheader("📑 Điền Form Excel & Trích xuất PDF Tự Động")
    st.info("Thêm linh hoạt các cặp mapping và chọn trực tiếp Kiểu xử lý dữ liệu ngay trên giao diện.")

    # ==============================================================================
    # 1. TẢI FILE ĐẦU VÀO
    # ==============================================================================
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file_tong = st.file_uploader("1. Select File Tổng dữ liệu Excel", type=["xlsx", "xls"], key="tab6_file_tong")
        uploaded_file_form = st.file_uploader("2. Select File Form Mẫu Excel", type=["xlsx", "xls"], key="tab6_file_form")
    
    with col2:
        uploaded_pdf_files = st.file_uploader("3. Select các tệp PDF đính kèm (nếu có)", type=["pdf"], accept_multiple_files=True, key="tab6_pdf_files")

    if uploaded_file_tong and uploaded_file_form:
        try:
            df_preview = pd.read_excel(uploaded_file_tong, nrows=1)
            excel_columns = list(df_preview.columns)
        except Exception as e:
            st.error(f"Không thể đọc file Tổng: {e}")
            st.stop()

        st.markdown("---")
        st.subheader("⚙️ Cấu hình Ghép Cặp & Kiểu Xử Lý (Dynamic Mapping)")

        # Cột định danh chính (Mã quản lý)
        id_col = st.selectbox(
            "🔑 Chọn cột chứa Mã Quản Lý (Dùng làm tên File Excel xuất ra):",
            options=excel_columns,
            index=min(27, len(excel_columns)-1) if len(excel_columns) > 27 else 0,
            key="tab6_id_col"
        )

        # Danh sách các kiểu biến đổi logic hỗ trợ
        TRANSFORM_OPTIONS = [
            "Nguyên bản (Direct)",
            "Cắt lấy phần sau dấu '/'",
            "Tạo mã 'M' (Prefix M)",
            "Định dạng Ngày (DD/MMM/YYYY)",
            "Tra cứu PDF theo Mã GCN",
            "Viết HOA toàn bộ",
            "Viết thường toàn bộ",
            "Đánh tích nhóm '6' (ü)"
        ]

        # Khởi tạo danh sách cặp mapping mặc định mang đầy đủ logic mẫu ban đầu của bạn
        if "mapping_pairs" not in st.session_state:
            st.session_state.mapping_pairs = [
                {"excel_col": excel_columns[min(27, len(excel_columns)-1)], "transform_type": "Nguyên bản (Direct)", "target_cell": "J11"},
                {"excel_col": excel_columns[min(26, len(excel_columns)-1)], "transform_type": "Nguyên bản (Direct)", "target_cell": "U11"},
                {"excel_col": excel_columns[min(7, len(excel_columns)-1)], "transform_type": "Nguyên bản (Direct)", "target_cell": "U9"},
                {"excel_col": excel_columns[min(6, len(excel_columns)-1)], "transform_type": "Nguyên bản (Direct)", "target_cell": "J10"},
                {"excel_col": excel_columns[min(5, len(excel_columns)-1)], "transform_type": "Cắt lấy phần sau dấu '/'", "target_cell": "J9"},
                {"excel_col": excel_columns[min(27, len(excel_columns)-1)], "transform_type": "Tạo mã 'M' (Prefix M)", "target_cell": "U10"},
                {"excel_col": excel_columns[min(30, len(excel_columns)-1)] if len(excel_columns)>30 else excel_columns[0], "transform_type": "Định dạng Ngày (DD/MMM/YYYY)", "target_cell": "I18, G51"},
                {"excel_col": excel_columns[min(31, len(excel_columns)-1)] if len(excel_columns)>31 else excel_columns[0], "transform_type": "Định dạng Ngày (DD/MMM/YYYY)", "target_cell": "I19"},
                {"excel_col": excel_columns[min(25, len(excel_columns)-1)] if len(excel_columns)>25 else excel_columns[0], "transform_type": "Tra cứu PDF theo Mã GCN", "target_cell": "I20"},
            ]

        st.write("#### ➕ Danh sách các quy tắc Mapping")

        # Nút Thêm Cặp Mới
        if st.button("➕ Thêm Quy Tắc Mapping Mới", key="tab6_add_pair"):
            st.session_state.mapping_pairs.append({
                "excel_col": excel_columns[0], 
                "transform_type": "Nguyên bản (Direct)", 
                "target_cell": ""
            })
            st.rerun()

        # Render từng hàng ghép cặp với 3 trường: Cột Nguồn | Kiểu Xử Lý | Ô Đích
        pairs_to_remove = []
        for idx, pair in enumerate(st.session_state.mapping_pairs):
            c_col, c_trans, c_cell, c_del = st.columns([3, 3, 2, 1])
            
            with c_col:
                current_col_idx = excel_columns.index(pair["excel_col"]) if pair["excel_col"] in excel_columns else 0
                selected_col = st.selectbox(
                    f"Cột File Tổng #{idx+1}",
                    options=excel_columns,
                    index=current_col_idx,
                    key=f"tab6_col_{idx}"
                )
                st.session_state.mapping_pairs[idx]["excel_col"] = selected_col

            with c_trans:
                current_trans_idx = TRANSFORM_OPTIONS.index(pair["transform_type"]) if pair["transform_type"] in TRANSFORM_OPTIONS else 0
                selected_trans = st.selectbox(
                    f"Kiểu Xử Lý #{idx+1}",
                    options=TRANSFORM_OPTIONS,
                    index=current_trans_idx,
                    key=f"tab6_trans_{idx}"
                )
                st.session_state.mapping_pairs[idx]["transform_type"] = selected_trans

            with c_cell:
                target_cell = st.text_input(
                    f"Ô Form Mẫu #{idx+1}",
                    value=pair["target_cell"],
                    placeholder="VD: J11 hoặc I18, G51",
                    key=f"tab6_cell_{idx}"
                )
                st.session_state.mapping_pairs[idx]["target_cell"] = target_cell

            with c_del:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("❌", key=f"tab6_del_{idx}"):
                    pairs_to_remove.append(idx)

        # Xóa các dòng khi bấm nút ❌
        if pairs_to_remove:
            for idx in sorted(pairs_to_remove, reverse=True):
                st.session_state.mapping_pairs.pop(idx)
            st.rerun()

        # ==============================================================================
        # 3. QUY TẮC ĐẶC BIỆT RIÊNG CÔ ĐƠN (CHECKMARK ü)
        # ==============================================================================
        st.markdown("---")
        with st.expander("🛠️ Cấu hình Tích Dấu Checkmark (ü)", expanded=False):
            r5_active = st.checkbox("Bật quy tắc đánh dấu tích (ü) theo Mã Quản Lý", value=True, key="tab6_r5_act")
            col_r5_a, col_r5_b = st.columns(2)
            with col_r5_a:
                r5_k = st.text_input("Ô đánh tích nếu chứa nhóm '6' (K14):", value="K14", key="tab6_r5_k")
            with col_r5_b:
                r5_n = st.text_input("Ô đánh tích cho nhóm còn lại (N14):", value="N14", key="tab6_r5_n")

        # ==============================================================================
        # 4. THỰC THI & TẢI KẾT QUẢ
        # ==============================================================================
        st.markdown("---")
        if st.button("🚀 Bắt đầu Tạo Form & Đóng Gói ZIP", type="primary", key="tab6_run_btn"):
            
            mapping_config = {
                "id_column": id_col,
                "dynamic_pairs": st.session_state.mapping_pairs,
                "special_rules": {
                    "checkmark_logic": {"active": r5_active, "cell_option1": r5_k, "cell_option2": r5_n}
                }
            }

            with st.spinner("Đang tự động đọc dữ liệu, điền Form Excel và nén ZIP..."):
                zip_path, msg = run_generate_forms(
                    file_tong_bytes=uploaded_file_tong,
                    file_form_bytes=uploaded_file_form,
                    pdf_files=uploaded_pdf_files if uploaded_pdf_files else [],
                    mapping_config=mapping_config
                )

            if zip_path:
                st.success(msg)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="📥 Tải File ZIP Kết Quả",
                        data=f.read(),
                        file_name=f"Form_Excel_Completed.zip",
                        mime="application/zip",
                        key="tab6_download_btn"
                    )
            else:
                st.error(msg) 
                
with tab7:
    st.subheader("🏷️ Đổi tên file PDF theo Excel")

    # 1. Khai báo các Input Upload File
    uploaded_excel = st.file_uploader(
        "Tải lên file Excel tổng",
        type=["xlsx", "xls"],
        accept_multiple_files=False,
        key="rename_excel"
    )

    uploaded_pdfs = st.file_uploader(
        "Tải lên các file PDF cần đổi tên",
        type=["pdf"],
        accept_multiple_files=True,
        key="rename_pdfs"
    )

    # Hiển thị thông báo số lượng file đã chọn
    if uploaded_excel:
        st.success(f"Dữ liệu Excel: {uploaded_excel.name}")

    if uploaded_pdfs:
        st.success(f"Danh sách PDF: {len(uploaded_pdfs)} file")

    # 2. Xử lý đọc tiêu đề cột Excel để đưa vào Dropdown
    match_col = None
    primary_col = None
    fallback_col = None

    if uploaded_excel:
        try:
            # Đọc nhanh danh sách cột trong Excel
            df_preview = pd.read_excel(uploaded_excel, nrows=1)
            columns_list = list(df_preview.columns)

            st.markdown("---")
            st.markdown("##### ⚙️ Cấu hình cột đối chiếu & ghép tên")

            col1, col2, col3 = st.columns(3)

            with col1:
                match_col = st.selectbox(
                    "Cột khớp tên PDF cũ:",
                    options=columns_list,
                    key="rename_match_col",
                    help="Cột chứa giá trị trùng với tên file PDF hiện tại"
                )

            with col2:
                primary_col = st.selectbox(
                    "Cột lấy tên (Ưu tiên 1):",
                    options=columns_list,
                    key="rename_primary_col",
                    help="Giá trị cột này sẽ được ghép vào trước tên file cũ"
                )

            with col3:
                fallback_col = st.selectbox(
                    "Cột lấy tên (Dự phòng):",
                    options=columns_list,
                    key="rename_fallback_col",
                    help="Dùng khi Cột Ưu tiên 1 bị trống hoặc chứa dấu '/'"
                )

        except Exception as e:
            st.error(f"Lỗi đọc cấu trúc file Excel: {str(e)}")

    st.markdown("---")

    # 3. Nút bấm thực hiện đổi tên
    if st.button("🚀 Bắt đầu đổi tên", key="btn_rename_pdf"):

        # Validation kiểm tra đầu vào
        if not uploaded_excel:
            st.error("Chưa chọn file Excel tổng")
            st.stop()

        if not uploaded_pdfs:
            st.error("Chưa chọn danh sách file PDF")
            st.stop()

        if not match_col or not primary_col or not fallback_col:
            st.error("Vui lòng cấu hình đầy đủ các cột đối chiếu")
            st.stop()

        # Tiến hành xử lý
        with st.spinner("Đang xử lý đổi tên các file PDF..."):
            
            # Đưa file Excel về đầu stream trước khi đọc lại trong backend
            uploaded_excel.seek(0)
            
            # Gọi hàm xử lý backend
            zip_path, msg = rename_pdf_files(
                file_excel_bytes=uploaded_excel,
                pdf_files=uploaded_pdfs,
                match_col=match_col,
                primary_name_col=primary_col,
                fallback_name_col=fallback_col
            )

        # Trả về kết quả
        if zip_path:
            st.success(msg)

            with open(zip_path, "rb") as f:
                st.download_button(
                    "📥 Tải file ZIP đã đổi tên",
                    data=f.read(),
                    file_name="Danh_Sach_PDF_Da_Doi_Ten.zip",
                    mime="application/zip",
                    key="dl_renamed_zip"
                )
        else:
            st.error(msg)                                     