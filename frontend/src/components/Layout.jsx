import React from 'react';
import { Link, useLocation } from 'react-router-dom';

// Danh sách 9 Page lớn của bạn
const PAGES = [
  { path: '/', name: '1. Xử lý PDF' },
  { path: '/split', name: '2.🧠 Tách PDF Thông Minh' },
  {
    path: '/pdf-scan-split',
    name: '3. ⚡ Nhận diện & Tách PDF GCN',
    icon: 'FileText'
  },
  {
    path: '/gcn-locator',
    name: '4. 📊 Định Vị Trang GCN'
  },
  {
    path: '/pdf-merge',
    name: '5. Tự động hoá hồ sơ'
  },
  {
    path: '/excel-tools',
    name: '6. 📊 Xử Lý Excel Nâng Cao'
  },
  {
    path: '/file-renamer',
    name: '7. Đổi tên File Hàng loạt'
  },
  {
    path: '/excel-to-pdf',
    name: '8. Xuất PDF Hàng Loạt'
  },
];

export default function Layout({ children }) {
  const location = useLocation();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'Arial, sans-serif' }}>
      {/* SIDEBAR BÊN TRÁI - NƠI CHỨA 9 PAGE LỚN */}
      <div style={{ width: '240px', backgroundColor: '#1e293b', color: '#fff', padding: '20px 10px' }}>
        <h2 style={{ fontSize: '18px', textAlign: 'center', marginBottom: '20px', color: '#38bdf8' }}>
          APP XỬ LÝ FILE
        </h2>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {PAGES.map((page) => {
            const isActive = location.pathname === page.path;
            return (
              <Link
                key={page.path}
                to={page.path}
                style={{
                  padding: '10px 15px',
                  borderRadius: '6px',
                  color: isActive ? '#fff' : '#94a3b8',
                  backgroundColor: isActive ? '#0284c7' : 'transparent',
                  textDecoration: 'none',
                  fontSize: '14px',
                  fontWeight: isActive ? 'bold' : 'normal',
                }}
              >
                {page.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* VÙNG NỘI DUNG CHÍNH BÊN PHẢI */}
      <div style={{ flex: 1, backgroundColor: '#f8fafc', padding: '30px' }}>
        {children}
      </div>
    </div>
  );
}