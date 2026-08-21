import React, { useState } from 'react';
import AutoSplitTab from '../features/pdfScanSplit/AutoSplitTab';
import CheckMissingTab from '../features/pdfScanSplit/CheckMissingTab';

const PdfScanSplit = () => {
  const [activeTab, setActiveTab] = useState('split'); // 'split' hoặc 'check'

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ maxWidth: '850px', margin: '0 auto', marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '10px' }}>
          ⚡ Tự động nhận diện GCN & Quản lý PDF
        </h1>
        <p style={{ color: '#666', margin: 0 }}>
          Hệ thống OCR thông minh hỗ trợ phân tách trang PDF và đối chiếu mã GCN tự động.
        </p>
      </div>

      <div
        style={{
          maxWidth: '850px',
          margin: '0 auto',
          padding: '20px',
          border: '1px solid #ddd',
          borderRadius: '8px',
          backgroundColor: '#fff',
        }}
      >
        {/* Navigation Tabs Page Level */}
        <div
          style={{
            display: 'flex',
            borderBottom: '2px solid #007bff',
            marginBottom: '20px',
          }}
        >
          <button
            onClick={() => setActiveTab('split')}
            style={{
              padding: '10px 20px',
              border: 'none',
              backgroundColor: activeTab === 'split' ? '#007bff' : '#f8f9fa',
              color: activeTab === 'split' ? '#ffffff' : '#333333',
              fontWeight: 'bold',
              cursor: 'pointer',
              borderTopLeftRadius: '6px',
              borderTopRightRadius: '6px',
              marginRight: '5px',
            }}
          >
            ⚡ Tab 1: Tách & Đặt tên PDF
          </button>
          <button
            onClick={() => setActiveTab('check')}
            style={{
              padding: '10px 20px',
              border: 'none',
              backgroundColor: activeTab === 'check' ? '#007bff' : '#f8f9fa',
              color: activeTab === 'check' ? '#ffffff' : '#333333',
              fontWeight: 'bold',
              cursor: 'pointer',
              borderTopLeftRadius: '6px',
              borderTopRightRadius: '6px',
            }}
          >
            🔍 Tab 2: Kiểm tra GCN Thiếu / Thừa
          </button>
        </div>

        {/* Tab Content Rendering */}
        {activeTab === 'split' ? <AutoSplitTab /> : <CheckMissingTab />}
      </div>
    </div>
  );
};

export default PdfScanSplit;