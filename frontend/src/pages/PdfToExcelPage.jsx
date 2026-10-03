import React from 'react';
import ExportPdfToExcelTab from '../features/excel/ExportPdfToExcelTab';

export default function PdfToExcelPage() {
  return (
    <div style={{ padding: '20px' }}>
      <h2 style={{ marginBottom: '10px', color: '#333' }}>EXPORT PDF TO EXCEL CHUẨN XÁC 100%</h2>
      <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
        Trích xuất bảng dữ liệu từ danh sách file PDF sang Excel với độ chính xác cao, hỗ trợ kiểm duyệt ma trận ô gộp & xử lý hàng loạt.
      </p>

      {/* Card Nội Dung Trắng Standard */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '6px',
          border: '1px solid #ccc',
          padding: '20px',
        }}
      >
        <ExportPdfToExcelTab />
      </div>
    </div>
  );
}