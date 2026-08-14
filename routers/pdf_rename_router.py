import os
import re
import tempfile
import zipfile
import io
import pandas as pd
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/api/pdf-rename", tags=["PdfRename"])

def clean_value(val):
    """Hàm phụ trợ: Kiểm tra và làm sạch giá trị đọc từ Excel"""
    if pd.isna(val):
        return ""
    val_str = str(val).strip()
    if val_str in ["/", "", "NA", "na", "NaN", "nan"]:
        return ""
    return val_str

@router.post("/preview-columns")
async def preview_columns(file_excel: UploadFile = File(...)):
    """API Đọc danh sách các cột từ File Excel để trả về cho Frontend"""
    try:
        contents = await file_excel.read()
        df_preview = pd.read_excel(io.BytesIO(contents), nrows=1)
        columns = [str(col) for col in df_preview.columns]
        return JSONResponse(content={"columns": columns})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể đọc file Excel: {str(e)}")

@router.post("/process-rename")
async def rename_pdf_files(
    file_excel: UploadFile = File(...),
    pdf_files: List[UploadFile] = File(...),
    match_col: str = Form(...),
    primary_name_col: str = Form(...),
    fallback_name_col: str = Form(...)
):
    """API chính để khớp tên, đổi tên các file PDF theo Excel và đóng gói ZIP"""
    try:
        if not pdf_files:
            raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất một file PDF.")

        # 1. Đọc file Excel
        file_bytes = await file_excel.read()
        df = pd.read_excel(io.BytesIO(file_bytes))

        # Tạo Dictionary tra cứu
        lookup_dict = {}
        for _, row in df.iterrows():
            match_key = clean_value(row.get(match_col))
            if match_key:
                lookup_dict[match_key.lower()] = {
                    "primary": clean_value(row.get(primary_name_col)),
                    "fallback": clean_value(row.get(fallback_name_col))
                }

        temp_dir = tempfile.mkdtemp()
        renamed_files = []
        logs = []
        logs.append("--- BẮT ĐẦU TIẾN TRÌNH ĐỔI TÊN FILE PDF ---")

        total_pdf = len(pdf_files)

        # 2. Lặp qua từng file PDF được tải lên
        for idx, pdf_file in enumerate(pdf_files, 1):
            old_full_name = pdf_file.filename
            old_name_no_ext, ext = os.path.splitext(old_full_name)
            old_key = old_name_no_ext.strip().lower()

            content = await pdf_file.read()

            # Kiểm tra xem tên file cũ có trong Excel không
            if old_key in lookup_dict:
                data = lookup_dict[old_key]
                primary_val = data["primary"]
                fallback_val = data["fallback"]

                # Logic chọn tên: Lấy cột 1, nếu rỗng thì lấy cột 2
                prefix_name = primary_val if primary_val else fallback_val

                if prefix_name:
                    new_name_no_ext = f"{prefix_name}_{old_name_no_ext}"
                else:
                    new_name_no_ext = old_name_no_ext
                    logs.append(f"[{idx}/{total_pdf}] Cảnh báo: File '{old_full_name}' cả 2 cột tên đều rỗng -> Giữ nguyên tên.")

                safe_new_name = re.sub(r'[\\/*?:"<>|]', '_', new_name_no_ext) + ext
                new_file_path = os.path.join(temp_dir, safe_new_name)
                
                with open(new_file_path, "wb") as f:
                    f.write(content)

                renamed_files.append(new_file_path)
                logs.append(f"[{idx}/{total_pdf}] Đổi tên: '{old_full_name}' -> '{safe_new_name}'")

            else:
                new_file_path = os.path.join(temp_dir, old_full_name)
                with open(new_file_path, "wb") as f:
                    f.write(content)
                renamed_files.append(new_file_path)
                logs.append(f"[{idx}/{total_pdf}] Không thấy trong Excel: Giữ nguyên '{old_full_name}'")

        # 3. Tạo file Log_Doi_Ten_PDF.txt
        log_path = os.path.join(temp_dir, "Log_Doi_Ten_PDF.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))

        # 4. Đóng gói ZIP
        zip_filename = f"Danh_Sach_PDF_Da_Doi_Ten_{total_pdf}files.zip"
        zip_path = os.path.join(tempfile.gettempdir(), zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for f_path in renamed_files:
                zipf.write(f_path, arcname=os.path.basename(f_path))
            zipf.write(log_path, arcname="Log_Doi_Ten_PDF.txt")

        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý hệ thống: {str(e)}")