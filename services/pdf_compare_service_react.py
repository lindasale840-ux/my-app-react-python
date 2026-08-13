import io
import re
import fitz
import pandas as pd
import pytesseract
from typing import List, Tuple, Dict, Any

# Giả định hàm tiền xử lý OCR từ module scan_splitter đã có trong hệ thống backend
try:
    from backend.scan_splitter import preprocess_image_for_ocr
except ImportError:
    # Hàm fallback phòng trường hợp import đường dẫn đặc thù
    def preprocess_image_for_ocr(page, dpi=300, top_percent=0.6):
        pix = page.get_pixmap(dpi=dpi)
        return pix.tobytes("png")


def parse_excel_columns(excel_bytes: bytes) -> List[str]:
    """Đọc file Excel từ bytes và trả về danh sách nhãn cột xem trước"""
    df = pd.read_excel(io.BytesIO(excel_bytes), header=None, nrows=5)
    df = df.fillna("").astype(str)
    
    columns_info = []
    num_cols = df.shape[1]
    for i in range(num_cols):
        sample_val = df.iloc[0, i] if len(df) > 0 else ""
        label = f"Cột {i} (Ví dụ: {sample_val})" if sample_val else f"Cột {i}"
        columns_info.append(label)
        
    return columns_info


def extract_gcn_from_text_digital(text: str) -> List[str]:
    """Bóc tách toàn bộ mã GCN từ text dạng văn bản (Digital PDF)"""
    if not text:
        return []
    all_matches = re.findall(r'([A-Z0-9]*[0-9][A-Z0-9]*-[A-Z0-9]*[0-9][A-Z0-9]*)', text, re.IGNORECASE)
    valid_matches = [
        m.upper().strip() 
        for m in all_matches 
        if not any(kw in m.upper() for kw in ["ISO", "TCVN", "ASTM", "JIS", "IEC"])
    ]
    return list(set(valid_matches))


def generate_ocr_variants(norm_candidate: str) -> List[str]:
    """Tạo các biến thể O/0 từ OCR để tránh sót lỗi nhận diện"""
    variants = [norm_candidate]
    if len(norm_candidate) >= 9:
        phan_he = norm_candidate[7]
        so_seri = norm_candidate[8:]

        if phan_he.isdigit():
            variants.append(norm_candidate[:7] + "O" + so_seri)
        if "O" in so_seri:
            variants.append(norm_candidate[:7] + phan_he + so_seri.replace("O", "0"))
        variants.append(norm_candidate[:7] + "O" + so_seri.replace("O", "0"))
    return list(dict.fromkeys(variants))


def extract_gcn_from_stream_ocr(pdf_bytes: bytes) -> List[str]:
    """Quét OCR trang đầu từ bộ nhớ RAM"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) == 0:
            doc.close()
            return []
        
        page = doc[0]
        img_array = preprocess_image_for_ocr(page, dpi=300, top_percent=0.6)
        text = pytesseract.image_to_string(img_array, lang="vie+eng", config='--oem 3 --psm 6')
        doc.close()

        text = text.upper()
        candidates = re.findall(r'([A-Z0-9]{3,}-[A-Z0-9]{4,})', text)
        
        extracted_gcns = []
        for candidate in candidates:
            norm_candidate = re.sub(r'[-\s\.]', '', candidate.upper())
            variants = generate_ocr_variants(norm_candidate)
            extracted_gcns.extend(variants)
            
        return extracted_gcns
    except Exception as e:
        print(f"Lỗi OCR từ Stream: {str(e)}")
        return []


def compare_excel_vs_pdf_filenames(
    excel_bytes: bytes, 
    pdf_files: List[Tuple[str, bytes]], 
    column_index: int = 0
) -> Dict[str, Any]:
    """Đối chiếu dữ liệu cột Excel với TÊN FILE PDF"""
    df = pd.read_excel(io.BytesIO(excel_bytes), header=None, dtype=str)
    
    if column_index >= len(df.columns):
        column_index = 0

    try:
        header_value = str(df.iloc[0, column_index]).strip().upper()
    except Exception:
        header_value = ""

    df[column_index] = df[column_index].fillna("").str.strip().str.upper()
    excel_values = set(df[column_index].unique())
    excel_values = {x for x in excel_values if x and len(x) > 1 and x != header_value and "MÃ" not in x and "TÊN" not in x}

    excel_map = {re.sub(r'[-\s\.]', '', val): val for val in excel_values}

    pdf_name_norms = set()
    for filename, _ in pdf_files:
        name_without_ext = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)
        norm_name = re.sub(r'[-\s\.]', '', name_without_ext.upper())
        pdf_name_norms.add(norm_name)

    missing_items = []
    matched_count = 0

    for norm_excel, orig_excel in excel_map.items():
        if norm_excel in pdf_name_norms:
            matched_count += 1
        else:
            missing_items.append(orig_excel)

    return {
        "total_excel": len(excel_map),
        "matched": matched_count,
        "missing": missing_items,
        "total_files_uploaded": len(pdf_files)
    }


def compare_excel_vs_pdf_content(
    excel_bytes: bytes, 
    pdf_files: List[Tuple[str, bytes]], 
    column_index: int = 0, 
    is_scan: bool = False
) -> Dict[str, Any]:
    """Đối chiếu dữ liệu cột Excel với NỘI DUNG BÊN TRONG FILE PDF"""
    df = pd.read_excel(io.BytesIO(excel_bytes), header=None, dtype=str)
    
    if column_index >= len(df.columns):
        column_index = 0

    try:
        header_value = str(df.iloc[0, column_index]).strip().upper()
    except Exception:
        header_value = ""

    df[column_index] = df[column_index].fillna("").str.strip().str.upper()
    excel_gcn_set = {x for x in df[column_index].unique() if x and len(x) > 2 and x != header_value and "MÃ" not in x and "CHỨNG NHẬN" not in x}

    excel_map = {re.sub(r'[-\s\.]', '', gcn): gcn for gcn in excel_gcn_set}

    all_pdf_extracted_norms = set()
    total_files = len(pdf_files)

    for idx, (filename, pdf_bytes) in enumerate(pdf_files):
        if is_scan:
            variants = extract_gcn_from_stream_ocr(pdf_bytes)
            for v in variants:
                all_pdf_extracted_norms.add(re.sub(r'[-\s\.]', '', v))
        else:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                full_text = "".join([page.get_text() for page in doc])
                doc.close()
                
                found_gcns = extract_gcn_from_text_digital(full_text)
                for gcn in found_gcns:
                    all_pdf_extracted_norms.add(re.sub(r'[-\s\.]', '', gcn))
            except Exception as e:
                print(f"Lỗi đọc file {filename}: {str(e)}")

    missing_gcns = []
    matched_count = 0

    for norm_excel, orig_excel in excel_map.items():
        if norm_excel in all_pdf_extracted_norms:
            matched_count += 1
        else:
            missing_gcns.append(orig_excel)

    return {
        "total_excel": len(excel_map),
        "matched": matched_count,
        "missing": missing_gcns,
        "total_files_scanned": total_files
    }