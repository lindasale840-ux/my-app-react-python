# routers/pdf_excel_router.py
import os
import tempfile
import io
import pandas as pd
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from urllib.parse import quote

router = APIRouter(prefix="/api/pdf-excel", tags=["PdfExcelCompare"])

COLUMN_MAP = {
    "GCN": 25,
    "Số seri": 26,
    "Mã quản lý": 27,
    "Tên thiết bị": 5,
    "Model": 6
}

def normalize(value):
    if pd.isna(value) or value is None:
        return ""
    return str(value).strip().upper()

# =========================================================
# CODE ĐÃ CẬP NHẬT HOÀN CHỈNH CHO HÀM process_comparison
# =========================================================
def process_comparison(pdf_files: List[UploadFile], excel_file: UploadFile, compare_type: str):
    if compare_type not in COLUMN_MAP:
        raise HTTPException(
            status_code=400, 
            detail=f"Loại đối chiếu '{compare_type}' không hợp lệ."
        )

    compare_col = COLUMN_MAP[compare_type]

    try:
        excel_bytes = excel_file.file.read()
        # 1. Bỏ qua header dòng 1 (header=0)
        df = pd.read_excel(io.BytesIO(excel_bytes), header=0, dtype=str)

        if compare_col >= len(df.columns):
            raise HTTPException(
                status_code=400, 
                detail=f"File Excel không có cột chỉ số {compare_col} (Tổng số cột: {len(df.columns)})"
            )

        excel_values = set()
        
        # 2. Dùng .iloc[:, compare_col] để lấy dữ liệu theo đúng vị trí chỉ số cột (bắt đầu từ dòng 2)
        for value in df.iloc[:, compare_col].tolist():
            val_norm = normalize(value)
            if val_norm:
                excel_values.add(val_norm)

        # các đoạn code xử lý PDF bên dưới giữ nguyên không đổi...

        pdf_values = []
        for file in pdf_files:
            filename_without_ext = os.path.splitext(file.filename)[0]
            pdf_values.append(normalize(filename_without_ext))

        matched = []
        missing_excel = []
        duplicates = []
        seen = set()

        for value in pdf_values:
            if value in seen:
                duplicates.append(value)
            seen.add(value)

            if value in excel_values:
                matched.append(value)
            else:
                missing_excel.append(value)

        missing_pdf = list(excel_values - set(pdf_values))

        return {
            "matched": matched,
            "missing_pdf": missing_pdf,
            "missing_excel": missing_excel,
            "duplicates": duplicates,
            "summary": {
                "total_pdf": len(pdf_files),
                "total_excel_items": len(excel_values),
                "matched_count": len(matched),
                "missing_pdf_count": len(missing_pdf),
                "missing_excel_count": len(missing_excel),
                "duplicates_count": len(duplicates)
            }
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý dữ liệu: {str(e)}")

@router.post("/compare")
async def compare_pdf_excel(
    pdf_files: List[UploadFile] = File(...),
    excel_file: UploadFile = File(...),
    compare_type: str = Form(...)
):
    """
    Nhận danh sách PDF và 1 File Excel, thực hiện đối chiếu và trả về JSON thống kê.
    """
    if not pdf_files:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất 1 file PDF.")
    if not excel_file:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên file Excel.")

    result = process_comparison(pdf_files, excel_file, compare_type)
    return result

@router.post("/export-report")
async def export_report(
    pdf_files: List[UploadFile] = File(...),
    excel_file: UploadFile = File(...),
    compare_type: str = Form(...)
):
    """
    Thực hiện đối chiếu và xuất kết quả ra file Excel báo cáo.
    """
    res = process_comparison(pdf_files, excel_file, compare_type)
    
    report_rows = []
    for x in res["matched"]:
        report_rows.append(["OK", x])
    for x in res["missing_pdf"]:
        report_rows.append(["Thiếu PDF", x])
    for x in res["missing_excel"]:
        report_rows.append(["Thiếu Excel", x])
    for x in res["duplicates"]:
        report_rows.append(["Trùng PDF", x])

    report_df = pd.DataFrame(report_rows, columns=["Trạng thái", "Giá trị"])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        report_df.to_excel(writer, index=False, sheet_name="BaoCaoDoiChieu")
    output.seek(0)

    filename = f"PDF_Excel_Report_{compare_type}.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )