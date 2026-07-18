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
    # Giữ nguyên regex thoáng của bạn nhưng tối ưu hóa hiệu năng
    all_matches = re.findall(r'([A-Z0-9]*[0-9][A-Z0-9]*-[A-Z0-9]*[0-9][A-Z0-9]*)', text, re.IGNORECASE)
    valid_matches = [m.upper().strip() for m in all_matches if not any(kw in m.upper() for kw in ["ISO", "TCVN", "ASTM", "JIS", "IEC"])]
    return list(set(valid_matches))

def generate_ocr_variants(norm_candidate):
    """Tạo các biến thể O/0 kịch độc từ scan_rename_folder.py để tránh sót lỗi OCR"""
    variants = [norm_candidate]
    if len(norm_candidate) >= 9: # Phòng thủ tránh lỗi IndexError nếu chuỗi quá ngắn
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
        # NỚI LỎNG REGEX: Dùng chung tư duy tìm kiếm mã có dấu gạch ngang giống bản Digital để tránh lệch luật
        candidates = re.findall(r'([A-Z0-9]{3,}-[A-Z0-9]{4,})', text)
        
        extracted_gcns = []
        for candidate in candidates:
            norm_candidate = re.sub(r'[-\s\.]', '', candidate.upper())
            variants = generate_ocr_variants(norm_candidate)
            extracted_gcns.extend(variants)
            
        return extracted_gcns
    except Exception as e:
        print(f"Error OCR từ Stream: {str(e)}")
        return []

def check_excel_vs_pdf_uploaded(uploaded_excel, uploaded_pdfs, column_index=25, is_scan=False, progress_callback=None):
    """
    Hàm đối chiếu có tích hợp callback để cập nhật tiến độ ra giao diện và terminal.
    """
    uploaded_excel.seek(0)
    df = pd.read_excel(uploaded_excel, header=None, dtype=str)
    
    if column_index not in df.columns:
        column_index = 0 if len(df.columns) > 0 else 0

    try:
        header_value = str(df.iloc[0, column_index]).strip().upper()
    except:
        header_value = ""

    df[column_index] = df[column_index].fillna("").str.strip().str.upper()
    excel_gcn_set = {x for x in df[column_index].unique() if x and len(x) > 2 and x != header_value and "MÃ" not in x and "CHỨNG NHẬN" not in x}

    excel_map = {re.sub(r'[-\s\.]', '', gcn): gcn for gcn in excel_gcn_set}
    
    # In ra terminal để debug
    print(f"\n[START] Bắt đầu đối chiếu. Tổng số mã trong Excel thu thập được: {len(excel_map)}")

    all_pdf_extracted_norms = set()
    total_files = len(uploaded_pdfs)

    for idx, file_buffered in enumerate(uploaded_pdfs):
        file_buffered.seek(0)
        pdf_bytes = file_buffered.read()
        file_buffered.seek(0)
        
        # Log ra Terminal để bạn theo dõi trực tiếp bên dưới máy
        print(f" -> [{idx+1}/{total_files}] Đang xử lý file: {file_buffered.name} (Chế độ: {'OCR Scan' if is_scan else 'Digital'})")
        
        # Cập nhật lên giao diện Streamlit nếu có callback
        if progress_callback:
            progress_callback(idx + 1, total_files, f"🔄 Đang xử lý tệp ({idx+1}/{total_files}): {file_buffered.name}")

        if is_scan:
            variants = extract_gcn_from_stream_ocr(pdf_bytes)
            print(f"    => OCR tìm thấy {len(variants)} biến thể mã.")
            for v in variants:
                all_pdf_extracted_norms.add(re.sub(r'[-\s\.]', '', v))
        else:
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                full_text = "".join([page.get_text() for page in doc])
                doc.close()
                
                found_gcns = extract_gcn_from_text_digital(full_text)
                print(f"    => Nhận diện nhanh (Digital) tìm thấy {len(found_gcns)} mã.")
                for gcn in found_gcns:
                    all_pdf_extracted_norms.add(re.sub(r'[-\s\.]', '', gcn))
            except Exception as e:
                print(f"    ❌ Lỗi đọc file {file_buffered.name}: {str(e)}")

    # Tiến hành đối chiếu
    missing_gcns = []
    matched_count = 0

    for norm_excel, orig_excel in excel_map.items():
        if norm_excel in all_pdf_extracted_norms:
            matched_count += 1
        else:
            missing_gcns.append(orig_excel)

    print(f"[DONE] Hoàn thành! Khớp: {matched_count} | Thiếu: {len(missing_gcns)}\n")

    return {
        "total_excel": len(excel_map),
        "matched": matched_count,
        "missing": missing_gcns,
        "total_files_scanned": total_files
    }
    
def check_excel_vs_pdf_filenames(uploaded_excel, uploaded_pdfs, column_index=0):
    """
    Chức năng tối giản: Đối chiếu dữ liệu cột Excel với TÊN FILE PDF.
    Không đọc nội dung file, không OCR -> Tốc độ siêu nhanh.
    """
    # 1. Đọc file Excel
    uploaded_excel.seek(0)
    df = pd.read_excel(uploaded_excel, header=None, dtype=str)
    
    # Kiểm tra phòng thủ nếu cột chọn vượt quá số cột thực tế
    if column_index >= len(df.columns):
        raise ValueError(f"File Excel chỉ có {len(df.columns)} cột (index từ 0 đến {len(df.columns)-1}). Bạn đang chọn cột index {column_index} không tồn tại!")

    # Lấy giá trị dòng đầu làm nhãn loại bỏ Header
    try:
        header_value = str(df.iloc[0, column_index]).strip().upper()
    except:
        header_value = ""

    # Chuẩn hóa dữ liệu cột Excel được chọn
    df[column_index] = df[column_index].fillna("").str.strip().str.upper()
    excel_values = set(df[column_index].unique())
    
    # Lọc bỏ dòng trống, dòng tiêu đề
    excel_values = {x for x in excel_values if x and len(x) > 1 and x != header_value and "MÃ" not in x and "TÊN" not in x}

    # Tạo map chuẩn hóa (xóa dấu gạch, dấu chấm, khoảng trắng) để đối chiếu chính xác hơn
    # Ví dụ: "GCN-123.45" -> "GCN12345"
    excel_map = {re.sub(r'[-\s\.]', '', val): val for val in excel_values}

    # 2. Thu thập và chuẩn hóa TÊN của các file PDF tải lên
    pdf_name_norms = set()
    for file_buffered in uploaded_pdfs:
        filename = file_buffered.name # Lấy tên file (ví dụ: "GCN-123.45.pdf")
        # Loại bỏ đuôi `.pdf` hoặc `.PDF` trước khi chuẩn hóa
        name_without_ext = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)
        # Chuẩn hóa tên file
        norm_name = re.sub(r'[-\s\.]', '', name_without_ext.upper())
        pdf_name_norms.add(norm_name)

    # 3. Đối chiếu tìm tên thiếu
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
        "total_files_uploaded": len(uploaded_pdfs)
    }    