import io
import os
import zipfile
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from services.pdf_version_service_react import run_pdf_version_downgrade

router = APIRouter(prefix="/api/pdf-version", tags=["PdfVersion"])

@router.post("/downgrade-batch")
async def downgrade_pdf_batch_endpoint(
    files: List[UploadFile] = File(...),
    compatibility: str = Form("1.4")
):
    if not files:
        raise HTTPException(status_code=400, detail="Vui lòng chọn ít nhất một file PDF!")

    try:
        zip_stream = io.BytesIO()
        
        with zipfile.ZipFile(zip_stream, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                file_bytes = await file.read()
                
                temp_out, err = run_pdf_version_downgrade(file_bytes, compatibility)
                
                if err or not temp_out or not os.path.exists(temp_out):
                    continue
                
                with open(temp_out, "rb") as f_out:
                    processed_bytes = f_out.read()
                
                try:
                    os.remove(temp_out)
                except:
                    pass
                
                zip_file.writestr(file.filename, processed_bytes)

        zip_stream.seek(0)
        
        return StreamingResponse(
            zip_stream,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''Downgraded_PDFs_v{compatibility}.zip"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý hạ phiên bản hàng loạt: {str(e)}")