import os
import json
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import socket

# CHÚ Ý: Đây là "Chìa khóa tối cao" của riêng bạn. Tuyệt đối không thay đổi sau khi đã phát hành Key.
SECRET_MASTER_SALT = b"PDF_SMART_STREAMLIT_SECRET_2026"

def _get_cipher():
    """Tạo bộ mã hóa/giải mã dựa trên chìa khóa tối cao"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SECRET_MASTER_SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(b"SuperSecretPassword123"))
    return Fernet(key)

def generate_license_key(customer_name: str, expiry_date_str: str) -> str:
    """
    HÀM DÀNH CHO BẠN (ADMIN): Tạo ra chuỗi Key kích hoạt
    expiry_date_str có định dạng: 'YYYY-MM-DD' (Ví dụ: '2026-12-31')
    """
    data = {
        "user": customer_name,
        "expiry": expiry_date_str
    }
    json_data = json.dumps(data).encode('utf-8')
    cipher = _get_cipher()
    encrypted_data = cipher.encrypt(json_data)
    
    # Biến đổi thành chuỗi dạng hoa, phân tách bằng dấu gạch ngang cho giống Product Key xịn
    hex_key = encrypted_data.hex().upper()
    chunks = [hex_key[i:i+4] for i in range(0, len(hex_key), 4)]
    return "-".join(chunks) # Lấy độ dài vừa phải để dễ nhìn

def verify_license_key(product_key: str):
    """
    HÀM DÀNH CHO APP: Giải mã bản quyền và kiểm tra hạn dùng
    """
    # =========================================================
    # 👑 ĐẶC QUYỀN CHO ADMIN: TỰ ĐỘNG MỞ KHÓA TRÊN CẢ 2 MÁY
    # =========================================================
    try:
        current_hostname = socket.gethostname().upper()
        
        # Bạn điền tên máy ở nhà vào đây, và điền sẵn một cái tên dự phòng cho máy công ty
        # Ví dụ: ["LAPTOP-HOME", "PC-COMPANY"]
        admin_machines = ["THINH09091994", "THINH-GST"]
        
        if current_hostname in [name.upper() for name in admin_machines]: 
            return {
                "valid": True, 
                "user": "ADMIN TỐI CAO (Đặc quyền)", 
                "expiry": "Vô thời hạn", 
                "days_left": 9999,
                "msg": "Bản quyền Admin hợp lệ!"
            }
    except Exception:
        pass
    if not product_key:
        return {"valid": False, "msg": "Chưa nhập mã kích hoạt!"}
    
    try:
        # Khôi phục lại chuỗi mã hóa ban đầu từ Product Key
        hex_key = product_key.replace("-", "").lower()
        encrypted_data = bytes.fromhex(hex_key)
        
        cipher = _get_cipher()
        decrypted_data = cipher.decrypt(encrypted_data)
        data = json.loads(decrypted_data.decode('utf-8'))
        
        # Kiểm tra ngày hết hạn
        expiry_date = datetime.strptime(data["expiry"], "%Y-%m-%d")
        current_date = datetime.now()
        
        if current_date > expiry_date:
            return {"valid": False, "msg": f"Mã đã hết hạn sử dụng vào ngày {data['expiry']}!"}
            
        return {
            "valid": True, 
            "user": data["user"], 
            "expiry": data["expiry"], 
            "days_left": (expiry_date - current_date).days,
            "msg": "Bản quyền hợp lệ!"
        }
    except Exception:
        return {"valid": False, "msg": "Mã kích hoạt không hợp lệ hoặc đã bị chỉnh sửa!"}