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
  { path: '/excel', name: '2. Xử lý Excel' },
  { path: '/page-3', name: '3. Chức năng 3' },
  { path: '/page-4', name: '4. Chức năng 4' },
  { path: '/page-5', name: '5. Chức năng 5' },
  { path: '/page-6', name: '6. Chức năng 6' },
  { path: '/page-7', name: '7. Chức năng 7' },
  { path: '/page-8', name: '8. Chức năng 8' },
  { path: '/page-9', name: '9. Chức năng 9' },
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