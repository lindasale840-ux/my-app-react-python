import React, { useState } from 'react';
import TabMultiLookup from '../features/excel/TabMultiLookup';

const ExcelToolsPage = () => {
  const [activeTab, setActiveTab] = useState('multi-lookup');

  const tabs = [
    { id: 'multi-lookup', label: '1. Tra Cứu Nhiều Giá Trị (Multi-Lookup)' },
    { id: 'tab-2', label: '2. Tính Năng Excel Tiếp Theo (Sắp ra mắt)' }
  ];

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Page Title */}
      <h2 style={{ marginBottom: '20px', color: '#2c3e50', borderBottom: '2px solid #007bff', paddingBottom: '10px' }}>
        📊 BỘ CÔNG CỤ XỬ LÝ EXCEL NÂNG CAO
      </h2>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #ccc', marginBottom: '20px' }}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderBottom: isActive ? '3px solid #007bff' : 'none',
                backgroundColor: 'transparent',
                color: isActive ? '#007bff' : '#555',
                fontWeight: isActive ? 'bold' : 'normal',
                cursor: 'pointer',
                fontSize: '14px',
                transition: 'all 0.2s'
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Card Nội dung trắng */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          border: '1px solid #ddd',
          padding: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}
      >
        {activeTab === 'multi-lookup' && <TabMultiLookup />}
        {activeTab === 'tab-2' && (
          <div style={{ padding: '40px', textAlign: 'center', color: '#888' }}>
            📌 Tính năng tiếp theo đang được xây dựng...
          </div>
        )}
      </div>
    </div>
  );
};

export default ExcelToolsPage;