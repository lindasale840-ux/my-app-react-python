from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import fitz  # PyMuPDF
from io import BytesIO

router = APIRouter(prefix="/api/pdf-unlock", tags=["PdfUnlock"])

@router.post("/unlock")
async def unlock_pdf_endpoint(file: UploadFile = File(...)):
    """
    API Mở khóa PDF (Gỡ Owner Password & Restricted Permissions)
    Bảo toàn 100% Vector, Font chữ, Text và Hình ảnh bằng cách copy luồng trang trực tiếp qua PyMuPDF.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Vui lòng tải lên file có định dạng .pdf!")

    try:
        # Đọc dữ liệu file từ Request
        file_bytes = await file.read()
        
        # Mở document gốc
        doc_src = fitz.open(stream=file_bytes, filetype="pdf")
        
        # Tạo document mới hoàn toàn "sạch"
        doc_dst = fitz.open()
        
        # Copy trực tiếp toàn bộ các trang sang document mới (Không qua render ảnh)
        doc_dst.insert_pdf(doc_src)
        
        # Xuất dữ liệu PDF ra bộ nhớ đệm
        output_buffer = BytesIO()
        doc_dst.save(output_buffer)
        output_buffer.seek(0)
        
        # Đóng các document để giải phóng bộ nhớ
        doc_src.close()
        doc_dst.close()

        # Tạo tên file output
        clean_filename = f"Unlocked_{file.filename}"

        return StreamingResponse(
            output_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{clean_filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý mở khóa PDF: {str(e)}")