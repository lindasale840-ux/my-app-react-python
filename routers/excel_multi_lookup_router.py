import os
import re
import shutil
import tempfile
import pandas as pd
from typing import List, Optional
from urllib.parse import quote
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/api/excel/multi-lookup", tags=["Excel Multi-Lookup"])


def cleanup_temp_dir(temp_dir: str):
    """Hàm chạy ẩn để xóa thư mục tạm sau khi phản hồi hoàn tất"""
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


def read_dataframe(file_path: str, filename: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".csv":
        try:
            return pd.read_csv(file_path, dtype=str)
        except Exception:
            return pd.read_csv(file_path, dtype=str, encoding="utf-8-sig")
    elif ext in [".xlsx", ".xls"]:
        engine = "openpyxl" if ext == ".xlsx" else "xlrd"
        # Đóng file triệt để sau khi đọc xong bằng Context Manager
        with pd.ExcelFile(file_path, engine=engine) as xl:
            if sheet_name:
                return pd.read_excel(xl, sheet_name=sheet_name, dtype=str)
            else:
                return pd.read_excel(xl, dtype=str)
    else:
        raise ValueError("Định dạng file không được hỗ trợ. Vui lòng tải file .xlsx, .xls hoặc .csv")


@router.post("/inspect")
async def inspect_excel_file(file: UploadFile = File(...)):
    """Đọc thông tin danh sách Sheet và các Cột của file Excel tải lên"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".xlsx", ".xls", ".csv"]:
        raise HTTPException(status_code=400, detail="Vui lòng tải file Excel (.xlsx, .xls) hoặc CSV (.csv).")

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        sheets = []
        columns = []

        if ext == ".csv":
            sheets = ["Sheet1"]
            df = pd.read_csv(temp_path, nrows=5, dtype=str)
            columns = [str(c) for c in df.columns]
        else:
            engine = "openpyxl" if ext == ".xlsx" else "xlrd"
            with pd.ExcelFile(temp_path, engine=engine) as xl:
                sheets = xl.sheet_names
                if sheets:
                    df = pd.read_excel(xl, sheet_name=sheets[0], nrows=5, dtype=str)
                    columns = [str(c) for c in df.columns]

        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "sheets": sheets,
            "columns": columns
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc thông tin file Excel: {str(e)}")
    finally:
        # Xóa an toàn trên Windows
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass


@router.post("/get-columns")
async def get_sheet_columns(
    file: UploadFile = File(...),
    sheet_name: str = Form(...)
):
    """Lấy danh sách cột khi đổi Sheet"""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        ext = os.path.splitext(file.filename)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(temp_path, nrows=5, dtype=str)
        else:
            engine = "openpyxl" if ext == ".xlsx" else "xlrd"
            with pd.ExcelFile(temp_path, engine=engine) as xl:
                df = pd.read_excel(xl, sheet_name=sheet_name, nrows=5, dtype=str)

        columns = [str(c) for c in df.columns]
        return JSONResponse({"columns": columns})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy danh sách cột: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass


@router.post("/multi-lookup")
async def process_multi_lookup(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sheet_name: str = Form(...),
    lookup_column: str = Form(...),
    lookup_values: str = Form(...),
    match_mode: str = Form("Exact"),
    case_sensitive: bool = Form(False)
):
    """Thực hiện Multi-Lookup lấy toàn bộ kết quả trùng khớp và trả về file Excel"""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        df = read_dataframe(temp_path, file.filename, sheet_name=sheet_name)
        df = df.fillna("")

        if lookup_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy cột '{lookup_column}' trong Sheet '{sheet_name}'")

        raw_values = [v.strip() for v in lookup_values.split("\n") if v.strip()]
        if not raw_values:
            raise HTTPException(status_code=400, detail="Vui lòng nhập ít nhất 1 giá trị cần tìm kiếm.")

        search_keys = list(dict.fromkeys(raw_values))

        col_series = df[lookup_column].astype(str)
        matched_mask = pd.Series(False, index=df.index)

        stats_list = []

        for key in search_keys:
            if match_mode == "Exact":
                if case_sensitive:
                    mask = (col_series == key)
                else:
                    mask = (col_series.str.lower() == key.lower())
            else:
                if case_sensitive:
                    mask = col_series.str.contains(re.escape(key), regex=True, na=False)
                else:
                    mask = col_series.str.contains(re.escape(key), case=False, regex=True, na=False)

            count = mask.sum()
            matched_mask = matched_mask | mask

            stats_list.append({
                "Gia_Tri_Tim_Kiem": key,
                "Trang_Thai": "Tìm thấy" if count > 0 else "Không tìm thấy",
                "So_Luong_Dong": int(count)
            })

        df_result = df[matched_mask].copy()
        df_stats = pd.DataFrame(stats_list)

        found_keys = [item["Gia_Tri_Tim_Kiem"] for item in stats_list if item["So_Luong_Dong"] > 0]
        missing_keys = [item["Gia_Tri_Tim_Kiem"] for item in stats_list if item["So_Luong_Dong"] == 0]

        output_filename = "KetQua_MultiLookup.xlsx"
        output_path = os.path.join(temp_dir, output_filename)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df_result.to_excel(writer, sheet_name="Ket_Qua_Tim_Kiem", index=False)
            df_stats.to_excel(writer, sheet_name="Thong_Ke_Tra_Cuu", index=False)

        safe_missing_summary = quote(f"{len(found_keys)}/{len(search_keys)} giá trị tìm thấy")

        headers = {
            "Access-Control-Expose-Headers": "X-Total-Input, X-Total-Found, X-Total-Missing, X-Total-Rows, X-Summary-Status",
            "X-Total-Input": str(len(search_keys)),
            "X-Total-Found": str(len(found_keys)),
            "X-Total-Missing": str(len(missing_keys)),
            "X-Total-Rows": str(len(df_result)),
            "X-Summary-Status": safe_missing_summary
        }

        # Dọn dẹp thư mục tạm sau khi file đã được gửi về cho client thành công
        background_tasks.add_task(cleanup_temp_dir, temp_dir)

        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )

    except HTTPException:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý Tra cứu Excel: {str(e)}")


@router.post("/preview-lookup")
async def preview_multi_lookup(
    file: UploadFile = File(...),
    sheet_name: str = Form(...),
    lookup_column: str = Form(...),
    lookup_values: str = Form(...),
    match_mode: str = Form("Exact"),
    case_sensitive: bool = Form(False)
):
    """Xem trước 20 dòng kết quả đầu tiên trên giao diện web"""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)

    try:
        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        df = read_dataframe(temp_path, file.filename, sheet_name=sheet_name)
        df = df.fillna("")

        if lookup_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy cột '{lookup_column}'")

        raw_values = [v.strip() for v in lookup_values.split("\n") if v.strip()]
        search_keys = list(dict.fromkeys(raw_values))

        col_series = df[lookup_column].astype(str)
        matched_mask = pd.Series(False, index=df.index)

        stats_list = []

        for key in search_keys:
            if match_mode == "Exact":
                mask = (col_series == key) if case_sensitive else (col_series.str.lower() == key.lower())
            else:
                mask = col_series.str.contains(re.escape(key), case=not case_sensitive, regex=True, na=False)

            count = mask.sum()
            matched_mask = matched_mask | mask

            stats_list.append({
                "key": key,
                "found": bool(count > 0),
                "count": int(count)
            })

        df_result = df[matched_mask]
        preview_data = df_result.head(20).to_dict(orient="records")

        return JSONResponse({
            "success": True,
            "total_input": len(search_keys),
            "total_found": len([s for s in stats_list if s["found"]]),
            "total_missing": len([s for s in stats_list if not s["found"]]),
            "total_rows_matched": len(df_result),
            "stats": stats_list,
            "columns": list(df.columns),
            "preview_rows": preview_data
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xem trước kết quả: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass