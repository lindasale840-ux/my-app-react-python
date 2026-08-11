import fitz  # PyMuPDF
import os
import zipfile
import re
import pandas as pd

# ==============================================================================
# CONFIG TỌA ĐỘ
# ==============================================================================
CONFIG_TRUNG_VIET = {
    "so_gcn":   [150, 175, 189],
    "ma_ql":    [365, 347, 361],
    "ten_tb":   [115, 279, 293],
    "kieu_may": [110, 313, 327]
}

CONFIG_TRUNG_ANH = {
    "so_gcn":   [135, 165, 180],
    "ma_ql":    [305, 334, 355],
    "ten_tb":   [135, 265, 280],
    "kieu_may": [135, 288, 313]
}

# ==============================================================================
# 🛠️ HÀM TÁCH TỪ KHÓA & KIỂM TRA THEO ĐÚNG LOGIC GỐC CỦA PYMUPDF
# ==============================================================================
def parse_keywords(keyword_input):
    """Tách chuỗi nhập từ giao diện thành danh sách các từ khóa"""
    if not keyword_input:
        return []
    keywords = re.split(r'[,;\n]+', str(keyword_input))
    return [kw.strip() for kw in keywords if kw.strip()]

def search_any_keyword_in_page(page, keyword_list):
    """
    SỬ DỤNG LẠI CHÍNH XÁC LOGIC CŨ (fitz.search_for)
    Giúp tìm kiếm chuẩn xác vị trí từ khóa mà không bị nhận diện nhầm Header/Footer ở trang sau.
    """
    for kw in keyword_list:
        # flags=1 là Case-Insensitive (không phân biệt hoa/thường) chuẩn của PyMuPDF
        rects = page.search_for(kw, flags=1)
        if rects:
            return True
    return False

# ==============================================================================

def get_text_next_to_keyword(page, keyword, shift_right=500):
    rects = page.search_for(keyword, flags=1)
    if not rects:
        return ""
    rect = rects[0]
    search_area = fitz.Rect(rect.x1, rect.y0 - 2, rect.x1 + shift_right, rect.y1 + 2)
    return page.get_text("text", clip=search_area).strip()

def get_text_by_absolute_coordinates(page, x0, y0, y1):
    search_area = fitz.Rect(x0, y0, 600, y1)
    return page.get_text("text", clip=search_area).strip()

def detect_language_structure(page_text):
    page_text_clean = re.sub(r'\s+', ' ', page_text)
    if "CALIBRATION CERTIFICATE" in page_text_clean:
        return "TRUNG_ANH"
    if "Certificate No" in page_text_clean or "Client" in page_text_clean:
        return "VIET_ANH"
    return "TRUNG_VIET"

def extract_info_smart(page, naming_type):
    full_text = page.get_text("text")
    lang_type = detect_language_structure(full_text)

    # 1. TRUNG - ANH
    if lang_type == "TRUNG_ANH":
        if naming_type == "so_gcn":
            c = CONFIG_TRUNG_ANH["so_gcn"]
            raw = get_text_by_absolute_coordinates(page, c[0], c[1], c[2])
            match = re.search(r'([A-Z0-9]+-[A-Z0-9]+)', raw, re.IGNORECASE)
            if match: return match.group(1).strip().upper()
                
        elif naming_type == "ma_ql":
            c = CONFIG_TRUNG_ANH["ma_ql"]
            raw = get_text_by_absolute_coordinates(page, c[0], c[1], c[2])
            clean_raw = raw.replace("Management No.", "").replace("\n", " ").replace(":", "").strip()
            clean_raw = re.sub(r'\s*-\s*', '-', clean_raw)
            clean_raw = re.sub(r'\s+', '-', clean_raw)
            clean_raw = re.sub(r'-+', '-', clean_raw)
            if clean_raw not in ["/", "", "nan"]:
                return re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', clean_raw)
                
        elif naming_type == "ten_tb":
            c_ten = CONFIG_TRUNG_ANH["ten_tb"]
            c_kieu = CONFIG_TRUNG_ANH["kieu_may"]
            raw_ten = get_text_by_absolute_coordinates(page, c_ten[0], c_ten[1], c_ten[2])
            raw_kieu = get_text_by_absolute_coordinates(page, c_kieu[0], c_kieu[1], c_kieu[2])
            ten_tb = raw_ten.split("(")[0].strip() if "(" in raw_ten else raw_ten.strip()
            kieu_may = raw_kieu.replace("技术特征", "").replace(":", "").strip()
            ten_tb = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', ten_tb.replace("\n", " ")).strip()
            kieu_may = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', kieu_may.replace("\n", " ")).strip()
            if ten_tb or kieu_may:
                return f"{ten_tb}_{kieu_may}" if ten_tb and kieu_may else ten_tb

    # 2. TRUNG - VIỆT
    elif lang_type == "TRUNG_VIET":
        if naming_type == "so_gcn":
            c = CONFIG_TRUNG_VIET["so_gcn"]
            raw = get_text_by_absolute_coordinates(page, c[0], c[1], c[2])
            match = re.search(r'([A-Z0-9]+-[A-Z0-9]+)', raw, re.IGNORECASE)
            if match: return match.group(1).strip()
                
        elif naming_type == "ma_ql":
            c = CONFIG_TRUNG_VIET["ma_ql"]
            raw = get_text_by_absolute_coordinates(page, c[0], c[1], c[2])
            clean_raw = raw.replace("\n", " ").replace(":", "").strip()
            clean_raw = re.sub(r'\s*-\s*', '-', clean_raw)
            clean_raw = re.sub(r'\s+', '-', clean_raw)
            clean_raw = re.sub(r'-+', '-', clean_raw)
            if clean_raw not in ["/", "", "号"]:
                return re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', clean_raw)
                
        elif naming_type == "ten_tb":
            c_ten = CONFIG_TRUNG_VIET["ten_tb"]
            c_kieu = CONFIG_TRUNG_VIET["kieu_may"]
            raw_ten = get_text_by_absolute_coordinates(page, c_ten[0], c_ten[1], c_ten[2])
            raw_kieu = get_text_by_absolute_coordinates(page, c_kieu[0], c_kieu[1], c_kieu[2])
            ten_tb = raw_ten.split("/")[-1].strip() if "/" in raw_ten else raw_ten.strip()
            kieu_may = raw_kieu.strip()
            for kw in ["Đặc trưng", "Đặc Trưng", "技术", "见結果页"]:
                if kw in kieu_may: kieu_may = kieu_may.split(kw)[0].strip()
            ten_tb = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', ten_tb.replace("\n", " ")).strip()
            kieu_may = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', kieu_may.replace("\n", " ")).strip()
            if ten_tb or kieu_may:
                return f"{ten_tb}_{kieu_may}" if ten_tb and kieu_may else ten_tb

    # 3. VIỆT - ANH HOẶC FORM KHÁC (GIẤY THỬ NGHIỆM)
    if naming_type == "so_gcn":
        for kw in ["Mã số GCN", "Số GCN", "Số/No", "No."]:
            raw = get_text_next_to_keyword(page, kw)
            match = re.search(r'([A-Z0-9]+-[A-Z0-9]+)', raw, re.IGNORECASE)
            if match: return match.group(1).strip()
            
    elif naming_type == "ma_ql":
        for kw in ["Mã quản lý", "Mã QL", "Management No"]:
            raw = get_text_next_to_keyword(page, kw)
            clean_raw = raw.replace("\n", " ").replace(":", "").replace("/", "").strip()
            clean_raw = re.sub(r'\s*-\s*', '-', clean_raw)
            clean_raw = re.sub(r'\s+', '-', clean_raw)
            clean_raw = re.sub(r'-+', '-', clean_raw)
            if clean_raw: return re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', clean_raw)

    elif naming_type == "ten_tb":
        raw_ten = get_text_next_to_keyword(page, "Tên thiết bị") or get_text_next_to_keyword(page, "Thiết bị") or get_text_next_to_keyword(page, "Tên mẫu")
        raw_kieu = get_text_next_to_keyword(page, "Model") or get_text_next_to_keyword(page, "Kiểu máy")
        
        ten_tb = raw_ten.replace(":", "").strip()
        if "/" in ten_tb: ten_tb = ten_tb.split("/")[0].strip()
        kieu_may = raw_kieu.replace(":", "").strip()
        
        ten_tb = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', ten_tb.replace("\n", " ")).strip()
        kieu_may = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', kieu_may.replace("\n", " ")).strip()
        
        if ten_tb or kieu_may:
            return f"{ten_tb}_{kieu_may}" if (ten_tb and kieu_may) else (ten_tb if ten_tb else kieu_may)

    # Fallback Regex nếu không đo được bằng tọa độ
    all_gcn = re.findall(r'([A-Z0-9]{2,}-[A-Z0-9]{2,})', full_text)
    if all_gcn:
        valid = [g for g in all_gcn if not any(k in g.upper() for k in ["ISO", "TCVN", "ASTM", "JIS", "IEC"])]
        if valid:
            return f"GCN_{valid[0]}"

    return None

# ==============================================================================
# HÀM TÁCH PDF SMART - BẢO TOÀN LOGIC CŨ 100%
# ==============================================================================
def smart_split_pdf(pdf_path, keyword="Giấy chứng nhận", naming_type="ma_ql"):
    doc = fitz.open(pdf_path)
    
    keyword_list = parse_keywords(keyword)
    if not keyword_list:
        doc.close()
        return None, "❌ HỦY BỎ TÁCH FILE: Từ khóa nhập vào bị trống!"

    # 🌟 Tìm điểm cắt đúng theo logic search_for chuẩn gốc của PyMuPDF
    cut_points = []
    for i in range(len(doc)):
        if search_any_keyword_in_page(doc[i], keyword_list):
            cut_points.append(i)

    if not cut_points:
        doc.close()
        return None, f"❌ HỦY BỎ TÁCH FILE: Không tìm thấy từ khóa nào trong danh sách!"

    base_dir = os.path.dirname(pdf_path)
    zip_name = f"Ket_Qua_Tach_Theo_{naming_type}.zip"
    zip_path = os.path.join(base_dir, zip_name)

    output_folder = os.path.join(base_dir, "temp_split")
    if os.path.exists(output_folder):
        for f in os.listdir(output_folder): os.remove(os.path.join(output_folder, f))
    else:
        os.makedirs(output_folder, exist_ok=True)
        
    used_names = {}
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for i in range(len(cut_points)):
            start = cut_points[i]
            end = cut_points[i+1] if i + 1 < len(cut_points) else len(doc)
            
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start, to_page=end-1)
            
            first_page = new_doc[0]
            extracted_name = extract_info_smart(first_page, naming_type)
            
            if not extracted_name:
                filename = f"Khong_Do_Duoc_Ten_{i+1}.pdf"
            else:
                if extracted_name in used_names:
                    used_names[extracted_name] += 1
                    filename = f"{extracted_name}_{used_names[extracted_name]}.pdf"
                else:
                    used_names[extracted_name] = 0
                    filename = f"{extracted_name}.pdf"
            
            save_path = os.path.join(output_folder, filename)
            new_doc.save(save_path)
            zipf.write(save_path, filename)
            new_doc.close()
            
    doc.close()
    return zip_path, f"🎉 Đã cắt thành công!"


def smart_split_pdf_with_excel(pdf_path, excel_path, keyword="Giấy chứng nhận, Certificate, Certificate of Calibration", naming_type="ten_tb"):
    """
    HÀM EXCEL NÂNG CẤP ĐỒNG BỘ:
    1. Hỗ trợ ĐA TỪ KHÓA (nhập phân cách bằng dấu phẩy, ví dụ: 'Giấy chứng nhận, Certificate').
    2. Tìm kiếm theo vị trí chữ nguyên bản PyMuPDF (không phân biệt hoa/thường, không sợ ngắt dòng).
    3. Tra cứu file Excel theo Số GCN bóc tách từ trang đầu.
    """
    doc = fitz.open(pdf_path)
    keywords = parse_keywords(keyword)
    
    if not keywords:
        doc.close()
        return None, "❌ Vui lòng nhập ít nhất một từ khóa để tìm kiếm!"

    # 1. Kiểm tra sự tồn tại của BẤT KỲ từ khóa nào trong file PDF
    has_keyword = False
    for page in doc:
        if search_any_keyword_in_page(page, keywords):
            has_keyword = True
            break
            
    if not has_keyword:
        doc.close()
        return None, f"❌ HỦY BỎ TÁCH FILE: Không tìm thấy bất kỳ từ khóa nào trong danh sách '{keyword}' trên file PDF. Vui lòng kiểm tra lại!"

    # 2. Đọc file Excel
    try:
        df = pd.read_excel(excel_path, header=None, dtype=str)
        df[25] = df[25].fillna("").str.strip().str.upper()
    except Exception as e:
        doc.close()
        return None, f"❌ Lỗi khi đọc file Excel: {str(e)}"

    # 3. Tìm các điểm cắt (Cut Points) dựa trên danh sách đa từ khóa
    cut_points = []
    for i, page in enumerate(doc):
        if search_any_keyword_in_page(page, keywords):
            cut_points.append(i)

    base_dir = os.path.dirname(pdf_path)
    zip_name = f"Tach_Excel_Theo_{naming_type}.zip"
    zip_path = os.path.join(base_dir, zip_name)

    output_folder = os.path.join(base_dir, "temp_split_excel")
    if os.path.exists(output_folder):
        for f in os.listdir(output_folder): 
            try:
                os.remove(os.path.join(output_folder, f))
            except:
                pass
    else:
        os.makedirs(output_folder, exist_ok=True)
        
    used_names = {}
    
    # 4. Tiến hành cắt và tra cứu Excel
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for i in range(len(cut_points)):
            start = cut_points[i]
            end = cut_points[i+1] if i + 1 < len(cut_points) else len(doc)
            
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start, to_page=end-1)
            
            first_page_text = new_doc[0].get_text("text")
            gcn_key = None
            
            # Quét Regex lấy Số GCN
            all_matches = re.findall(r'([A-Z0-9]*[0-9][A-Z0-9]*-[A-Z0-9]*[0-9][A-Z0-9]*)', first_page_text, re.IGNORECASE)
            if all_matches:
                valid_matches = [m for m in all_matches if not any(kw in m.upper() for kw in ["ISO", "TCVN", "ASTM", "JIS", "IEC"])]
                gcn_key = valid_matches[0].strip().upper() if valid_matches else all_matches[0].strip().upper()
            
            if gcn_key:
                final_filename = f"GCN_{gcn_key}_Khong_Co_Trong_Excel"
            else:
                final_filename = f"Khong_Do_Duoc_GCN_{i+1}"
            
            # Khớp thông tin từ Excel
            if gcn_key:
                excel_column_clean = df[25].astype(str).str.strip().str.upper()
                matched_rows = df[excel_column_clean == gcn_key]
                
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

            # Xử lý trùng tên file
            final_filename = re.sub(r'\s+', ' ', final_filename).strip()
            if final_filename in used_names:
                used_names[final_filename] += 1
                filename = f"{final_filename} ({used_names[final_filename]}).pdf"
            else:
                used_names[final_filename] = 0
                filename = f"{final_filename}.pdf"
                
            save_path = os.path.join(output_folder, filename)
            new_doc.save(save_path)
            zipf.write(save_path, filename)
            new_doc.close()
            
    doc.close()
    return zip_path, f"🎉 Đã cắt và đối chiếu Excel thành công dựa trên từ khóa: '{keyword}'!"