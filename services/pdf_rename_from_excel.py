import os
import re
import tempfile
import zipfile
import pandas as pd

def clean_value(val):
    """Hàm phụ trợ: Kiểm tra và làm sạch giá trị đọc từ Excel"""
    if pd.isna(val):
        return ""
    val_str = str(val).strip()
    # Nếu là dấu / hoặc các dạng rỗng
    if val_str in ["/", "", "NA", "na", "NaN", "nan"]:
        return ""
    return val_str

def rename_pdf_files(file_excel_bytes, pdf_files, match_col, primary_name_col, fallback_name_col):
    """
    Đổi tên file PDF dựa theo dữ liệu Excel và đóng gói ZIP.
    - match_col: Cột Excel dùng để khớp với tên file PDF cũ
    - primary_name_col: Cột lấy tên ưu tiên 1
    - fallback_name_col: Cột lấy tên dự phòng (khi cột 1 rỗng hoặc là '/')
    """
    try:
        # 1. Đọc file Excel
        df = pd.read_excel(file_excel_bytes)
        
        # Tạo Dictionary tra cứu để tìm kiếm cho nhanh:
        # Key: Tên file cũ (đã xóa khoảng trắng) -> Value: {primary: ..., fallback: ...}
        lookup_dict = {}
        for idx, row in df.iterrows():
            match_key = clean_value(row.get(match_col))
            if match_key:
                lookup_dict[match_key.lower()] = {
                    "primary": clean_value(row.get(primary_name_col)),
                    "fallback": clean_value(row.get(fallback_name_col))
                }

        temp_dir = tempfile.mkdtemp()
        renamed_files = []
        logs = []
        logs.append("--- BẮT ĐẦU TIẾN TRÌNH ĐỔI TÊN FILE PDF ---")

        total_pdf = len(pdf_files)

        # 2. Lặp qua từng file PDF được tải lên
        for idx, pdf_file in enumerate(pdf_files, 1):
            old_full_name = pdf_file.name
            old_name_no_ext, ext = os.path.splitext(old_full_name)
            old_key = old_name_no_ext.strip().lower()

            # Kiểm tra xem tên file cũ có trong Excel không
            if old_key in lookup_dict:
                data = lookup_dict[old_key]
                primary_val = data["primary"]
                fallback_val = data["fallback"]

                # Logic chọn tên: Lấy cột 1, nếu rỗng thì lấy cột 2
                prefix_name = primary_val if primary_val else fallback_val

                if prefix_name:
                    # Ghép tên mới = Tên lựa chọn + Tên cũ
                    # Có thể dùng dấu _ hoặc - làm phân cách cho đẹp mắt
                    new_name_no_ext = f"{prefix_name}_{old_name_no_ext}"
                else:
                    # Trường hợp cả 2 cột đều rỗng -> Giữ nguyên tên cũ
                    new_name_no_ext = old_name_no_ext
                    logs.append(f"[{idx}/{total_pdf}] Cảnh báo: File '{old_full_name}' cả 2 cột đều rỗng -> Giữ nguyên tên.")

                # Làm sạch tên file mới (xóa các ký tự cấm của Windows như \ / : * ? " < > |)
                safe_new_name = re.sub(r'[\\/*?:"<>|]', '_', new_name_no_ext) + ext
                
                # Lưu file ra thư mục tạm
                new_file_path = os.path.join(temp_dir, safe_new_name)
                with open(new_file_path, "wb") as f:
                    f.write(pdf_file.getvalue() if hasattr(pdf_file, 'getvalue') else pdf_file.read())
                
                renamed_files.append(new_file_path)
                logs.append(f"[{idx}/{total_pdf}] Đổi tên: '{old_full_name}' -> '{safe_new_name}'")

            else:
                # Nếu không tìm thấy tên file trong Excel -> Giữ nguyên tên cũ và lưu vào zip
                new_file_path = os.path.join(temp_dir, old_full_name)
                with open(new_file_path, "wb") as f:
                    f.write(pdf_file.getvalue() if hasattr(pdf_file, 'getvalue') else pdf_file.read())
                renamed_files.append(new_file_path)
                logs.append(f"[{idx}/{total_pdf}] Không thấy trong Excel: Giữ nguyên '{old_full_name}'")

        # 3. Tạo file Log_Doi_Ten_PDF.txt
        log_path = os.path.join(temp_dir, "Log_Doi_Ten_PDF.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))

        # 4. Nén tất cả vào ZIP
        zip_path = os.path.join(tempfile.gettempdir(), "Danh_Sach_PDF_Da_Doi_Ten.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for f_path in renamed_files:
                zipf.write(f_path, arcname=os.path.basename(f_path))
            zipf.write(log_path, arcname="Log_Doi_Ten_PDF.txt")

        return zip_path, f"Thành công! Đã xử lý đổi tên {len(pdf_files)} file PDF."

    except Exception as e:
        return None, f"Lỗi xử lý: {str(e)}"