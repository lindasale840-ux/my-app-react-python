from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import fitz  # PyMuPDF
from io import BytesIO
from urllib.parse import quote

router = APIRouter(prefix="/api/pdf-unlock", tags=["PdfUnlock"])

@router.post("/unlock")
async def unlock_pdf_endpoint(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Vui lòng tải lên file có định dạng .pdf!")

    try:
        file_bytes = await file.read()
        
        doc_src = fitz.open(stream=file_bytes, filetype="pdf")
        doc_dst = fitz.open()
        
        # Copy toàn bộ trang từ document gốc
        doc_dst.insert_pdf(doc_src)
        
        # 🟢 CHỈ SỬA FONT CHO CÁC Ô NHẬP CHỮ (TEXT FIELDS)
        # Giữ nguyên Checkbox, Radio Button và Nút bấm không bị ảnh hưởng
        for page in doc_dst:
            for field in page.widgets():
                # Kiểm tra nếu chỉ là ô nhập văn bản (Text field)
                if field.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                    # Gán font chuẩn hỗ trợ hiển thị
                    field.text_font = "Helv"
                    
                    # Giữ nguyên kích thước chữ gốc nếu có, hoặc đặt tự động (0)
                    # field.text_size = 10 
                    
                    # Cập nhật riêng cho ô Text này
                    field.update()

        output_buffer = BytesIO()
        # Lưu file và bảo toàn nguyên vẹn cấu trúc các ô form khác
        doc_dst.save(output_buffer, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
        output_buffer.seek(0)
        
        doc_src.close()
        doc_dst.close()

        raw_filename = f"Unlocked_{file.filename}"
        encoded_filename = quote(raw_filename)

        return StreamingResponse(
            output_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý mở khóa PDF: {str(e)}")