import os
import tempfile
import zipfile
import shutil
from typing import List
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pypdf import PdfReader, PdfWriter

router = APIRouter(prefix="/api/pdf_merge", tags=["PDF Merge"])

# ----------------- TAB 1: MERGE BY NAME -----------------
@router.post("/merge-by-name")
async def merge_by_name(
    files_a: List[UploadFile] = File(...),
    files_b: List[UploadFile] = File(...)
):
    temp_dir = tempfile.mkdtemp()
    try:
        output_dir = os.path.join(temp_dir, "merge_by_name")
        os.makedirs(output_dir, exist_ok=True)

        dict_b_paths = {}
        for file_b in files_b:
            key = file_b.filename.lower()
            file_b_path = os.path.join(temp_dir, f"b_{file_b.filename}")
            with open(file_b_path, "wb") as f:
                content = await file_b.read()
                f.write(content)
            dict_b_paths[key] = file_b_path

        merged_count = 0
        skipped_count = 0

        for file_a in files_a:
            file_name = file_a.filename
            key = file_name.lower()

            file_a_path = os.path.join(temp_dir, f"a_{file_name}")
            with open(file_a_path, "wb") as f:
                content = await file_a.read()
                f.write(content)

            if key not in dict_b_paths:
                skipped_count += 1
                continue

            path_b = dict_b_paths[key]
            writer = PdfWriter()

            reader_a = PdfReader(file_a_path)
            for page in reader_a.pages:
                writer.add_page(page)

            reader_b = PdfReader(path_b)
            for page in reader_b.pages:
                writer.add_page(page)

            output_pdf = os.path.join(output_dir, file_name)
            with open(output_pdf, "wb") as f:
                writer.write(f)

            merged_count += 1

        if merged_count == 0:
            raise HTTPException(
                status_code=400,
                detail=f"Không tìm thấy file nào trùng tên để ghép. Bỏ qua {skipped_count} file."
            )

        zip_path = os.path.join(temp_dir, "Merged_By_Name.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in os.listdir(output_dir):
                zipf.write(os.path.join(output_dir, file), arcname=file)

        headers = {
            "Access-Control-Expose-Headers": "X-Merged-Count, X-Skipped-Count",
            "X-Merged-Count": str(merged_count),
            "X-Skipped-Count": str(skipped_count)
        }

        return FileResponse(
            path=zip_path,
            filename="Merged_By_Name.zip",
            media_type="application/zip",
            headers=headers
        )

    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


# ----------------- TAB 2: MERGE BY EXCEL -----------------
@router.post("/get-excel-columns")
async def get_excel_columns(excel_file: UploadFile = File(...)):
    """Đọc và trả về danh sách tiêu đề cột từ file Excel để UI làm dropdown selection"""
    try:
        contents = await excel_file.read()
        temp_excel = os.path.join(tempfile.gettempdir(), excel_file.filename)
        with open(temp_excel, "wb") as f:
            f.write(contents)

        df = pd.read_excel(temp_excel, nrows=2)
        columns = df.columns.astype(str).tolist()

        if os.path.exists(temp_excel):
            os.remove(temp_excel)

        return JSONResponse(content={"columns": columns})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể đọc file Excel: {str(e)}")


@router.post("/merge-by-excel")
async def merge_by_excel(
    column_a: str = Form(...),
    column_b: str = Form(...),
    excel_file: UploadFile = File(...),
    files_a: List[UploadFile] = File(...),
    files_b: List[UploadFile] = File(...)
):
    temp_dir = tempfile.mkdtemp()
    try:
        output_dir = os.path.join(temp_dir, "merge_by_excel")
        os.makedirs(output_dir, exist_ok=True)

        # Lưu file Excel
        excel_path = os.path.join(temp_dir, excel_file.filename)
        with open(excel_path, "wb") as f:
            f.write(await excel_file.read())

        # Lưu các file Bộ A
        dict_a = {}
        for item in files_a:
            path_a = os.path.join(temp_dir, f"a_{item.filename}")
            with open(path_a, "wb") as f:
                f.write(await item.read())
            dict_a[item.filename] = path_a

        # Lưu các file Bộ B
        dict_b = {}
        for item in files_b:
            path_b = os.path.join(temp_dir, f"b_{item.filename}")
            with open(path_b, "wb") as f:
                f.write(await item.read())
            dict_b[item.filename] = path_b

        # Đọc dữ liệu Excel
        df = pd.read_excel(excel_path, dtype=str).fillna("")

        if column_a not in df.columns or column_b not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Cột '{column_a}' hoặc '{column_b}' không tồn tại trong file Excel"
            )

        report_rows = []
        success_count = 0

        for _, row in df.iterrows():
            file_a_name = str(row[column_a]).strip()
            file_b_name = str(row[column_b]).strip()

            if not file_a_name and not file_b_name:
                continue

            if file_a_name not in dict_a:
                report_rows.append([file_a_name, file_b_name, "Thiếu File A"])
                continue

            if file_b_name not in dict_b:
                report_rows.append([file_a_name, file_b_name, "Thiếu File B"])
                continue

            writer = PdfWriter()

            # Đọc & thêm các trang từ File A
            reader_a = PdfReader(dict_a[file_a_name])
            for page in reader_a.pages:
                writer.add_page(page)

            # Đọc & thêm các trang từ File B
            reader_b = PdfReader(dict_b[file_b_name])
            for page in reader_b.pages:
                writer.add_page(page)

            output_pdf = os.path.join(output_dir, file_a_name)
            with open(output_pdf, "wb") as f:
                writer.write(f)

            success_count += 1
            report_rows.append([file_a_name, file_b_name, "OK"])

        if len(report_rows) == 0:
            raise HTTPException(status_code=400, detail="File Excel không có dòng dữ liệu hợp lệ")

        # Xuất file báo cáo Excel
        report_path = os.path.join(output_dir, "Merge_Report.xlsx")
        pd.DataFrame(
            report_rows,
            columns=["File A", "File B", "Ket Qua"]
        ).to_excel(report_path, index=False)

        # Nén thư mục kết quả thành ZIP
        zip_path = os.path.join(temp_dir, "Merge_By_Excel.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in os.listdir(output_dir):
                zipf.write(os.path.join(output_dir, file), arcname=file)

        headers = {
            "Access-Control-Expose-Headers": "X-Success-Count, X-Total-Count",
            "X-Success-Count": str(success_count),
            "X-Total-Count": str(len(report_rows))
        }

        return FileResponse(
            path=zip_path,
            filename="Merge_By_Excel.zip",
            media_type="application/zip",
            headers=headers
        )

    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))