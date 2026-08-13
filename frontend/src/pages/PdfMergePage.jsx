import React, { useState } from 'react';
import MergeByNameTab from '../features/pdfMerge/MergeByNameTab';
import MergeByExcelTab from '../features/pdfMerge/MergeByExcelTab';

const PdfMergePage = () => {
  const [activeTab, setActiveTab] = useState('tab1');

  // Danh sách Tab - Sẽ bổ sung Tab 2, Tab 3 vào đây sau
  const tabs = [
    { id: 'tab1', label: '📎 Ghép theo tên file' },
    { id: 'tab2', label: '📊 Ghép theo Excel' },
    // { id: 'tab2', label: 'Tab 2 - Chức năng tiếp theo' },
  ];

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '20px', fontSize: '24px', color: '#333' }}>
        QUẢN LÝ GHÉP HỒ SƠ PDF
      </h1>

      {/* Navigation Tabs Header */}
      <div style={{
        display: 'flex',
        borderBottom: '2px solid #ddd',
        marginBottom: '20px'
      }}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 20px',
                border: 'none',
                backgroundColor: 'transparent',
                borderBottom: isActive ? '3px solid #007bff' : '3px solid transparent',
                color: isActive ? '#007bff' : '#555',
                fontWeight: isActive ? 'bold' : 'normal',
                cursor: 'pointer',
                fontSize: '15px',
                marginRight: '10px',
                transition: 'all 0.2s'
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Card nội dung trắng */}
      <div style={{
        backgroundColor: '#ffffff',
        border: '1px solid #ddd',
        borderRadius: '6px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}>
        {activeTab === 'tab1' && <MergeByNameTab />}
        {activeTab === 'tab2' && <MergeByExcelTab />}
        {/* {activeTab === 'tab2' && <Tab2Component />} */}
      </div>
    </div>
  );
};

export default PdfMergePage;