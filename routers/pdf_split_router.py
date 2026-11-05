import os
import re
import fitz  # PyMuPDF
import zipfile
import tempfile
import pandas as pd
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/pdfsplit", tags=["PDFSplit"])

# ==============================================================================
# BỘ TỪ KHÓA MỎ NEO ĐA NGÔN NGỮ (VIỆT - ANH - TRUNG)
# ==============================================================================
KEYWORDS_SO_GCN = [
    "Mã số GCN", "Số GCN", "Số/No", "Certificate No.", "Certificate No", 
    "No.", "证书编号", "证书号", "编号"
]

KEYWORDS_MA_QL = [
    "Mã quản lý", "Mã QL", "Management No.", "Management No", "Mgmt No",
    "管理号", "管理编号", "器具编号"
]

KEYWORDS_TEN_TB = [
    "Tên thiết bị", "Tên mẫu", "Thiết bị", "Name of Object", "Sample Name", 
    "Instrument Name", "Equipment", "Description", "器具名称", "样品名称", "仪器名称"
]

KEYWORDS_KIEU_MAY = [
    "Kiểu máy", "Model/Type", "Model", "Type", "Specifications", "Specification",
    "型号/规格", "型号规格", "型号", "规格", "技术特征"
]

# Các từ rác tiêu đề cần lọc bỏ khi bốc trúng chữ xung quanh mỏ neo
TRASH_TEXTS = [
    "Technical specifications", "Technical Specification", "Technical spec",
    "Management No.", "Management No", "Certificate No.", "Certificate No",
    "Specification", "Specifications", "技术特征", "技术", "见结果页", "见結果页",
    "Đặc trưng", "Đặc Trưng"
]

# ==============================================================================
# HÀM HỖ TRỢ XỬ LÝ CHUỖI & TÌM KIẾM
# ==============================================================================
def parse_keywords(keyword_input: str) -> List[str]:
    if not keyword_input:
        return []
    keywords = re.split(r'[,;\n]+', str(keyword_input))
    return [kw.strip() for kw in keywords if kw.strip()]

def search_any_keyword_in_page(page, keyword_list: List[str]) -> bool:
    for kw in keyword_list:
        rects = page.search_for(kw, flags=1)
        if rects:
            return True
    return False

def clean_extracted_value(text: str) -> str:
    if not text:
        return ""
    for trash in TRASH_TEXTS:
        text = re.sub(re.escape(trash), "", text, flags=re.IGNORECASE)

    text = text.replace(":", "").replace("：", "").replace("\n", " ").strip()
    text = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', text)
    text = re.sub(r'\s*-\s*', '-', text)  # Giữ nguyên dấu - chuẩn không bị dính khoảng trắng
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_text_next_to_anchors(page, anchor_keywords: List[str], shift_right=450, shift_down=35) -> str:
    """
    Tìm vị trí Mỏ neo (Anchor keyword). 
    Quét vùng bên phải, nếu không có chữ thì quét vùng ngay bên dưới.
    """
    for kw in anchor_keywords:
        rects = page.search_for(kw, flags=1)
        if rects:
            rect = rects[0]
            # 1. Thử lấy chữ bên phải mỏ neo
            search_area_right = fitz.Rect(rect.x1, rect.y0 - 2, rect.x1 + shift_right, rect.y1 + 4)
            val_right = page.get_text("text", clip=search_area_right).strip()
            clean_val = clean_extracted_value(val_right)
            if clean_val and len(clean_val) > 1:
                return clean_val

            # 2. Nếu bên phải trống, thử lấy chữ dòng bên dưới mỏ neo
            search_area_below = fitz.Rect(rect.x0 - 5, rect.y1, rect.x1 + shift_right, rect.y1 + shift_down)
            val_below = page.get_text("text", clip=search_area_below).strip()
            clean_val_below = clean_extracted_value(val_below)
            if clean_val_below and len(clean_val_below) > 1:
                return clean_val_below
    return ""

def extract_gcn_with_flexible_regex(page) -> Optional[str]:
    """
    Tìm Mã GCN: Chỉ lấy chữ nằm cạnh từ khóa 'Số GCN', 'Certificate No', '证书编号'...
    """
    # Nếu truyền vào đối tượng trang PDF (PyMuPDF page)
    if hasattr(page, "search_for"):
        # Tìm chữ bên cạnh/bên dưới mỏ neo Số GCN
        val_anchor = get_text_next_to_anchors(page, KEYWORDS_SO_GCN)
        if val_anchor:
            # Lấy mã dạng C202607-R0108 trong vùng mỏ neo
            m = re.search(r'([A-Z0-9]{2,}\s*[-_]\s*[A-Z0-9]{2,}(?:\s*[-_]\s*[A-Z0-9]+)?)', val_anchor, re.IGNORECASE)
            if m:
                return re.sub(r'\s*', '', m.group(1)).upper()
            # Nếu vùng mỏ neo không có dấu gạch ngang, trả về nguyên chuỗi đã làm sạch
            return val_anchor

    # Fallback nếu truyền vào là chuỗi text thuần
    text = page.get_text("text") if hasattr(page, "get_text") else str(page)
    m = re.search(r'([A-Z0-9]{2,}\s*[-_]\s*[A-Z0-9]{2,}(?:\s*[-_]\s*[A-Z0-9]+)?)', text, re.IGNORECASE)
    return re.sub(r'\s*', '', m.group(1)).upper() if m else None

def extract_info_smart_anchors(page, naming_type: str) -> Optional[str]:
    """Trích xuất thông tin dựa vào Mỏ Neo Từ Khóa + Fallback Regex"""
    full_text = page.get_text("text")

    if naming_type == "so_gcn":
        val = get_text_next_to_anchors(page, KEYWORDS_SO_GCN)
        if val:
            gcn_match = extract_gcn_with_flexible_regex(val)
            if gcn_match:
                return gcn_match
            return val
        # Fallback toàn trang
        return extract_gcn_with_flexible_regex(full_text)

    elif naming_type == "ma_ql":
        val = get_text_next_to_anchors(page, KEYWORDS_MA_QL)
        if val and val.lower() not in ["/", "", "none", "nan", "号"]:
            return val
        # Fallback Regex mã QL phổ biến (vd: PC-13624, TB-01)
        match_ma = re.search(r'([A-Z]{1,4}\s*[-_]\s*\d{3,6})', full_text, re.IGNORECASE)
        if match_ma:
            return re.sub(r'\s*', '', match_ma.group(1)).upper()

    elif naming_type == "ten_tb":
        raw_ten = get_text_next_to_anchors(page, KEYWORDS_TEN_TB)
        raw_kieu = get_text_next_to_anchors(page, KEYWORDS_KIEU_MAY)
        
        # Làm sạch nâng cao cho tên thiết bị
        if "/" in raw_ten:
            raw_ten = raw_ten.split("/")[0].strip()
        if "(" in raw_ten:
            raw_ten = raw_ten.split("(")[0].strip()

        if raw_kieu and raw_kieu in raw_ten:
            raw_ten = raw_ten.replace(raw_kieu, "").strip()

        if raw_ten and raw_kieu:
            return f"{raw_ten}_{raw_kieu}"
        return raw_ten if raw_ten else raw_kieu

    # Mặc định Fallback lấy Số GCN
    gcn_fallback = extract_gcn_with_flexible_regex(full_text)
    return f"GCN_{gcn_fallback}" if gcn_fallback else None

def append_page_count_to_filename(base_name: str, page_count: int, include_page_count: bool) -> str:
    """
    Nối số trang vào cuối tên file nếu include_page_count = True.
    Ví dụ: 'MA_QL_01' -> 'MA_QL_01_3Trang'
    """
    if include_page_count and page_count > 0:
        return f"{base_name}_{page_count}Trang"
    return base_name


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@router.post("/split-smart")
async def split_pdf_smart(
    pdf_file: UploadFile = File(...),
    keyword: str = Form("Giấy chứng nhận, Certificate, 证书"),
    naming_type: str = Form("ma_ql"),
    include_page_count: bool = Form(False)  # <-- THÊM THAM SỐ NÀY
):
    keyword_list = parse_keywords(keyword)
    if not keyword_list:
        raise HTTPException(status_code=400, detail="Từ khóa nhập vào bị trống!")

    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, pdf_file.filename)
    
    try:
        content = await pdf_file.read()
        with open(pdf_path, "wb") as f:
            f.write(content)

        doc = fitz.open(pdf_path)
        cut_points = [i for i in range(len(doc)) if search_any_keyword_in_page(doc[i], keyword_list)]

        if not cut_points:
            doc.close()
            raise HTTPException(status_code=400, detail="Không tìm thấy từ khóa nào trong file PDF!")

        zip_path = os.path.join(temp_dir, f"Ket_Qua_Tach_Theo_{naming_type}.zip")
        used_names = {}

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for i in range(len(cut_points)):
                start = cut_points[i]
                end = cut_points[i + 1] if i + 1 < len(cut_points) else len(doc)

                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start, to_page=end - 1)

                page_count = len(new_doc)  # <-- ĐẾM SỐ TRANG CỦA FILE TÁCH
                first_page = new_doc[0]
                extracted_name = extract_info_smart_anchors(first_page, naming_type)

                if not extracted_name:
                    filename_base = f"Khong_Do_Duoc_Ten_{i+1}"
                else:
                    filename_base = re.sub(r'\s+', ' ', extracted_name).strip()
                    filename_base = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', filename_base)

                # <-- NỐI HẬU TỐ SỐ TRANG NẾU CÓ CHỌN
                filename_base = append_page_count_to_filename(filename_base, page_count, include_page_count)

                if filename_base in used_names:
                    used_names[filename_base] += 1
                    filename = f"{filename_base}_{used_names[filename_base]}.pdf"
                else:
                    used_names[filename_base] = 0
                    filename = f"{filename_base}.pdf"

                temp_pdf_path = os.path.join(temp_dir, filename)
                new_doc.save(temp_pdf_path)
                zipf.write(temp_pdf_path, filename)
                new_doc.close()

        doc.close()
        return FileResponse(
            path=zip_path,
            filename=f"Tach_PDF_{naming_type}.zip",
            media_type="application/zip"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/split-excel")
async def split_pdf_excel(
    pdf_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
    keyword: str = Form("Giấy chứng nhận, Certificate, Certificate of Calibration, 证书"),
    naming_type: str = Form("ten_tb"),
    include_page_count: bool = Form(False)  # <-- THÊM THAM SỐ NÀY
):
    keywords = parse_keywords(keyword)
    if not keywords:
        raise HTTPException(status_code=400, detail="Vui lòng nhập ít nhất một từ khóa!")

    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, pdf_file.filename)
    excel_path = os.path.join(temp_dir, excel_file.filename)

    try:
        with open(pdf_path, "wb") as f:
            f.write(await pdf_file.read())
        with open(excel_path, "wb") as f:
            f.write(await excel_file.read())

        doc = fitz.open(pdf_path)
        has_keyword = any(search_any_keyword_in_page(page, keywords) for page in doc)
        if not has_keyword:
            doc.close()
            raise HTTPException(status_code=400, detail=f"Không tìm thấy từ khóa nào trong danh sách '{keyword}'!")

        df = pd.read_excel(excel_path, header=None, dtype=str)
        df[25] = df[25].fillna("").str.strip().str.upper()

        cut_points = []
        last_gcn_found = None

        for i, page in enumerate(doc):
            if search_any_keyword_in_page(page, keywords):
                page_text = page.get_text("text")
                current_gcn = extract_gcn_with_flexible_regex(page)

                if not cut_points or (current_gcn and current_gcn != last_gcn_found):
                    cut_points.append(i)
                    if current_gcn:
                        last_gcn_found = current_gcn

        zip_path = os.path.join(temp_dir, f"Tach_Excel_Theo_{naming_type}.zip")
        used_names = {}

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for i in range(len(cut_points)):
                start = cut_points[i]
                end = cut_points[i + 1] if i + 1 < len(cut_points) else len(doc)

                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start, to_page=end - 1)

                page_count = len(new_doc)  # <-- ĐẾM SỐ TRANG CỦA FILE TÁCH
                first_page_text = new_doc[0].get_text("text")
                gcn_key = extract_gcn_with_flexible_regex(new_doc[0])

                if gcn_key:
                    final_filename = f"GCN_{gcn_key}_Khong_Co_Trong_Excel"
                    excel_column_clean = (
                        df[25].astype(str)
                        .str.strip()
                        .str.upper()
                        .str.replace(r'\s*', '', regex=True)
                        .str.replace('_', '-')
                    )

                    clean_gcn_key = gcn_key.replace('_', '-')
                    matched_rows = df[excel_column_clean == clean_gcn_key]

                    if matched_rows.empty:
                        matched_rows = df[excel_column_clean.str.contains(gcn_key, na=False, regex=False)]

                    if not matched_rows.empty:
                        row = matched_rows.iloc[0]
                        excel_ten = str(row[5]).strip() if pd.notna(row[5]) else ""
                        excel_kieu = str(row[6]).strip() if pd.notna(row[6]) else ""
                        excel_ma_ql = str(row[27]).strip() if pd.notna(row[27]) else ""

                        if naming_type == "ten_tb":
                            clean_ten = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', excel_ten)
                            clean_kieu = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', excel_kieu)
                            if clean_kieu and clean_kieu in clean_ten:
                                clean_ten = clean_ten.replace(clean_kieu, "").strip()
                            if clean_ten and clean_kieu:
                                final_filename = f"{clean_ten}_{clean_kieu}"
                            else:
                                final_filename = clean_ten if clean_ten else (clean_kieu if clean_kieu else f"ThietBi_{gcn_key}")
                        elif naming_type == "ma_ql":
                            if excel_ma_ql in ["/", "", "nan"] or "nan" in excel_ma_ql.lower():
                                final_filename = f"Khong_Thay_MaQL_{gcn_key}"
                            else:
                                final_filename = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', excel_ma_ql)
                        elif naming_type == "so_gcn":
                            final_filename = f"{gcn_key}"
                        elif naming_type == "gcn_ten_tb":
                            clean_ten = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', excel_ten)
                            final_filename = f"{gcn_key}_{clean_ten}" if clean_ten else f"GCN_{gcn_key}"
                else:
                    final_filename = f"Khong_Do_Duoc_GCN_{i+1}"

                final_filename = re.sub(r'\s+', ' ', final_filename).strip()

                # <-- NỐI HẬU TỐ SỐ TRANG NẾU CÓ CHỌN
                final_filename = append_page_count_to_filename(final_filename, page_count, include_page_count)

                if final_filename in used_names:
                    used_names[final_filename] += 1
                    filename = f"{final_filename} ({used_names[final_filename]}).pdf"
                else:
                    used_names[final_filename] = 0
                    filename = f"{final_filename}.pdf"

                temp_pdf_path = os.path.join(temp_dir, filename)
                new_doc.save(temp_pdf_path)
                zipf.write(temp_pdf_path, filename)
                new_doc.close()

        doc.close()
        return FileResponse(
            path=zip_path,
            filename=f"Tach_Excel_{naming_type}.zip",
            media_type="application/zip"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))