from backend.scan_rename_folder import (
    rename_scan_folder
)


def run_scan_rename(
    folder_path,
    excel_path,
    naming_type
):
    return rename_scan_folder(
        folder_path=folder_path,
        excel_path=excel_path,
        naming_type=naming_type
    )
    
import os
import re
import time
import zipfile
import tempfile
import io
import logging
import warnings
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import fitz  # PyMuPDF
import pandas as pd
import numpy as np
import cv2
import pytesseract
from PIL import Image, ImageEnhance

# ============================================================
# CẤU HÌNH HỆ THỐNG
# ============================================================
warnings.filterwarnings("ignore")
logging.getLogger("PIL").setLevel(logging.ERROR)

# 🎯 ĐOẠN CẤU HÌNH ĐƯỜNG DẪN SCAN TỰ ĐỘNG:
if getattr(sys, 'frozen', False):
    # Nếu đang chạy từ file .EXE đã đóng gói cài vào máy khách
    base_path = sys._MEIPASS
    tesseract_exe_path = os.path.join(base_path, 'Tesseract-OCR', 'tesseract.exe')
    pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
else:
    # Nếu đang chạy Local bằng lệnh streamlit run ở máy của bạn
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ============================================================
# HÀM BỔ TRỢ 1: CLEAN FILENAME
# ============================================================
def clean_filename(text):
    """Loại bỏ các ký tự không hợp lệ trong tên file"""
    if not text:
        return ""
    return re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', text).strip()


# ============================================================
# HÀM BỔ TRỢ 2: TIỀN XỬ LÝ ẢNH OCR - TỐI ƯU CHO TESSERACT
# ============================================================
def preprocess_image_for_ocr(page, dpi=300, top_percent=0.6):
    """
    Tối ưu ảnh OCR cho Tesseract bằng OpenCV
    """
    rect = page.rect
    crop_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y0 + rect.height * top_percent)
    mat = fitz.Matrix(dpi / 72, dpi / 72)

    pix = page.get_pixmap(matrix=mat, clip=crop_rect)
    img_data = pix.tobytes("png")

    pil_img = Image.open(io.BytesIO(img_data))

    if pil_img.mode != 'L':
        pil_img = pil_img.convert('L')

    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(2.5)

    enhancer = ImageEnhance.Sharpness(pil_img)
    pil_img = enhancer.enhance(2.5)

    width, height = pil_img.size
    pil_img = pil_img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)

    img_array = np.array(pil_img)
    _, img_array = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return img_array


# ============================================================
# HÀM BỔ TRỢ 3: LOGIC VÉT CẠN BIẾN THỂ THEO Ý KIẾN CỦA BẠN
# ============================================================
import re

def extract_gcn_intelligent(text, excel_gcn_list):
    """
    Tạo ra tất cả các bản sao (biến thể) có khả năng xảy ra của mã GCN,
    sau đó đối chiếu lần lượt với Excel để tìm ra kết quả đúng nhất.
    Tự động mở rộng cho TẤT CẢ các chữ cái đầu có trong file Excel.
    """
    if not text or not excel_gcn_list:
        return None

    text = text.upper()

    # =========================================================
    # 0. CHUẨN HÓA DẠNG EXCEL & TỰ ĐỘNG LẤY TẤT CẢ CHỮ CÁI ĐẦU HỢP LỆ
    # =========================================================
    excel_map = {}
    valid_prefix_letters = set()  # Tập hợp chứa các chữ cái đầu (VD: {'C', 'T', 'A', 'K'...})

    for gcn in excel_gcn_list:
        if not gcn:
            continue
        norm = re.sub(r'[-\s\.]', '', str(gcn).upper())
        excel_map[norm] = str(gcn).upper()
        
        # Nếu ký tự đầu là chữ cái (A-Z), lưu vào danh sách prefix hợp lệ
        if norm and norm[0].isalpha():
            valid_prefix_letters.add(norm[0])

    # Nếu Excel rỗng hoặc không có mã hợp lệ
    if not valid_prefix_letters:
        valid_prefix_letters = {'C', 'T'} # Backup mặc định nếu file excel lỗi

    # Bảng ánh xạ lỗi OCR phổ biến của các chữ cái đầu khi bị quét nhầm thành Số/Ký tự
    # (Có thể bổ sung thêm nếu sau này OCR hay đọc nhầm ký tự nào đó)
    ocr_error_map = {
        '0': ['C', 'O', 'Q', 'D'],
        'O': ['C', '0', 'Q', 'D'],
        '7': ['T', '1', 'I'],
        '1': ['T', 'I', '7', 'L'],
        'I': ['T', '1', '7', 'L'],
        '+': ['T'],
        '|': ['T', 'I', '1']
    }

    # =========================================================
    # 1. REGEX QUÉT RỘNG TỰ ĐỘNG
    # Chấp nhận ký tự đầu là tất cả các chữ cái có trong Excel + các lỗi OCR phổ biến
    # =========================================================
    prefix_pattern = "".join(valid_prefix_letters.union(set(ocr_error_map.keys())))
    
    candidates = re.findall(
        rf'[{prefix_pattern}][A-Z0-9]{{6}}[- ]?[A-Z0-9]{{1,2}}[- ]?[A-Z0-9]{{4,6}}',
        text
    )

    if not candidates:
        return None

    for candidate in candidates:
        # Xóa ký tự phân cách của ứng viên gốc
        norm_candidate = re.sub(r'[-\s\.]', '', candidate.upper())
        
        if len(norm_candidate) < 8:
            continue

        # Tách cấu trúc logic của chuỗi ứng viên
        ky_tu_dau = norm_candidate[0]     # Ký tự đầu
        sau_so_dau = norm_candidate[1:7]   # Phân đoạn Năm/Tháng (Ví dụ: 202605)
        phan_he = norm_candidate[7]       # Phân hệ (Có thể là chữ O hoặc số 0)
        so_seri = norm_candidate[8:]       # Số sê-ri phía sau

        # =========================================================
        # TẠO TẬP HỢP TẤT CẢ CÁC BẢN SAO CÓ KHẢ NĂNG (GIỮ NGUYÊN LOGIC GỐC)
        # =========================================================
        possible_variants = []

        # TỰ ĐỘNG LỌC VÀ NẮN KÝ TỰ ĐẦU DỰA TRÊN DẠNG EXCEL
        dau_opts = []
        
        # Nếu ký tự quét được đã nằm trong danh sách chữ cái Excel -> Giữ nguyên
        if ky_tu_dau in valid_prefix_letters:
            dau_opts.append(ky_tu_dau)

        # Nếu ký tự quét được bị nghi ngờ là lỗi OCR (ví dụ 0, O, 7, 1, I...)
        if ky_tu_dau in ocr_error_map:
            for possible_char in ocr_error_map[ky_tu_dau]:
                if possible_char in valid_prefix_letters:
                    dau_opts.append(possible_char)

        # Trường hợp dự phòng nếu không tìm thấy gợi ý nào phù hợp
        if not dau_opts:
            dau_opts = [ky_tu_dau]

        # Phân đoạn năm/tháng: Thử cả bản gốc và bản nắn chữ O thành số 0
        sau_so_opts = [sau_so_dau, sau_so_dau.replace('O', '0')]
        
        # Phân hệ: Thử cả chữ O và số 0
        phan_he_opts = [phan_he]
        if phan_he == '0': phan_he_opts.append('O')
        elif phan_he == 'O': phan_he_opts.append('0')
            
        # Số seri: Thử cả bản gốc và bản nắn chữ O thành số 0
        so_seri_opts = [so_seri]
        if 'O' in so_seri:
            so_seri_opts.append(so_seri.replace('O', '0'))

        # Sử dụng vòng lặp tích đề các để tạo ra toàn bộ các bản sao hoán vị có thể có
        for d in dau_opts:
            for s6 in sau_so_opts:
                for ph in phan_he_opts:
                    for ss in so_seri_opts:
                        variant = f"{d}{s6}{ph}{ss}"
                        possible_variants.append(variant)

        # Loại bỏ các bản sao bị trùng lặp trong danh sách
        possible_variants = list(dict.fromkeys(possible_variants))

        # =========================================================
        # ĐỐI CHIẾU LẦN LƯỢT VỚI EXCEL (TRÚNG CÁI NÀO ĂN CÁI ĐÓ)
        # =========================================================
        for variant in possible_variants:
            if variant in excel_map:
                print(f"🎯 MATCH THÀNH CÔNG (Bản sao khớp: {variant}): {candidate} -> {excel_map[variant]}")
                return excel_map[variant]

    return None
# ============================================================
# HÀM BỔ TRỢ 4: XỬ LÝ OCR CHO 1 TRANG (ĐA LUỒNG SẼ GỌI HÀM NÀY)
# ============================================================
def process_page_ocr(page_num, page, excel_gcn_list, dpi=300, top_percent=0.6, lang='vie+eng'):
    """
    Xử lý OCR độc lập cho 1 trang phục vụ chạy song song ThreadPool
    """
    try:
        start_time = time.time()
        img_array = preprocess_image_for_ocr(page, dpi=dpi, top_percent=top_percent)

        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-. '
        page_text = pytesseract.image_to_string(img_array, lang=lang, config=custom_config)
        page_text = re.sub(r'\n+', ' ', page_text).strip()

        if page_text:
            print(f"📄 Trang {page_num+1}: Đọc được {len(page_text)} ký tự")
        else:
            print(f"📄 Trang {page_num+1}: Không đọc được text nào")

        detected_gcn = extract_gcn_intelligent(page_text, excel_gcn_list)
        elapsed = time.time() - start_time
        
        return {
            'page_num': page_num,
            'gcn': detected_gcn,
            'text': page_text,
            'time': elapsed
        }
    except Exception as e:
        print(f"⚠️ Lỗi trang {page_num+1}: {str(e)}")
        return {'page_num': page_num, 'gcn': None, 'text': '', 'time': 0}


# ============================================================
# HÀM CHÍNH CHO TAB 2: PHÂN TÁCH VÀ GỘP NHÓM HOÀN CHỈNH
# ============================================================
def run_auto_split_rename(pdf_total_path, excel_path, naming_type="ten_tb"):
    """
    KẾT HỢP HOÀN HẢO: Thuật toán xử lý ảnh đa luồng nâng cao của bạn
    kèm cơ chế đọc Excel thông minh chống lệch cột từ Tab 1.
    """
    global_start = time.time()
    print("="*60)
    print("🚀 [TAB 2] BẮT ĐẦU PHÂN TÁCH GỘP NHÓM SCAN PDF (ĐA LUỒNG + OPENCV)")
    print("="*60)

    # Đã đồng bộ sử dụng pdf_total_path
    doc = fitz.open(pdf_total_path)
    total_pages = len(doc)
    print(f"📑 Tổng số trang: {total_pages}")

    # Đọc file Excel thông minh
    try:
        print("📊 Đọc file Excel đối chiếu...")
        df = pd.read_excel(excel_path, dtype=str)
        
        gcn_col_name = df.columns[0]
        for col in df.columns:
            if "GCN" in str(col).upper() or "CHỨNG NHẬN" in str(col).upper():
                gcn_col_name = col
                break
        
        print(f"🎯 Đã xác định cột chứa mã GCN: [{gcn_col_name}]")
        df[gcn_col_name] = df[gcn_col_name].fillna("").str.strip().str.upper()
        excel_gcn_list = df[gcn_col_name].unique().tolist()
        excel_gcn_list = [x for x in excel_gcn_list if x and len(x) > 2]
        print(f"✅ Đã nạp {len(excel_gcn_list)} mã GCN từ Excel.")
    except Exception as e:
        doc.close()
        return None, f"❌ Lỗi đọc Excel hệ thống: {str(e)}"

    # Chạy đa luồng OCR Tesseract kết hợp xử lý ảnh OpenCV của bạn
    print(f"⚡ Bắt đầu kích hoạt 4 luồng xử lý ảnh nâng cao...")
    page_results = []
    max_workers = 4
    dpi = 300
    top_percent = 0.6

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_page_ocr, i, doc[i], excel_gcn_list, dpi, top_percent): i
            for i in range(total_pages)
        }
        for future in as_completed(futures):
            result = future.result()
            page_results.append(result)
            if result['gcn']:
                print(f"✅ Trang {result['page_num']+1}: TÌM THẤY GCN = {result['gcn']} ({result['time']:.2f}s)")
            else:
                print(f"⏭️ Trang {result['page_num']+1}: Không tìm thấy GCN ({result['time']:.2f}s)")

    page_results.sort(key=lambda x: x['page_num'])

    # Thuật toán gom cụm cuốn chiếu chống sót phụ lục/trang sau của bạn
    print("\n📦 Đang tiến hành gộp cụm trang phụ lục và trang trống...")
    page_groups = []
    current_group = None
    consecutive_none_count = 0  # Biến đếm số trang None liên tiếp trong cụm hiện tại
    
    for result in page_results:
        gcn = result['gcn']
        page_num = result['page_num']

        if gcn:
            consecutive_none_count = 0  # Reset bộ đếm khi gặp mã mới
            if current_group is None:
                current_group = {'gcn': gcn, 'pages': [page_num], 'requires_check': False}
            elif current_group['gcn'] == gcn:
                current_group['pages'].append(page_num)
            else:
                page_groups.append(current_group)
                current_group = {'gcn': gcn, 'pages': [page_num], 'requires_check': False}
        else:
            if current_group is None:
                current_group = {'gcn': f"Khong_Xac_Dinh_{page_num+1}", 'pages': [page_num], 'requires_check': False}
                print(f"⚠️ Trang {page_num+1}: Định dạng trang rác đầu file tổng.")
            else:
                consecutive_none_count += 1
                current_group['pages'].append(page_num)
                
                # CHỈ GẮN CỜ khi xuất hiện từ 2 trang trống/None liên tiếp trở lên trong cùng 1 cụm
                # Nghĩa là đã qua trang trắng cuối (1 trang) mà vẫn tiếp tục đụng thêm trang None (trang đầu bộ mới bị hụt)
                if consecutive_none_count >= 2:
                    current_group['requires_check'] = True

    if current_group:
        page_groups.append(current_group)

    # 5. Đóng gói xuất tệp tin thành phẩm vào ZIP trực tiếp trên RAM (Chống lỗi trống file ZIP)
    print("\n💾 Đang đóng gói dữ liệu trực tiếp vào luồng bộ nhớ ZIP...")
    
    # Khởi tạo một luồng bộ nhớ tạm trên RAM
    zip_buffer = io.BytesIO()
    used_names = {}

    # Sử dụng zip_buffer thay vì ghi xuống ổ cứng
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for group in page_groups:
            gcn_key = group['gcn']
            pages = group['pages']
            requires_check = group.get('requires_check', False) # Lấy cờ cảnh báo
            
            new_doc = fitz.open()
            for p_idx in pages:
                new_doc.insert_pdf(doc, from_page=p_idx, to_page=p_idx)

            if "Khong_Xac_Dinh" in gcn_key:
                final_filename = f"Trang_Rac_Dau_File_{pages[0]+1}"
            else:
                matched_rows = df[df[gcn_col_name].astype(str).str.strip().str.upper() == gcn_key]

                if not matched_rows.empty:
                    row = matched_rows.iloc[0]
                    
                    def get_val(col_idx, col_name_keyword):
                        for c in df.columns:
                            if col_name_keyword.upper() in str(c).upper():
                                return str(row[c]).strip() if pd.notna(row[c]) else ""
                        if len(row) > col_idx:
                            return str(row.iloc[col_idx]).strip() if pd.notna(row.iloc[col_idx]) else ""
                        return ""

                   # ======================================================
                    # 🔥 ĐÃ SỬA: SỬ DỤNG .iloc ĐỂ TRÁNH LỖI KEYERROR
                    # ======================================================
                    ten_tb = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ""
                    kieu_tb = str(row.iloc[6]).strip() if pd.notna(row.iloc[6]) else ""
                    nha_sx = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else ""
                    dac_trung = str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else ""
                    ma_xuat_xuong = str(row.iloc[26]).strip() if pd.notna(row.iloc[26]) else ""
                    ma_ql = str(row.iloc[27]).strip() if pd.notna(row.iloc[27]) else ""
                    # Đổi tên biến gcn để khớp với Khối logic đặt tên của Tab 1
                    gcn = gcn_key

                    # ======================================================
                    # CHUẨN HÓA VÀ LÀM SẠCH BIẾN ĐẦU VÀO ĐỒNG BỘ THEO TAB 1
                    # ======================================================
                    ten_clean = clean_filename(ten_tb)
                    kieu_clean = clean_filename(kieu_tb)
                    nha_sx_clean = clean_filename(nha_sx)
                    dac_trung_clean = clean_filename(dac_trung)
                    ma_xuat_xuong_clean = clean_filename(ma_xuat_xuong)
                    ma_ql_clean = clean_filename(ma_ql)

                    # Xử lý cắt chuỗi theo dấu "/" cho Tên Thiết Bị
                    ten_truoc_slash_clean = ""
                    ten_sau_slash_clean = ""
                    if ten_tb and "/" in ten_tb:
                        parts_slash = ten_tb.split("/", 1)
                        ten_truoc_slash_clean = clean_filename(parts_slash[0])
                        ten_sau_slash_clean = clean_filename(parts_slash[1])
                    else:
                        ten_truoc_slash_clean = ten_clean
                        ten_sau_slash_clean = ten_clean

                    # ======================================================
                    # KHỐI LOGIC ĐIỀU HƯỚNG ĐẶT TÊN (BÊ NGUYÊN 100% TỪ TAB 1)
                    # ======================================================
                    # 1. Tên + Mã quản lý
                    if naming_type == "ten_ma_ql":
                        if ten_clean and ma_ql_clean:
                            final_filename = f"{ten_clean}_{ma_ql_clean}"
                        else:
                            final_filename = ten_clean if ten_clean else (ma_ql_clean if ma_ql_clean else f"ThietBi_{gcn}")

                    # 2. Tên trước dấu / + Mã quản lý
                    elif naming_type == "ten_truoc_slash_ma_ql":
                        if ten_truoc_slash_clean and ma_ql_clean:
                            final_filename = f"{ten_truoc_slash_clean}_{ma_ql_clean}"
                        else:
                            final_filename = ten_truoc_slash_clean if ten_truoc_slash_clean else (ma_ql_clean if ma_ql_clean else f"ThietBi_{gcn}")

                    # 3. Tên sau dấu / + Mã quản lý
                    elif naming_type == "ten_sau_slash_ma_ql":
                        if ten_sau_slash_clean and ma_ql_clean:
                            final_filename = f"{ten_sau_slash_clean}_{ma_ql_clean}"
                        else:
                            final_filename = ten_sau_slash_clean if ten_sau_slash_clean else (ma_ql_clean if ma_ql_clean else f"ThietBi_{gcn}")

                    # 🌟 LỰA CHỌN MỚI 1: Tên + Mã quản lý (Ưu tiên) HOẶC Tên + Mã xuất xưởng
                    elif naming_type == "ten_ma_ql_hoac_ten_ma_xx":
                        gcn_clean = clean_filename(gcn)
                        
                        # Bước 1: Ưu tiên ghép Tên + Mã quản lý (Loại trừ thêm trường hợp là "/" hoặc "_")
                        if ten_clean and ma_ql_clean and ma_ql_clean != "/" and ma_ql_clean != "_":
                            final_filename = f"{ten_clean}_{ma_ql_clean}"
                        # Bước 2: Nếu không có Mã quản lý, ghép Tên + Mã xuất xưởng (Loại trừ cả "/", "_" và "nan")
                        elif ten_clean and ma_xuat_xuong_clean and ma_xuat_xuong_clean != "/" and ma_xuat_xuong_clean != "_" and ma_xuat_xuong_clean.lower() != "nan":
                            final_filename = f"{ten_clean}_{ma_xuat_xuong_clean}"
                        # Bước 3: Nếu chỉ có Tên thiết bị
                        elif ten_clean:
                            final_filename = ten_clean
                        # Bước 4: Cứu cánh cuối cùng nếu trống tất cả
                        else:
                            final_filename = gcn_clean if gcn_clean else f"ThietBi_{gcn}"


                    # 🌟 LỰA CHỌN MỚI 2: Tên + Mã xuất xưởng (Ưu tiên) HOẶC Tên + Mã quản lý
                    elif naming_type == "ten_ma_xx_hoac_ten_ma_ql":
                        gcn_clean = clean_filename(gcn)
                        
                        # Bước 1: Ưu tiên ghép Tên + Mã xuất xưởng
                        if ten_clean and ma_xuat_xuong_clean and ma_xuat_xuong_clean != "/" and ma_xuat_xuong_clean != "_" and ma_xuat_xuong_clean.lower() != "nan":
                            final_filename = f"{ten_clean}_{ma_xuat_xuong_clean}"
                        # Bước 2: Nếu không có Mã xuất xưởng, ghép Tên + Mã quản lý
                        elif ten_clean and ma_ql_clean and ma_ql_clean != "/" and ma_ql_clean != "_":
                            final_filename = f"{ten_clean}_{ma_ql_clean}"
                        # Bước 3: Nếu chỉ có Tên thiết bị
                        elif ten_clean:
                            final_filename = ten_clean
                        # Bước 4: Cứu cánh cuối cùng nếu trống tất cả
                        else:
                            final_filename = gcn_clean if gcn_clean else f"ThietBi_{gcn}"
                            
                            
                    # 🌟 CẬP NHẬT AN TOÀN: Ưu tiên Mã quản lý, nếu trống (hoặc là "/") thì lấy Mã xuất xưởng
                    elif naming_type == "ma_ql_hoac_ma_xx":
                        gcn_clean = clean_filename(gcn)
                        
                        # ĐÃ SỬA: Kiểm tra thêm trường hợp mã quản lý bị biến thành "_"
                        if ma_ql_clean and ma_ql_clean != "/" and ma_ql_clean != "_":
                            final_filename = ma_ql_clean
                        # ĐÃ SỬA: Kiểm tra thêm trường hợp mã xuất xưởng bị biến thành "_"
                        elif ma_xuat_xuong_clean and ma_xuat_xuong_clean != "/" and ma_xuat_xuong_clean != "_" and ma_xuat_xuong_clean.lower() != "nan":
                            final_filename = ma_xuat_xuong_clean
                        else:
                            # Nếu cả 2 đều trống hoặc chỉ có dấu "/", lấy số GCN làm cứu cánh
                            final_filename = gcn_clean if gcn_clean else f"ThietBi_{gcn}"

                    # 🌟 CẬP NHẬT AN TOÀN: Ưu tiên Mã xuất xưởng, nếu trống (hoặc là "/") thì lấy Mã quản lý
                    elif naming_type == "ma_xx_hoac_ma_ql":
                        gcn_clean = clean_filename(gcn)
                        
                        # ĐÃ SỬA: Kiểm tra thêm trường hợp mã xuất xưởng bị biến thành "_"
                        if ma_xuat_xuong_clean and ma_xuat_xuong_clean != "/" and ma_xuat_xuong_clean != "_" and ma_xuat_xuong_clean.lower() != "nan":
                            final_filename = ma_xuat_xuong_clean
                        # ĐÃ SỬA: Kiểm tra thêm trường hợp mã quản lý bị biến thành "_"
                        elif ma_ql_clean and ma_ql_clean != "/" and ma_ql_clean != "_":
                            final_filename = ma_ql_clean
                        else:
                            final_filename = gcn_clean if gcn_clean else f"ThietBi_{gcn}"
                    
                    # 🌟 CHÈN VÀO ĐÂY: Nhánh này nằm chung xuồng với các nhánh cũ, không lo bị ghi đè!
                    elif naming_type == "ten_va_so_gcn":
                        gcn_clean = clean_filename(gcn)
                        if ten_clean and gcn_clean:
                            final_filename = f"{ten_clean}_{gcn_clean}"
                        elif ten_clean:
                            final_filename = ten_clean
                        else:
                            final_filename = gcn_clean if gcn_clean else f"ThietBi_{gcn}"
                    # ---- Các option cũ của Tab 1 ----
                    elif naming_type == "ten_tb":
                        if ten_clean and kieu_clean:
                            final_filename = f"{ten_clean}_{kieu_clean}"
                        elif ten_clean:
                            final_filename = ten_clean
                        elif kieu_clean:
                            final_filename = kieu_clean
                        else:
                            final_filename = f"ThietBi_{gcn}"

                    elif naming_type == "ten_khong_model":
                        final_filename = ten_clean if ten_clean else f"Khong_Ten_{gcn}"

                    elif naming_type == "model_khong_ten":
                        final_filename = kieu_clean if kieu_clean else f"Khong_Model_{gcn}"

                    elif naming_type == "ma_xuat_xuong":
                        final_filename = ma_xuat_xuong_clean if ma_xuat_xuong_clean and ma_xuat_xuong_clean.lower() != "nan" else f"Khong_MaXuatXuong_{gcn}"

                    elif naming_type == "ten_ma_xuat_xuong":
                        parts = [p for p in [ten_clean, ma_xuat_xuong_clean] if p]
                        final_filename = "_".join(parts) if parts else f"ThietBi_{gcn}"

                    elif naming_type == "ten_dac_trung":
                        parts = [p for p in [ten_clean, dac_trung_clean] if p]
                        final_filename = "_".join(parts) if parts else f"ThietBi_{gcn}"

                    elif naming_type == "ten_model_nsx":
                        parts = [p for p in [ten_clean, kieu_clean, nha_sx_clean] if p]
                        final_filename = "_".join(parts) if parts else f"ThietBi_{gcn}"

                    elif naming_type == "ten_model_dac_trung":
                        parts = [p for p in [ten_clean, kieu_clean, dac_trung_clean] if p]
                        final_filename = "_".join(parts) if parts else f"ThietBi_{gcn}"

                    elif naming_type == "ma_ql":
                        final_filename = ma_ql_clean if ma_ql_clean else f"Khong_MaQL_{gcn}"

                    elif naming_type == "so_gcn":
                        final_filename = clean_filename(gcn)

                    else:
                        final_filename = clean_filename(gcn)
                else:
                    final_filename = f"Khong_Excel_{gcn_key}"

            # Làm sạch khoảng trắng thừa thừa trong tên file cuối cùng
            final_filename = re.sub(r'\s+', ' ', final_filename).strip()
            if not final_filename:
                final_filename = f"GCN_{gcn_key}"
                
            # ĐÍNH KÈM HẬU TỐ CẢNH BÁO NẾU CÓ NGHI VẤN NUỐT NHẦM HỒ SƠ DO LỖI OCR 5%
            if requires_check and "Khong_Xac_Dinh" not in gcn_key:
                final_filename = f"{final_filename}_CHECK_OCR"
                    
            # ======================================================
            # CHỐNG TRÙNG FILE TRÊN RAM (ĐÃ ĐỒNG BỘ)
            # ======================================================
            if final_filename in used_names:
                used_names[final_filename] += 1
                filename = f"{final_filename}_{used_names[final_filename]}.pdf"
            else:
                used_names[final_filename] = 0
                filename = f"{final_filename}.pdf"

            # Trích xuất bytes và nén trực tiếp vào RAM
            pdf_bytes = new_doc.tobytes()
            new_doc.close()
            zipf.writestr(filename, pdf_bytes)

    doc.close()
    
    # Đưa con trỏ luồng dữ liệu ZIP về vạch xuất phát để chuẩn bị cho Streamlit đọc trọn vẹn
    zip_buffer.seek(0)
    
    total_time = time.time() - global_start
    print(f"📊 Xử lý hoàn tất trong {total_time:.2f}s! Đã xuất {len(page_groups)} cụm file vào ZIP RAM.")
    
    # QUAN TRỌNG: Trả về chính cái zip_buffer này thay vì đường dẫn file vật lý dạng chuỗi
    return zip_buffer, f"🎉 Phân tách thành công {len(page_groups)} bộ GCN!"