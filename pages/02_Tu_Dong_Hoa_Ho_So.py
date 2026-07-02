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

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Ghép theo tên file",
        "Ghép theo Excel",
        "Đối chiếu PDF-Excel",
        "Gom hồ sơ trùng tên",
        "Tạo hồ sơ hàng loạt"
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