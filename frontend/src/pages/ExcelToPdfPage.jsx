import React, { useState } from 'react';
import BatchExportTab from '../features/excelToPdf/BatchExportTab';

const ExcelToPdfPage = () => {
  const [activeTab, setActiveTab] = useState('batch_export');

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      {/* TITLE PAGE */}
      <h2 style={{ marginBottom: '15px', color: '#333' }}>Xuất PDF Hàng Loạt từ File Excel</h2>

      {/* NAVIGATION TABS */}
      <div style={{ display: 'flex', borderBottom: '2px solid #007bff', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('batch_export')}
          style={{
            padding: '10px 20px',
            backgroundColor: activeTab === 'batch_export' ? '#007bff' : '#f8f9fa',
            color: activeTab === 'batch_export' ? '#ffffff' : '#007bff',
            border: '1px solid #007bff',
            borderBottom: 'none',
            borderRadius: '4px 4px 0 0',
            fontWeight: 'bold',
            cursor: 'pointer',
            marginRight: '5px',
          }}
        >
          Xuất PDF Hàng Loạt
        </button>
      </div>

      {/* CARD NỘI DUNG TRẮNG PADDING 20PX */}
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid #ddd',
          borderRadius: '6px',
          padding: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
        }}
      >
        {activeTab === 'batch_export' && <BatchExportTab />}
      </div>
    </div>
  );
};

export default ExcelToPdfPage;