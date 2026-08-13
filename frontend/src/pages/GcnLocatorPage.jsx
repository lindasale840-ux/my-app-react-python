import React from 'react';
import GcnLocatorTab from '../features/gcnLocator/GcnLocatorTab';

const GcnLocatorPage = () => {
  return (
    <div style={{ padding: '20px' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto', marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '10px' }}>
          📊 Bản đồ định vị vị trí trang Giấy chứng nhận
        </h1>
        <p style={{ color: '#666' }}>
          Sử dụng thuật toán Fast Skip Scan để nhanh chóng xác định chính xác trang bắt đầu của từng mã GCN trong bộ file PDF tổng hợp.
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
        <GcnLocatorTab />
      </div>
    </div>
  );
};

export default GcnLocatorPage;