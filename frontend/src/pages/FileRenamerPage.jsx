import React, { useState } from 'react';
import BatchRenameTab from '../features/fileRenamer/BatchRenameTab';

export default function FileRenamerPage() {
  const [activeTab, setActiveTab] = useState('batch_rename');

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
      {/* Tiêu đề trang */}
      <h2 style={{ marginBottom: '15px', color: '#333' }}>Công cụ Đổi tên file Hàng loạt (Batch File Renamer)</h2>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', borderBottom: '2px solid #007bff', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('batch_rename')}
          style={{
            padding: '10px 20px',
            border: 'none',
            backgroundColor: activeTab === 'batch_rename' ? '#007bff' : '#f8f9fa',
            color: activeTab === 'batch_rename' ? '#ffffff' : '#333333',
            cursor: 'pointer',
            fontWeight: 'bold',
            borderRadius: '5px 5px 0 0',
            marginRight: '5px'
          }}
        >
          Đổi tên theo Quy tắc
        </button>
      </div>

      {/* Main Content Card */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #ddd', borderRadius: '6px', padding: '20px', boxShadow: '0 2px 5px rgba(0,0,0,0.05)' }}>
        {activeTab === 'batch_rename' && <BatchRenameTab />}
      </div>
    </div>
  );
}