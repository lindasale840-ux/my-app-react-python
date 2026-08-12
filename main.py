from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Annotated
import os

from services.pdf_merge_service_react import merge_pdfs_logic

app = FastAPI(title="PDF & Excel Processing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API Backend Python đang chạy rất tốt!"}


# SỬA DÙNG ANNOTATED Ở ĐÂY
@app.post("/api/pdf/merge")
async def api_merge_pdfs(
    files: Annotated[List[UploadFile], File(description="Chọn các file PDF cần ghép")]
):
    """
    API nhận vào danh sách nhiều file PDF, ghép lại và trả về 1 file PDF hoàn chỉnh.
    """
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