import os
import json
import shutil
import tempfile
import zipfile
import traceback
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pypdf import PdfWriter

# Thư viện đọc nhẹ danh sách sheet không cần mở MS Excel COM
import openpyxl
import xlrd

# TỰ ĐỘNG THÊM ĐƯỜNG DẪN DLL CHO WIN32COM (Xử lý lỗi thiếu pywin32 DLL)
try:
    import win32com.client
    import pythoncom
    WIN32_AVAILABLE = True
except ImportError:
    try:
        import sys
        venv_path = os.path.dirname(sys.executable)
        py32_dll_path = os.path.join(venv_path, "Lib", "site-packages", "pywin32_system32")
        if os.path.exists(py32_dll_path):
            os.add_dll_directory(py32_dll_path)
        
        import win32com.client
        import pythoncom
        WIN32_AVAILABLE = True
    except Exception:
        WIN32_AVAILABLE = False

router = APIRouter(prefix="/api/excel-to-pdf", tags=["ExcelToPdf"])


def remove_temp_dir(path: str):
    """Hàm dọn dẹp thư mục tạm sau khi FastAPI trả file về client thành công"""
    shutil.rmtree(path, ignore_errors=True)


def convert_excel_to_pdf_win32(input_excel_path: str, output_pdf_path: str, selected_sheets: Optional[List[str]] = None):
    """
    Hàm bổ trợ mở file Excel bằng COM/win32com và xuất PDF theo danh sách selected_sheets.
    """
    pythoncom.CoInitialize()
    excel_app = None
    wb = None
    try:
        excel_app = win32com.client.DispatchEx("Excel.Application")
        excel_app.Visible = False
        excel_app.DisplayAlerts = False

        abs_input_path = os.path.abspath(input_excel_path)
        abs_output_path = os.path.abspath(output_pdf_path)

        wb = excel_app.Workbooks.Open(abs_input_path, ReadOnly=True, UpdateLinks=False)

        # Lấy danh sách tên tất cả sheet thực tế trong file Excel
        existing_sheet_names = [s.Name for s in wb.Sheets]

        # Nếu có truyền selected_sheets -> Lọc các sheet hợp lệ và giữ đúng thứ tự chọn của người dùng
        if selected_sheets and isinstance(selected_sheets, list) and len(selected_sheets) > 0:
            valid_sheets = [s for s in selected_sheets if s in existing_sheet_names]
        else:
            valid_sheets = existing_sheet_names

        if not valid_sheets:
            valid_sheets = existing_sheet_names

        # Chọn đúng danh sách valid_sheets và Export
        wb.Sheets(valid_sheets).Select()
        wb.ActiveSheet.ExportAsFixedFormat(0, abs_output_path) # 0 = xlTypePDF

    except Exception as e:
        raise Exception(f"Lỗi COM/win32 khi xuất PDF: {str(e)}")
    finally:
        if wb:
            wb.Close(False)
        if excel_app:
            excel_app.Quit()
        pythoncom.CoUninitialize()
        
@router.post("/inspect-sheets")
async def inspect_excel_sheets(files: List[UploadFile] = File(...)):
    """
    API MỚI: Đọc nhanh danh sách Sheet của từng file Excel tải lên.
    Dùng để hiển thị danh sách sheet cho người dùng chọn trên Frontend.
    """
    if not files:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất một file Excel.")

    result = []
    temp_dir = tempfile.mkdtemp()

    try:
        for idx, file in enumerate(files):
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in [".xlsx", ".xls"]:
                continue

            temp_file_path = os.path.join(temp_dir, f"inspect_{idx}{ext}")
            with open(temp_file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            sheets = []
            if ext == ".xlsx":
                wb = openpyxl.load_workbook(temp_file_path, read_only=True, keep_links=False)
                sheets = wb.sheetnames
                wb.close()
            elif ext == ".xls":
                wb = xlrd.open_workbook(temp_file_path, on_demand=True)
                sheets = wb.sheet_names()

            result.append({
                "file_index": idx,
                "filename": file.filename,
                "sheets": sheets
            })

        return JSONResponse(content={"success": True, "data": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc thông tin sheet: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/convert")
async def batch_convert_excel_to_pdf(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    export_type: str = Form("zip"),  # 'zip' hoặc 'single_pdf'
    options: Optional[str] = Form(None)  # Chuỗi JSON chứa cấu hình chọn sheet & đổi tên
):
    """
    API CHUYỂN ĐỔI: Giữ nguyên logic cũ và hỗ trợ mở rộng chọn Sheet + đổi tên linh hoạt.
    """
    if not files:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất một file Excel.")

    # Giải mã options JSON từ Frontend nếu có
    parsed_options = {}
    if options:
        try:
            parsed_options = json.loads(options)
        except Exception:
            parsed_options = {}

    # Cấu hình chi tiết từng file từ Frontend:
    # Key là tên file gốc hoặc index của file (ví dụ: file_configs: {"0": {"sheets": ["Sheet1"], "custom_name": "TenMoi.pdf"}})
    file_configs = parsed_options.get("file_configs", {})

    temp_dir = tempfile.mkdtemp()

    try:
        generated_pdf_paths = []

        for idx, file in enumerate(files):
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in [".xlsx", ".xls"]:
                continue

            # Lưu file Excel tạm với tên tiếng Anh không dấu
            input_filename = f"file_{idx}{ext}"
            input_path = os.path.join(temp_dir, input_filename)

            with open(input_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # --- TÍNH TOÁN CẤU HÌNH CHO TỪNG FILE ---
            # Tìm cấu hình của file theo index hoặc tên file gốc
            cfg = file_configs.get(str(idx)) or file_configs.get(file.filename) or {}
            
            selected_sheets = cfg.get("sheets")  # Danh sách tên Sheet cần xuất theo thứ tự
            custom_name = cfg.get("custom_name") # Tên file PDF tùy chỉnh nếu có

            # Xử lý tên file đầu ra
            base_name = os.path.splitext(file.filename)[0]
            if custom_name and custom_name.strip():
                final_pdf_name = custom_name.strip()
                if not final_pdf_name.lower().endswith(".pdf"):
                    final_pdf_name += ".pdf"
            else:
                final_pdf_name = f"{base_name}.pdf"

            output_pdf_path = os.path.join(temp_dir, f"out_{idx}.pdf")

            # Thực hiện chuyển đổi sang PDF (truyền danh sách sheet được chọn)
            convert_excel_to_pdf_win32(input_path, output_pdf_path, selected_sheets=selected_sheets)

            if os.path.exists(output_pdf_path):
                generated_pdf_paths.append((final_pdf_name, output_pdf_path))

        if not generated_pdf_paths:
            raise HTTPException(status_code=400, detail="Không có file Excel hợp lệ nào được chuyển đổi.")
        # Lấy custom_filename tổng (nếu có truyền ở cấp cao nhất trong options)
        global_custom_name = parsed_options.get("global_custom_name", "").strip()
        # XỬ LÝ ĐẦU RA (ZIP / SINGLE PDF)
        if export_type == "zip":
            zip_filename = global_custom_name if global_custom_name else "Excel_Exported_PDFs.zip"
            if not zip_filename.lower().endswith(".zip"):
                zip_filename += ".zip"

            zip_path = os.path.join(temp_dir, "output.zip")

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for pdf_name, pdf_path in generated_pdf_paths:
                    zipf.write(pdf_path, arcname=pdf_name)

            background_tasks.add_task(remove_temp_dir, temp_dir)
            return FileResponse(path=zip_path, filename=zip_filename, media_type="application/zip")

        elif export_type == "single_pdf":
            merged_filename = global_custom_name if global_custom_name else "Excel_Merged_Export.pdf"
            if not merged_filename.lower().endswith(".pdf"):
                merged_filename += ".pdf"

            merged_path = os.path.join(temp_dir, "output.pdf")

            merger = PdfWriter()
            for _, pdf_path in generated_pdf_paths:
                merger.append(pdf_path)

            merger.write(merged_path)
            merger.close()

            background_tasks.add_task(remove_temp_dir, temp_dir)
            return FileResponse(path=merged_path, filename=merged_filename, media_type="application/pdf")

        else:
            raise HTTPException(status_code=400, detail="Tham số export_type không hợp lệ.")

    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("\n--- CHI TIẾT LỖI CONVERT EXCEL ---")
        traceback.print_exc()
        print("-----------------------------------\n")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý Excel: {str(e)}")