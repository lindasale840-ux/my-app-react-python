import React from 'react';
import AutoSplitTab from '../features/pdfScanSplit/AutoSplitTab';

const PdfScanSplit = () => {
  return (
    <div style={{ padding: '20px' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto', marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '10px' }}>
          ⚡ Tự động nhận diện GCN & Tách PDF
        </h1>
        <p style={{ color: '#666' }}>
          Hệ thống OCR thông minh giúp phân tách trang và đặt tên file tự động.
        </p>
      </div>

      <div style={{ 
        maxWidth: '800px', 
        margin: '0 auto', 
        padding: '20px', 
        border: '1px solid #ddd', 
        borderRadius: '8px', 
        backgroundColor: '#fff' 
      }}>
        <AutoSplitTab />
      </div>
    </div>
  );
};

export default PdfScanSplit;