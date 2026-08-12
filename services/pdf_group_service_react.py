import io
import zipfile
import pandas as pd
from typing import List, Tuple

def parse_excel_columns(excel_bytes: bytes) -> List[str]:
    """
    Đọc file Excel từ bytes và trả về danh sách tên cột/mẫu dữ liệu hàng đầu tiên
    """
    df = pd.read_excel(io.BytesIO(excel_bytes), header=None, nrows=5)
    df = df.fillna("").astype(str)
    
    columns_info = []
    num_cols = df.shape[1]
    for i in range(num_cols):
        sample_val = df.iloc[0, i] if len(df) > 0 else ""
        label = f"Cột {i} (Ví dụ: {sample_val})" if sample_val else f"Cột {i}"
        columns_info.append(label)
        
    return columns_info


def process_group_pdfs(
    excel_bytes: bytes,
    pdfs_data: List[Tuple[str, bytes]],
    match_col_idx: int,
    target_col_idx: int
) -> Tuple[bytes, str]:
    """
    Tạo cấu trúc thư mục con trong file ZIP hoàn toàn trên RAM
    """
    # 1. Đọc file Excel
    df = pd.read_excel(io.BytesIO(excel_bytes), header=None, dtype=str)
    df = df.fillna("").astype(str)

    # Map: { Ma_GCN_Upper: Ten_Thu_Muc }
    excel_map = {}
    for _, row in df.iterrows():
        if match_col_idx < len(row) and target_col_idx < len(row):
            gcn_raw = str(row[match_col_idx]).strip().upper()
            target_val = str(row[target_col_idx]).strip()
            if gcn_raw:
                excel_map[gcn_raw] = target_val

    # 2. Chuẩn bị buffer ZIP trên RAM
    zip_buffer = io.BytesIO()
    success_count = 0
    fail_count = 0
    log_lines = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Duyệt từng file PDF
        for pdf_name, pdf_bytes in pdfs_data:
            # Lấy tên file không bao gồm phần mở rộng .pdf
            gcn_key = pdf_name.rsplit('.', 1)[0].strip().upper()

            if gcn_key in excel_map and excel_map[gcn_key]:
                group_name = excel_map[gcn_key]
                # Lọc ký tự hợp lệ cho tên folder
                group_folder = "".join([c for c in group_name if c.isalnum() or c in ' _-']).strip()
                if not group_folder:
                    group_folder = "Nhom_Khong_Ten"
                
                success_count += 1
                log_lines.append(f"Khớp thành công: {pdf_name} -> Thư mục [{group_folder}]")
            else:
                group_folder = "Khong_Tim_Thay"
                fail_count += 1
                log_lines.append(f"Không khớp: {pdf_name} -> Thư mục [Khong_Tim_Thay]")

            # Đường dẫn tương đối bên trong file ZIP
            arc_path = f"{group_folder}/{pdf_name}"
            zipf.writestr(arc_path, pdf_bytes)

        # Đưa file LOG vào thẳng root của ZIP
        log_content = "\n".join(log_lines)
        zipf.writestr("LOG_Doi_Chieu.txt", log_content.encode("utf-8"))

    zip_buffer.seek(0)
    summary_msg = f"✅ Phân loại xong! Khớp thành công: {success_count} file. Thất bại: {fail_count} file."
    
    return zip_buffer.getvalue(), summary_msg