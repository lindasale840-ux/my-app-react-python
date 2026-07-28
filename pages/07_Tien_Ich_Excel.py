import streamlit as st
import tempfile
import pandas as pd

from services.excel_merge_service import (
    run_excel_merge
)

from services.excel_cleaner_service import (
    run_excel_cleaner
)

from services.excel_compare_service import (
    run_excel_compare
)

from services.excel_smart_search_service import (
    run_smart_search
)

from services.excel_consistency_service import (
    run_consistency_check
)

from services.excel_audit_service import (
    run_data_audit
)

from services.find_missing_excel_files import (
    find_missing_excel_files_v2
)

from services.filter_excel_files_by_list import (
    filter_excel_files_by_list
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
    "📊 TIỆN ÍCH EXCEL"
)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "VLOOKUP Siêu Tốc",
        "Data Cleaner",
        "So Sánh Excel",
        "🔎 Smart Search Excel",
        "📊 Data Audit",
        "Đối chiếu tên Excel",
        "Lọc file excel theo file tổng tên"
    ]
)

with tab1:


    st.subheader(
        "⚡ VLOOKUP / Merge Siêu Tốc"
    )

    file_a = st.file_uploader(
        "File chính",
        type=["xlsx", "xls"],
        key="file_a"
    )

    file_b = st.file_uploader(
        "File tham chiếu",
        type=["xlsx", "xls"],
        key="file_b"
    )

    if file_a and file_b:

        df_a = pd.read_excel(
            file_a,
            nrows=5
        )

        df_b = pd.read_excel(
            file_b,
            nrows=5
        )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:

            keys_a = st.multiselect(
                "Cột khóa File A",
                df_a.columns,
                default=[df_a.columns[0]]
            )

        with col2:

            keys_b = st.multiselect(
                "Cột khóa File B",
                df_b.columns,
                default=[df_b.columns[0]]
            )

        join_label = st.selectbox(
            "Kiểu ghép dữ liệu",
            [
                "Left Join (giữ toàn bộ File A)",
                "Inner Join (chỉ giữ dữ liệu khớp)",
                "Full Join (giữ tất cả)"
            ]
        )

        join_map = {
            "Left Join (giữ toàn bộ File A)": "left",
            "Inner Join (chỉ giữ dữ liệu khớp)": "inner",
            "Full Join (giữ tất cả)": "outer"
        }

        join_type = join_map[join_label]

        selected_columns = st.multiselect(
            "Các cột muốn lấy từ File B",
            [
                c
                for c in df_b.columns
                if c not in keys_b
            ]
        )

        force_merge = st.checkbox(
            "⚠️ Vẫn merge nếu phát hiện dữ liệu bất thường",
            value=False
        )

        if st.button(
            "🚀 Ghép dữ liệu"
        ):

            if len(keys_a) != len(keys_b):

                st.error(
                    "Số lượng khóa phải giống nhau"
                )

                st.stop()

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
            ) as tmp_a:

                tmp_a.write(
                    file_a.getvalue()
                )

                path_a = tmp_a.name

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
            ) as tmp_b:

                tmp_b.write(
                    file_b.getvalue()
                )

                path_b = tmp_b.name

            (
                result_file,
                df_preview,
                df_not_match,
                summary,
                business_summary,
                business_detail,
                msg
            ) = run_excel_merge(
                path_a,
                path_b,
                keys_a,
                keys_b,
                selected_columns,
                join_type,
                force_merge
            )

            if result_file:

                st.success(msg)

                c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

                c1.metric(
                    "Tổng dòng",
                    summary["total"]
                )

                c2.metric(
                    "Khớp",
                    summary["match"]
                )

                c3.metric(
                    "Không khớp",
                    summary["not_match"]
                )

                c4.metric(
                    "Tỷ lệ",
                    f"{summary['percent']}%"
                )

                c5.metric(
                    "Duplicate A",
                    summary["duplicate_a"]
                )

                c6.metric(
                    "Duplicate B",
                    summary["duplicate_b"]
                )

                c7.metric(
                    "Business Error",
                    summary["business_error"]
                )

                st.markdown("---")

                st.subheader(
                    "👀 Preview kết quả"
                )

                st.dataframe(
                    df_preview.head(100),
                    use_container_width=True
                )

                if len(df_not_match):

                    st.warning(
                        f"Có {len(df_not_match)} dòng không khớp"
                    )

                    st.dataframe(
                        df_not_match.head(100),
                        use_container_width=True
                    )

                with open(
                    result_file,
                    "rb"
                ) as f:

                    st.download_button(
                        "📥 Tải Excel kết quả",
                        data=f.read(),
                        file_name="Merged.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            else:

                st.error(msg)

                if len(business_summary):

                    st.markdown(
                        "### 🚨 Business Error Summary"
                    )

                    st.dataframe(
                        business_summary,
                        use_container_width=True
                    )

                    st.markdown(
                        "### 🔍 Business Error Detail"
                    )

                    st.dataframe(
                        business_detail,
                        use_container_width=True
                    )


                       
                
# ==================================================
# TAB 2
# ==================================================

with tab2:

    st.subheader(
        "🧹 Data Cleaner & Validator"
    )

    excel_file = st.file_uploader(
        "Chọn Excel",
        type=["xlsx", "xls"],
        key="clean_excel"
    )

    if excel_file:

        df_preview = pd.read_excel(
            excel_file,
            nrows=5
        )

        cols = list(
            df_preview.columns
        )

        st.dataframe(
            df_preview
        )

        phone_col = st.selectbox(
            "Cột SĐT",
            [""] + cols
        )

        email_col = st.selectbox(
            "Cột Email",
            [""] + cols
        )

        name_col = st.selectbox(
            "Cột Họ tên",
            [""] + cols
        )

        gcn_col = st.selectbox(
            "Cột GCN",
            [""] + cols
        )

        maql_col = st.selectbox(
            "Cột Mã quản lý",
            [""] + cols
        )

        serial_col = st.selectbox(
            "Cột Serial",
            [""] + cols
        )

        model_col = st.selectbox(
            "Cột Model",
            [""] + cols
        )

        if st.button(
            "🚀 Làm sạch dữ liệu"
        ):

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
            ) as tmp:

                tmp.write(
                    excel_file.getvalue()
                )

                path = tmp.name

            (
                output_file,
                preview,
                stats,
                msg
            ) = run_excel_cleaner(
                path,
                phone_col or None,
                email_col or None,
                name_col or None,
                gcn_col or None,
                maql_col or None,
                serial_col or None,
                model_col or None
            )

            if output_file:

                st.success(msg)

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "SĐT sửa",
                    stats["phones"]
                )

                c2.metric(
                    "Tên sửa",
                    stats["names"]
                )

                c3.metric(
                    "Email lỗi",
                    stats["email_errors"]
                )

                c4.metric(
                    "Trùng SĐT",
                    stats["duplicates"]
                )

                st.markdown("---")

                st.write(
                    "### Preview"
                )

                st.dataframe(
                    preview,
                    use_container_width=True
                )

                st.markdown("---")

                st.info(
                    f"GCN trùng: {stats['gcn_duplicates']} | "
                    f"Mã QL trùng: {stats['maql_duplicates']} | "
                    f"Serial trùng: {stats['serial_duplicates']} | "
                    f"Model trùng: {stats['model_duplicates']}"
                )

                with open(
                    output_file,
                    "rb"
                ) as f:

                    st.download_button(
                        "📥 Tải Excel sạch",
                        data=f.read(),
                        file_name="Excel_Cleaned.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            else:

                st.error(msg)
                
                
# ==================================================
# TAB 3
# ==================================================

with tab3:

    st.subheader(
        "🔍 So sánh 2 file Excel"
    )

    file_a = st.file_uploader(
        "File A",
        type=["xlsx", "xls"],
        key="compare_a"
    )

    file_b = st.file_uploader(
        "File B",
        type=["xlsx", "xls"],
        key="compare_b"
    )

    if file_a and file_b:

        preview_a = pd.read_excel(
            file_a,
            nrows=5
        )

        preview_b = pd.read_excel(
            file_b,
            nrows=5
        )

        col1, col2 = st.columns(2)

        with col1:

            keys_a = st.multiselect(
                "Cột khóa File A",
                preview_a.columns,
                default=[preview_a.columns[0]]
            )

        with col2:

            keys_b = st.multiselect(
                "Cột khóa File B",
                preview_b.columns,
                default=[preview_b.columns[0]]
            )

        if st.button(
            "🚀 So sánh dữ liệu"
        ):

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
            ) as tmp1:

                tmp1.write(
                    file_a.getvalue()
                )

                path_a = tmp1.name

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
            ) as tmp2:

                tmp2.write(
                    file_b.getvalue()
                )

                path_b = tmp2.name

            (
                output_file,
                df_match,
                df_only_a,
                df_only_b,
                df_detail,
                summary,
                msg
            ) = run_excel_compare(
                path_a,
                path_b,
                keys_a,
                keys_b
            )

            if output_file:

                st.success(msg)

                c1, c2, c3, c4, c5 = st.columns(5)

                c1.metric(
                    "Khớp",
                    summary["match"]
                )

                c2.metric(
                    "Chỉ File A",
                    summary["only_a"]
                )

                c3.metric(
                    "Chỉ File B",
                    summary["only_b"]
                )

                c4.metric(
                    "Ô dữ liệu thay đổi",
                    summary["differences"]
                )

                c5.metric(
                    "Hồ sơ thay đổi",
                    summary["changed_keys"]
                )

                st.markdown("---")

                st.subheader(
                    "✅ Dữ liệu khớp"
                )

                st.dataframe(
                    df_match.head(100)
                )

                st.subheader(
                    "⚠️ Chỉ có trong File A"
                )

                st.dataframe(
                    df_only_a.head(100)
                )

                st.subheader(
                    "⚠️ Chỉ có trong File B"
                )

                st.dataframe(
                    df_only_b.head(100)
                )

                with open(
                    output_file,
                    "rb"
                ) as f:
                    
                    st.subheader(
                        "🔍 Sai khác chi tiết"
                    )

                    if len(df_detail):

                        st.info(
                            f"Phát hiện {summary['changed_keys']} Key bị thay đổi dữ liệu"
                        )

                        audit_df = (

                            df_detail

                            .groupby("Column")

                            .size()

                            .reset_index(
                                name="Số lần thay đổi"
                            )

                            .sort_values(
                                "Số lần thay đổi",
                                ascending=False
                            )
                        )

                        st.subheader(
                            "📊 Audit Report"
                        )

                        st.dataframe(
                            audit_df,
                            use_container_width=True
                        )

                    st.download_button(
                        "📥 Tải Excel kết quả",
                        data=f.read(),
                        file_name="Excel_Compare.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            else:

                st.error(msg) 

with tab4:


    st.subheader(
        "🔎 Smart Search Excel"
    )

    uploaded_file = st.file_uploader(
        "Excel nguồn",
        type=["xlsx", "xls"],
        key="search_excel"
    )

    if uploaded_file:

        # =====================
        # Load file 1 lần
        # =====================

        full_df = pd.read_excel(
            uploaded_file,
            dtype=str
        ).fillna("")

        columns = list(
            full_df.columns
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".xlsx"
        ) as tmp:

            tmp.write(
                uploaded_file.getvalue()
            )

            excel_path = tmp.name

        # ==================================================
        # SEARCH
        # ==================================================

        st.markdown("### 🔎 Tìm kiếm dữ liệu")

        search_columns = st.multiselect(
            "Các cột tham gia tìm kiếm",
            columns,
            default=columns,
            key="search_columns"
        )

        search_text = st.text_input(
            "Từ khóa",
            key="search_text"
        )

        if st.button(
            "🚀 Tìm kiếm",
            key="search_btn"
        ):

            if not search_columns:

                st.error(
                    "Chọn ít nhất 1 cột"
                )

                st.stop()

            (
                output_file,
                result_df,
                msg
            ) = run_smart_search(
                excel_path,
                search_text,
                search_columns
            )

            if output_file:

                st.success(msg)

                st.metric(
                    "Kết quả",
                    len(result_df)
                )

                st.dataframe(
                    result_df,
                    use_container_width=True
                )

                with open(
                    output_file,
                    "rb"
                ) as f:

                    st.download_button(
                        "📥 Tải kết quả",
                        data=f.read(),
                        file_name="Search_Result.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            else:

                st.error(msg)

        # ==================================================
        # CONSISTENCY CHECK
        # ==================================================

        st.markdown("---")

        st.subheader(
            "🧪 Consistency Check"
        )

        st.info(
            "Ví dụ: 1 Model có nhiều Giá khác nhau, 1 GCN có nhiều Model..."
        )

        check_key = st.selectbox(
            "Cột khóa",
            columns,
            key="check_key"
        )

        check_value = st.selectbox(
            "Cột cần kiểm tra",
            columns,
            key="check_value"
        )

        if st.button(
            "🚀 Kiểm tra dữ liệu",
            key="consistency_btn"
        ):

            (
                output_file,
                issue_df,
                detail_df,
                msg
            ) = run_consistency_check(
                excel_path,
                check_key,
                check_value
            )

            if output_file:

                st.warning(msg)

                c1, c2 = st.columns(2)

                c1.metric(
                    "Key bất thường",
                    len(issue_df)
                )

                c2.metric(
                    "Dòng liên quan",
                    len(detail_df)
                )

                st.markdown(
                    "### 📊 Summary"
                )

                st.dataframe(
                    issue_df,
                    use_container_width=True
                )

                st.markdown(
                    "### 🔍 Chi tiết"
                )

                st.dataframe(
                    detail_df,
                    use_container_width=True
                )

                with open(
                    output_file,
                    "rb"
                ) as f:

                    st.download_button(
                        "📥 Tải báo cáo",
                        data=f.read(),
                        file_name="Consistency_Check.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            else:

                st.success(msg)
                
                
# ==================================================

# TAB 5

# ==================================================

with tab5:


    st.subheader(
        "📊 Data Audit"
    )

    uploaded_file = st.file_uploader(
        "Excel nguồn",
        type=["xlsx", "xls"],
        key="audit_excel"
    )

    if uploaded_file:

        preview_df = pd.read_excel(
            uploaded_file,
            nrows=5,
            dtype=str
        )

        columns = list(
            preview_df.columns
        )

        st.dataframe(
            preview_df,
            use_container_width=True
        )

        key_col = st.selectbox(
            "Key Column",
            columns,
            key="audit_key"
        )

        value_col = st.selectbox(
            "Value Column",
            columns,
            key="audit_value"
        )

        if st.button(
            "🚀 Audit dữ liệu",
            key="audit_btn"
        ):

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
            ) as tmp:

                tmp.write(
                    uploaded_file.getvalue()
                )

                excel_path = tmp.name

            (
                output_file,
                duplicate_summary,
                duplicate_detail,
                issue_df,
                detail_df,
                relationship_df,
                msg
            ) = run_data_audit(
                excel_path,
                key_col,
                value_col
            )

            if output_file:

                st.success(msg)

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Tổng cột",
                    len(columns)
                )

                c2.metric(
                    "Model nhiều giá",
                    len(issue_df)
                )

                c3.metric(
                    "Dòng bất thường",
                    len(detail_df)
                )

                st.markdown("---")

                st.subheader(
                    "📊 Duplicate Summary"
                )

                st.dataframe(
                    duplicate_summary,
                    use_container_width=True
                )

                st.subheader(
                    "🔥 Top Duplicate Values"
                )

                st.dataframe(
                    duplicate_detail,
                    use_container_width=True
                )

                st.subheader(
                    "💰 Model có nhiều giá"
                )

                st.dataframe(
                    issue_df,
                    use_container_width=True
                )

                st.subheader(
                    "🔍 Chi tiết"
                )

                st.dataframe(
                    detail_df,
                    use_container_width=True
                )
                
                st.subheader(
                    "🔗 Relationship Audit"
                )

                st.dataframe(
                    relationship_df,
                    use_container_width=True
                )

                with open(
                    output_file,
                    "rb"
                ) as f:

                    st.download_button(
                        "📥 Tải báo cáo Audit",
                        data=f.read(),
                        file_name="Data_Audit.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            else:

                st.error(msg)


with tab6:
    st.subheader("🔍 Tìm & Trích xuất file Excel còn thiếu")

    # 1. Chọn chế độ đối chiếu bằng Radio Button
    compare_mode = st.radio(
        "Chọn nguồn dữ liệu để đối chiếu:",
        options=["So sánh với Folder A", "So sánh với File Excel danh sách tổng"],
        horizontal=True,
        key="rad_compare_mode"
    )

    st.markdown("---")

    uploaded_excel_a = None
    uploaded_excel_list = None
    selected_name_col = None

    # 2. Khai báo Input tùy theo chế độ được chọn
    if compare_mode == "So sánh với Folder A":
        col_a, col_b = st.columns(2)

        with col_a:
            uploaded_excel_a = st.file_uploader(
                "Folder A (Thư mục đối chiếu)",
                type=["xlsx", "xls"],
                accept_multiple_files=True,
                key="compare_excel_a"
            )
            if uploaded_excel_a:
                st.success(f"Folder A: {len(uploaded_excel_a)} file")

        with col_b:
            uploaded_excel_b = st.file_uploader(
                "Folder B (Thư mục nguồn/thực tế)",
                type=["xlsx", "xls"],
                accept_multiple_files=True,
                key="compare_excel_b_mode1"
            )
            if uploaded_excel_b:
                st.success(f"Folder B: {len(uploaded_excel_b)} file")

    else: # Chế độ: So sánh với File Excel danh sách tổng
        col_list, col_b = st.columns(2)

        with col_list:
            uploaded_excel_list = st.file_uploader(
                "File Excel danh sách tổng",
                type=["xlsx", "xls"],
                accept_multiple_files=False,
                key="compare_excel_list"
            )
            
            # Chọn cột chứa tên file trong Excel
            if uploaded_excel_list:
                st.success(f"File danh sách: {uploaded_excel_list.name}")
                try:
                    df_preview = pd.read_excel(uploaded_excel_list, nrows=1)
                    selected_name_col = st.selectbox(
                        "Cột chứa tên file Excel:",
                        options=list(df_preview.columns),
                        key="select_name_col_list"
                    )
                except Exception as e:
                    st.error(f"Lỗi đọc file Excel: {str(e)}")

        with col_b:
            uploaded_excel_b = st.file_uploader(
                "Folder chứa các file Excel thực tế",
                type=["xlsx", "xls"],
                accept_multiple_files=True,
                key="compare_excel_b_mode2"
            )
            if uploaded_excel_b:
                st.success(f"Folder thực tế: {len(uploaded_excel_b)} file")

    st.markdown("---")

    # 3. Nút bấm xử lý
    if st.button("🚀 Bắt đầu đối chiếu & Trích xuất", key="btn_compare_excel"):

        if not uploaded_excel_b:
            st.error("Chưa chọn danh sách file Excel thực tế trong Thư mục!")
            st.stop()

        mode_key = "folder" if compare_mode == "So sánh với Folder A" else "excel_list"

        if mode_key == "excel_list":
            if not uploaded_excel_list:
                st.error("Chưa chọn File Excel danh sách tổng")
                st.stop()
            if not selected_name_col:
                st.error("Chưa chọn cột tên file trong Excel")
                st.stop()
            uploaded_excel_list.seek(0)

        with st.spinner("Đang đối chiếu dữ liệu..."):
            zip_path, msg = find_missing_excel_files_v2(
                mode=mode_key,
                files_b=uploaded_excel_b,
                files_a=uploaded_excel_a,
                excel_list_bytes=uploaded_excel_list,
                name_col=selected_name_col
            )

        if zip_path:
            st.success(msg)

            with open(zip_path, "rb") as f:
                st.download_button(
                    "📥 Tải file ZIP kết quả đối chiếu",
                    data=f.read(),
                    file_name="Ket_Qua_Doi_Chieu_Excel.zip",
                    mime="application/zip",
                    key="dl_missing_excel_zip_v2"
                )
        else:
            st.error(msg)
            
with tab7:
    st.subheader("🎯 Lọc & Gom file Excel theo danh sách từ File Tổng")

    # 1. Upload File tổng và Thư mục chứa file Excel thực tế
    col_excel, col_folder = st.columns(2)

    uploaded_excel_master = None
    filter_name_col = None

    with col_excel:
        uploaded_excel_master = st.file_uploader(
            "Tải lên File Excel Tổng (chứa danh sách tên)",
            type=["xlsx", "xls"],
            accept_multiple_files=False,
            key="filter_excel_master"
        )

        # Chọn cột chứa tên file cần lọc
        if uploaded_excel_master:
            st.success(f"File tổng: {uploaded_excel_master.name}")
            try:
                df_preview = pd.read_excel(uploaded_excel_master, nrows=1)
                filter_name_col = st.selectbox(
                    "Cột chứa danh sách tên file cần lọc:",
                    options=list(df_preview.columns),
                    key="select_filter_name_col"
                )
            except Exception as e:
                st.error(f"Lỗi đọc file Excel tổng: {str(e)}")

    with col_folder:
        uploaded_target_files = st.file_uploader(
            "Tải lên Thư mục chứa các file Excel thực tế",
            type=["xlsx", "xls"],
            accept_multiple_files=True,
            key="filter_target_files"
        )
        if uploaded_target_files:
            st.success(f"Số lượng file thực tế: {len(uploaded_target_files)} file")

    st.markdown("---")

    # 2. Nút thực hiện lọc
    if st.button("🚀 Bắt đầu lọc & Trích xuất file", key="btn_filter_excel"):

        if not uploaded_excel_master:
            st.error("Chưa chọn File Excel tổng chứa danh sách!")
            st.stop()

        if not filter_name_col:
            st.error("Chưa chọn cột chứa tên file trong Excel tổng!")
            st.stop()

        if not uploaded_target_files:
            st.error("Chưa chọn danh sách file Excel thực tế!")
            st.stop()

        # Đưa stream file về đầu
        uploaded_excel_master.seek(0)

        with st.spinner("Đang tiến hành lọc file theo danh sách..."):
            zip_path, msg = filter_excel_files_by_list(
                excel_list_bytes=uploaded_excel_master,
                name_col=filter_name_col,
                target_files=uploaded_target_files
            )

        # 3. Trả về kết quả & Nút tải về
        if zip_path:
            if "Cảnh báo" in msg:
                st.warning(msg)
            else:
                st.success(msg)

            with open(zip_path, "rb") as f:
                st.download_button(
                    "📥 Tải file ZIP các Excel đã lọc",
                    data=f.read(),
                    file_name="Danh_Sach_Excel_Da_Loc.zip",
                    mime="application/zip",
                    key="dl_filtered_excel_zip"
                )
        else:
            st.error(msg)            