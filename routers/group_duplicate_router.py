import os
import re
import shutil
import tempfile
import zipfile
from collections import defaultdict
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/group-duplicate", tags=["Group Duplicate"])


def get_base_name(filename: str) -> str:
    name = os.path.splitext(filename)[0]

    # Khớp mẫu ABC_1, ABC_02, ABC_123
    match = re.match(r"^(.*?)_(\d{1,3})$", name)
    if match:
        return match.group(1).strip()

    # Khớp mẫu ABC(1), ABC(02), ABC(123)
    match = re.match(r"^(.*?)\((\d{1,3})\)$", name)
    if match:
        return match.group(1).strip()

    return name.strip()


@router.post("/process")
async def group_duplicate_files(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ít nhất một file.")

    temp_dir = tempfile.mkdtemp()
    output_root = os.path.join(temp_dir, "group_duplicate_result")

    try:
        os.makedirs(output_root, exist_ok=True)
        groups = defaultdict(list)

        # 1. Lưu tạm file và phân nhóm theo base_name
        for file in files:
            base_name = get_base_name(file.filename)
            groups[base_name].append(file)

        largest_group = ""
        largest_count = 0
        total_files = 0

        # 2. Tạo cấu trúc thư mục con cho từng nhóm và lưu file
        for group_name, group_files in groups.items():
            folder_path = os.path.join(output_root, group_name)
            os.makedirs(folder_path, exist_ok=True)

            count = 0
            for file in group_files:
                save_path = os.path.join(folder_path, file.filename)
                contents = await file.read()
                with open(save_path, "wb") as f:
                    f.write(contents)

                count += 1
                total_files += 1

            if count > largest_count:
                largest_count = count
                largest_group = group_name

        # 3. Nén tất cả các thư mục con thành file ZIP
        zip_path = os.path.join(temp_dir, "HoSo_Gom.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, filenames in os.walk(output_root):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    arcname = os.path.relpath(full_path, output_root)
                    zipf.write(full_path, arcname)

        headers = {
            "Access-Control-Expose-Headers": "X-Total-Groups, X-Total-Files, X-Largest-Group, X-Largest-Count",
            "X-Total-Groups": str(len(groups)),
            "X-Total-Files": str(total_files),
            "X-Largest-Group": str(largest_group),
            "X-Largest-Count": str(largest_count),
        }

        return FileResponse(
            path=zip_path,
            filename="HoSo_Gom.zip",
            media_type="application/zip",
            headers=headers
        )

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý gom hồ sơ: {str(e)}")