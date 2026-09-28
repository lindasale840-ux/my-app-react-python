import os
import shutil
import tempfile
import traceback
from typing import List, Optional  # Thêm Optional
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


from typing import List, Optional  # Thêm Optional

@router.post("/compare-with-excel")
async def compare_pdf_with_excel(
    background_tasks: BackgroundTasks,
    excel_file: UploadFile = File(...),
    column_names: List[str] = Form(...),
    info_column: Optional[str] = Form(None),  # <--- Bổ sung tham số tùy chọn này
    pdf_files: List[UploadFile] = File(...)
):
    if not excel_file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File Excel không hợp lệ.")
    if not pdf_files:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên các file PDF để đối chiếu.")
    if not column_names:
        raise HTTPException(status_code=400, detail="Vui lòng chọn ít nhất một cột để đối chiếu.")

    temp_dir = tempfile.mkdtemp()
    excel_path = os.path.join(temp_dir, excel_file.filename)

    try:
        content = await excel_file.read()
        with open(excel_path, "wb") as f:
            f.write(content)

        df_excel = pd.read_excel(excel_path)

        # Kiểm tra cột đối chiếu
        missing_cols = [col for col in column_names if col not in df_excel.columns]
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Các cột sau không tồn tại trong Excel: {', '.join(missing_cols)}")
        
        # Kiểm tra cột thông tin bổ sung (nếu có chọn)
        if info_column and info_column not in df_excel.columns:
            raise HTTPException(status_code=400, detail=f"Cột thông tin bổ sung '{info_column}' không tồn tại trong Excel.")

        pdf_map = {}
        for f in pdf_files:
            if f.filename.lower().endswith(".pdf"):
                base_name = os.path.splitext(f.filename)[0].strip()
                if base_name:
                    pdf_map[base_name.lower()] = f.filename

        excel_map = {}
        row_status_tracker = []

        for idx, row in df_excel.iterrows():
            row_codes = {}
            for col in column_names:
                val = row[col]
                cleaned_val = clean_text(val) if 'clean_text' in globals() else (str(val).strip() if pd.notna(val) else "")
                if cleaned_val:
                    norm_key = cleaned_val.lower()
                    row_codes[col] = {
                        "original": cleaned_val,
                        "norm": norm_key
                    }
                    if norm_key not in excel_map:
                        excel_map[norm_key] = cleaned_val

            # Lấy thông tin bổ sung (ví dụ: Mã chứng nhận) từ cột được chọn
            extra_info_val = ""
            if info_column:
                raw_info = row[info_column]
                extra_info_val = str(raw_info).strip() if pd.notna(raw_info) else "(Trống)"

            row_status_tracker.append({
                "row_index": idx,
                "codes": row_codes,
                "info_val": extra_info_val
            })

        # 1. Danh sách Dòng KHÔNG CÓ file PDF (Thiếu PDF)
        missing_pdf_list = []
        for item in row_status_tracker:
            codes_in_row = item["codes"]
            if not codes_in_row:
                continue

            has_pdf = any(info["norm"] in pdf_map for info in codes_in_row.values())

            if not has_pdf:
                row_info = {}
                # Hiển thị cột thông tin bổ sung lên đầu nếu có
                if info_column:
                    row_info[f"Thông tin ({info_column})"] = item["info_val"]

                for col_name in column_names:
                    row_info[f"Mã ({col_name})"] = codes_in_row.get(col_name, {}).get("original", "(Trống)")
                
                row_info.update({
                    "Trạng thái": "Thiếu File PDF",
                    "Ghi chú": "Không tìm thấy file PDF trùng với bất kỳ mã nào ở dòng này"
                })
                missing_pdf_list.append(row_info)

        # 2. File PDF thừa
        extra_pdf_list = []
        for norm_code, pdf_name in pdf_map.items():
            if norm_code not in excel_map:
                extra_info_dict = {f"Thông tin ({info_column})": "(Không có)"} if info_column else {}
                extra_info_dict.update({
                    "Tên File PDF Upload": pdf_name,
                    "Trạng thái": "Thừa File PDF",
                    "Ghi chú": "Có file PDF nhưng không tìm thấy mã tương ứng trong các cột Excel đã chọn"
                })
                extra_pdf_list.append(extra_info_dict)

        # 3. Báo cáo Chi Tiết Tổng Hợp
        detailed_list = []
        for item in row_status_tracker:
            codes_in_row = item["codes"]
            if not codes_in_row:
                continue

            matched_pdf = ""
            status = "Thiếu File PDF"
            for info in codes_in_row.values():
                if info["norm"] in pdf_map:
                    matched_pdf = pdf_map[info["norm"]]
                    status = "Đủ"
                    break

            row_detail = {}
            if info_column:
                row_detail[f"Thông tin ({info_column})"] = item["info_val"]

            for col_name in column_names:
                row_detail[f"Mã ({col_name})"] = codes_in_row.get(col_name, {}).get("original", "(Trống)")
            
            row_detail.update({
                "Tên File PDF Tải Lên": matched_pdf,
                "Trạng thái": status
            })
            detailed_list.append(row_detail)

        for norm_code, pdf_name in pdf_map.items():
            if norm_code not in excel_map:
                row_detail = {}
                if info_column:
                    row_detail[f"Thông tin ({info_column})"] = "(Không có)"
                for col_name in column_names:
                    row_detail[f"Mã ({col_name})"] = "(Không có)"
                
                row_detail.update({
                    "Tên File PDF Tải Lên": pdf_name,
                    "Trạng thái": "Thừa File PDF"
                })
                detailed_list.append(row_detail)

        # Xuất file Báo Cáo Excel 2 Sheet
        output_report_path = os.path.join(temp_dir, "Bao_Cao_Doi_Chieu_PDF.xlsx")
        with pd.ExcelWriter(output_report_path, engine="openpyxl") as writer:
            df_missing = pd.DataFrame(
                missing_pdf_list if missing_pdf_list else [{"Thông báo": "Tất cả các mã trong các cột được chọn đều có đủ file PDF!"}]
            )
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