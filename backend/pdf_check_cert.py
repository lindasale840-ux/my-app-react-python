import os
import re
import fitz
import pandas as pd
import pytesseract
from backend.scan_splitter import preprocess_image_for_ocr

def extract_gcn_from_text_digital(text):
    """Bốc tách toàn bộ mã GCN từ text dạng văn bản (Digital PDF)"""
    if not text:
        return []
    all_matches = re.findall(r'([A-Z0-9]*[0-9][A-Z0-9]*-[A-Z0-9]*[0-9][A-Z0-9]*)', text, re.IGNORECASE)
    valid_matches = [m.upper().strip() for m in all_matches if not any(kw in m.upper() for kw in ["ISO", "TCVN", "ASTM", "JIS", "IEC"])]
    return list(set(valid_matches))

def generate_ocr_variants(norm_candidate):
    """Tạo các biến thể O/0 kịch độc từ scan_rename_folder.py để tránh sót lỗi OCR"""
    variants = [norm_candidate]
    if len(norm_candidate) >= 8:
        phan_he = norm_candidate[7]
        so_seri = norm_candidate[8:]

        if phan_he.isdigit():
            variants.append(norm_candidate[:7] + "O" + so_seri)
        if "O" in so_seri:
            variants.append(norm_candidate[:7] + phan_he + so_seri.replace("O", "0"))
        variants.append(norm_candidate[:7] + "O" + so_seri.replace("O", "0"))
    return list(dict.fromkeys(variants))

def extract_gcn_from_stream_ocr(pdf_stream):
    """Quét OCR trang đầu từ bộ nhớ (Dành cho file PDF Upload)"""
    try:
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        if len(doc) == 0:
            doc.close()
            return []
        
        page = doc[0]
        img_array = preprocess_image_for_ocr(page, dpi=300, top_percent=0.6)
        text = pytesseract.image_to_string(img_array, lang="vie+eng", config='--oem 3 --psm 6')
        doc.close()

        text = text.upper()
        candidates = re.findall(r'C\d{6}[- ]?[A-Z0-9]{1,2}[- ]?[A-Z0-9]{4,6}', text)
        
        extracted_gcns = []
        for candidate in candidates:
            norm_candidate = re.sub(r'[-\s\.]', '', candidate.upper())
            variants = generate_ocr_variants(norm_candidate)
            extracted_gcns.extend(variants)
            
        return extracted_gcns
    except Exception as e:
        print(f"Error OCR từ Stream: {str(e)}")
        return []

def check_excel_vs_pdf_uploaded(uploaded_pdfs, uploaded_excel, column_index=25, is_scan=False):
    """
    Hàm đối chiếu lõi sử dụng file upload trực tiếp từ Streamlit (Không cần đường dẫn ổ đĩa)
    """
    # 1. Đọc danh sách GCN từ file Excel đã upload
    df = pd.read_excel(uploaded_excel, header=None, dtype=str)
    df[column_index] = df[column_index].fillna("").str.strip().str.upper()
    excel_gcn_set = set(df[column_index].unique())
    excel_gcn_set = {x for x in excel_gcn_set if x and len(x) > 2}

    excel_map = {}
    for gcn in excel_gcn_set:
        norm = re.sub(r'[-\s\.]', '', gcn)
        excel_map[norm] = gcn

    # 2. Đọc danh sách file PDF đã upload
    all_pdf_extracted_norms = set()

    for file_buffered in uploaded_pdfs:
        # Đọc dữ liệu binary của file vào bộ nhớ
        pdf_bytes = file_buffered.read()
        # Reset pointer để tránh lỗi đọc lại file sau này nếu cần
        file_buffered.seek(0) 
        
        if is_scan:
            # Thuật toán OCR
            variants = extract_gcn_from_stream_ocr(pdf_bytes)
            for v in variants:
                all_pdf_extracted_norms.add(re.sub(r'[-\s\.]', '', v))
        else:
            # Thuật toán đọc text trực tiếp
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
                doc.close()
                
                found_gcns = extract_gcn_from_text_digital(full_text)
                for gcn in found_gcns:
                    all_pdf_extracted_norms.add(re.sub(r'[-\s\.]', '', gcn))
            except Exception as e:
                print(f"Error đọc file {file_buffered.name}: {str(e)}")

    # 3. Tiến hành đối chiếu
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
        "total_files_scanned": len(uploaded_pdfs)
    }