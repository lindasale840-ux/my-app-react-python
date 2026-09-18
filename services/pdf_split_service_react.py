import fitz
import tempfile
import zipfile
import time
import os
import base64
from pypdf import PdfReader, PdfWriter
from io import BytesIO
import re
import json

def get_pdf_thumbnails_logic(file_bytes):
    """
    Render toàn bộ trang PDF thành ảnh Thumbnail dạng Base64
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    thumbnails = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # 🟢 ĐÃ SỬA: Tăng Matrix từ (0.25, 0.25) lên (1.5, 1.5)
        # Giúp tăng độ phân giải lên gấp 6 lần, kính lúp soi chữ cực kỳ nét không bị vỡ!
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
        
        img_bytes = pix.tobytes("png")
        base64_img = base64.b64encode(img_bytes).decode("utf-8")
        thumbnails.append(f"data:image/png;base64,{base64_img}")
        
    doc.close()
    return thumbnails

def sanitize_filename(filename: str) -> str:
    """Làm sạch tên file, loại bỏ ký tự không hợp lệ trên Windows/Linux"""
    filename = re.sub(r'[\\/*?:"<>|]', "", filename).strip()
    return filename if filename else "Split_Document"

def split_pdf_by_ranges_logic(file_bytes: bytes, ranges_text: str):
    """
    Tách PDF theo dải trang và đặt tên tùy chỉnh.
    Giữ nguyên tên hàm và tên biến trả về (zip_path, message).
    """
    try:
        reader = PdfReader(BytesIO(file_bytes))
        total_pages = len(reader.pages)
        
        # Danh sách chứa cấu trúc: [{"start": int, "end": int, "name": str}]
        items_to_process = []

        # 1. Thử parse dạng JSON mới (Frontend gửi dải trang + tên file)
        try:
            parsed_data = json.loads(ranges_text)
            if isinstance(parsed_data, list):
                for item in parsed_data:
                    # Hỗ trợ nhận 'range' (hoặc 'range_str') và 'name'
                    r_str = item.get("range", "")
                    custom_name = item.get("name", "").strip()
                    
                    if "-" in r_str:
                        parts = r_str.split("-")
                        start_p, end_p = int(parts[0]), int(parts[1])
                    else:
                        start_p = end_p = int(r_str)
                        
                    items_to_process.append({
                        "start": start_p,
                        "end": end_p,
                        "name": custom_name
                    })
        except Exception:
            # 2. Fallback: Nếu không phải JSON, parse dạng chuỗi cũ "1-3, 4-8, 9-12"
            raw_ranges = [r.strip() for r in ranges_text.split(",") if r.strip()]
            for idx, r_str in enumerate(raw_ranges, start=1):
                if "-" in r_str:
                    parts = r_str.split("-")
                    start_p, end_p = int(parts[0]), int(parts[1])
                else:
                    start_p = end_p = int(r_str)
                items_to_process.append({
                    "start": start_p,
                    "end": end_p,
                    "name": f"Phan_{idx}"  # Tên mặc định nếu chạy dạng cũ
                })

        if not items_to_process:
            return None, "Không tìm thấy dải trang hợp lệ để tách!"

        # Tạo thư mục tạm để chứa các file PDF đã tách
        temp_dir = tempfile.mkdtemp()
        created_files = []

        for idx, item in enumerate(items_to_process, start=1):
            start_p = item["start"]
            end_p = item["end"]
            raw_name = item["name"]

            # Kiểm tra giới hạn trang hợp lệ
            if start_p < 1 or end_p > total_pages or start_p > end_p:
                continue

            writer = PdfWriter()
            # pypdf tính trang từ 0 nên cần -1
            for p_num in range(start_p - 1, end_p):
                writer.add_page(reader.pages[p_num])

            # Chuẩn hóa tên file
            clean_name = sanitize_filename(raw_name) if raw_name else f"File_{idx}"
            if not clean_name.lower().endswith(".pdf"):
                clean_name += ".pdf"

            output_file_path = os.path.join(temp_dir, clean_name)
            
            # Tránh trùng tên file trong cùng zip
            dup_count = 1
            base_name, ext = os.path.splitext(clean_name)
            while os.path.exists(output_file_path):
                output_file_path = os.path.join(temp_dir, f"{base_name}_{dup_count}{ext}")
                dup_count += 1

            with open(output_file_path, "wb") as f_out:
                writer.write(f_out)
            
            created_files.append(output_file_path)

        if not created_files:
            return None, "Không thể tạo file PDF nào từ dải trang đã chọn!"

        # Nén tất cả file PDF thành 1 file ZIP
        zip_path = os.path.join(temp_dir, "Split_Results.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for f_path in created_files:
                zipf.write(f_path, arcname=os.path.basename(f_path))

        return zip_path, "Tách và đặt tên file thành công!"

    except Exception as e:
        return None, f"Lỗi xử lý PDF: {str(e)}"