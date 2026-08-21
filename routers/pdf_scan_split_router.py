# backend/routers/pdf_scan_split_router.py
import os
import re
import time
import zipfile
import io
import warnings
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import fitz  # PyMuPDF
import pandas as pd
import numpy as np
import cv2
import pytesseract
from PIL import Image, ImageEnhance

# Configure logs and warnings
warnings.filterwarnings("ignore")
logging.getLogger("PIL").setLevel(logging.ERROR)

router = APIRouter(prefix="/api/pdf_scan_split", tags=["PdfScanSplit"])


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS (LOGIC GỐC TRÍCH XUẤT)
# ---------------------------------------------------------------------------
def clean_filename(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'[\/\\\:\*\?\"\<\>\|]', '_', str(text)).strip()


def preprocess_image_for_ocr(page, dpi=300, top_percent=0.6):
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


def extract_gcn_intelligent(text: str, excel_gcn_list: list) -> Optional[str]:
    if not text or not excel_gcn_list:
        return None

    text = text.upper()

    excel_map = {}
    valid_prefix_letters = set()

    for gcn in excel_gcn_list:
        if not gcn:
            continue
        norm = re.sub(r'[-\s\.]', '', str(gcn).upper())
        excel_map[norm] = str(gcn).upper()
        
        if norm and norm[0].isalpha():
            valid_prefix_letters.add(norm[0])

    if not valid_prefix_letters:
        valid_prefix_letters = {'C', 'T'}

    ocr_error_map = {
        '0': ['C', 'O', 'Q', 'D'],
        'O': ['C', '0', 'Q', 'D'],
        '7': ['T', '1', 'I'],
        '1': ['T', 'I', '7', 'L'],
        'I': ['T', '1', '7', 'L'],
        '+': ['T'],
        '|': ['T', 'I', '1']
    }

    prefix_pattern = "".join(valid_prefix_letters.union(set(ocr_error_map.keys())))
    candidates = re.findall(
        rf'[{prefix_pattern}][A-Z0-9]{{6}}[- ]?[A-Z0-9]{{1,2}}[- ]?[A-Z0-9]{{4,6}}',
        text
    )

    if not candidates:
        return None

    for candidate in candidates:
        norm_candidate = re.sub(r'[-\s\.]', '', candidate.upper())
        
        if len(norm_candidate) < 8:
            continue

        ky_tu_dau = norm_candidate[0]
        sau_so_dau = norm_candidate[1:7]
        phan_he = norm_candidate[7]
        so_seri = norm_candidate[8:]

        possible_variants = []

        dau_opts = []
        if ky_tu_dau in valid_prefix_letters:
            dau_opts.append(ky_tu_dau)

        if ky_tu_dau in ocr_error_map:
            for possible_char in ocr_error_map[ky_tu_dau]:
                if possible_char in valid_prefix_letters:
                    dau_opts.append(possible_char)

        if not dau_opts:
            dau_opts = [ky_tu_dau]

        sau_so_opts = [sau_so_dau, sau_so_dau.replace('O', '0')]
        
        phan_he_opts = [phan_he]
        if phan_he == '0': phan_he_opts.append('O')
        elif phan_he == 'O': phan_he_opts.append('0')
            
        so_seri_opts = [so_seri]
        if 'O' in so_seri:
            so_seri_opts.append(so_seri.replace('O', '0'))

        for d in dau_opts:
            for s6 in sau_so_opts:
                for ph in phan_he_opts:
                    for ss in so_seri_opts:
                        variant = f"{d}{s6}{ph}{ss}"
                        possible_variants.append(variant)

        possible_variants = list(dict.fromkeys(possible_variants))

        for variant in possible_variants:
            if variant in excel_map:
                return excel_map[variant]

    return None


def process_page_ocr(page_num, page, excel_gcn_list, dpi=300, top_percent=0.6, lang='vie+eng'):
    try:
        start_time = time.time()
        img_array = preprocess_image_for_ocr(page, dpi=dpi, top_percent=top_percent)

        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-. '
        page_text = pytesseract.image_to_string(img_array, lang=lang, config=custom_config)
        page_text = re.sub(r'\n+', ' ', page_text).strip()

        detected_gcn = extract_gcn_intelligent(page_text, excel_gcn_list)
        elapsed = time.time() - start_time
        
        return {
            'page_num': page_num,
            'gcn': detected_gcn,
            'text': page_text,
            'time': elapsed
        }
    except Exception as e:
        return {'page_num': page_num, 'gcn': None, 'text': '', 'time': 0}
    
# ---------------------------------------------------------------------------
# HELPER MỚI (Dành riêng cho Tab 2 - Trích xuất KHÁCH QUAN mọi Mã GCN)
# ---------------------------------------------------------------------------
def extract_gcn_raw_standalone(text: str) -> Optional[str]:
    """Tìm mã GCN thực tế trong PDF (Khắt khe hơn để tránh bắt nhầm chữ THUYETMINH, TEC...)"""
    if not text:
        return None

    text = text.upper()
    # Chỉ bắt các chuỗi bắt đầu bằng C hoặc T, có định dạng chuẩn kiểu C202605-01-0162 hoặc C202605-00162
    candidates = re.findall(r'\b[CT][A-Z0-9]{5,8}[-\/][A-Z0-9]{1,3}[-\/][A-Z0-9]{3,6}\b', text)
    
    if not candidates:
        # Thử mẫu phụ có 1 dấu gạch ngang (VD: C202605-00162)
        candidates = re.findall(r'\b[CT][A-Z0-9]{5,8}[-\/][A-Z0-9]{3,8}\b', text)

    if candidates:
        code = re.sub(r'\s+', '', candidates[0])
        # Tự động sửa lỗi OCR hay đọc nhầm số 0 thành chữ O ở phần đuôi mã
        prefix = code[0]
        rest = code[1:]
        rest_fixed = re.sub(r'(?<=[-\/0-9])O(?=[0-9])|(?<=[0-9])O(?=[-\/0-9])', '0', rest)
        return f"{prefix}{rest_fixed}"

    return None

def process_page_ocr_standalone(page_num, page, dpi=300, top_percent=0.6, lang='vie+eng'):
    """Hàm OCR cho Tab 2: Bắt tất cả mã GCN có trên trang"""
    try:
        img_array = preprocess_image_for_ocr(page, dpi=dpi, top_percent=top_percent)
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/. '
        page_text = pytesseract.image_to_string(img_array, lang=lang, config=custom_config)
        page_text = re.sub(r'\n+', ' ', page_text).strip()

        detected_gcn = extract_gcn_raw_standalone(page_text)
        return {'page_num': page_num, 'gcn': detected_gcn}
    except Exception:
        return {'page_num': page_num, 'gcn': None}


# ---------------------------------------------------------------------------
# API ENDPOINT
# ---------------------------------------------------------------------------
@router.post("/process")
async def process_pdf_split(
    pdf_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
    naming_type: str = Form("ten_tb")
):
    try:
        # 1. Read files into memory
        pdf_bytes = await pdf_file.read()
        excel_bytes = await excel_file.read()

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)

        if total_pages == 0:
            raise HTTPException(status_code=400, detail="File PDF không chứa trang nào.")

        # 2. Read Excel
        try:
            df = pd.read_excel(io.BytesIO(excel_bytes), dtype=str)
            gcn_col_name = df.columns[0]
            for col in df.columns:
                if "GCN" in str(col).upper() or "CHỨNG NHẬN" in str(col).upper():
                    gcn_col_name = col
                    break
            
            df[gcn_col_name] = df[gcn_col_name].fillna("").str.strip().str.upper()
            excel_gcn_list = df[gcn_col_name].unique().tolist()
            excel_gcn_list = [x for x in excel_gcn_list if x and len(str(x)) > 2]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Lỗi cấu trúc File Excel: {str(e)}")

        # 3. Multithread OCR Page Processing
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
                page_results.append(future.result())

        page_results.sort(key=lambda x: x['page_num'])

        # 4. Group pages intelligently
        page_groups = []
        current_group = None
        consecutive_none_count = 0

        for result in page_results:
            gcn = result['gcn']
            page_num = result['page_num']

            if gcn:
                consecutive_none_count = 0
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
                else:
                    consecutive_none_count += 1
                    current_group['pages'].append(page_num)
                    if consecutive_none_count >= 2:
                        current_group['requires_check'] = True

        if current_group:
            page_groups.append(current_group)

        # 5. Export split PDF files to ZIP in RAM
        zip_buffer = io.BytesIO()
        used_names = {}

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for group in page_groups:
                gcn_key = group['gcn']
                pages = group['pages']
                requires_check = group.get('requires_check', False)

                new_doc = fitz.open()
                for p_idx in pages:
                    new_doc.insert_pdf(doc, from_page=p_idx, to_page=p_idx)

                if "Khong_Xac_Dinh" in gcn_key:
                    final_filename = f"Trang_Rac_Dau_File_{pages[0]+1}"
                else:
                    matched_rows = df[df[gcn_col_name].astype(str).str.strip().str.upper() == gcn_key]

                    if not matched_rows.empty:
                        row = matched_rows.iloc[0]

                        ten_tb = str(row.iloc[5]).strip() if len(row) > 5 and pd.notna(row.iloc[5]) else ""
                        kieu_tb = str(row.iloc[6]).strip() if len(row) > 6 and pd.notna(row.iloc[6]) else ""
                        nha_sx = str(row.iloc[7]).strip() if len(row) > 7 and pd.notna(row.iloc[7]) else ""
                        dac_trung = str(row.iloc[8]).strip() if len(row) > 8 and pd.notna(row.iloc[8]) else ""
                        ma_xuat_xuong = str(row.iloc[26]).strip() if len(row) > 26 and pd.notna(row.iloc[26]) else ""
                        ma_ql = str(row.iloc[27]).strip() if len(row) > 27 and pd.notna(row.iloc[27]) else ""
                        gcn = gcn_key

                        ten_clean = clean_filename(ten_tb)
                        kieu_clean = clean_filename(kieu_tb)
                        nha_sx_clean = clean_filename(nha_sx)
                        dac_trung_clean = clean_filename(dac_trung)
                        ma_xuat_xuong_clean = clean_filename(ma_xuat_xuong)
                        ma_ql_clean = clean_filename(ma_ql)

                        if ten_tb and "/" in ten_tb:
                            parts_slash = ten_tb.split("/", 1)
                            ten_truoc_slash_clean = clean_filename(parts_slash[0])
                            ten_sau_slash_clean = clean_filename(parts_slash[1])
                        else:
                            ten_truoc_slash_clean = ten_clean
                            ten_sau_slash_clean = ten_clean

                        # Naming logic
                        if naming_type == "ten_ma_ql":
                            final_filename = f"{ten_clean}_{ma_ql_clean}" if ten_clean and ma_ql_clean else (ten_clean or ma_ql_clean or f"ThietBi_{gcn}")
                        elif naming_type == "ten_truoc_slash_ma_ql":
                            final_filename = f"{ten_truoc_slash_clean}_{ma_ql_clean}" if ten_truoc_slash_clean and ma_ql_clean else (ten_truoc_slash_clean or ma_ql_clean or f"ThietBi_{gcn}")
                        elif naming_type == "ten_sau_slash_ma_ql":
                            final_filename = f"{ten_sau_slash_clean}_{ma_ql_clean}" if ten_sau_slash_clean and ma_ql_clean else (ten_sau_slash_clean or ma_ql_clean or f"ThietBi_{gcn}")
                        elif naming_type == "ten_ma_ql_hoac_ten_ma_xx":
                            gcn_clean = clean_filename(gcn)
                            if ten_clean and ma_ql_clean and ma_ql_clean not in ["/", "_"]:
                                final_filename = f"{ten_clean}_{ma_ql_clean}"
                            elif ten_clean and ma_xuat_xuong_clean and ma_xuat_xuong_clean not in ["/", "_"] and ma_xuat_xuong_clean.lower() != "nan":
                                final_filename = f"{ten_clean}_{ma_xuat_xuong_clean}"
                            elif ten_clean:
                                final_filename = ten_clean
                            else:
                                final_filename = gcn_clean if gcn_clean else f"ThietBi_{gcn}"
                        elif naming_type == "ten_ma_xx_hoac_ten_ma_ql":
                            gcn_clean = clean_filename(gcn)
                            if ten_clean and ma_xuat_xuong_clean and ma_xuat_xuong_clean not in ["/", "_"] and ma_xuat_xuong_clean.lower() != "nan":
                                final_filename = f"{ten_clean}_{ma_xuat_xuong_clean}"
                            elif ten_clean and ma_ql_clean and ma_ql_clean not in ["/", "_"]:
                                final_filename = f"{ten_clean}_{ma_ql_clean}"
                            elif ten_clean:
                                final_filename = ten_clean
                            else:
                                final_filename = gcn_clean if gcn_clean else f"ThietBi_{gcn}"
                        elif naming_type == "ma_ql_hoac_ma_xx":
                            gcn_clean = clean_filename(gcn)
                            if ma_ql_clean and ma_ql_clean not in ["/", "_"]:
                                final_filename = ma_ql_clean
                            elif ma_xuat_xuong_clean and ma_xuat_xuong_clean not in ["/", "_"] and ma_xuat_xuong_clean.lower() != "nan":
                                final_filename = ma_xuat_xuong_clean
                            else:
                                final_filename = gcn_clean if gcn_clean else f"ThietBi_{gcn}"
                        elif naming_type == "ma_xx_hoac_ma_ql":
                            gcn_clean = clean_filename(gcn)
                            if ma_xuat_xuong_clean and ma_xuat_xuong_clean not in ["/", "_"] and ma_xuat_xuong_clean.lower() != "nan":
                                final_filename = ma_xuat_xuong_clean
                            elif ma_ql_clean and ma_ql_clean not in ["/", "_"]:
                                final_filename = ma_ql_clean
                            else:
                                final_filename = gcn_clean if gcn_clean else f"ThietBi_{gcn}"
                        elif naming_type == "ten_va_so_gcn":
                            gcn_clean = clean_filename(gcn)
                            final_filename = f"{ten_clean}_{gcn_clean}" if ten_clean and gcn_clean else (ten_clean or gcn_clean or f"ThietBi_{gcn}")
                        elif naming_type == "ten_tb":
                            final_filename = f"{ten_clean}_{kieu_clean}" if ten_clean and kieu_clean else (ten_clean or kieu_clean or f"ThietBi_{gcn}")
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

                final_filename = re.sub(r'\s+', ' ', final_filename).strip()
                if not final_filename:
                    final_filename = f"GCN_{gcn_key}"

                if requires_check and "Khong_Xac_Dinh" not in gcn_key:
                    final_filename = f"{final_filename}_CHECK_OCR"

                if final_filename in used_names:
                    used_names[final_filename] += 1
                    filename = f"{final_filename}_{used_names[final_filename]}.pdf"
                else:
                    used_names[final_filename] = 0
                    filename = f"{final_filename}.pdf"

                pdf_out_bytes = new_doc.tobytes()
                new_doc.close()
                zipf.writestr(filename, pdf_out_bytes)

        doc.close()
        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=PDF_Split_Result.zip"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")
    
    
def normalize_fuzzy_key(s: str) -> str:
    """
    Quy đổi tất cả các ký tự hay bị OCR đọc nhầm về một 'Dạng đại diện duy nhất'.
    Giúp 0/O, 1/I/7/L, C/Q, T/+ hòa làm 1 khi so sánh.
    """
    if not s:
        return ""
    # 1. Xóa toàn bộ dấu phân cách
    clean = re.sub(r'[-\s\.\/]', '', str(s).upper())
    if not clean:
        return ""

    # 2. Bảng quy đổi lỗi OCR kinh điển
    # Giữ nguyên ký tự đầu (C/T), chỉ sửa phần thân mã
    prefix = clean[0]
    body = clean[1:]
    
    # Ép tất cả O -> 0, I/L/7 -> 1, Q/D -> C (nếu có)
    body = body.replace('O', '0').replace('I', '1').replace('L', '1').replace('7', '1')
    
    return f"{prefix}{body}"


def generate_ocr_variants(candidate: str) -> list:
    """
    Tạo ra danh sách tất cả các biến thể có thể xảy ra từ kết quả quét OCR
    (Tham khảo theo đúng thuật toán sinh biến thể của bạn)
    """
    if not candidate:
        return []
        
    norm = re.sub(r'[-\s\.\/]', '', str(candidate).upper())
    variants = [norm]
    
    if len(norm) >= 8:
        dau = norm[0]
        sau_so_dau = norm[1:7]
        phan_he = norm[7]
        so_seri = norm[8:]
        
        # Biến thể cho Phân hệ (0 <-> O)
        phan_he_opts = [phan_he]
        if phan_he == '0': phan_he_opts.append('O')
        elif phan_he == 'O': phan_he_opts.append('0')
        
        # Biến thể cho Số Seri (O -> 0 và 0 -> O)
        so_seri_opts = [so_seri]
        if 'O' in so_seri: so_seri_opts.append(so_seri.replace('O', '0'))
        if '0' in so_seri: so_seri_opts.append(so_seri.replace('0', 'O'))
        
        for ph in phan_he_opts:
            for ss in so_seri_opts:
                v = f"{dau}{sau_so_dau}{ph}{ss}"
                variants.append(v)
                
    return list(dict.fromkeys(variants))
    
# ---------------------------------------------------------------------------
# ENDPOINT TAB 2 (ĐÃ ĐƯỢC CẬP NHẬT CHUẨN XÁC CHÚC NĂNG ĐỐI CHIẾU)
# ---------------------------------------------------------------------------
@router.post("/check_missing")
async def check_missing_gcn(
    pdf_file: UploadFile = File(...),
    excel_file: UploadFile = File(...)
):
    try:
        pdf_bytes = await pdf_file.read()
        excel_bytes = await excel_file.read()

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)

        if total_pages == 0:
            raise HTTPException(status_code=400, detail="File PDF không chứa trang nào.")

       # 1. Trích xuất Excel & Tạo map chuẩn hóa kép (Map gốc & Map Fuzzy)
        try:
            df = pd.read_excel(io.BytesIO(excel_bytes), dtype=str)
            gcn_col_name = df.columns[0]
            for col in df.columns:
                if "GCN" in str(col).upper() or "CHỨNG NHẬN" in str(col).upper():
                    gcn_col_name = col
                    break
            
            df[gcn_col_name] = df[gcn_col_name].fillna("").str.strip().str.upper()
            excel_gcn_raw_list = [x for x in df[gcn_col_name].unique().tolist() if x and len(str(x)) > 2]
            
            # Map 1: Fuzzy Key -> Mã hiển thị Excel chuẩn
            excel_fuzzy_map = {}
            # Map 2: Exact Key -> Mã hiển thị Excel chuẩn
            excel_exact_map = {}

            for gcn in excel_gcn_raw_list:
                exact_k = re.sub(r'[-\s\.\/]', '', str(gcn).upper())
                fuzzy_k = normalize_fuzzy_key(gcn)
                
                excel_exact_map[exact_k] = str(gcn)
                excel_fuzzy_map[fuzzy_k] = str(gcn)

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Lỗi đọc file Excel: {str(e)}")

        # 2. Quét OCR PDF KHÁCH QUAN (Không dùng excel_gcn_list để lọc)
        page_results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(process_page_ocr_standalone, i, doc[i], 300, 0.6): i
                for i in range(total_pages)
            }
            for future in as_completed(futures):
                page_results.append(future.result())

        doc.close()

        # 3. Thu thập danh sách mã quét được từ PDF (Áp dụng Sinh Biến Thể + Match Thông Minh)
        pdf_detected_map = {} # Khóa fuzzy -> Mã hiển thị đại diện

        for res in page_results:
            raw_gcn = res.get('gcn')
            if not raw_gcn:
                continue

            # A. Sinh toàn bộ biến thể từ chuỗi OCR
            variants = generate_ocr_variants(raw_gcn)
            
            matched_excel_code = None
            # B. Thử dò từng biến thể xem có nằm trong Excel không
            for var in variants:
                exact_k = re.sub(r'[-\s\.\/]', '', var)
                fuzzy_k = normalize_fuzzy_key(var)
                
                if exact_k in excel_exact_map:
                    matched_excel_code = excel_exact_map[exact_k]
                    break
                elif fuzzy_k in excel_fuzzy_map:
                    matched_excel_code = excel_fuzzy_map[fuzzy_k]
                    break

            # C. Xác định Khóa và Tên hiển thị cho Mã PDF vừa quét
            fuzzy_key = normalize_fuzzy_key(raw_gcn)
            
            if matched_excel_code:
                # Nếu khớp biến thể với Excel -> Lấy tên đẹp từ Excel
                pdf_detected_map[fuzzy_key] = matched_excel_code
            else:
                # Nếu Excel ĐÃ BỊ XÓA MÃ NÀY -> Vẫn giữ lại mã (chuyển các chữ O lỗi trong seri thành 0)
                # Đảm bảo KHÔNG BỊ MẤT MÃ khi Excel bị xóa!
                best_fix = raw_gcn
                if len(raw_gcn) > 8:
                    prefix = raw_gcn[:8]
                    rest = raw_gcn[8:].replace('O', '0')
                    best_fix = f"{prefix}{rest}"
                pdf_detected_map[fuzzy_key] = best_fix

        # 4. Phân loại theo Tập Hợp (Lấy PDF làm Chuẩn)
        excel_fuzzy_keys = set(excel_fuzzy_map.keys())
        pdf_fuzzy_keys = set(pdf_detected_map.keys())

        matched_keys = pdf_fuzzy_keys.intersection(excel_fuzzy_keys)
        missing_keys = pdf_fuzzy_keys - excel_fuzzy_keys  # PDF có mà Excel không có -> Báo THIẾU
        extra_keys = excel_fuzzy_keys - pdf_fuzzy_keys    # Excel có mà PDF không có -> Báo THỪA

        matched_gcns = sorted([pdf_detected_map[k] for k in matched_keys])
        missing_gcns = sorted([pdf_detected_map[k] for k in missing_keys])
        extra_gcns = sorted([excel_fuzzy_map[k] for k in extra_keys])

        total_pdf = len(pdf_fuzzy_keys)
        matched_count = len(matched_gcns)
        match_rate = f"{(matched_count / total_pdf * 100):.1f}%" if total_pdf > 0 else "0.0%"

        return JSONResponse(content={
            "success": True,
            "summary": {
                "total_pdf_detected": total_pdf,
                "total_excel": len(excel_fuzzy_keys),
                "matched_count": matched_count,
                "missing_count": len(missing_gcns),
                "extra_count": len(extra_gcns),
                "match_rate": match_rate
            },
            "details": {
                "missing": missing_gcns,
                "extra": extra_gcns,
                "matched": matched_gcns
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý đối chiếu: {str(e)}")