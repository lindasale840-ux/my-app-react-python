from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from typing import List, Annotated
import os

# Import các logic xử lý từ thư mục services
from services.pdf_merge_service_react import merge_pdfs_logic
from services.pdf_split_service_react import get_pdf_thumbnails_logic, split_pdf_by_ranges_logic

router = APIRouter(prefix="/api/pdf", tags=["PDF Operations"])

# 1. API Ghép PDF (Chuyển từ main.py cũ sang)
@router.post("/merge")
async def api_merge_pdfs(
    files: Annotated[List[UploadFile], File(description="Chọn các file PDF cần ghép")]
):
    if not files:
        raise HTTPException(status_code=400, detail="Vui lòng gửi ít nhất 1 file PDF.")

    output_path, message = merge_pdfs_logic(files)

    if not output_path:
        raise HTTPException(status_code=500, detail=f"Lỗi khi ghép file: {message}")

    return FileResponse(
        path=output_path,
        filename=os.path.basename(output_path),
        media_type="application/pdf"
    )

# 2. API Lấy danh sách ảnh Thumbnails của file PDF
@router.post("/thumbnails")
async def api_get_pdf_thumbnails(file: Annotated[UploadFile, File(...)]):
    file_bytes = await file.read()
    thumbnails = get_pdf_thumbnails_logic(file_bytes)
    return {"total_pages": len(thumbnails), "thumbnails": thumbnails}

# 3. API Cắt PDF theo danh sách điểm cắt
@router.post("/split-ranges")
async def api_split_pdf_ranges(
    file: Annotated[UploadFile, File(...)],
    ranges_text: Annotated[str, Form(...)]
):
    file_bytes = await file.read()
    zip_path, message = split_pdf_by_ranges_logic(file_bytes, ranges_text)
    
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=500, detail=f"Lỗi khi tách file: {message}")
        
    return FileResponse(
        path=zip_path,
        filename="Split_Results.zip",
        media_type="application/zip"
    )