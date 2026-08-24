import React, { useState } from 'react';
import { ExtractPdfNamesTab } from '../features/pdfTools/ExtractPdfNamesTab';
import { ComparePdfExcelTab } from '../features/pdfTools/ComparePdfExcelTab';

export const PdfToolsPage1 = () => {
  const [activeTab, setActiveTab] = useState('extract');

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '20px', color: '#333' }}>
        TRÍCH XUẤT VÀ ĐỐI CHIẾU FILE PDF VỚI EXCEL
      </h2>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', borderBottom: '2px solid #ddd', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('extract')}
          style={{
            padding: '10px 20px',
            border: 'none',
            borderBottom: activeTab === 'extract' ? '3px solid #007bff' : 'none',
            backgroundColor: 'transparent',
            color: activeTab === 'extract' ? '#007bff' : '#555',
            fontWeight: activeTab === 'extract' ? 'bold' : 'normal',
            cursor: 'pointer',
            fontSize: '15px'
          }}
        >
          Trích Xuất Tên PDF sang Excel
        </button>

        <button
          onClick={() => setActiveTab('compare')}
          style={{
            padding: '10px 20px',
            border: 'none',
            borderBottom: activeTab === 'compare' ? '3px solid #007bff' : 'none',
            backgroundColor: 'transparent',
            color: activeTab === 'compare' ? '#007bff' : '#555',
            fontWeight: activeTab === 'compare' ? 'bold' : 'normal',
            cursor: 'pointer',
            fontSize: '15px'
          }}
        >
          Đối Chiếu PDF Với File Excel (Nâng Cao)
        </button>
      </div>

      {/* Card Nội Dung Trắng */}
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}>
        {activeTab === 'extract' && <ExtractPdfNamesTab />}
        {activeTab === 'compare' && <ComparePdfExcelTab />}
      </div>
    </div>
  );
};

export default PdfToolsPage1;