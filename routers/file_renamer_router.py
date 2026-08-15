import os
import json
import shutil
import tempfile
import re
import unicodedata
import zipfile
from typing import List, Dict, Any
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix="/api/file-renamer", tags=["FileRenamer"])


def remove_vietnamese_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt khỏi chuỗi text."""
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text


def compute_new_filename(stem: str, ext: str, rule_mode: str, config: Dict[str, Any], index: int) -> str:
    """
    Tính toán tên mới của file dựa trên rule_mode và config.
    stem: tên file không gồm đuôi mở rộng.
    ext: đuôi file bao gồm dấu chấm (vd: .pdf).
    index: chỉ số thứ tự (0-indexed).
    """
    new_stem = stem

    if rule_mode == "SPLIT_SEPARATOR":
        sep = config.get("separator", "_")
        action = config.get("action", "BEFORE_FIRST")
        index_n = int(config.get("index_n", 1))

        if sep in stem:
            parts = stem.split(sep)
            if action == "BEFORE_FIRST":
                new_stem = parts[0]
            elif action == "AFTER_FIRST":
                new_stem = sep.join(parts[1:])
            elif action == "BEFORE_LAST":
                new_stem = sep.join(parts[:-1])
            elif action == "AFTER_LAST":
                new_stem = parts[-1]
            elif action == "INDEX_N":
                # index_n là 1-based
                if 1 <= index_n <= len(parts):
                    new_stem = parts[index_n - 1]
                else:
                    new_stem = stem

    elif rule_mode == "REPLACE_REMOVE":
        search_text = config.get("search_text", "")
        replace_text = config.get("replace_text", "")
        match_case = config.get("match_case", False)

        if search_text:
            if match_case:
                new_stem = stem.replace(search_text, replace_text)
            else:
                pattern = re.escape(search_text)
                new_stem = re.sub(pattern, replace_text, stem, flags=re.IGNORECASE)

    elif rule_mode == "PREFIX_SUFFIX":
        prefix = config.get("prefix", "")
        suffix = config.get("suffix", "")
        new_stem = f"{prefix}{stem}{suffix}"

    elif rule_mode == "SEQUENCE_NUMBERING":
        base_name = config.get("base_name", "")
        start_number = int(config.get("start_number", 1))
        padding_digits = int(config.get("padding_digits", 2))
        position = config.get("position", "SUFFIX")  # PREFIX, SUFFIX, REPLACE_ALL

        seq_val = start_number + index
        formatted_num = str(seq_val).zfill(padding_digits)

        if position == "REPLACE_ALL":
            new_stem = f"{base_name}{formatted_num}" if base_name else formatted_num
        elif position == "PREFIX":
            prefix_str = f"{base_name}_" if base_name else ""
            new_stem = f"{prefix_str}{formatted_num}_{stem}"
        elif position == "SUFFIX":
            suffix_str = f"_{base_name}" if base_name else ""
            new_stem = f"{stem}{suffix_str}_{formatted_num}"

    elif rule_mode == "CASE_CONVERSION":
        case_type = config.get("case_type", "UPPER")
        if case_type == "UPPER":
            new_stem = stem.upper()
        elif case_type == "LOWER":
            new_stem = stem.lower()
        elif case_type == "TITLE":
            new_stem = stem.title()
        elif case_type == "REMOVE_ACCENTS":
            new_stem = remove_vietnamese_accents(stem)

    # Đảm bảo tên file không rỗng
    if not new_stem.strip():
        new_stem = stem

    return f"{new_stem}{ext}"


def cleanup_directory(dir_path: str):
    """Hàm phụ trợ dọn dẹp thư mục tạm sau khi trả response."""
    try:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path, ignore_errors=True)
    except Exception as e:
        print(f"Lỗi khi dọn dẹp thư mục tạm {dir_path}: {e}")


@router.post("/preview")
async def preview_rename(
    files: List[UploadFile] = File(...),
    rule_mode: str = Form(...),
    rule_config: str = Form(...)
):
    """API Preview danh sách tên file sau khi áp dụng quy tắc."""
    try:
        try:
            config = json.loads(rule_config)
        except Exception:
            config = {}

        items = []
        new_names_seen = {}
        has_conflict = False

        for idx, file_item in enumerate(files):
            orig_filename = file_item.filename
            path_obj = Path(orig_filename)
            stem = path_obj.stem
            ext = path_obj.suffix

            new_filename = compute_new_filename(stem, ext, rule_mode, config, idx)

            # Kiểm tra xung đột trùng tên
            status = "OK"
            message = ""
            if new_filename in new_names_seen:
                has_conflict = True
                status = "CONFLICT"
                message = f"Trùng tên với file số {new_names_seen[new_filename] + 1}"
                # Đánh dấu cả file trước đó bị trùng
                items[new_names_seen[new_filename]]["status"] = "CONFLICT"
                items[new_names_seen[new_filename]]["message"] = f"Trùng tên với file số {idx + 1}"
            else:
                new_names_seen[new_filename] = idx

            items.append({
                "id": f"file_{idx + 1}",
                "original_name": orig_filename,
                "new_name": new_filename,
                "ext": ext,
                "status": status,
                "message": message
            })

        return {
            "success": True,
            "total_files": len(files),
            "has_conflict": has_conflict,
            "items": items
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý Preview: {str(e)}")


@router.post("/process")
async def process_rename(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    rule_mode: str = Form(...),
    rule_config: str = Form(...)
):
    """API thực hiện đổi tên và đóng gói vào file ZIP trả về."""
    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(cleanup_directory, temp_dir)

    try:
        try:
            config = json.loads(rule_config)
        except Exception:
            config = {}

        zip_filename = "DanhSachFile_DaDoiTen.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        # Xử lý lưu các file đã đổi tên và nén lại
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            used_names = set()

            for idx, file_item in enumerate(files):
                orig_filename = file_item.filename
                path_obj = Path(orig_filename)
                stem = path_obj.stem
                ext = path_obj.suffix

                new_filename = compute_new_filename(stem, ext, rule_mode, config, idx)

                # Nếu bị trùng tên thực tế khi ghi, thêm số thứ tự hậu tố để tránh ghi đè
                final_filename = new_filename
                conflict_counter = 1
                while final_filename in used_names:
                    final_stem = Path(new_filename).stem
                    final_filename = f"{final_stem}_({conflict_counter}){ext}"
                    conflict_counter += 1

                used_names.add(final_filename)

                # Đọc nội dung file
                file_content = await file_item.read()

                # Viết trực tiếp vào zip archive
                zip_file.writestr(final_filename, file_content)

        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi thực hiện đổi tên file: {str(e)}")