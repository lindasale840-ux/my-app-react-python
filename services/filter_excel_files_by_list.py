import os
import tempfile
import zipfile
import pandas as pd

def clean_file_name_str(val):
    """Chuẩn hóa tên file: xóa khoảng trắng, đưa về chữ thường, loại bỏ đuôi .xlsx/.xls"""
    if pd.isna(val):
        return ""
    s = str(val).strip().lower()
    if s.endswith(".xlsx"):
        s = s[:-5]
    elif s.endswith(".xls"):
        s = s[:-4]
    return s.strip()

def filter_excel_files_by_list(excel_list_bytes, name_col, target_files):
    """
    Đọc danh sách tên từ File Tổng -> Lọc ra các file Excel thực tế trùng tên -> Đóng gói ZIP.
    - excel_list_bytes: Stream file Excel tổng
    - name_col: Cột chứa danh sách tên file cần lọc
    - target_files: Thư mục chứa danh sách các file Excel thực tế
    """
    try:
        # 1. Đọc danh sách tên file cần lọc từ File Tổng
        df = pd.read_excel(excel_list_bytes)
        if name_col not in df.columns:
            return None, f"Không tìm thấy cột '{name_col}' trong file Excel tổng!"

        # Tập hợp tên file cần tìm (Set để tra cứu cực nhanh)
        target_names_set = set()
        for val in df[name_col]:
            clean_name = clean_file_name_str(val)
            if clean_name:
                target_names_set.add(clean_name)

        if not target_names_set:
            return None, "Không tìm thấy dữ liệu tên file hợp lệ nào trong cột đã chọn!"

        logs = []
        logs.append("--- BẮT ĐẦU TIẾN TRÌNH LỌC FILE EXCEL THEO DANH SÁCH ---")
        logs.append(f"Số lượng tên file cần lọc trong Excel tổng: {len(target_names_set)}")
        logs.append(f"Số lượng file thực tế tải lên: {len(target_files)}")
        logs.append("-" * 50)

        # 2. Lặp qua danh sách file thực tế và tiến hành lọc
        matched_files = []
        found_names_set = set()

        for file_obj in target_files:
            clean_real_name = clean_file_name_str(file_obj.name)
            
            # Kiểm tra xem tên file thực tế có nằm trong danh sách cần lọc không
            if clean_real_name in target_names_set:
                matched_files.append(file_obj)
                found_names_set.add(clean_real_name)
                logs.append(f"[KHỚP - ĐÃ LỌC] {file_obj.name}")

        # Ghi Log cho các file có tên trong Excel nhưng KHÔNG TÌM THẤY file thực tế
        missing_in_folder = target_names_set - found_names_set
        if missing_in_folder:
            logs.append("-" * 50)
            logs.append(f"⚠️ CẢNH BÁO: Có {len(missing_in_folder)} tên file trong danh sách Excel nhưng KHÔNG TÌM THẤY file thực tế:")
            for m_name in missing_in_folder:
                logs.append(f"  - Thiếu file: '{m_name}.xlsx'")

        if not matched_files:
            return None, "Không tìm thấy file Excel nào trùng khớp với danh sách trong file tổng!"

        # 3. Lưu file lọc được ra thư mục tạm & tạo file ZIP
        temp_dir = tempfile.mkdtemp()
        saved_paths = []

        for f_match in matched_files:
            file_path = os.path.join(temp_dir, f_match.name)
            with open(file_path, "wb") as f:
                f.write(f_match.getvalue() if hasattr(f_match, 'getvalue') else f_match.read())
            saved_paths.append(file_path)

        # Tạo file Log
        log_path = os.path.join(temp_dir, "Log_Chi_Tiet_Loc_File.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))

        # Đóng gói ZIP
        zip_path = os.path.join(tempfile.gettempdir(), "Danh_Sach_Excel_Da_Loc.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for f_path in saved_paths:
                zipf.write(f_path, arcname=os.path.basename(f_path))
            zipf.write(log_path, arcname="Log_Chi_Tiet_Loc_File.txt")

        msg = f"Lọc thành công {len(matched_files)}/{len(target_names_set)} file Excel khớp với danh sách!"
        if missing_in_folder:
            msg += f" (Cảnh báo: Thiếu {len(missing_in_folder)} file không tìm thấy)."

        return zip_path, msg

    except Exception as e:
        return None, f"Lỗi xử lý: {str(e)}"