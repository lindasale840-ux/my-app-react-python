import fitz
import tempfile
import zipfile
import time
import os
import base64

def get_pdf_thumbnails_logic(file_bytes):
    """
    Render toàn bộ trang PDF thành ảnh Thumbnail dạng Base64
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    thumbnails = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25)) # Scale nhỏ để load siêu nhanh
        img_bytes = pix.tobytes("png")
        base64_img = base64.b64encode(img_bytes).decode("utf-8")
        thumbnails.append(f"data:image/png;base64,{base64_img}")
        
    doc.close()
    return thumbnails

def split_pdf_by_ranges_logic(file_bytes, ranges_text):
    """
    Tách PDF theo danh sách các khoảng trang và đóng gói ZIP
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    timestamp = int(time.time())

    output_dir = os.path.join(tempfile.gettempdir(), f"split_range_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    zip_path = os.path.join(tempfile.gettempdir(), f"Split_Range_{timestamp}.zip")
    parts = []

    try:
        # SỬA TẠI ĐÂY: Chuyển chuỗi literal '\\n' hoặc '\r\n' thành ký tự xuống dòng chuẩn '\n'
        normalized_ranges = ranges_text.replace('\\n', '\n').replace('\r\n', '\n')

        for idx, line in enumerate(normalized_ranges.strip().splitlines(), start=1):
            line = line.strip()
            if not line:
                continue

            # Tách trang đầu và trang cuối theo dấu '-'
            start_page, end_page = map(int, line.split("-"))
            new_doc = fitz.open()
            new_doc.insert_pdf(
                doc,
                from_page=start_page - 1,
                to_page=end_page - 1
            )

            output_pdf = os.path.join(output_dir, f"Part_{idx}.pdf")
            new_doc.save(output_pdf)
            new_doc.close()
            parts.append(output_pdf)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for pdf_file in parts:
                zipf.write(pdf_file, os.path.basename(pdf_file))

        doc.close()
        return zip_path, f"✅ Đã tạo {len(parts)} file PDF"

    except Exception as e:
        doc.close()
        return None, str(e)