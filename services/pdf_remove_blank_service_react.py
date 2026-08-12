import fitz
import numpy as np
import io
import zipfile

def is_blank_page(page, dpi=100, threshold=0.98):
    """
    Thuật toán kiểm tra trang trống cải tiến:
    Cắt bỏ 25% diện tích Header (Logo/Tên công ty) để chỉ quét 75% phía dưới.
    """
    rect = page.rect
    width = rect.width
    height = rect.height
    
    y_start = height * 0.25
    search_region = fitz.Rect(0, y_start, width, height)
    
    text_in_region = page.get_text("text", clip=search_region).strip()
    if len(text_in_region) > 5:
        return False

    pix = page.get_pixmap(
        matrix=fitz.Matrix(dpi / 72, dpi / 72),
        colorspace=fitz.csGRAY,
        clip=search_region
    )

    img = np.frombuffer(pix.samples, dtype=np.uint8)

    if img.size == 0:
        return True

    white_ratio = np.sum(img > 245) / img.size
    return white_ratio >= threshold


def process_pdf_in_memory(file_bytes: bytes, threshold: float = 0.98):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    new_doc = fitz.open()
    removed_pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        if is_blank_page(page, threshold=threshold):
            removed_pages.append(page_num + 1)
            continue

        new_doc.insert_pdf(
            doc,
            from_page=page_num,
            to_page=page_num
        )

    if len(new_doc) == 0 and len(doc) > 0:
        new_doc.insert_pdf(doc, from_page=0, to_page=0)
        if 1 in removed_pages:
            removed_pages.remove(1)

    output_pdf_bytes = new_doc.tobytes()
    
    new_doc.close()
    doc.close()

    return output_pdf_bytes, removed_pages


def run_remove_blank_pages_batch(files_data: list, threshold: float = 0.98):
    """
    files_data là danh sách tuple: [(file_name, file_bytes), ...]
    Nếu chỉ có 1 file -> trả về trực tiếp file_bytes PDF
    Nếu có nhiều file -> đóng gói ZIP trên RAM
    """
    if len(files_data) == 1:
        file_name, file_bytes = files_data[0]
        clean_bytes, removed = process_pdf_in_memory(file_bytes, threshold)
        info_msg = f"{file_name}: Đã xóa các trang số [{', '.join(map(str, removed)) if removed else 'Không có'}]"
        return clean_bytes, info_msg, "application/pdf", f"cleaned_{file_name}"

    zip_buffer = io.BytesIO()
    summary_lines = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_name, file_bytes in files_data:
            clean_bytes, removed = process_pdf_in_memory(file_bytes, threshold)
            zipf.writestr(f"cleaned_{file_name}", clean_bytes)
            removed_str = ", ".join(map(str, removed)) if removed else "Không có"
            summary_lines.append(f"• {file_name}: Đã xóa trang [{removed_str}]")

    zip_buffer.seek(0)
    return zip_buffer.getvalue(), "\n".join(summary_lines), "application/zip", "cleaned_pdfs.zip"