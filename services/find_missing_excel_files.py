import os
import tempfile
import zipfile
import pandas as pd

def clean_file_name_str(val):
    """Chuẩn hóa chuỗi tên file: bỏ khoảng trắng, đổi về chữ thường, bỏ đuôi .xlsx nếu có"""
    if pd.isna(val):
        return ""
    s = str(val).strip().lower()
    if s.endswith(".xlsx"):
        s = s[:-5]
    elif s.endswith(".xls"):
        s = s[:-4]
    return s.strip()

def find_missing_excel_files_v2(mode, files_b, files_a=None, excel_list_bytes=None, name_col=None):
    """
    Tìm file Excel thiếu ở B so với A hoặc so với File Excel danh sách tổng.
    - mode: 'folder' (So sánh Folder A vs B) hoặc 'excel_list' (So sánh File danh sách vs Folder B)
    """
    try:
        names_in_a = set()
        logs = []
        logs.append("--- BẮT ĐẦU ĐỐI CHIẾU FILE EXCEL CÒN THIẾU ---")
        logs.append(f"Chế độ kiểm tra: {'So sánh 2 Folder' if mode == 'folder' else 'So sánh với File Excel danh sách'}")

        # -------------------------------------------------------------
        # BƯỚC 1: XÂY DỰNG TẬP HỢP TÊN FILE CHUẨN ĐỂ ĐỐI CHIẾU (A)
        # -------------------------------------------------------------
        if mode == 'folder':
            if not files_a:
                return None, "Chưa chọn danh sách file cho Folder A!"
            
            # Lấy tên file không kèm đuôi mở rộng
            for f in files_a:
                clean_name = clean_file_name_str(f.name)
                if clean_name:
                    names_in_a.add(clean_name)
            logs.append(f"Tổng số file trong Folder A: {len(files_a)}")

        elif mode == 'excel_list':
            if not excel_list_bytes or not name_col:
                return None, "Chưa upload File danh sách tổng hoặc chưa chọn cột tên file!"
            
            df = pd.read_excel(excel_list_bytes)
            if name_col not in df.columns:
                return None, f"Không tìm thấy cột '{name_col}' trong file Excel!"
            
            for val in df[name_col]:
                clean_name = clean_file_name_str(val)
                if clean_name:
                    names_in_a.add(clean_name)
            logs.append(f"Tổng số tên file cần có trong File Excel danh sách: {len(names_in_a)}")

        logs.append(f"Tổng số file thực tế có trong Folder B: {len(files_b)}")
        logs.append("-" * 50)

        # -------------------------------------------------------------
        # BƯỚC 2: SO SÁNH VỚI FOLDER B ĐỂ TÌM FILE THIẾU
        # -------------------------------------------------------------
        missing_files = []
        
        if mode == 'folder':
            # Tìm file có ở B nhưng THIẾU ở A
            for pdf_b in files_b:
                clean_b_name = clean_file_name_str(pdf_b.name)
                if clean_b_name not in names_in_a:
                    missing_files.append(pdf_b)
                    logs.append(f"[THIẾU TRONG FOLDER A] {pdf_b.name}")
        else:
            # Tìm file có trong Danh sách Excel nhưng KHÔNG CÓ TRONG FOLDER B
            # Tạo map thực tế ở Folder B
            files_b_map = {clean_file_name_str(f.name): f for f in files_b}
            
            # Lặp qua danh sách tên cần có
            for target_name in names_in_a:
                if target_name not in files_b_map:
                    logs.append(f"[THIẾU TRONG FOLDER B] File tên: '{target_name}.xlsx'")
                else:
                    # Nếu có trong B thì không bị thiếu
                    pass

            # Đối với chế độ 'excel_list': gom các file có ở B mà NẰM TRONG danh sách bị thiếu (nếu dùng để trích xuất)
            # Hoặc gom các file CÓ TRONG B mà khớp với danh sách (tùy thuộc vào nhu cầu trích xuất file thực tế)
            # Logic: Lọc các file ở B chưa được điểm danh / Hoặc gom file hiện có ở B
            for pdf_b in files_b:
                clean_b_name = clean_file_name_str(pdf_b.name)
                if clean_b_name not in names_in_a:
                    missing_files.append(pdf_b)
                    logs.append(f"[FILE DƯ Ở B / KHÔNG CÓ TRONG DANH SÁCH] {pdf_b.name}")

        # -------------------------------------------------------------
        # BƯỚC 3: ĐÓNG GÓI VÀ XUẤT FILE ZIP
        # -------------------------------------------------------------
        temp_dir = tempfile.mkdtemp()
        saved_paths = []

        # Lưu các file bị lẻ/thiếu phát hiện được
        for f_missing in missing_files:
            file_path = os.path.join(temp_dir, f_missing.name)
            with open(file_path, "wb") as f:
                f.write(f_missing.getvalue() if hasattr(f_missing, 'getvalue') else f_missing.read())
            saved_paths.append(file_path)

        # File Log chi tiết luôn luôn được tạo
        log_path = os.path.join(temp_dir, "Log_Chi_Tiet_Doi_Chieu.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(logs))

        zip_path = os.path.join(tempfile.gettempdir(), "Ket_Qua_Doi_Chieu_Excel.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for f_path in saved_paths:
                zipf.write(f_path, arcname=os.path.basename(f_path))
            zipf.write(log_path, arcname="Log_Chi_Tiet_Doi_Chieu.txt")

        return zip_path, f"Hoàn tất đối chiếu! Đã xuất log và {len(missing_files)} file liên quan vào ZIP."

    except Exception as e:
        return None, f"Lỗi xử lý: {str(e)}"