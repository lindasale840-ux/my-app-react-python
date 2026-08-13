import React from 'react';
import PdfSplitTab from '../features/pdfsplit/PdfSplitTab';

export default function PDFSPLIT() {
  const getTabStyle = () => ({
    padding: '10px 20px',
    cursor: 'pointer',
    borderBottom: '2px solid #007bff',
    fontWeight: 'bold',
    color: '#007bff',
    background: 'none',
    borderTop: 'none',
    borderLeft: 'none',
    borderRight: 'none'
  });

  return (
    <div style={{ padding: '20px', backgroundColor: '#f4f6f9', minHeight: '100vh' }}>
      <h2 style={{ marginBottom: '20px', color: '#333' }}>🧠 Tách PDF Thông Minh</h2>
      
      <div style={{ display: 'flex', borderBottom: '1px solid #ccc', marginBottom: '20px' }}>
        <button style={getTabStyle()}>Tách PDF</button>
      </div>

      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          padding: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}
      >
        <PdfSplitTab />
      </div>
    </div>
  );
}