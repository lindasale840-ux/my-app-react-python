import streamlit as st
import os
import json
from backend.license_manager import generate_license_key, verify_license_key

st.set_page_config(page_title="Bản quyền ứng dụng", layout="wide")
st.header("🔑 Quản lý Bản quyền & Kích hoạt Ứng dụng")

LICENSE_FILE = "license.json"

# Đọc key đã lưu cũ nếu có
saved_key = ""
if os.path.exists(LICENSE_FILE):
    try:
        with open(LICENSE_FILE, "r") as f:
            saved_key = json.load(f).get("product_key", "")
    except:
        pass

# Giao diện chia làm 2 phân vùng (Sử dụng sidebar của trang bản quyền)
menu = st.sidebar.radio("Chức năng Bản quyền", ["Kích hoạt phần mềm", "Tạo Key (Chỉ dành cho Admin)"])

if menu == "Kích hoạt phần mềm":
    st.subheader("🛠 Trạng thái bản quyền của bạn")
    status = verify_license_key(saved_key)
    
    if status["valid"]:
        st.success(f"✅ Phần mềm ĐÃ KÍCH HOẠT thành công!")
        st.info(f"👤 **Người sở hữu:** {status['user']}  \n📅 **Hạn dùng đến ngày:** {status['expiry']} (Còn {status['days_left']} ngày)")
    else:
        st.error(f"❌ Chưa được kích hoạt hoặc hết hạn! Lý do: {status['msg']}")
        
    st.write("---")
    new_key = st.text_area("Nhập mã kích hoạt mới tại đây:", value=saved_key, placeholder="XXXX-XXXX-XXXX-...")
    
    if st.button("💾 Lưu và Kích hoạt", type="primary"):
        check_new = verify_license_key(new_key.strip())
        if check_new["valid"]:
            with open(LICENSE_FILE, "w") as f:
                json.dump({"product_key": new_key.strip()}, f)
            st.success(f"🎉 Kích hoạt thành công! Bản quyền thuộc về: {check_new['user']}")
            st.rerun()
        else:
            st.error(f"❌ Kích hoạt thất bại: {check_new['msg']}")

elif menu == "Tạo Key (Chỉ dành cho Admin)":
    st.subheader("🔑 Trình tạo mã kích hoạt bảo mật")
    admin_pass = st.text_input("Nhập mật khẩu Admin để mở khóa:", type="password")
    
    if admin_pass == "famille123": 
        cust_name = st.text_input("Tên khách hàng / Tên máy tính:", placeholder="Ví dụ: Bạn A - Phòng Kinh Doanh")
        expiry_date = st.date_input("Hết hạn vào ngày:")
        
        if st.button("✨ Sinh mã Key Bản Quyền"):
            if not cust_name:
                st.error("Vui lòng nhập tên khách hàng!")
            else:
                formatted_date = expiry_date.strftime("%Y-%m-%d")
                generated_key = generate_license_key(cust_name, formatted_date)
                st.success("🎉 Đã tạo mã thành công! Hãy copy chuỗi dưới đây gửi cho khách hàng:")
                st.code(generated_key, language="text")
    elif admin_pass != "":
        st.error("Sai mật khẩu Admin!")