import streamlit as st
import sys
import os
import json
import zipfile
import io

# Thiết lập cấu hình trang Streamlit đồng bộ
st.set_page_config(page_title="Tiện ích Word", page_icon="📝", layout="wide")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from security import check_security
from backend.license_manager import verify_license_key

# =========================================================
# KHÓA BẢN QUYỀN VÒNG NGOÀI
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
    st.stop() 

# Gọi hàm kiểm tra an ninh ngay đầu trang
check_security()

# Import các hàm logic từ backend
from backend.word_processor import fix_and_format_word
from backend.word_mail_merge import mail_merge_docx

# ==========================================
# KHỐI TIÊU ĐỀ TRANG CHÍNH & NÚT DỌN CACHE
# ==========================================
col_title, col_reset = st.columns([5, 1.5])
with col_title:
    st.title("📝 Bộ Tiện Ích Xử Lý File Word")
    st.write("Tổng hợp các công cụ tối ưu hóa, sửa lỗi font, trộn thư và hỗ trợ đa ngôn ngữ tự động.")

with col_reset:
    st.write("") # Tạo khoảng cách dòng
    st.write("") 
    # Nút dọn dẹp cache và làm mới hệ thống
    if st.button("🧹 Xóa Cache & Làm Mới App", type="secondary", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        
        # Reset các biến trạng thái nếu có
        for key in list(st.session_state.keys()):
            del st.session_state[key]
            
        st.success("Đã dọn dẹp bộ nhớ đệm!")
        st.rerun()

st.divider()

# ĐỊNH NGHĨA HỆ THỐNG CÁC TAB CHỨC NĂNG
tab1, tab2, tab3 = st.tabs([
    "🎨 Chuẩn Hóa & Căn Lề In", 
    "✉️ Trộn Thư (Mail Merge)", 
    "➕ Chức năng Word mới (Sắp ra mắt)"
])

# ==========================================
# TAB 1: CHUẨN HÓA & CĂN LỀ IN VĂN BẢN
# ==========================================
with tab1:
    st.subheader("🎨 Chuẩn hóa font chữ, chuyển đổi mã & Xử lý hàng loạt")
    st.write("Dọn sạch định dạng lỗi, tự động phát hiện đổi font tiếng Trung, sửa văn bản lỗi font TCVN3 và xuất file ZIP hàng loạt.")
    st.divider()

    uploaded_files = st.file_uploader(
        "Tải lên một hoặc nhiều tệp Word cần xử lý (.docx, .doc):", 
        type=["docx", "doc"],
        accept_multiple_files=True,
        key="word_uploader_tab1"
    )

    if uploaded_files:
        st.success(f"📂 Đã nạp thành công **{len(uploaded_files)}** tệp văn bản.")
        has_doc_old_file = any(file.name.split(".")[-1].lower() == "doc" for file in uploaded_files)
        
        if has_doc_old_file:
            st.error("⚠️ Danh sách tải lên của bạn có chứa file đuôi `.doc` đời cũ.")
            st.info(
                "💡 **Để tránh lỗi xử lý:** Bạn vui lòng mở các file đuôi `.doc` này lên bằng Word trên máy tính, "
                "chọn **Save As** và lưu lại dưới dạng file **.docx** rồi tải lại lên đây nhé!"
            )
        else:
            st.subheader("⚙️ Cấu hình thông số chuẩn hóa")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                font_option = st.selectbox(
                    "Chọn Font chính (Việt/Anh):",
                    options=["Times New Roman", "Arial", "Calibri", "Roboto"],
                    index=0
                )
                font_size = st.number_input(
                    "Cỡ chữ tiêu chuẩn (Size):", 
                    min_value=10, max_value=18, value=13, step=1
                )
                
            with col2:
                line_spacing = st.selectbox(
                    "Giãn dòng (Line Spacing):",
                    options=[1.0, 1.15, 1.3, 1.5],
                    index=1
                )
                space_after = st.slider(
                    "Khoảng cách đoạn (Space After - pt):", 
                    min_value=0, max_value=12, value=6, step=2
                )
                
            with col3:
                st.write("**🔧 Tính năng sửa lỗi chuyên sâu:**")
                auto_convert_tcvn = st.checkbox(
                    "Sửa lỗi bảng mã cũ (TCVN3 / .VnTime)",
                    value=False,
                    key="tcvn_tab1"
                )
                detect_chinese = st.checkbox(
                    "Nhận dạng tự động & Đổi font tiếng Trung",
                    value=False,
                    key="chinese_tab1"
                )
                
                chinese_font = "SimSun"
                if detect_chinese:
                    chinese_font = st.selectbox(
                        "Chọn Font riêng cho tiếng Trung:",
                        options=["SimSun", "Microsoft YaHei", "KaiTi", "SimHei"],
                        index=0,
                        key="chinese_font_tab1"
                    )
            
            st.divider()
            
            if st.button("🚀 Bắt đầu xử lý hàng loạt", type="primary", key="btn_process_tab1"):
                processed_files = []
                error_files = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, file in enumerate(uploaded_files):
                    status_text.write(f"Đang xử lý file ({idx+1}/{len(uploaded_files)}): `{file.name}`")
                    try:
                        processed_stream = fix_and_format_word(
                            word_file=file,
                            target_font=font_option,
                            font_size=font_size,
                            line_spacing=line_spacing,
                            space_after=space_after,
                            auto_convert_tcvn3=auto_convert_tcvn,
                            detect_chinese=detect_chinese,
                            chinese_font=chinese_font
                        )
                        processed_files.append((f"Chuan_Hoa_{file.name}", processed_stream))
                    except Exception as e:
                        error_files.append((file.name, str(e)))
                    progress_bar.progress(int((idx + 1) / len(uploaded_files) * 100))
                
                status_text.empty()
                progress_bar.empty()
                
                if error_files:
                    st.warning("⚠️ Một số file gặp lỗi trong quá trình xử lý:")
                    for err_file, err_msg in error_files:
                        st.write(f"- `{err_file}`: {err_msg}")
                
                if processed_files:
                    st.success(f"🎉 Đã xử lý thành công **{len(processed_files)}/{len(uploaded_files)}** file Word!")
                    if len(processed_files) == 1:
                        single_name, single_stream = processed_files[0]
                        st.download_button(
                            label="📥 Tải xuống file Word hoàn chỉnh",
                            data=single_stream,
                            file_name=single_name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    else:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            for name, stream in processed_files:
                                zip_file.writestr(name, stream.getvalue())
                        zip_buffer.seek(0)
                        
                        st.download_button(
                            label="📥 Tải xuống toàn bộ tệp nén (ZIP)",
                            data=zip_buffer,
                            file_name="Bo_Tien_Ich_Word_Hoan_Thanh.zip",
                            mime="application/zip"
                        )

# ==========================================
# TAB 2: TRỘN TÀI LIỆU (MAIL MERGE) - MỚI
# ==========================================
with tab2:
    st.subheader("✉️ Trộn dữ liệu Excel vào File Word mẫu (Mail Merge)")
    st.write("Tự động điền hàng loạt thông tin từ danh sách Excel vào các phôi Word có sẵn (như Hợp đồng, Giấy mời, Quyết định...).")
    st.divider()
    
    st.info(
        "💡 **Hướng dẫn thiết lập phôi mẫu cực dễ:**\n"
        "- **Trong file Word mẫu (.docx):** Tại những vị trí cần điền thông tin tự động, bạn gõ tên nhãn đặt trong dấu ngoặc nhọn đôi. Ví dụ: `{{ ho_ten }}`, `{{ chuc_vu }}`, `{{ ngay_sinh }}`.\n"
        "- **Trong file Excel (.xlsx):** Tạo các cột có tiêu đề trùng khớp hoàn toàn với tên nhãn trong file mẫu (ví dụ tiêu đề cột là `ho_ten`, `chuc_vu`, `ngay_sinh`). Mỗi hàng dữ liệu bên dưới tương ứng với một người."
    )
    
    st.divider()
    
    # KHU VỰC CẤU HÌNH FONT SONG NGỮ & ĐỊNH DẠNG NÂNG CAO CHO TAB 2 (CẬP NHẬT)
    st.write("⚙️ **Cấu hình định dạng cho tài liệu xuất ra:**")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        font_option_tab2 = st.selectbox(
            "Chọn Font chính (Việt/Anh):",
            options=["Times New Roman", "Arial", "Calibri", "Roboto"],
            index=0,
            key="font_tab2"
        )
        font_size_tab2 = st.number_input(
            "Cỡ chữ tiêu chuẩn (Size):", 
            min_value=10, max_value=18, value=13, step=1,
            key="size_tab2"
        )
    with col_f2:
        st.write("**🔧 Kiểu dáng chữ điền thêm (`{{ tag }}`):**")
        cb_bold = st.checkbox("Bold (In đậm 📌)", value=False, key="style_bold")
        cb_italic = st.checkbox("Italic (In nghiêng ✍️)", value=False, key="style_italic")
        cb_underline = st.checkbox("Underline (Gạch chân 🔗)", value=False, key="style_underline")
        
    with col_f3:
        st.write("**🎨 Ngôn ngữ & Màu sắc chữ điền thêm:**")
        detect_chinese_tab2 = st.checkbox(
            "Nhận dạng & Đổi font tiếng Trung",
            value=False,
            key="chinese_check_tab2"
        )
        if detect_chinese_tab2:
            chinese_font_tab2 = st.selectbox(
                "Chọn Font riêng cho tiếng Trung:",
                options=["SimSun", "Microsoft YaHei", "KaiTi", "SimHei"],
                index=0,
                key="chinese_font_select_tab2"
            )
        else:
            chinese_font_tab2 = "SimSun"
            
        # Hộp chọn màu sắc cực xịn
        text_color_tab2 = st.color_picker(
            "Chọn màu riêng cho chữ điền thêm:", 
            value="#000000", 
            key="color_tab2",
            help="Mặc định là màu đen (#000000). Bạn có thể chọn màu xanh, đỏ... để làm nổi bật thông tin điền thêm."
        )
        
    st.divider()
    
    col_w, col_e = st.columns(2)
    
    with col_w:
        st.write("👉 **Bước 1: Tải lên Phôi mẫu Word**")
        template_file = st.file_uploader(
            "Tải file Word mẫu (.docx):", 
            type=["docx"],
            key="template_uploader"
        )
        
    with col_e:
        st.write("👉 **Bước 2: Tải lên Danh sách Excel**")
        excel_file = st.file_uploader(
            "Tải file Excel chứa dữ liệu (.xlsx, .xls):", 
            type=["xlsx", "xls"],
            key="excel_uploader"
        )
        
    if template_file is not None and excel_file is not None:
        st.success("✅ Đã nhận đủ cả 2 file phôi mẫu và dữ liệu nguồn.")
        st.divider()
        
        # Nút kích hoạt trộn thư
        if st.button("🚀 Tiến hành trộn & Tạo tài liệu hàng loạt", type="primary", key="btn_mail_merge"):
            with st.spinner("Hệ thống đang phân tích dữ liệu Excel và tạo tài liệu..."):
                try:
                    output_files = mail_merge_docx(
                        template_file=template_file, 
                        excel_file=excel_file,
                        target_font=font_option_tab2,
                        font_size=font_size_tab2,
                        detect_chinese=detect_chinese_tab2,
                        chinese_font=chinese_font_tab2,
                        is_bold=cb_bold,
                        is_italic=cb_italic,
                        is_underline=cb_underline,
                        text_color=text_color_tab2
                    )
                    
                    if output_files:
                        st.success(f"🎉 Xuất bản thành công **{len(output_files)}** tài liệu cá nhân hóa!")
                        
                        # Gom toàn bộ file Word thành phẩm vào 1 file nén ZIP
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            for file_name, file_stream in output_files:
                                zip_file.writestr(file_name, file_stream.getvalue())
                        zip_buffer.seek(0)
                        
                        st.download_button(
                            label="📥 Tải xuống toàn bộ tài liệu đã trộn (ZIP)",
                            data=zip_buffer,
                            file_name="Danh_Sach_Tai_Lieu_Tron_Thu.zip",
                            mime="application/zip"
                        )
                except Exception as e:
                    st.error(f"❌ Có lỗi phát sinh trong quá trình trộn thư: {str(e)}")
                    st.info("💡 **Gợi ý kiểm tra:** Hãy chắc chắn các tiêu đề cột trong file Excel trùng khớp với các biến nằm trong dấu ngoặc `{{ ... }}` của file Word mẫu nhé.")

# ==========================================
# TAB 3: KHÔNG GIAN CHỜ CHỨC NĂNG MỚI
# ==========================================
with tab3:
    st.subheader("🛠️ Tính năng đang được phát triển")
    st.info("Tab chờ số 3 sẵn sàng cho các bài toán tiếp theo...")