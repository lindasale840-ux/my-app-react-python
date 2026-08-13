from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from typing import List, Annotated
import os
import urllib.parse
from fastapi.responses import Response
import zipfile
import io
from fastapi.responses import StreamingResponse
import pandas as pd

# Import các logic xử lý từ thư mục services
from services.pdf_merge_service_react import merge_pdfs_logic
from services.pdf_split_service_react import get_pdf_thumbnails_logic, split_pdf_by_ranges_logic
from services.pdf_compress_service_react import compress_pdf_logic
from services.pdf_reduce_service_react import reduce_pdf_logic
from services.pdf_version_service_react import run_pdf_version_downgrade
from services.pdf_remove_blank_service_react import run_remove_blank_pages_batch
from services.pdf_group_service_react import parse_excel_columns, process_group_pdfs
from services.pdf_compare_service_react import (
    parse_excel_columns,
    compare_excel_vs_pdf_filenames,
    compare_excel_vs_pdf_content
)

router = APIRouter(prefix="/api/pdf", tags=["PDF Operations"])

# 1. API Ghép PDF (Chuyển từ main.py cũ sang)
@router.post("/merge")
async def api_merge_pdfs(
    files: Annotated[List[UploadFile], File(description="Chọn các file PDF cần ghép")]
):
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

# 2. API Lấy danh sách ảnh Thumbnails của file PDF
@router.post("/thumbnails")
async def api_get_pdf_thumbnails(file: Annotated[UploadFile, File(...)]):
    file_bytes = await file.read()
    thumbnails = get_pdf_thumbnails_logic(file_bytes)
    return {"total_pages": len(thumbnails), "thumbnails": thumbnails}

# 3. API Cắt PDF theo danh sách điểm cắt
@router.post("/split-ranges")
async def api_split_pdf_ranges(
    file: Annotated[UploadFile, File(...)],
    ranges_text: Annotated[str, Form(...)]
):
    file_bytes = await file.read()
    zip_path, message = split_pdf_by_ranges_logic(file_bytes, ranges_text)
    
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=500, detail=f"Lỗi khi tách file: {message}")
        
    return FileResponse(
        path=zip_path,
        filename="Split_Results.zip",
        media_type="application/zip"
    )
    
@router.post("/compress")
async def api_compress_pdf(
    file: Annotated[UploadFile, File(...)],
    mode: Annotated[str, Form(...)] = "normal"
):
    file_bytes = await file.read()
    output_path, message, old_size, new_size = compress_pdf_logic(file_bytes, mode)

    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail=f"Lỗi khi nén file: {message}")

    return FileResponse(
        path=output_path,
        filename=f"compressed_{file.filename}",
        media_type="application/pdf",
        headers={
            "X-Old-Size": str(old_size),
            "X-New-Size": str(new_size),
            "Access-Control-Expose-Headers": "X-Old-Size, X-New-Size"
        }
    )    

# THÊM ENDPOINT GIẢM DUNG LƯỢNG PDF
@router.post("/reduce")
async def api_reduce_pdf(
    file: Annotated[UploadFile, File(...)],
    dpi: Annotated[int, Form(...)] = 120,
    quality: Annotated[int, Form(...)] = 70
):
    file_bytes = await file.read()
    output_path, old_size, new_size = reduce_pdf_logic(file_bytes, dpi, quality)

    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Lỗi khi xử lý giảm dung lượng PDF")

    return FileResponse(
        path=output_path,
        filename=f"reduced_{file.filename}",
        media_type="application/pdf",
        headers={
            "X-Old-Size": str(old_size),
            "X-New-Size": str(new_size),
            "Access-Control-Expose-Headers": "X-Old-Size, X-New-Size"
        }
    )
    
@router.post("/downgrade-version")
async def api_downgrade_pdf_version(
    file: Annotated[UploadFile, File(...)],
    compatibility: Annotated[str, Form(...)] = "1.4"
):
    file_bytes = await file.read()
    output_path, error_msg = run_pdf_version_downgrade(file_bytes, compatibility)

    if error_msg or not output_path or not os.path.exists(output_path):
        raise HTTPException(
            status_code=500, 
            detail=f"Lỗi khi hạ phiên bản PDF: {error_msg or 'Không tạo được file'}"
        )

    return FileResponse(
        path=output_path,
        filename=f"v{compatibility}_{file.filename}",
        media_type="application/pdf"
    )    

@router.post("/remove-blank-pages")
async def api_remove_blank_pages(
    files: List[UploadFile] = File(...),
    threshold: Annotated[float, Form(...)] = 0.98
):
    if not files:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất 1 file PDF")

    files_data = []
    for f in files:
        content = await f.read()
        files_data.append((f.filename, content))

    output_bytes, summary_text, media_type, download_filename = run_remove_blank_pages_batch(
        files_data, threshold
    )

    encoded_summary = urllib.parse.quote(summary_text)

    return Response(
        content=output_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{download_filename}"',
            "X-Remove-Summary": encoded_summary,
            "Access-Control-Expose-Headers": "X-Remove-Summary, Content-Disposition"
        }
    ) 
    
@router.post("/parse-excel-cols")
async def api_parse_excel_cols(excel_file: UploadFile = File(...)):
    """Đọc xem file Excel có bao nhiêu cột để Frontend tạo Dropdown lựa chọn"""
    try:
        content = await excel_file.read()
        columns = parse_excel_columns(content)
        return {"columns": columns}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi khi đọc file Excel: {str(e)}")


@router.post("/group-by-excel")
async def api_group_pdf_by_excel(
    excel_file: UploadFile = File(...),
    pdf_files: List[UploadFile] = File(...),
    match_col_idx: Annotated[int, Form(...)] = 0,
    target_col_idx: Annotated[int, Form(...)] = 1
):
    if not pdf_files:
        raise HTTPException(status_code=400, detail="Vui lòng chọn ít nhất 1 file PDF")

    excel_bytes = await excel_file.read()
    
    pdfs_data = []
    for f in pdf_files:
        c = await f.read()
        pdfs_data.append((f.filename, c))

    try:
        zip_bytes, summary_msg = process_group_pdfs(
            excel_bytes=excel_bytes,
            pdfs_data=pdfs_data,
            match_col_idx=match_col_idx,
            target_col_idx=target_col_idx
        )

        encoded_summary = urllib.parse.quote(summary_msg)

        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="Ket_Qua_Gom_Nhom_PDF.zip"',
                "X-Group-Summary": encoded_summary,
                "Access-Control-Expose-Headers": "X-Group-Summary, Content-Disposition"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý phân loại: {str(e)}")
    
@router.post("/compare-excel-vs-pdf")
async def api_compare_excel_vs_pdf(
    excel_file: UploadFile = File(...),
    pdf_files: List[UploadFile] = File(...),
    column_index: Annotated[int, Form(...)] = 0,
    compare_mode: Annotated[str, Form(...)] = "filename", # "filename" hoặc "content"
    is_scan: Annotated[bool, Form(...)] = False
):
    if not pdf_files:
        raise HTTPException(status_code=400, detail="Vui lòng chọn ít nhất 1 file PDF!")

    excel_bytes = await excel_file.read()
    
    pdfs_data = []
    for f in pdf_files:
        content = await f.read()
        pdfs_data.append((f.filename, content))

    try:
        if compare_mode == "filename":
            result = compare_excel_vs_pdf_filenames(
                excel_bytes=excel_bytes,
                pdf_files=pdfs_data,
                column_index=column_index
            )
        else:
            result = compare_excel_vs_pdf_content(
                excel_bytes=excel_bytes,
                pdf_files=pdfs_data,
                column_index=column_index,
                is_scan=is_scan
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi thực hiện đối chiếu: {str(e)}")               
    

@router.post("/collect-and-zip")
async def collect_and_zip_pdf(
    excel_file: UploadFile = File(...),
    pdf_files: List[UploadFile] = File(...),
    selected_col: str = Form(...),
    zip_name: str = Form("Ket_Qua_Gom_PDF"),
    advanced_mode: bool = Form(False),
    cut_length: int = Form(9)
):
    try:
        # 1. Đọc file Excel
        contents = await excel_file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        if selected_col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Không tìm thấy cột '{selected_col}' trong file Excel.")
            
        excel_codes = df[selected_col].dropna().astype(str).str.strip().unique()
        
        # 2. Đọc danh sách file PDF tải lên vào bộ nhớ
        uploaded_pdfs = {}
        for pdf in pdf_files:
            pdf_bytes = await pdf.read()
            uploaded_pdfs[pdf.filename] = pdf_bytes

        matched_files = []  # Lưu tuple: (filename, bytes_data, subfolder_name)
        missing_codes = []

        # 3. Tiến hành đối chiếu và phân nhóm
        for code in excel_codes:
            subfolder_name = ""
            if advanced_mode:
                subfolder_name = code[:cut_length].strip()

            found = False
            for filename, file_bytes in uploaded_pdfs.items():
                if code in filename:
                    matched_files.append((filename, file_bytes, subfolder_name))
                    found = True

            if not found:
                missing_codes.append(code)

        if not matched_files:
            return {
                "success": False,
                "message": "Không tìm thấy file PDF nào trùng khớp với danh sách trong Excel!",
                "missing_codes": missing_codes
            }

        # 4. Tạo file ZIP trong Memory Buffer
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, file_bytes, subfolder in matched_files:
                if advanced_mode and subfolder:
                    archive_name = f"{subfolder}/{filename}"
                else:
                    archive_name = filename
                
                zipf.writestr(archive_name, file_bytes)

        zip_buffer.seek(0)
        
        # Đóng gói và trả về stream file ZIP để Frontend tải về trực tiếp
        filename_out = f"{zip_name}.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename_out}",
                "X-Missing-Codes": ",".join(missing_codes)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Có lỗi xảy ra: {str(e)}")    