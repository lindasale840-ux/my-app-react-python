import streamlit as st
import tempfile
import math
import fitz
from PIL import Image
import io
from services.pdf_split_service import run_pdf_split_range
from services.pdf_merge_service import run_pdf_merge
from services.image_to_pdf_service import run_image_to_pdf
from backend.group_pdf_by_excel_column import group_pdf_by_excel_column
import pandas as pd
from services.image_to_pdf_ocr_service import (
    run_image_to_pdf_ocr
)

from services.pdf_compress_service import (
    run_pdf_compress
)

from services.pdf_reduce_v2_service import (
    run_pdf_reduce_v2
)

from services.pdf_version_service import (
    run_pdf_version_downgrade
)

from services.remove_blank_page_service import (
    run_remove_blank_last_page
)

from services.remove_blank_pages_v2_service import (
    run_remove_blank_pages_batch
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

st.title("🛠️ TIỆN ÍCH PDF")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "Ghép PDF",
    "Tách PDF",
    "Ảnh → PDF",
    "Nén PDF",
    "Giảm dung lượng",
    "Hạ phiên bản PDF",
    "Xoá trang trắng",
    "Xếp chung thư mục theo GCN",
    "Đối chiếu Excel & PDF 🎯",
    "📦 Gom & Nén PDF Theo Danh Sách Excel"
])

# ==================================================
# TAB 1 - GHÉP PDF
# ==================================================

with tab1:

    st.subheader("📎 Ghép nhiều file PDF")

    uploaded_files = st.file_uploader(
        "Chọn các file PDF",
        type=["pdf"],
        accept_multiple_files=True
    )

    st.info(
        "Thứ tự file trong danh sách sẽ là thứ tự ghép."
    )

    if st.button(
        "🚀 Ghép PDF",
        key="merge_pdf"
    ):

        if not uploaded_files:

            st.error("Vui lòng chọn file PDF")

            st.stop()

        temp_paths = []

        for file in uploaded_files:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as tmp:

                tmp.write(file.getvalue())

                temp_paths.append(tmp.name)

        with st.spinner("Đang ghép PDF..."):

            output_pdf, msg = run_pdf_merge(
                temp_paths
            )

        if output_pdf:

            st.success(msg)

            with open(output_pdf, "rb") as f:

                st.download_button(
                    label="📥 Tải PDF đã ghép",
                    data=f.read(),
                    file_name="Merged.pdf",
                    mime="application/pdf"
                )

        else:

            st.error(msg)

# ==================================================
# TAB 2-7 (tạm thời placeholder)
# ==================================================
# Giữ nguyên hàm cache của bạn
@st.cache_data(show_spinner=False)
def get_thumbnail(pdf_bytes, page_num, zoom=0.25):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    doc.close()
    return img

def next_thumb_page():
    if st.session_state.thumb_page < st.session_state.total_thumb_pages:
        st.session_state.thumb_page += 1


def prev_thumb_page():
    if st.session_state.thumb_page > 1:
        st.session_state.thumb_page -= 1
  
def reset_split_state():
    """Xóa toàn bộ bộ nhớ tạm của file cũ khi người dùng upload file mới hoặc bấm X xóa file"""
    if "cut_pages" in st.session_state:
        st.session_state.cut_pages = []
    if "split_pdf_path" in st.session_state:
        # Nếu muốn xóa triệt để file tạm trong ổ cứng để đỡ nặng máy:
        import os
        try:
            if os.path.exists(st.session_state.split_pdf_path):
                os.remove(st.session_state.split_pdf_path)
        except:
            pass
        del st.session_state.split_pdf_path
    if "thumb_page" in st.session_state:
        st.session_state.thumb_page = 1        
        
# ==========================================
#  ĐOẠN CODE TRONG TAB 2
# ==========================================
with tab2:
    st.subheader("✂️ Tách PDF theo điểm cắt")

    uploaded_pdf = st.file_uploader(
        "Chọn PDF",
        type=["pdf"],
        key="split_pdf",
        on_change=reset_split_state
    )

    if uploaded_pdf:
        if "split_pdf_path" not in st.session_state:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_pdf.getvalue())
                st.session_state.split_pdf_path = tmp.name

        pdf_path = st.session_state.split_pdf_path
        pdf_bytes = uploaded_pdf.getvalue()

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        doc.close()

        st.info(f"Tổng số trang: {total_pages}")

        if "cut_pages" not in st.session_state:
            st.session_state.cut_pages = []

        # ==========================
        # PAGINATION THUMBNAIL
        # ==========================
        thumb_per_page = 50
        total_thumb_pages = max(1, math.ceil(total_pages / thumb_per_page))
        st.session_state.total_thumb_pages = total_thumb_pages

        col1, col2, col3 = st.columns([2, 2, 6])

        if "thumb_page" not in st.session_state:
            st.session_state.thumb_page = 1

        with col1:
            st.number_input(
                "Trang preview",
                min_value=1,
                max_value=total_thumb_pages,
                key="thumb_page"
            )

        thumb_page = st.session_state.thumb_page

        with col2:
            st.markdown(
                f"<div style='margin-top:32px'>{total_thumb_pages} trang preview</div>",
                unsafe_allow_html=True
            )

        start_idx = (thumb_page - 1) * thumb_per_page
        end_idx = min(start_idx + thumb_per_page, total_pages)

        # =============================================================
        # BỌC LƯỚI ẢNH VÀ TOGGLE VÀO TRONG ST.FORM
        # Người dùng có thể bấm thoải mái 50 toggle mà không bị load lại trang
        # =============================================================
        with st.form(key="pdf_cut_nodes_form"):
            st.markdown("### Chọn các trang kết thúc hồ sơ")
            cols = st.columns(4)
            
            # Tạo một dictionary tạm để lưu trạng thái toggle hiện tại trong form
            current_form_states = {}

            for idx in range(start_idx, end_idx):
                from utils.pdf_thumbnail_cache import get_thumbnail
                img = get_thumbnail(pdf_bytes, idx)

                with cols[(idx - start_idx) % 4]:
                    st.image(img, caption=f"Trang {idx + 1}")

                    # Lưu trạng thái toggle vào dictionary tạm, key là số trang thực tế (idx + 1)
                    current_form_states[idx + 1] = st.toggle(
                        "✂ Cắt tại đây",
                        value=(idx + 1 in st.session_state.cut_pages),
                        key=f"cut_{idx}"
                    )

            st.markdown("<br>", unsafe_allow_html=True)
            # Nút submit bắt buộc của Form để áp dụng các điểm cắt
            submit_cuts = st.form_submit_button("💾 Xác nhận & Lưu điểm cắt của trang này")

            if submit_cuts:
                # Duyệt qua các toggle trong form và cập nhật chính xác vào cut_pages gốc
                for page_num, checked in current_form_states.items():
                    if checked:
                        if page_num not in st.session_state.cut_pages:
                            st.session_state.cut_pages.append(page_num)
                    else:
                        if page_num in st.session_state.cut_pages:
                            st.session_state.cut_pages.remove(page_num)
                
                # Ép ứng dụng rerun một lần duy nhất để cập nhật bảng "Khoảng trang tự sinh" bên dưới
                st.rerun()

        # =============================================================
        # KẾT THÚC VÙNG FORM
        # =============================================================

        st.markdown("---")

        # Nút chuyển trang preview lớn (Nằm ngoài form)
        col_prev, col_next = st.columns(2)
        with col_prev:
            st.button(
                "⬅ Previous",
                on_click=prev_thumb_page,
                key="prev_thumb_page"
            )
        with col_next:
            st.button(
                "Next ➡",
                on_click=next_thumb_page,
                key="next_thumb_page"
            )
                    
        # Xử lý hiển thị khoảng trang tự sinh (Giữ nguyên logic của bạn)
        cut_pages = sorted(st.session_state.cut_pages)
        
        if cut_pages:
            cut_pages = sorted(list(set(cut_pages)))
            ranges = []
            start_page = 1

            for end_page in cut_pages:
                ranges.append(f"{start_page}-{end_page}")
                start_page = end_page + 1

            if start_page <= total_pages:
                ranges.append(f"{start_page}-{total_pages}")

            generated_text = "\n".join(ranges)

            st.markdown("### Khoảng trang tự sinh")
            st.code(generated_text)
        else:
            generated_text = ""
            st.warning("Chưa chọn điểm cắt nào")

        st.markdown("---")

        # Nút bấm tiến hành Tách PDF (Giữ nguyên logic của bạn)
        if st.button("🚀 Tách PDF", key="split_by_checkbox"):
            if not generated_text:
                st.error("Vui lòng chọn ít nhất 1 điểm cắt")
                st.stop()

            with st.spinner("Đang tách PDF..."):
                zip_path, msg = run_pdf_split_range(
                    pdf_path,
                    generated_text
                )

            if zip_path:
                st.session_state.cut_pages = []
                st.success(msg)

                with open(zip_path, "rb") as f:
                    st.download_button(
                        "📥 Tải ZIP",
                        data=f.read(),
                        file_name="Split.zip",
                        mime="application/zip"
                    )
            else:
                st.error(msg)
                
with tab3:

    st.subheader(
        "🖼️ Ảnh → PDF"
    )

    uploaded_images = st.file_uploader(
        "Chọn ảnh",
        type=[
            "jpg",
            "jpeg",
            "png",
            "bmp",
            "webp"
        ],
        accept_multiple_files=True,
        key="image_to_pdf"
    )

    if uploaded_images:

        st.success(
            f"Đã chọn {len(uploaded_images)} ảnh"
        )

        st.markdown("### Preview")

        cols = st.columns(4)

        for i, img_file in enumerate(uploaded_images):

            image = Image.open(img_file)

            with cols[i % 4]:

                st.image(
                    image,
                    caption=f"{i+1}"
                )

        st.markdown("---")

        reverse_order = st.checkbox(
            "Đảo ngược thứ tự ảnh"
        )

        ocr_mode = st.checkbox(
            "🔍 OCR PDF (tìm kiếm được)"
        )
        paper_size = st.selectbox(
            "Khổ giấy",
            [
                "Giữ nguyên",
                "A4",
                "A5"
            ]
        )

        orientation = st.selectbox(
            "Chiều giấy",
            [
                "Tự động",
                "Dọc",
                "Ngang"
            ]
        )

    if st.button(
        "🚀 Chuyển thành PDF",
        key="convert_image_pdf"
    ):

        if not uploaded_images:

            st.error(
                "Vui lòng chọn ảnh"
            )

            st.stop()

        temp_paths = []

        for img in uploaded_images:

            suffix = "." + img.name.split(".")[-1]

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix
            ) as tmp:

                tmp.write(
                    img.getvalue()
                )

                temp_paths.append(
                    tmp.name
                )

        with st.spinner(
            "Đang tạo PDF..."
        ):

            if ocr_mode:

                pdf_path, msg = run_image_to_pdf_ocr(
                    temp_paths
                )

            else:

                pdf_path, msg = run_image_to_pdf(
                    image_paths=temp_paths,
                    paper_size=paper_size,
                    orientation=orientation
                )

        if pdf_path:

            st.success(msg)

            with open(
                pdf_path,
                "rb"
            ) as f:

                st.download_button(
                    "📥 Tải PDF",
                    data=f.read(),
                    file_name="Images.pdf",
                    mime="application/pdf"
                )

        else:

            st.error(msg)

with tab4:

    st.subheader(
        "📦 Nén PDF"
    )

    uploaded_pdf = st.file_uploader(
        "Chọn PDF",
        type=["pdf"],
        key="compress_pdf"
    )

    if st.button(
        "🚀 Nén PDF",
        key="compress_btn"
    ):

        if not uploaded_pdf:

            st.error(
                "Vui lòng chọn PDF"
            )

            st.stop()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as tmp:

            tmp.write(
                uploaded_pdf.getvalue()
            )

            pdf_path = tmp.name

        output_pdf, msg = run_pdf_compress(
            pdf_path,
            mode="normal"
        )

        st.success(msg)

        with open(
            output_pdf,
            "rb"
        ) as f:

            st.download_button(
                "📥 Tải PDF",
                f.read(),
                "Compressed.pdf",
                "application/pdf"
            )

with tab5:

    st.subheader(
        "🪶 Giảm dung lượng PDF"
    )

    uploaded_pdf = st.file_uploader(
        "Chọn PDF",
        type=["pdf"],
        key="reduce_pdf"
    )

    dpi = st.selectbox(
        "Mức giảm",
        [
            150,
            120,
            100
        ]
    )

    quality = st.selectbox(
        "Chất lượng ảnh",
        [
            80,
            70,
            60
        ]
    )

    if st.button(
        "🚀 Giảm dung lượng",
        key="reduce_btn_v2"
    ):

        if not uploaded_pdf:

            st.error(
                "Vui lòng chọn PDF"
            )

            st.stop()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as tmp:

            tmp.write(
                uploaded_pdf.getvalue()
            )

            pdf_path = tmp.name

        with st.spinner(
            "Đang giảm dung lượng..."
        ):

            output_pdf, msg = run_pdf_reduce_v2(
                pdf_path,
                dpi=dpi,
                jpeg_quality=quality
            )

        if output_pdf:

            st.success(msg)

            with open(
                output_pdf,
                "rb"
            ) as f:

                st.download_button(
                    "📥 Tải PDF",
                    f.read(),
                    "Reduced_V2.pdf",
                    "application/pdf"
                )

        else:

            st.error(msg)
with tab6:

    st.subheader(
        "📄 Hạ phiên bản PDF"
    )

    uploaded_pdf = st.file_uploader(
        "Chọn PDF",
        type=["pdf"],
        key="pdf_version"
    )

    compatibility = st.selectbox(
        "Phiên bản PDF đích",
        [
            "1.3",
            "1.4",
            "1.5",
            "1.6",
            "1.7"
        ]
    )

    st.info(
        "PDF 1.4 tương thích rất tốt với các phần mềm cũ."
    )

    if st.button(
        "🚀 Hạ phiên bản PDF",
        key="version_btn"
    ):

        if not uploaded_pdf:

            st.error(
                "Vui lòng chọn PDF"
            )

            st.stop()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as tmp:

            tmp.write(
                uploaded_pdf.getvalue()
            )

            pdf_path = tmp.name

        with st.spinner(
            "Đang chuyển đổi..."
        ):

            output_pdf, msg = (
                run_pdf_version_downgrade(
                    pdf_path,
                    compatibility
                )
            )

        if output_pdf:

            st.success(msg)

            with open(
                output_pdf,
                "rb"
            ) as f:

                st.download_button(
                    "📥 Tải PDF",
                    data=f.read(),
                    file_name=f"PDF_v{compatibility}.pdf",
                    mime="application/pdf"
                )

        else:

            st.error(msg)

with tab7:
    st.subheader("🧹 Xóa trang trắng (Hàng loạt trực tiếp từ RAM)")

    uploaded_pdfs = st.file_uploader(
        "Chọn các file PDF cần lọc trang trắng",
        type=["pdf"],
        accept_multiple_files=True,
        key="remove_blank_batch"
    )

    threshold = st.slider(
        "Mật độ điểm trắng tối thiểu để coi là trang trống (%)",
        95.0, 100.0, 98.0, 0.1,
        help="98% có nghĩa là nếu trang giấy có trên 98% là màu trắng (chỉ có dưới 2% vết mực/nhiễu/logo), trang đó sẽ bị xóa."
    )

    if uploaded_pdfs:
        st.info(f"📁 Đã chọn {len(uploaded_pdfs)} tệp tin.")

    if st.button("🚀 Xử lý xóa trang trắng hàng loạt", key="remove_blank_batch_btn"):
        if not uploaded_pdfs:
            st.error("⚠️ Vui lòng chọn ít nhất 1 file PDF.")
            st.stop()

        with st.spinner("⏳ Hệ thống đang dựng ảnh và phân tích mật độ mực từng trang..."):
            try:
                # 🔥 ĐÃ SỬA: Truyền trực tiếp mảng file upload nhị phân từ RAM (Không tạo file tạm nữa)
                # Chia cho 100 để đổi từ % (98.0) về dạng thập phân (0.98) khớp với Backend
                zip_buffer, report = run_remove_blank_pages_batch(uploaded_pdfs, threshold / 100.0)
                
                st.success("🎉 Đã lọc sạch các trang trống hoàn tất!")
                st.text_area("📊 Báo cáo chi tiết kết quả lọc:", report, height=200)

                if zip_buffer:
                    st.download_button(
                        label="📥 Tải về file nén kết quả (.ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="BlankRemoved_RAM.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
            except Exception as e:
                st.exception(e)
            
with tab8: # Hoặc tab8 tùy bạn đặt tên
    st.subheader("📂 Phân loại & Gom nhóm PDF theo danh mục Excel như (CHERVON)")
    st.write("Đối chiếu tên file PDF (Mã GCN) with Excel để tự động nhóm vào từng Folder riêng biệt.")

    # 1. Upload files
    uploaded_excel = st.file_uploader("1. Chọn file Excel danh mục đối chiếu", type=["xlsx", "xls"], key="group_excel")
    uploaded_pdfs = st.file_uploader("2. Chọn các file PDF cần gom nhóm (Chọn nhiều file cùng lúc)", type=["pdf"], accept_multiple_files=True, key="group_pdfs")

    if uploaded_excel and uploaded_pdfs:
        if "tmp_excel_group_path" not in st.session_state:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_excel.getvalue())
                st.session_state.tmp_excel_group_path = tmp.name
        
        excel_path = st.session_state.tmp_excel_group_path

        try:
            df_preview = pd.read_excel(excel_path, header=None, nrows=5).fillna("")
            column_options = {f"Cột {i} (Ví dụ: {df_preview.iloc[0, i] if len(df_preview) > 0 else ''})": i for i in range(df_preview.shape[1])}
        except Exception as e:
            st.error(f"Không thể đọc file Excel: {e}")
            st.stop()

        # Tạo sẵn các biến lưu trạng thái trong session_state nếu chưa có
        if "group_zip_path" not in st.session_state:
            st.session_state.group_zip_path = None
        if "group_msg" not in st.session_state:
            st.session_state.group_msg = ""

        # =============================================================
        # BỌC PHẦN LỰA CHỌN CỘT VÀ NÚT CHẠY VÀO TRONG ST.FORM
        # =============================================================
        with st.form(key="pdf_grouping_form"):
            st.markdown("### 🛠 Cấu hình đối chiếu")
            
            col_match, col_target = st.columns(2)
            with col_match:
                match_col_label = st.selectbox(
                    "Cột chứa mã Giấy chứng nhận (khớp với tên file PDF):", 
                    options=list(column_options.keys()),
                    index=25 if 25 < len(column_options) else 0
                )
            with col_target:
                target_col_label = st.selectbox(
                    "Cột cần trả về (Dùng để đặt tên Folder gom nhóm):", 
                    options=list(column_options.keys()),
                    index=5 if 5 < len(column_options) else 0
                )

            match_col_idx = column_options[match_col_label]
            target_col_idx = column_options[target_col_label]

            st.markdown("<br>", unsafe_allow_html=True)
            submit_grouping = st.form_submit_button("🚀 Tiến hành Gom nhóm & Nén ZIP")

            if submit_grouping:
                with st.spinner("Hệ thống đang đối chiếu dữ liệu và nhóm thư mục..."):
                    # CHẠY LOGIC VÀ LƯU KẾT QUẢ VÀO SESSION STATE
                    zip_path, msg = group_pdf_by_excel_column(
                        uploaded_pdfs, 
                        excel_path, 
                        match_col_idx, 
                        target_col_idx
                    )
                    st.session_state.group_zip_path = zip_path
                    st.session_state.group_msg = msg

        # =============================================================
        # KẾT THÚC VÙNG FORM -> ĐẶT NÚT DOWNLOAD Ở ĐÂY (BÊN NGOÀI FORM)
        # =============================================================
        
        # Kiểm tra xem nếu session_state đã có file zip thì hiển thị ra màn hình ngoài
        if st.session_state.group_zip_path:
            st.success(st.session_state.group_msg)
            with open(st.session_state.group_zip_path, "rb") as f:
                st.download_button(
                    label="📥 Tải xuống File ZIP kết quả",
                    data=f.read(),
                    file_name="Ket_Qua_Gom_Nhom_PDF.zip",
                    mime="application/zip"
                )
                
with tab9:
    st.header("🔍 Đối chiếu danh sách Excel với File PDF Upload")
    st.write("Tải lên file Excel và các file PDF để kiểm tra xem mã Giấy chứng nhận nào trong Excel đang bị thiếu.")

    import io
    from backend.pdf_check_cert import check_excel_vs_pdf_uploaded

    # Kéo thả file trực tiếp
    col1, col2 = st.columns(2)
    with col1:
        uploaded_excel = st.file_uploader("📥 Chọn file Excel danh sách:", type=["xlsx", "xls"], key="chk_excel_file")
    with col2:
        uploaded_pdfs = st.file_uploader("📥 Chọn các file PDF cần đối chiếu (Chọn nhiều file):", type=["pdf"], accept_multiple_files=True, key="chk_pdf_files")

    col3, col4 = st.columns(2)
    with col3:
        column_index = st.number_input("Chỉ số cột chứa mã GCN (Cột Z là 25):", min_value=0, value=25, step=1)
    with col4:
        pdf_type = st.radio("Loại tệp PDF tải lên:", ["PDF Văn bản (Digital)", "PDF Scan (Cần chạy OCR)"], horizontal=True)

    if st.button("🚀 Bắt đầu đối chiếu chính xác", type="primary"):
        if not uploaded_excel:
            st.error("⚠️ Vui lòng tải lên file Excel danh sách!")
        elif not uploaded_pdfs:
            st.error("⚠️ Vui lòng tải lên ít nhất một file PDF để đối chiếu!")
        else:
            with st.spinner("🔄 Đang xử lý dữ liệu và đối chiếu... Vui lòng đợi trong giây lát!"):
                is_scan = (pdf_type == "PDF Scan (Cần chạy OCR)")
                
                # Gọi hàm xử lý từ bộ nhớ RAM
                results = check_excel_vs_pdf_uploaded(
                    uploaded_pdfs=uploaded_pdfs,
                    uploaded_excel=uploaded_excel,
                    column_index=int(column_index),
                    is_scan=is_scan
                )

                # =========================================================
                # 🛠 XỬ LÝ SỬA LỖI 1: LOẠI BỎ DÒNG HEADER TIÊU ĐỀ
                # =========================================================
                # Đọc lại dòng đầu tiên của cột để biết chính xác chữ tiêu đề là gì
                try:
                    uploaded_excel.seek(0)
                    df_raw_header = pd.read_excel(uploaded_excel, header=None, nrows=1, dtype=str)
                    header_value = str(df_raw_header.iloc[0, int(column_index)]).strip().upper()
                except:
                    header_value = ""

                # Lọc danh sách thiếu: bỏ qua chữ trùng với tiêu đề cột
                clean_missing = [x for x in results['missing'] if x.upper() != header_value and "MÃ" not in x.upper() and "CHỨNG NHẬN" not in x.upper()]
                
                # Tính toán lại các con số sau khi đã trừ đi dòng header
                actual_total_excel = results['total_excel'] - 1 if header_value in results['missing'] else results['total_excel']
                actual_missing_count = len(clean_missing)
                actual_matched = actual_total_excel - actual_missing_count

                # Hiển thị kết quả trực quan
                st.success(f"📊 Đã kiểm tra xong {results['total_files_scanned']} file PDF bạn tải lên!")
                
                metric1, metric2, metric3 = st.columns(3)
                metric1.metric("Tổng mã trong Excel", actual_total_excel)
                metric2.metric("Tìm thấy trong PDF", actual_matched)
                metric3.metric("Bị thiếu / Không khớp", actual_missing_count, delta_color="inverse")

                st.write("---")
                if clean_missing:
                    st.warning(f"⚠️ Phát hiện {actual_missing_count} mã có trong Excel nhưng KHÔNG TÌM THẤY file PDF tương ứng:")
                    
                    # Tạo dataframe để hiển thị lên giao diện
                    df_missing = pd.DataFrame(clean_missing, columns=["Mã GCN Bị Thiếu"])
                    st.dataframe(df_missing, use_container_width=True)

                    # =========================================================
                    # 🛠 XỬ LÝ YÊU CẦU 2: TẠO NÚT DOWNLOAD FILE EXCEL KẾT QUẢ
                    # =========================================================
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_missing.to_excel(writer, index=False, sheet_name='Ket_Qua_Thieu')
                    
                    st.download_button(
                        label="📥 Tải về file Excel kết quả thiếu",
                        data=buffer.getvalue(),
                        file_name="Danh_sach_GCN_bi_thieu.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="secondary"
                    )
                else:
                    st.balloons()
                    st.success("🎉 Tuyệt vời! Tất cả các mã định danh trong Excel đều trùng khớp hoàn toàn với các file PDF bạn đã tải lên!")
                    
with tab10:
    st.header("📦 Gom & Nén PDF Theo Danh Sách Excel")
    st.write("Tìm các file PDF có tên nằm trong danh sách Excel, gộp lại và đóng gói thành file ZIP.")

    import os
    import zipfile
    import shutil
    import pandas as pd

    # 1. Nhập thông tin đầu vào cơ bản
    col1, col2 = st.columns(2)
    with col1:
        excel_file = st.file_uploader("👉 Chọn file Excel danh sách:", type=["xlsx", "xls"], key="excel_tab10_v2")
    with col2:
        folder_path = st.text_input("📁 Nhập đường dẫn thư mục chứa các file PDF:", placeholder="Ví dụ: D:/ChungNhan/PDF_Goc", key="folder_tab10_v2")

    if excel_file and folder_path:
        try:
            df = pd.read_excel(excel_file)
            columns = df.columns.tolist()
            
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                selected_col = st.selectbox("🎯 Chọn cột chứa Mã Giấy Chứng Nhận:", columns)
            with col_sel2:
                zip_name = st.text_input("📝 Tên file nén ZIP đầu ra:", value="Ket_Qua_Gom_PDF")

            # =========================================================
            # 🔥 CHỨC NĂNG NÂNG CAO DÀNH CHO KHÁCH HÀNG KHÓ TÍNH
            # =========================================================
            st.markdown("---")
            advanced_mode = st.checkbox("⚙️ Kích hoạt chế độ phân loại thư mục chuyên sâu trước khi nén")
            
            cut_length = 9 # Giá trị mặc định theo ví dụ của bạn
            if advanced_mode:
                st.info("💡 Hệ thống sẽ dựa vào Mã Chứng Nhận trong Excel để tạo các thư mục con tương ứng, sau đó sao chép file vào từng thư mục rồi mới tiến hành nén lại.")
                cut_length = st.number_input(
                    "✂️ Nhập số ký tự đầu của mã để đặt tên thư mục gốc:", 
                    min_value=1, 
                    max_value=50, 
                    value=9,
                    help="Ví dụ: Mã 'RIV-00C-D-I-0014' lấy 9 ký tự đầu sẽ tạo thư mục 'RIV-00C-D'"
                )
            st.markdown("---")
            # =========================================================

            if st.button("🚀 Tiến hành Gom và Nén File", type="primary", key="btn_run_tab10"):
                if not os.path.exists(folder_path):
                    st.error("❌ Đường dẫn thư mục không tồn tại! Vui lòng kiểm tra lại.")
                else:
                    excel_codes = df[selected_col].dropna().astype(str).str.strip().unique()
                    all_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
                    
                    matched_files = [] # Lưu tuple: (đường_dẫn_file_gốc, tên_thư_mục_con)
                    missing_codes = []

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # 1. Tiến hành đối chiếu và phân nhóm
                    for index, code in enumerate(excel_codes):
                        percent = int((index + 1) / len(excel_codes) * 100)
                        progress_bar.progress(percent)
                        status_text.text(f"🔍 Đang đối chiếu mã: {code}")

                        # Xác định tên thư mục con nếu bật chế độ nâng cao
                        subfolder_name = ""
                        if advanced_mode:
                            # Cắt lấy số ký tự theo cấu hình, nếu mã ngắn hơn thì lấy toàn bộ mã
                            subfolder_name = code[:cut_length].strip()
                        
                        found = False
                        for file_name in all_files:
                            if code in file_name:
                                file_full_path = os.path.join(folder_path, file_name)
                                matched_files.append((file_full_path, subfolder_name))
                                found = True
                        
                        if not found:
                            missing_codes.append(code)

                    # 2. Xử lý đóng gói (ZIP)
                    if matched_files:
                        output_zip_path = os.path.join(folder_path, f"{zip_name}.zip")
                        status_text.text("📦 Đang tiến hành cấu trúc cây thư mục và nén ZIP...")
                        
                        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            for file_path, subfolder in matched_files:
                                base_name = os.path.basename(file_path)
                                
                                if advanced_mode and subfolder:
                                    # Nếu có chế độ nâng cao, đặt file bên trong đường dẫn thư mục con
                                    archive_name = os.path.join(subfolder, base_name)
                                else:
                                    # Chế độ thường: xếp phẳng tất cả file ở thư mục gốc của file ZIP
                                    archive_name = base_name
                                    
                                zipf.write(file_path, archive_name)

                        # Hiển thị kết quả trực quan
                        st.success(f"🎉 Đã hoàn thành! Đã gom và phân loại {len(matched_files)} file PDF.")
                        st.info(f"💾 File nén cấu trúc thông minh đã lưu tại: `{output_zip_path}`")
                        
                        if missing_codes:
                            with st.expander(f"⚠️ Có {len(missing_codes)} mã trong Excel KHÔNG tìm thấy file PDF tương ứng"):
                                st.write(missing_codes)
                    else:
                        st.warning("😭 Không tìm thấy file PDF nào trùng khớp với danh sách trong Excel!")
                        
        except Exception as e:
            st.error(f"❌ Có lỗi xảy ra trong quá trình xử lý: {str(e)}")