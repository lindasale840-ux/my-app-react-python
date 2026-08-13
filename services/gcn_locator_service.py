import fitz
import pandas as pd
import io
import time

def run_requested_gcn_extractor_pure_simple(pdf_total_path, requested_gcn_text, process_ocr_func=None):
    """
    Service Layer Tab 3: BẢN ĐƠN GIẢN NGUYÊN BẢN (FAST SKIP SCAN)
    - Thuần túy tìm kiếm nhanh vị trí trang và xuất báo cáo Excel.
    - Quét nhảy cóc 3 trang để tối ưu tốc độ tối đa cho file nặng.
    """
    global_start = time.time()
    print(f"🚀 [TAB 3] BẮT ĐẦU XỬ LÝ ĐỊNH VỊ NHANH (BẢN ĐƠN GIẢN NGUYÊN BẢN)")
    
    # 1. Chuẩn hóa danh sách mã GCN cần tìm từ người dùng nhập vào
    requested_list = [
        line.strip().upper() 
        for line in requested_gcn_text.split("\n") 
        if line.strip() and len(line.strip()) > 2
    ]
    
    if not requested_list:
        return None, "❌ Danh sách mã GCN yêu cầu trống hoặc không hợp lệ."

    doc = fitz.open(pdf_total_path)
    total_pages = len(doc)
    
    detected_map = {}
    
    # 2. THUẬT TOÁN FAST SKIP SCAN
    pages_to_scan = sorted(list(set(range(0, total_pages, 3)) | {total_pages - 1}))
    print(f"⚡ Kích hoạt Quét lướt định vị nhanh trên {len(pages_to_scan)}/{total_pages} trang hình ảnh...")
    
    for idx in pages_to_scan:
        res = process_ocr_func(idx, doc[idx], requested_list, 300, 0.6)
        if res['gcn']:
            detected_map[idx] = res['gcn']
            
    # Quét lùi xác định chính xác điểm biên xuất hiện đầu tiên của mã GCN
    confirmed_milestones = {}
    for idx, gcn in list(detected_map.items()):
        start_check = max(0, idx - 2)
        for reverse_idx in range(idx, start_check - 1, -1):
            if reverse_idx in confirmed_milestones:
                break
            res = process_ocr_func(reverse_idx, doc[reverse_idx], requested_list, 300, 0.6)
            if res['gcn'] == gcn:
                confirmed_milestones[gcn] = reverse_idx
            else:
                break

    doc.close()

    # 3. XUẤT BÁO CÁO EXCEL VỊ TRÍ TRANG
    report_data = []
    for gcn in requested_list:
        page_pos = confirmed_milestones.get(gcn, None)
        report_data.append({
            "Mã Giấy Chứng Nhận Yêu Cầu": gcn,
            "Trạng Thái Tìm Thấy": "Thành công" if page_pos is not None else "Không tìm thấy trong file tổng",
            "Vị trí Trang Bắt đầu (Bắt đầu từ 1)": page_pos + 1 if page_pos is not None else "N/A"
        })
    
    df_report = pd.DataFrame(report_data)
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_report.to_excel(writer, index=False, sheet_name="BaoCao_ViTri_GCN")
    excel_buffer.seek(0)
    
    elapsed_time = time.time() - global_start
    print(f"⏱️ Hoàn thành quét định vị trong {elapsed_time:.2f} giây.")
    
    return excel_buffer, f"🎉 Đã hoàn thành bản đồ định vị nhanh cho {len(confirmed_milestones)}/{len(requested_list)} mã GCN!"