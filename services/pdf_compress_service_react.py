import fitz
import tempfile
import time
import os

def compress_pdf_logic(file_bytes, mode="normal"):
    """
    Xử lý nén file PDF từ bytes dữ liệu và trả về kết quả
    """
    timestamp = int(time.time())
    input_path = os.path.join(tempfile.gettempdir(), f"input_compress_{timestamp}.pdf")
    output_path = os.path.join(tempfile.gettempdir(), f"compressed_{mode}_{timestamp}.pdf")

    with open(input_path, "wb") as f:
        f.write(file_bytes)

    try:
        doc = fitz.open(input_path)

        if mode == "normal":
            doc.save(
                output_path,
                garbage=4,
                deflate=True,
                clean=True
            )
        else:
            doc.save(
                output_path,
                garbage=4,
                deflate=True,
                clean=True,
                deflate_images=True,
                deflate_fonts=True
            )

        old_size = round(os.path.getsize(input_path) / (1024 * 1024), 2)
        new_size = round(os.path.getsize(output_path) / (1024 * 1024), 2)

        doc.close()

        if os.path.exists(input_path):
            os.remove(input_path)

        # SỬA TẠI ĐÂY: Dùng chuỗi ASCII không chứa Emoji/Tiếng Việt có dấu
        info_msg = f"Compressed: {old_size} MB -> {new_size} MB"
        return output_path, info_msg, old_size, new_size

    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        return None, str(e), 0, 0