from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
import tempfile
import os
from services.gcn_locator_service import run_requested_gcn_extractor_pure_simple
from services.scan_rename_service import process_page_ocr

router = APIRouter(prefix="/api/gcn_locator", tags=["GcnLocator"])

@router.post("/locate")
async def locate_gcn_pages(
    pdf_file: UploadFile = File(...),
    requested_gcn_text: str = Form(...)
):
    if not pdf_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File tải lên phải là file PDF.")
    
    if not requested_gcn_text.strip():
        raise HTTPException(status_code=400, detail="Danh sách mã GCN không được để trống.")

    # Lưu file tạm để PyMuPDF đọc
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await pdf_file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        excel_buffer, message = run_requested_gcn_extractor_pure_simple(
            pdf_total_path=tmp_path,
            requested_gcn_text=requested_gcn_text,
            process_ocr_func=process_page_ocr  # <--- ĐÂY LÀ ĐIỂM QUAN TRỌNG NHẤT
        )
        
        if excel_buffer is None:
            raise HTTPException(status_code=400, detail=message)

        headers = {
            'Content-Disposition': 'attachment; filename="BaoCao_ViTri_GCN.xlsx"'
        }
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)