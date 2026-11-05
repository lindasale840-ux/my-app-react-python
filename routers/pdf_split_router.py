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
    "No.", "证书编号", "证书号", "编号", "Mã GCN", "GCN No"
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

def clean_extracted_value(text: str, anchor_keywords: List[str] = None) -> str:
    if not text:
        return ""
    
    # 1. Nếu giá trị quét ra trùng hoặc chứa chính từ khóa mỏ neo -> loại bỏ ngay
    if anchor_keywords:
        for kw in anchor_keywords:
            if kw.lower() in text.lower():
                text = text.replace(kw, "").strip()

    # 2. Cắt bỏ các cụm từ rác kỹ thuật
    trash_patterns = [
        r"kỹ thuật.*", r"ky thuat.*", r"xem trang kết quả.*", r"xem kết quả.*",
        r"see results.*", r"specification.*", r"technical.*",
        r"\(.*?\)"
    ]
    for pattern in trash_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    for trash in TRASH_TEXTS:
        text = re.sub(re.escape(trash), "", text, flags=re.IGNORECASE)

    # 3. Chỉ lấy dòng đầu tiên
    text = text.split('\n')[0].strip()

    text = text.replace(":", "").replace("：", "").strip()
    text = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', text)
    text = re.sub(r'\s*-\s*', '-', text)  
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_text_next_to_anchors(page, anchor_keywords: List[str], shift_right=400, shift_down=35) -> str:
    """
    Tìm vị trí Mỏ neo. Cho phép nhận mã ngắn từ 1 ký tự (len >= 1 như 1, 2, 3),
    nhưng loại trừ tuyệt đối các từ rác đơn lẻ.
    """
    for kw in anchor_keywords:
        rects = page.search_for(kw, flags=1)
        if rects:
            for rect in rects:
                # 1. Thử lấy chữ bên phải mỏ neo
                search_area_right = fitz.Rect(rect.x1, rect.y0 - 2, rect.x1 + shift_right, rect.y1 + 4)
                val_right = page.get_text("text", clip=search_area_right).strip()
                clean_val = clean_extracted_value(val_right, anchor_keywords)
                
                # Cho phép len >= 1 (để nhận '1', '2', '3'), nhưng loại bỏ các từ rác cụ thể
                if clean_val and len(clean_val) >= 1 and clean_val.lower() not in [kw.lower(), "số", "so", "_", "-", "khách hàng", "khach hang"]:
                    return clean_val

                # 2. Nếu bên phải trống, lấy chữ dòng bên dưới mỏ neo
                search_area_below = fitz.Rect(rect.x0 - 5, rect.y1, rect.x1 + shift_right, rect.y1 + shift_down)
                val_below = page.get_text("text", clip=search_area_below).strip()
                clean_val_below = clean_extracted_value(val_below, anchor_keywords)
                if clean_val_below and len(clean_val_below) >= 1 and clean_val_below.lower() not in [kw.lower(), "số", "so", "_", "-", "khách hàng", "khach hang"]:
                    return clean_val_below
    return ""

def extract_gcn_with_flexible_regex(page) -> Optional[str]:
    """
    Trích xuất GCN chuẩn xác: Dùng mỏ neo để tìm vùng, 
    nhưng BẮT BUỘC phải khớp qua Regex mới được công nhận là mã GCN.
    """
    text_to_search = ""
    
    if hasattr(page, "search_for"):
        # 1. Thử tìm qua mỏ neo trước
        val_anchor = get_text_next_to_anchors(page, KEYWORDS_SO_GCN)
        if val_anchor:
            print(f"[DEBUG] Vùng mỏ neo quét được: '{val_anchor}'")
            # QUAN TRỌNG: Phải chạy Regex trên text mỏ neo, KHÔNG ĐƯỢC lấy nguyên cục trả về!
            gcn_from_anchor = run_gcn_regex_filter(val_anchor)
            if gcn_from_anchor:
                print(f"[DEBUG] -> Khớp Regex thành công từ mỏ neo: '{gcn_from_anchor}'")
                return gcn_from_anchor

        # 2. Nếu mỏ neo không có hoặc text mỏ neo không khớp Regex, quét toàn trang
        text_to_search = page.get_text("text") if hasattr(page, "get_text") else str(page)
    else:
        text_to_search = str(page)

    return run_gcn_regex_filter(text_to_search)


def run_gcn_regex_filter(text: str) -> Optional[str]:
    """Hàm lọc độc lập: Đã cập nhật hỗ trợ các định dạng mã GCN mới (.AC, _AC, AC)"""
    if not text:
        return None
    text_upper = text.upper()

    # 1. Khớp mã dạng chuẩn cũ có gạch ngang (vd: C202610-T0871) hoặc tiền tố AC
    m_dashed = re.search(r'\b(?:[_\.\-\s]*)*((?:AC|C)[A-Z0-9]{2,}\s*[-_]\s*[A-Z0-9]{2,}(?:\s*[-_]\s*[A-Z0-9]+)?)\b', text_upper)
    if m_dashed:
        return re.sub(r'\s*', '', m_dashed.group(1))

    # 2. Khớp mã mới có tiền tố AC, _AC, .AC hoặc C
    m_code = re.search(r'([_\.]?(?:AC|C)\d[A-Z0-9\.\-\_]{4,25})', text_upper)
    if m_code:
        cand = re.sub(r'\s*', '', m_code.group(1))
        if "CERTIFICATE" not in cand and "KHACH" not in cand and "KHÁCH" not in cand:
            return cand

    return None

def extract_info_smart_anchors(page, naming_type: str) -> Optional[str]:
    """Trích xuất thông tin dựa vào Mỏ Neo Từ Khóa + Fallback Regex"""
    full_text = page.get_text("text")

    if naming_type == "so_gcn":
        # Gọi thẳng extract_gcn_with_flexible_regex với page để tận dụng trọn vẹn bộ lọc regex mới
        gcn_match = extract_gcn_with_flexible_regex(page)
        if gcn_match:
            return gcn_match
        # Fallback lấy toàn trang nếu mỏ neo không tìm thấy
        return extract_gcn_with_flexible_regex(full_text)

    elif naming_type == "ma_ql":
        val = get_text_next_to_anchors(page, KEYWORDS_MA_QL, shift_right=400, shift_down=35)
        
        if val:
            val_lower = val.lower()
            if val_lower not in ["/", "", "none", "nan", "号", "management no.", "management no", "mã quản lý", "mã ql", "mgmt no"]:
                if not any(kw.lower() in val_lower for kw in KEYWORDS_MA_QL):
                    clean_ql = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', val)
                    clean_ql = re.sub(r'\s+', ' ', clean_ql).strip()
                    # Cho phép nhận mã quản lý 1 ký tự (len >= 1)
                    if len(clean_ql) >= 1:
                        return clean_ql
                        
        return ""

    elif naming_type == "ten_tb":
        # Giảm shift_right xuống 250 để chỉ lấy gọn phần tên/model đứng ngay sát mỏ neo, tránh quét lan sang thông số
        raw_ten = get_text_next_to_anchors(page, KEYWORDS_TEN_TB, shift_right=250, shift_down=25)
        raw_kieu = get_text_next_to_anchors(page, KEYWORDS_KIEU_MAY, shift_right=200, shift_down=25)
        
        # Làm sạch nâng cao cho tên thiết bị
        if "/" in raw_ten:
            raw_ten = raw_ten.split("/")[0].strip()
        if "(" in raw_ten:
            raw_ten = raw_ten.split("(")[0].strip()

        if raw_kieu and raw_kieu in raw_ten:
            raw_ten = raw_ten.replace(raw_kieu, "").strip()

        # Giới hạn độ dài tối đa cho tên thiết bị và model để tránh file name quá dài
        raw_ten = raw_ten[:60].strip()
        raw_kieu = raw_kieu[:30].strip()

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
        
        # Hàm chuẩn hóa key đồng bộ giữa Excel và PDF
        def normalize_key(k: str) -> str:
            if not k:
                return ""
            # Bỏ ký tự rác ở đầu và loại bỏ toàn bộ khoảng trắng
            return re.sub(r'^[\s_\.\-]+', '', str(k).upper()).replace(' ', '')

        excel_column_clean = df[25].fillna("").apply(normalize_key)

        cut_points = []
        last_gcn_found = None

        # --- SỬA TỪ ĐOẠN NÀY ĐỂ BẢO TOÀN LOGIC CẮT VÀ GOM NHÓM ---
        for i, page in enumerate(doc):
            if search_any_keyword_in_page(page, keywords):
                # Lấy trực tiếp mã GCN từ trang bằng hàm flexible regex mới
                current_gcn = extract_gcn_with_flexible_regex(page)

                # Nếu tìm thấy mã GCN mới khác với mã trước đó, đánh dấu là một điểm cắt mới
                if current_gcn and current_gcn != last_gcn_found:
                    cut_points.append(i)
                    last_gcn_found = current_gcn
                elif not cut_points:
                    # Đảm bảo trang đầu tiên có chứa từ khóa luôn được thêm làm điểm cắt khởi đầu
                    cut_points.append(i)

        # Nếu file có từ khóa nhưng Regex chưa bắt kịp ngay trang đầu, ép cắt từ trang 0
        if not cut_points and len(doc) > 0:
            cut_points.append(0)

        zip_path = os.path.join(temp_dir, f"Tach_Excel_Theo_{naming_type}.zip")
        used_names = {}

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for i in range(len(cut_points)):
                start = cut_points[i]
                end = cut_points[i + 1] if i + 1 < len(cut_points) else len(doc)

                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start, to_page=end - 1)

                page_count = len(new_doc)
                gcn_key = extract_gcn_with_flexible_regex(new_doc[0])
                print(f"[EXCEL DEBUG] GCN trích xuất được từ PDF: '{gcn_key}'")

                # KHỞI TẠO GIÁ TRỊ MẶC ĐỊNH AN TOÀN ĐỂ TRÁNH LỖI UNBOUNDLOCALERROR
                final_filename = f"Khong_Match_Excel_{i+1}"

                if gcn_key and "KHÁCHHÀNG" not in gcn_key.upper():
                    clean_gcn_key = normalize_key(gcn_key)
                    print(f"[EXCEL DEBUG] GCN sau khi normalize: '{clean_gcn_key}'")
                    matched_rows = df[excel_column_clean == clean_gcn_key]

                    if matched_rows.empty:
                        matched_rows = df[excel_column_clean.str.contains(clean_gcn_key, na=False, regex=False)]

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
                        final_filename = f"Khong_Tim_Thay_Trong_Excel_{gcn_key}"
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