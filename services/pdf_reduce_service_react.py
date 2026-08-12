import fitz
import os
import tempfile
import time
from PIL import Image
import io

def reduce_pdf_logic(file_bytes, dpi=120, jpeg_quality=70):
    """
    Giảm dung lượng PDF bằng cách rasterize các trang thành ảnh JPEG tối ưu
    """
    timestamp = int(time.time())
    input_path = os.path.join(tempfile.gettempdir(), f"input_reduce_{timestamp}.pdf")
    output_pdf = os.path.join(tempfile.gettempdir(), f"reduced_v2_{timestamp}.pdf")

    with open(input_path, "wb") as f:
        f.write(file_bytes)

    try:
        doc = fitz.open(input_path)
        new_pdf = fitz.open()

        for page_num in range(len(doc)):
            page = doc[page_num]

            pix = page.get_pixmap(
                matrix=fitz.Matrix(dpi / 72, dpi / 72),
                alpha=False
            )

            img = Image.open(io.BytesIO(pix.tobytes("jpg")))
            temp_img = io.BytesIO()

            img.save(
                temp_img,
                format="JPEG",
                quality=jpeg_quality,
                optimize=True
            )

            rect = fitz.Rect(0, 0, img.width, img.height)
            pdf_page = new_pdf.new_page(width=img.width, height=img.height)
            pdf_page.insert_image(rect, stream=temp_img.getvalue())

        new_pdf.save(
            output_pdf,
            garbage=4,
            deflate=True
        )

        old_size = round(os.path.getsize(input_path) / (1024 * 1024), 2)
        new_size = round(os.path.getsize(output_pdf) / (1024 * 1024), 2)

        doc.close()
        new_pdf.close()

        if os.path.exists(input_path):
            os.remove(input_path)

        return output_pdf, old_size, new_size

    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        return None, 0, 0