import React, { useState } from 'react';
import TabMergePdf from '../features/pdf/TabMergePdf';

export default function PdfToolsPage() {
  // Quản lý Tab đang chọn (Mặc định là Tab 1)
  const [activeTab, setActiveTab] = useState('merge');

  return (
    <div>
      <h1 style={{ marginBottom: '20px', color: '#0f172a' }}>Công Cụ Xử Lý File PDF</h1>

      {/* THANH TAB NAVIGATION */}
      <div style={{ display: 'flex', borderBottom: '2px solid #e2e8f0', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('merge')}
          style={{
            padding: '10px 20px',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            fontSize: '15px',
            fontWeight: 'bold',
            color: activeTab === 'merge' ? '#0284c7' : '#64748b',
            borderBottom: activeTab === 'merge' ? '3px solid #0284c7' : '3px solid transparent',
            marginBottom: '-2px',
          }}
        >
          Ghép File PDF
        </button>

        <button
          onClick={() => setActiveTab('split')}
          style={{
            padding: '10px 20px',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            fontSize: '15px',
            fontWeight: 'bold',
            color: activeTab === 'split' ? '#0284c7' : '#64748b',
            borderBottom: activeTab === 'split' ? '3px solid #0284c7' : '3px solid transparent',
            marginBottom: '-2px',
          }}
        >
          Tách File PDF (Sắp làm)
        </button>

        <button
          onClick={() => setActiveTab('scan')}
          style={{
            padding: '10px 20px',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            fontSize: '15px',
            fontWeight: 'bold',
            color: activeTab === 'scan' ? '#0284c7' : '#64748b',
            borderBottom: activeTab === 'scan' ? '3px solid #0284c7' : '3px solid transparent',
            marginBottom: '-2px',
          }}
        >
          PDF Scan (Sắp làm)
        </button>
      </div>

      {/* HIỂN THỊ NỘI DUNG THEO TAB ĐƯỢC CHỌN */}
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        {activeTab === 'merge' && <TabMergePdf />}
        {activeTab === 'split' && <div>Nội dung Tab Tách PDF sẽ để ở đây...</div>}
        {activeTab === 'scan' && <div>Nội dung Tab PDF Scan sẽ để ở đây...</div>}
      </div>
    </div>
  );
}