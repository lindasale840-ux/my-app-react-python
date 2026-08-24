import os
import shutil
import tempfile
import zipfile
import traceback
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pypdf import PdfWriter

# TỰ ĐỘNG THÊM ĐƯỜNG DẪN DLL CHO WIN32COM (Xử lý lỗi thiếu pywin32 DLL)
try:
    import win32com.client
    import pythoncom
    WIN32_AVAILABLE = True
except ImportError:
    try:
        # Nếu import lỗi, thử nạp trực tiếp đường dẫn site-packages/pywin32_system32
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


def convert_excel_to_pdf_win32(excel_path: str, pdf_path: str):
    if not WIN32_AVAILABLE:
        raise Exception("Thư viện pywin32 chưa được cài đặt trên Server Windows.")

    # Khởi tạo COM cho thread hiện tại
    pythoncom.CoInitialize()
    excel_app = None
    wb = None
    try:
        # Gọi MS Excel ngầm
        excel_app = win32com.client.DispatchEx("Excel.Application")
        excel_app.Visible = False
        excel_app.DisplayAlerts = False
        excel_app.ScreenUpdating = False
        excel_app.EnableEvents = False
        
        try:
            excel_app.Interactive = False
        except Exception:
            pass

        # Sử dụng đường dẫn tuyệt đối chuẩn Windows
        abs_excel_path = os.path.abspath(excel_path)
        abs_pdf_path = os.path.abspath(pdf_path)

        # Mở workbook và xuất PDF (xlTypePDF = 0)
        wb = excel_app.Workbooks.Open(abs_excel_path, ReadOnly=True, UpdateLinks=False)
        wb.ExportAsFixedFormat(0, abs_pdf_path)

    except Exception as e:
        raise Exception(f"Lỗi MS Excel khi xử lý file '{os.path.basename(excel_path)}': {str(e)}")
    finally:
        if wb:
            try:
                wb.Close(False)
            except Exception:
                pass
        if excel_app:
            try:
                excel_app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


@router.post("/convert")
async def batch_convert_excel_to_pdf(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    export_type: str = Form("zip")  # 'zip' hoặc 'single_pdf'
):
    if not files:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất một file Excel.")

    # Tạo thư mục tạm an toàn trong thư mục Temp của Hệ Điều Hành
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

            # Tên file PDF đầu ra
            base_name = os.path.splitext(file.filename)[0]
            output_pdf_name = f"{base_name}.pdf"
            output_pdf_path = os.path.join(temp_dir, f"out_{idx}.pdf")

            # Thực hiện chuyển đổi sang PDF
            convert_excel_to_pdf_win32(input_path, output_pdf_path)

            if os.path.exists(output_pdf_path):
                generated_pdf_paths.append((output_pdf_name, output_pdf_path))

        if not generated_pdf_paths:
            raise HTTPException(status_code=400, detail="Không có file Excel hợp lệ nào được chuyển đổi.")

        # XỬ LÝ ĐẦU RA (ZIP / SINGLE PDF)
        if export_type == "zip":
            zip_filename = "Excel_Exported_PDFs.zip"
            zip_path = os.path.join(temp_dir, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for pdf_name, pdf_path in generated_pdf_paths:
                    zipf.write(pdf_path, arcname=pdf_name)

            # Đăng ký dọn dẹp thư mục tạm sau khi người dùng tải xong
            background_tasks.add_task(remove_temp_dir, temp_dir)
            return FileResponse(path=zip_path, filename=zip_filename, media_type="application/zip")

        elif export_type == "single_pdf":
            merged_filename = "Excel_Merged_Export.pdf"
            merged_path = os.path.join(temp_dir, merged_filename)

            merger = PdfWriter()
            for _, pdf_path in generated_pdf_paths:
                merger.append(pdf_path)

            merger.write(merged_path)
            merger.close()

            # Đăng ký dọn dẹp thư mục tạm sau khi người dùng tải xong
            background_tasks.add_task(remove_temp_dir, temp_dir)
            return FileResponse(path=merged_path, filename=merged_filename, media_type="application/pdf")

        else:
            raise HTTPException(status_code=400, detail="Tham số export_type không hợp lệ.")

    except HTTPException:
        # Nếu có lỗi HTTP xảy ra, dọn dẹp thư mục tạm ngay lập tức
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    except Exception as e:
        # Dọn dẹp thư mục tạm nếu gặp lỗi hệ thống khác
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("\n--- CHI TIẾT LỖI CONVERT EXCEL ---")
        traceback.print_exc()
        print("-----------------------------------\n")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý Excel: {str(e)}")