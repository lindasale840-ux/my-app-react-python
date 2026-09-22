import React from 'react';
import PdfUnlockTab from '../features/pdfUnlock/PdfUnlockTab';

export default function PdfUnlockPage() {
  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '15px', color: '#333' }}>🔓 Mở khóa & Gỡ bỏ bảo vệ PDF</h2>
      
      {/* Navigation Tabs */}
      <div style={{ display: 'flex', borderBottom: '2px solid #007bff', marginBottom: '20px' }}>
        <div style={{ padding: '10px 20px', backgroundColor: '#007bff', color: '#fff', fontWeight: 'bold', borderRadius: '4px 4px 0 0' }}>
          Mở khóa PDF
        </div>
      </div>

      {/* Card nội dung trắng */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #ddd', borderRadius: '6px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
        <PdfUnlockTab />
      </div>
    </div>
  );
}