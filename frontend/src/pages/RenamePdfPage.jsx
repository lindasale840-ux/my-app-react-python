import React from 'react';
import RenamePdfFromExcelTab from '../features/renamePdf/RenamePdfFromExcelTab';

const RenamePdfPage = () => {
  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '15px', color: '#333333' }}>
        ĐỔI TÊN HÀNG LOẠT FILE PDF THEO FILE EXCEL TỔNG
      </h2>
      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <RenamePdfFromExcelTab />
      </div>
    </div>
  );
};

export default RenamePdfPage;