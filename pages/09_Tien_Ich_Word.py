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

# Import hàm logic nâng cấp mới từ backend
from backend.word_processor import fix_and_format_word

# ==========================================
# KHỐI TIÊU ĐỀ TRANG CHÍNH
# ==========================================
st.title("📝 Bộ Tiện Ích Xử Lý File Word")
st.write("Tổng hợp các công cụ tối ưu hóa, sửa lỗi font, chuyển đổi bảng mã cũ và hỗ trợ đa ngôn ngữ.")

# ĐỊNH NGHĨA HỆ THỐNG CÁC TAB CHỨC NĂNG
tab1, tab2, tab3 = st.tabs([
    "🎨 Chuẩn Hóa & Căn Lề In", 
    "➕ Chức năng Word mới 1 (Sắp ra mắt)", 
    "➕ Chức năng Word mới 2 (Sắp ra mắt)"
])

# ==========================================
# TAB 1: CHUẨN HÓA & CĂN LỀ IN VĂN BẢN
# ==========================================
with tab1:
    st.subheader("🎨 Chuẩn hóa font chữ, chuyển đổi mã & Xử lý hàng loạt")
    st.write("Dọn sạch định dạng lỗi, tự động phát hiện đổi font tiếng Trung, sửa văn bản lỗi font TCVN3 và xuất file ZIP hàng loạt.")
    st.divider()

    # Khu vực Upload - CHO PHÉP TẢI LÊN NHIỀU FILE CÙNG LÚC (accept_multiple_files=True)
    uploaded_files = st.file_uploader(
        "Tải lên một hoặc nhiều tệp Word cần xử lý (.docx, .doc):", 
        type=["docx", "doc"],
        accept_multiple_files=True,
        key="word_uploader_tab1"
    )

    if uploaded_files: # Kiểm tra xem có danh sách file được up lên không
        st.success(f"📂 Đã nạp thành công **{len(uploaded_files)}** tệp văn bản.")
        
        # Kiểm tra nhanh xem có file .doc cũ nào lọt vào danh sách không
        has_doc_old_file = False
        for file in uploaded_files:
            if file.name.split(".")[-1].lower() == "doc":
                has_doc_old_file = True
                break
        
        if has_doc_old_file:
            st.error("⚠️ Danh sách tải lên của bạn có chứa file đuôi `.doc` đời cũ.")
            st.info(
                "💡 **Để tránh lỗi xử lý:** Bạn vui lòng mở các file đuôi `.doc` này lên bằng Word trên máy tính, "
                "chọn **Save As** và lưu lại dưới dạng file **.docx** rồi tải lại lên đây nhé!"
            )
        else:
            # GIAO DIỆN CẤU HÌNH THÔNG SỐ NÂNG CAO
            st.subheader("⚙️ Cấu hình thông số chuẩn hóa")
            
            # Chia làm 3 cột cấu hình thông minh
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
                # Hộp kiểm sửa lỗi bảng mã TCVN3 (.VnTime)
                auto_convert_tcvn = st.checkbox(
                    "Sửa lỗi bảng mã cũ (TCVN3 / .VnTime)",
                    value=False,
                    help="Tích chọn nếu tài liệu của khách hàng bị lỗi hiển thị font, chữ bị biến dạng giun dế khó đọc."
                )
                # Hộp kiểm nhận diện tiếng Trung
                detect_chinese = st.checkbox(
                    "Nhận dạng tự động & Đổi font tiếng Trung",
                    value=False,
                    help="Hệ thống tự nhận diện các ký tự tiếng Trung (Hanzi) để định hình font chữ chuẩn riêng biệt."
                )
                
                # Hiển thị chọn font Trung Quốc chỉ khi người dùng tích chọn nhận diện
                chinese_font = "SimSun"
                if detect_chinese:
                    chinese_font = st.selectbox(
                        "Chọn Font riêng cho tiếng Trung:",
                        options=["SimSun", "Microsoft YaHei", "KaiTi", "SimHei"],
                        index=0
                    )
            
            st.divider()
            
            # NÚT BẤM KÍCH HOẠT XỬ LÝ HÀNG LOẠT
            if st.button("🚀 Bắt đầu xử lý hàng loạt", type="primary"):
                processed_files = [] # Lưu danh sách file byte đã xử lý để nén ZIP
                error_files = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, file in enumerate(uploaded_files):
                    status_text.write(f"正在处理... Đang xử lý file ({idx+1}/{len(uploaded_files)}): `{file.name}`")
                    try:
                        # Gọi hàm xử lý backend
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
                    
                    # Cập nhật thanh tiến trình
                    progress_bar.progress(int((idx + 1) / len(uploaded_files) * 100))
                
                status_text.empty()
                progress_bar.empty()
                
                # Hiển thị báo cáo xử lý lỗi nếu có
                if error_files:
                    st.warning("⚠️ Một số file gặp lỗi trong quá trình xử lý:")
                    for err_file, err_msg in error_files:
                        st.write(f"- `{err_file}`: {err_msg}")
                
                # TIẾN HÀNH ĐÓNG GÓI ZIP NẾU CÓ THÀNH PHẨM THÀNH CÔNG
                if processed_files:
                    st.success(f"🎉 Đã xử lý thành công **{len(processed_files)}/{len(uploaded_files)}** file Word!")
                    
                    # Nếu chỉ xử lý 1 file duy nhất -> Cho tải trực tiếp file .docx
                    if len(processed_files) == 1:
                        single_name, single_stream = processed_files[0]
                        st.download_button(
                            label="📥 Tải xuống file Word hoàn chỉnh",
                            data=single_stream,
                            file_name=single_name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    # Nếu xử lý nhiều file -> Tự đóng gói thành file .zip để tải hàng loạt
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
# TAB 2: KHÔNG GIAN CHỜ CHỨC NĂNG MỚI 1
# ==========================================
with tab2:
    st.subheader("🛠️ Tính năng đang được phát triển")
    st.info("Khu vực này được thiết kế sẵn để bạn bổ sung các logic xử lý Word nâng cao tiếp theo. Khi có code mới, bạn chỉ cần viết code giao diện vào đây.")

# ==========================================
# TAB 3: KHÔNG GIAN CHỜ CHỨC NĂNG MỚI 2
# ==========================================
with tab3:
    st.subheader("🛠️ Tính năng nâng cao tương lai")
    st.info("Tab chờ số 3 sẵn sàng cho các bài toán như: Trích xuất bảng biểu từ Word, Trộn tài liệu tự động,...")