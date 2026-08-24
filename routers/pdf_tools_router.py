import os
import shutil
import tempfile
import traceback
from typing import List
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/api/pdf-tools", tags=["PdfTools"])


def remove_temp_dir(path: str):
    """Hàm dọn dẹp thư mục tạm sau khi trả file về client thành công"""
    shutil.rmtree(path, ignore_errors=True)


def clean_text(val):
    """Làm sạch dữ liệu chuỗi để so sánh chính xác"""
    if pd.isna(val):
        return ""
    val_str = str(val).strip()
    if val_str.upper() in ["NAN", "NONE", "N/A", "NA", "/", ""]:
        return ""
    return val_str


@router.post("/extract-names")
async def extract_pdf_names(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    if not files:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất một file PDF.")

    temp_dir = tempfile.mkdtemp()

    try:
        data = []
        for idx, file in enumerate(files, start=1):
            filename = file.filename
            if not filename.lower().endswith(".pdf"):
                continue

            # Đọc dung lượng file
            content = await file.read()
            size_kb = round(len(content) / 1024, 2)

            name_without_ext = os.path.splitext(filename)[0]

            data.append({
                "STT": idx,
                "Tên File PDF (Gồm đuôi)": filename,
                "Tên File PDF (Không đuôi)": name_without_ext,
                "Dung lượng (KB)": size_kb
            })

        if not data:
            raise HTTPException(status_code=400, detail="Không tìm thấy file .pdf hợp lệ trong danh sách tải lên.")

        # Xuất ra Excel
        df = pd.DataFrame(data)
        excel_path = os.path.join(temp_dir, "Danh_Sach_File_PDF.xlsx")
        
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Danh_Sach_PDF")

        background_tasks.add_task(remove_temp_dir, temp_dir)
        return FileResponse(
            path=excel_path,
            filename="Danh_Sach_File_PDF.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý file PDF: {str(e)}")


@router.post("/get-columns")
async def get_excel_columns(excel_file: UploadFile = File(...)):
    if not excel_file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File tải lên phải là file Excel (.xlsx, .xls).")

    temp_dir = tempfile.mkdtemp()
    temp_excel_path = os.path.join(temp_dir, excel_file.filename)

    try:
        content = await excel_file.read()
        with open(temp_excel_path, "wb") as f:
            f.write(content)

        # Đọc 2 dòng đầu để lấy danh sách tiêu đề cột
        df = pd.read_excel(temp_excel_path, nrows=2)
        columns = [str(col).strip() for col in df.columns if not str(col).startswith("Unnamed:")]

        return JSONResponse(content={"columns": columns})

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Không thể đọc danh sách cột từ file Excel: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/compare-with-excel")
async def compare_pdf_with_excel(
    background_tasks: BackgroundTasks,
    excel_file: UploadFile = File(...),
    column_name: str = Form(...),
    pdf_files: List[UploadFile] = File(...)
):
    if not excel_file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File Excel không hợp lệ.")
    if not pdf_files:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên các file PDF để đối chiếu.")

    temp_dir = tempfile.mkdtemp()
    excel_path = os.path.join(temp_dir, excel_file.filename)

    try:
        # Lưu file Excel
        content = await excel_file.read()
        with open(excel_path, "wb") as f:
            f.write(content)

        df_excel = pd.read_excel(excel_path)

        if column_name not in df_excel.columns:
            raise HTTPException(status_code=400, detail=f"Cột '{column_name}' không tồn tại trong file Excel.")

        # Lấy danh sách mã từ Excel và làm sạch
        excel_codes_raw = df_excel[column_name].tolist()
        excel_codes_cleaned = [clean_text(val) for val in excel_codes_raw]
        excel_codes_valid = [c for c in excel_codes_cleaned if c != ""]

        # Map chuẩn hóa (chữ thường, bỏ space thừa) -> Mã gốc Excel
        excel_map = {c.lower(): c for c in excel_codes_valid}

        # Lấy danh sách file PDF thực tế
        pdf_map = {}  # key_normalized -> pdf_filename
        for f in pdf_files:
            if f.filename.lower().endswith(".pdf"):
                base_name = os.path.splitext(f.filename)[0].strip()
                if base_name:
                    pdf_map[base_name.lower()] = f.filename

        # 1. Mã trong Excel nhưng KHÔNG CÓ file PDF (Thiếu PDF)
        missing_pdf_list = []
        for norm_code, original_code in excel_map.items():
            if norm_code not in pdf_map:
                missing_pdf_list.append({
                    "Mã Excel": original_code,
                    "Trạng thái": "Thiếu File PDF",
                    "Ghi chú": "Có trong Excel nhưng chưa có file PDF tải lên"
                })

        # 2. File PDF tải lên nhưng KHÔNG CÓ trong Excel (Thừa PDF)
        extra_pdf_list = []
        for norm_code, pdf_name in pdf_map.items():
            if norm_code not in excel_map:
                extra_pdf_list.append({
                    "Tên File PDF Upload": pdf_name,
                    "Trạng thái": "Thừa File PDF",
                    "Ghi chú": "Có file PDF nhưng không tìm thấy mã tương ứng trong Excel"
                })

        # 3. Báo cáo Chi Tiết Tổng Hợp
        detailed_list = []
        # Thêm danh sách từ Excel
        for norm_code, original_code in excel_map.items():
            status = "Đủ" if norm_code in pdf_map else "Thiếu File PDF"
            pdf_filename = pdf_map.get(norm_code, "")
            detailed_list.append({
                "Mã Trong Excel": original_code,
                "Tên File PDF Tải Lên": pdf_filename,
                "Trạng thái": status
            })

        # Thêm các file PDF thừa
        for norm_code, pdf_name in pdf_map.items():
            if norm_code not in excel_map:
                detailed_list.append({
                    "Mã Trong Excel": "(Không có)",
                    "Tên File PDF Tải Lên": pdf_name,
                    "Trạng thái": "Thừa File PDF"
                })

        # Xuất file Báo Cáo Excel 2 Sheet
        output_report_path = os.path.join(temp_dir, "Bao_Cao_Doi_Chieu_PDF.xlsx")
        with pd.ExcelWriter(output_report_path, engine="openpyxl") as writer:
            df_missing = pd.DataFrame(missing_pdf_list if missing_pdf_list else [{"Thông báo": "Tất cả các mã trong Excel đều có đủ file PDF!"}])
            df_missing.to_excel(writer, index=False, sheet_name="Danh_Sach_Thieu_PDF")

            df_detail = pd.DataFrame(detailed_list)
            df_detail.to_excel(writer, index=False, sheet_name="Tong_Hop_Doi_Chieu")

        background_tasks.add_task(remove_temp_dir, temp_dir)
        return FileResponse(
            path=output_report_path,
            filename="Bao_Cao_Doi_Chieu_PDF.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lỗi khi đối chiếu PDF với Excel: {str(e)}")