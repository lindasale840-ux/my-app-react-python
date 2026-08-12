import React, { useState } from 'react';
import TabMergePdf from '../features/pdf/TabMergePdf';
import PdfSplitByCutNodes from '../features/pdf/PdfSplitByCutNodes';
import TabCompressPdf from '../features/pdf/TabCompressPdf';
import TabReducePdf from "../features/pdf/TabReducePdf";
import TabVersionPdf from "../features/pdf/TabVersionPdf"; // Thêm Tab 5
import TabRemoveBlankPdf from "../features/pdf/TabRemoveBlankPdf"; // Thêm Tab 6

export default function PdfToolsPage() {
  // Quản lý Tab đang chọn (Mặc định là 'merge')
  const [activeTab, setActiveTab] = useState('merge');

  // Helper hàm style đồng bộ Inline Style cho tất cả các nút
  const getTabStyle = (tabKey) => ({
    padding: '10px 20px',
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: 'bold',
    color: activeTab === tabKey ? '#0284c7' : '#64748b',
    borderBottom: activeTab === tabKey ? '3px solid #0284c7' : '3px solid transparent',
    marginBottom: '-2px',
    transition: 'all 0.2s ease-in-out',
  });

  return (
    <div>
      <h1 style={{ marginBottom: '20px', color: '#0f172a' }}>Công Cụ Xử Lý File PDF</h1>

      {/* THANH TAB NAVIGATION */}
      <div style={{ display: 'flex', borderBottom: '2px solid #e2e8f0', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('merge')}
          style={getTabStyle('merge')}
        >
          Ghép File PDF
        </button>

        <button
          onClick={() => setActiveTab('split')}
          style={getTabStyle('split')}
        >
          Tách File PDF
        </button>

        <button
          onClick={() => setActiveTab('compress')}
          style={getTabStyle('compress')}
        >
          Nén PDF
        </button>

        <button
          onClick={() => setActiveTab('reduce')}
          style={getTabStyle('reduce')}
        >
          Giảm dung lượng PDF
        </button>
        <button onClick={() => setActiveTab('version')} style={getTabStyle('version')}>
          Hạ Phiên Bản PDF
        </button>

        <button onClick={() => setActiveTab('remove-blank')} style={getTabStyle('remove-blank')}>
          🧹 Xóa trang trắng
        </button>

        <button
          onClick={() => setActiveTab('scan')}
          style={getTabStyle('scan')}
        >
          PDF Scan (Sắp làm)
        </button>
      </div>

      {/* HIỂN THỊ NỘI DUNG THEO TAB ĐƯỢC CHỌN */}
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        {activeTab === 'merge' && <TabMergePdf />}
        {activeTab === 'split' && <PdfSplitByCutNodes />}
        {activeTab === 'compress' && <TabCompressPdf />}
        {activeTab === 'reduce' && <TabReducePdf />}
        {activeTab === 'version' && <TabVersionPdf />}
        {activeTab === 'remove-blank' && <TabRemoveBlankPdf />}
        {activeTab === 'scan' && <div>Nội dung Tab PDF Scan sẽ để ở đây...</div>}
      </div>
    </div>
  );
}