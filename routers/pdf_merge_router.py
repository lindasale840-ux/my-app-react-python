import os
import tempfile
import zipfile
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pypdf import PdfReader, PdfWriter

router = APIRouter(prefix="/api/pdf_merge", tags=["PDF Merge"])

@router.post("/merge-by-name")
async def merge_by_name(
    files_a: List[UploadFile] = File(...),
    files_b: List[UploadFile] = File(...)
):
    temp_dir = tempfile.mkdtemp()
    try:
        output_dir = os.path.join(temp_dir, "merge_by_name")
        os.makedirs(output_dir, exist_ok=True)

        # Lưu temporary files B vào dict
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

        # Ghép PDF theo tên file
        for file_a in files_a:
            file_name = file_a.filename
            key = file_name.lower()

            # Lưu file A tạm thời
            file_a_path = os.path.join(temp_dir, f"a_{file_name}")
            with open(file_a_path, "wb") as f:
                content = await file_a.read()
                f.write(content)

            if key not in dict_b_paths:
                skipped_count += 1
                continue

            path_b = dict_b_paths[key]
            writer = PdfWriter()

            # Đọc file A
            reader_a = PdfReader(file_a_path)
            for page in reader_a.pages:
                writer.add_page(page)

            # Đọc file B
            reader_b = PdfReader(path_b)
            for page in reader_b.pages:
                writer.add_page(page)

            # Xuất PDF ghép
            output_pdf = os.path.join(output_dir, file_name)
            with open(output_pdf, "wb") as f:
                writer.write(f)

            merged_count += 1

        if merged_count == 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Không tìm thấy file nào trùng tên để ghép. Bỏ qua {skipped_count} file."
            )

        # Nén thư mục output thành file ZIP
        zip_path = os.path.join(temp_dir, "Merged_By_Name.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in os.listdir(output_dir):
                zipf.write(os.path.join(output_dir, file), arcname=file)

        # Trả về FileResponse (FastAPI sẽ gửi kèm header custom để FE đọc số lượng)
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