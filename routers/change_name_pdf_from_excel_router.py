import os
import re
import json
import zipfile
import tempfile
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/api/rename-pdf-excel", tags=["RenamePdfExcel"])

# ==============================================================================
# HÀM HỖ TRỢ CHUẨN HÓA VÀ XỬ LÝ CHUỖI
# ==============================================================================
def normalize_key(text: str) -> str:
    """Chuẩn hóa khóa so sánh: Viết hoa, xóa khoảng trắng, đồng nhất '_' thành '-'"""
    if not text or str(text).lower() in ["nan", "none", "null"]:
        return ""
    text = str(text).strip().upper()
    text = re.sub(r'\s*', '', text)
    text = text.replace('_', '-')
    return text

def clean_filename(text: str) -> str:
    """Loại bỏ ký tự cấm của Windows khỏi tên file"""
    if not text:
        return ""
    text = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', str(text))
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@router.post("/parse-excel-columns")
async def parse_excel_columns(excel_file: UploadFile = File(...)):
    """Đọc danh sách các cột từ file Excel"""
    try:
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, excel_file.filename)
        with open(file_path, "wb") as f:
            f.write(await excel_file.read())

        # Đọc hàng đầu tiên để lấy danh sách cột
        df = pd.read_excel(file_path, nrows=2)
        columns = [str(col).strip() for col in df.columns]

        return JSONResponse(content={"status": "success", "columns": columns})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể đọc file Excel: {str(e)}")

@router.post("/preview-rename")
async def preview_rename(
    excel_file: UploadFile = File(...),
    pdf_files: List[UploadFile] = File(...),
    key_column: str = Form(...),
    target_columns: str = Form(...),  # Chuỗi JSON dạng array: ["Cột A", "Cột B"]
    separator: str = Form("_")
):
    """Đối chiếu tên file PDF hiện tại với Excel và trả về bảng Preview"""
    try:
        temp_dir = tempfile.mkdtemp()
        excel_path = os.path.join(temp_dir, excel_file.filename)
        with open(excel_path, "wb") as f:
            f.write(await excel_file.read())

        df = pd.read_excel(excel_path, dtype=str)
        if key_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy cột '{key_column}' trong Excel!")

        try:
            target_cols = json.loads(target_columns)
        except:
            target_cols = [target_columns]

        # Tạo dict ánh xạ: Normalized_Key -> New_Name
        excel_map = {}
        for idx, row in df.iterrows():
            raw_key = row.get(key_column, "")
            norm_k = normalize_key(raw_key)
            if not norm_k:
                continue

            # Ghép các cột tên mới
            val_parts = []
            for col in target_cols:
                if col in df.columns and pd.notna(row[col]):
                    c_val = clean_filename(str(row[col]))
                    if c_val and c_val.lower() not in ["nan", "none"]:
                        val_parts.append(c_val)

            new_name_val = separator.join(val_parts) if val_parts else ""
            if new_name_val:
                excel_map[norm_k] = new_name_val

        preview_results = []
        for pdf in pdf_files:
            original_filename = pdf.filename
            pdf_base_name = os.path.splitext(original_filename)[0]
            norm_pdf_key = normalize_key(pdf_base_name)

            matched_new_name = excel_map.get(norm_pdf_key)

            if matched_new_name:
                preview_results.append({
                    "original_name": original_filename,
                    "new_name": f"{matched_new_name}.pdf",
                    "status": "success",
                    "message": "🟢 Khớp dữ liệu thành công"
                })
            else:
                preview_results.append({
                    "original_name": original_filename,
                    "new_name": original_filename,
                    "status": "not_found",
                    "message": "🔴 Không tìm thấy mã trong Excel"
                })

        return JSONResponse(content={"status": "success", "data": preview_results})

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý đối chiếu: {str(e)}")

@router.post("/execute-rename-zip")
async def execute_rename_zip(
    excel_file: UploadFile = File(...),
    pdf_files: List[UploadFile] = File(...),
    key_column: str = Form(...),
    target_columns: str = Form(...),
    separator: str = Form("_")
):
    """Thực thi đổi tên hàng loạt file PDF và đóng gói thành ZIP"""
    try:
        temp_dir = tempfile.mkdtemp()
        excel_path = os.path.join(temp_dir, excel_file.filename)
        with open(excel_path, "wb") as f:
            f.write(await excel_file.read())

        df = pd.read_excel(excel_path, dtype=str)
        try:
            target_cols = json.loads(target_columns)
        except:
            target_cols = [target_columns]

        excel_map = {}
        for idx, row in df.iterrows():
            raw_key = row.get(key_column, "")
            norm_k = normalize_key(raw_key)
            if not norm_k:
                continue

            val_parts = []
            for col in target_cols:
                if col in df.columns and pd.notna(row[col]):
                    c_val = clean_filename(str(row[col]))
                    if c_val and c_val.lower() not in ["nan", "none"]:
                        val_parts.append(c_val)

            new_name_val = separator.join(val_parts) if val_parts else ""
            if new_name_val:
                excel_map[norm_k] = new_name_val

        zip_path = os.path.join(temp_dir, "Doi_Ten_PDF_Excel.zip")
        used_names = {}

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for pdf in pdf_files:
                pdf_content = await pdf.read()
                original_filename = pdf.filename
                pdf_base_name = os.path.splitext(original_filename)[0]
                norm_pdf_key = normalize_key(pdf_base_name)

                matched_new_name = excel_map.get(norm_pdf_key)

                if matched_new_name:
                    base_final = matched_new_name
                else:
                    base_final = pdf_base_name  # Giữ nguyên tên gốc nếu không tìm thấy

                # Xử lý trùng lặp tên file đầu ra
                if base_final in used_names:
                    used_names[base_final] += 1
                    final_filename = f"{base_final} ({used_names[base_final]}).pdf"
                else:
                    used_names[base_final] = 0
                    final_filename = f"{base_final}.pdf"

                temp_pdf = os.path.join(temp_dir, final_filename)
                with open(temp_pdf, "wb") as f:
                    f.write(pdf_content)

                zipf.write(temp_pdf, final_filename)

        return FileResponse(
            path=zip_path,
            filename="PDF_Doi_Ten_Theo_Excel.zip",
            media_type="application/zip"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xuất file ZIP: {str(e)}")