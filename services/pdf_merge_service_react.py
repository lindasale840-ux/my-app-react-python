import fitz
import tempfile
import time
import os

def merge_pdfs_logic(upload_files):
    """
    upload_files: Danh sách file nhận từ API
    """
    if not upload_files:
        return None, "Không có file PDF"

    merged_pdf = fitz.open()

    try:
        for file in upload_files:
            # Đọc trực tiếp byte stream từ file upload
            pdf_bytes = file.file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            merged_pdf.insert_pdf(doc)
            doc.close()

        timestamp = int(time.time())
        output_pdf = os.path.join(
            tempfile.gettempdir(),
            f"Merged_{timestamp}.pdf"
        )

        merged_pdf.save(output_pdf)
        merged_pdf.close()

        return output_pdf, f"✅ Ghép thành công {len(upload_files)} file PDF"

    except Exception as e:
        return None, str(e)