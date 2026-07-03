import fitz  # PyMuPDF
import os
import zipfile
import re
import pandas as pd  # Đảm bảo môi trường đã cài: pip install pandas openpyxl

# ==============================================================================
# 🎛️ BẢNG CẤU HÌNH TỌA ĐỘ TUYỆT ĐỐI CHO CÁC PHÂN HỆ NGÔN NGỮ (CHÍNH XÁC 100%)
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

def get_text_next_to_keyword(page, keyword, shift_right=500):
    """Tìm từ khóa và dịch phải tự động (Chống phân biệt hoa thường)"""
    rects = page.search_for(keyword, flags=1)
    if not rects:
        return ""
    rect = rects[0]
    search_area = fitz.Rect(rect.x1, rect.y0 - 2, rect.x1 + shift_right, rect.y1 + 2)
    return page.get_text("text", clip=search_area).strip()

def get_text_by_absolute_coordinates(page, x0, y0, y1):
    """Quét theo tọa độ cứng"""
    search_area = fitz.Rect(x0, y0, 600, y1)
    return page.get_text("text", clip=search_area).strip()

def detect_language_structure(page_text):
    """
    Tự động nhận diện cấu trúc form dựa vào các từ khóa đặc trưng
    """
    page_text_clean = re.sub(r'\s+', ' ', page_text)
    if "CALIBRATION CERTIFICATE" in page_text_clean:
        return "TRUNG_ANH"
    if "Certificate No" in page_text_clean or "Client" in page_text_clean:
        return "VIET_ANH"
    return "TRUNG_VIET"

def extract_info_smart(page, naming_type):
    """
    Bộ não trung tâm: Tự động phân tích ngôn ngữ và bóc tách sạch sẽ dữ liệu theo tọa độ cứng hoặc mềm
    """
    full_text = page.get_text("text")
    lang_type = detect_language_structure(full_text)
    
    print(f"\n[LOG WEB] --- TỰ ĐỘNG NHẬN DIỆN FORM: '{lang_type}' | CHẾ ĐỘ: '{naming_type}' ---")

    # ==========================================================================
    # PHÂN NHÁNH A: XỬ LÝ FORM TRUNG - ANH MỚI CẬP NHẬT (Áp dụng tọa độ cứng chuẩn)
    # ==========================================================================
    if lang_type == "TRUNG_ANH":
        if naming_type == "so_gcn":
            c = CONFIG_TRUNG_ANH["so_gcn"]
            raw = get_text_by_absolute_coordinates(page, c[0], c[1], c[2])
            # Làm sạch chuỗi, nhặt cụm mã GCN như C202605-L0437
            match = re.search(r'([A-Z0-9]+-[A-Z0-9]+)', raw, re.IGNORECASE)
            return match.group(1).strip().upper() if match else None
                
        elif naming_type == "ma_ql":
            c = CONFIG_TRUNG_ANH["ma_ql"]
            raw = get_text_by_absolute_coordinates(page, c[0], c[1], c[2])
            clean_raw = raw.replace("Management No.", "").replace("\n", " ").replace(":", "").strip()
            # Áp dụng chung cho cả mục ma_ql của TRUNG_ANH và TRUNG_VIET
            clean_raw = re.sub(r'\s*-\s*', '-', clean_raw)  # Co khoảng trắng quanh dấu trừ
            clean_raw = re.sub(r'\s+', '-', clean_raw)      # Đổi khoảng trắng đơn lẻ thành dấu trừ
            clean_raw = re.sub(r'-+', '-', clean_raw)       # Triệt tiêu dấu trừ kép (--) thành (-)
            return None if clean_raw in ["/", "", "nan"] else re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', clean_raw)
                
        elif naming_type == "ten_tb":
            c_ten = CONFIG_TRUNG_ANH["ten_tb"]
            c_kieu = CONFIG_TRUNG_ANH["kieu_may"]
            raw_ten = get_text_by_absolute_coordinates(page, c_ten[0], c_ten[1], c_ten[2])
            raw_kieu = get_text_by_absolute_coordinates(page, c_kieu[0], c_kieu[1], c_kieu[2])
            
            # Gọt tên thiết bị: Chỉ giữ lại phần Tiếng Việt trước dấu mở ngoặc Trung/Anh
            ten_tb = raw_ten.split("(")[0].strip() if "(" in raw_ten else raw_ten.strip()
            # Gọt kiểu máy: Bỏ chữ "技术特征" rác nếu bị dính vào
            kieu_may = raw_kieu.replace("技术特征", "").replace(":", "").strip()
            
            ten_tb = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', ten_tb.replace("\n", " ")).strip()
            kieu_may = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', kieu_may.replace("\n", " ")).strip()
            return f"{ten_tb}_{kieu_may}" if ten_tb and kieu_may else ten_tb

    # ==========================================================================
    # PHÂN NHÁNH 1: XỬ LÝ FORM TRUNG - VIỆT (Giống như cũ)
    # ==========================================================================
    elif lang_type == "TRUNG_VIET":
        if naming_type == "so_gcn":
            c = CONFIG_TRUNG_VIET["so_gcn"]
            raw = get_text_by_absolute_coordinates(page, c[0], c[1], c[2])
            match = re.search(r'([A-Z0-9]+-[A-Z0-9]+)', raw, re.IGNORECASE)
            return match.group(1).strip() if match else None
                
        elif naming_type == "ma_ql":
            c = CONFIG_TRUNG_VIET["ma_ql"]
            raw = get_text_by_absolute_coordinates(page, c[0], c[1], c[2])
            clean_raw = raw.replace("\n", " ").replace(":", "").strip()
            clean_raw = re.sub(r'\s*-\s*', '-', clean_raw)  # Co khoảng trắng quanh dấu trừ
            clean_raw = re.sub(r'\s+', '-', clean_raw)      # Đổi khoảng trắng đơn lẻ thành dấu trừ
            clean_raw = re.sub(r'-+', '-', clean_raw)       # Triệt tiêu dấu trừ kép (--) thành (-)
            return None if clean_raw in ["/", "", "号"] else re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', clean_raw)
                
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
            return f"{ten_tb}_{kieu_may}" if ten_tb and kieu_may else ten_tb

    # ==========================================================================
    # PHÂN NHÁNH 2: XỬ LÝ FORM VIỆT - ANH (Sử dụng thuật toán gọt Regex)
    # ==========================================================================
    else:
        if naming_type == "so_gcn":
            raw = get_text_next_to_keyword(page, "Mã số GCN")
            match = re.search(r'([A-Z0-9]+-[A-Z0-9]+)$', raw.strip(), re.IGNORECASE)
            if match:
                return match.group(1).strip()
            match_any = re.search(r'([A-Z0-9]+-[A-Z0-9]+)', raw, re.IGNORECASE)
            return match_any.group(1).strip() if match_any else None
                
        elif naming_type == "ma_ql":
            raw = get_text_next_to_keyword(page, "Mã quản lý")
            clean_raw = raw.replace("\n", " ").replace(":", "").replace("/", "").strip()
            clean_raw = re.sub(r'\s*-\s*', '-', clean_raw)  # Co khoảng trắng quanh dấu trừ
            clean_raw = re.sub(r'\s+', '-', clean_raw)      # Đổi khoảng trắng đơn lẻ thành dấu trừ
            clean_raw = re.sub(r'-+', '-', clean_raw)       # Triệt tiêu dấu trừ kép (--) thành (-)
            return None if clean_raw == "" else re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', clean_raw)
                
        elif naming_type == "ten_tb":
            raw_ten = get_text_next_to_keyword(page, "Tên thiết bị")
            if not raw_ten: raw_ten = get_text_next_to_keyword(page, "Thiết bị")
            
            raw_kieu = get_text_next_to_keyword(page, "Model")
            if not raw_kieu: raw_kieu = get_text_next_to_keyword(page, "Kiểu máy")
            
            ten_tb = raw_ten.replace(":", "").strip()
            if "/" in ten_tb:
                ten_tb = ten_tb.split("/")[0].strip()
                
            kieu_may = raw_kieu.replace(":", "").strip()
            for kw in ["Technical", "Technical specifications", "Đặc trưng", "/"]:
                if kw in kieu_may:
                    kieu_may = kieu_may.split(kw)[0].strip()
                    
            ten_tb = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', ten_tb.replace("\n", " ")).strip()
            kieu_may = re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', kieu_may.replace("\n", " ")).strip()
            
            if ten_tb and kieu_may:
                return f"{ten_tb}_{kieu_may}"
            return ten_tb if ten_tb else "ThietBi"

    return None

def smart_split_pdf(pdf_path, keyword="Giấy chứng nhận", naming_type="ma_ql"):
    """
    HÀM CŨ NÂNG CẤP: Khớp CHÍNH XÁC hoa thường từ TextBox và kiểm tra từ khóa ngay từ đầu.
    """
    doc = fitz.open(pdf_path)
    
    keyword_clean = keyword.strip()
    has_keyword = False
    for page in doc:
        page_text_clean = re.sub(r'\s+', ' ', page.get_text("text"))
        if keyword_clean in page_text_clean:
            has_keyword = True
            break
            
    if not has_keyword:
        doc.close()
        return None, f"❌ HỦY BỎ TÁCH FILE: Không tìm thấy từ khóa '{keyword}' (khớp chính xác hoa thường) trong bất kỳ trang nào của file PDF!"

    cut_points = []
    for i in range(len(doc)):
        page_text_clean = re.sub(r'\s+', ' ', doc[i].get_text("text"))
        if keyword_clean in page_text_clean:
            cut_points.append(i)

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
    return zip_path, f"🎉 Đã cắt thành công theo từ khóa '{keyword}'!"


def smart_split_pdf_with_excel(pdf_path, excel_path, keyword="Giấy chứng nhận", naming_type="ten_tb"):
    """
    HÀM EXCEL NÂNG CẤP: Khớp CHÍNH XÁC hoa thường từ TextBox và chặn hủy bỏ quy trình ngay lập tức nếu sai từ khóa.
    """
    doc = fitz.open(pdf_path)
    
    keyword_clean = keyword.strip()
    has_keyword = False
    for page in doc:
        page_text_clean = re.sub(r'\s+', ' ', page.get_text("text"))
        if keyword_clean in page_text_clean:
            has_keyword = True
            break
            
    if not has_keyword:
        doc.close()
        return None, f"❌ HỦY BỎ TÁCH FILE: Từ khóa '{keyword}' (chính xác hoa thường) không tồn tại trên file PDF. Vui lòng kiểm tra lại!"

    try:
        df = pd.read_excel(excel_path, header=None, dtype=str)
        df[25] = df[25].fillna("").str.strip().str.upper()
    except Exception as e:
        doc.close()
        return None, f"❌ Lỗi khi đọc file Excel: {str(e)}"

    cut_points = []
    for i in range(len(doc)):
        page_text_clean = re.sub(r'\s+', ' ', doc[i].get_text("text"))
        if keyword_clean in page_text_clean:
            cut_points.append(i)

    base_dir = os.path.dirname(pdf_path)
    zip_name = f"Tach_Excel_Theo_{naming_type}.zip"
    zip_path = os.path.join(base_dir, zip_name)

    output_folder = os.path.join(base_dir, "temp_split_excel")
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
            
            first_page_text = new_doc[0].get_text("text")
            gcn_key = None
            
            all_matches = re.findall(r'([A-Z0-9]*[0-9][A-Z0-9]*-[A-Z0-9]*[0-9][A-Z0-9]*)', first_page_text, re.IGNORECASE)
            if all_matches:
                valid_matches = [m for m in all_matches if not any(kw in m.upper() for kw in ["ISO", "TCVN", "ASTM", "JIS", "IEC"])]
                gcn_key = valid_matches[0].strip().upper() if valid_matches else all_matches[0].strip().upper()
            
            if gcn_key:
                final_filename = f"GCN_{gcn_key}_Khong_Co_Trong_Excel"
            else:
                final_filename = f"Khong_Do_Duoc_GCN_{i+1}"
            
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
    return zip_path, f"🎉 Đã cắt và đối chiếu Excel thành công dựa trên từ khóa '{keyword}'!"