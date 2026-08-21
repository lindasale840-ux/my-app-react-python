import React, { useState } from 'react';
import { checkMissingGcn } from '../../services/pdfScanSplitService';

const CheckMissingTab = () => {
  const [pdfFile, setPdfFile] = useState(null);
  const [excelFile, setExcelFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [activeSubTab, setActiveSubTab] = useState('missing'); // 'missing', 'extra', 'matched'
  const [copied, setCopied] = useState(false);

  const handleCheck = async () => {
    if (!pdfFile || !excelFile) {
      setError('Vui lòng chọn đầy đủ cả file PDF và file Excel!');
      return;
    }

    setError('');
    setLoading(true);
    setResult(null);

    try {
      const data = await checkMissingGcn(pdfFile, excelFile);
      if (data && data.success) {
        setResult(data);
      } else {
        setError('Không nhận được dữ liệu phản hồi hợp lệ.');
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Lỗi hệ thống khi kiểm tra.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (list) => {
    if (!list || list.length === 0) return;
    navigator.clipboard.writeText(list.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '15px', color: '#333' }}>
        🔍 Kiểm tra GCN Thiếu / Thừa (Đối chiếu PDF & Excel)
      </h2>

      {/* Group Inputs */}
      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
          1. Upload File PDF Scan Tổng:
        </label>
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => setPdfFile(e.target.files[0])}
          style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
          2. Upload File Excel Danh sách GCN:
        </label>
        <input
          type="file"
          accept=".xlsx, .xls"
          onChange={(e) => setExcelFile(e.target.files[0])}
          style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
        />
      </div>

      {/* Button Run */}
      <button
        onClick={handleCheck}
        disabled={loading}
        style={{
          backgroundColor: loading ? '#6c757d' : '#28a745',
          color: '#ffffff',
          padding: '10px 20px',
          border: 'none',
          borderRadius: '4px',
          fontWeight: 'bold',
          cursor: loading ? 'not-allowed' : 'pointer',
          width: '100%',
          marginBottom: '20px',
        }}
      >
        {loading ? '⏳ Đang quét OCR & Đối chiếu...' : '🚀 Bắt đầu Kiểm tra & Đối chiếu'}
      </button>

      {/* Alert Error */}
      {error && (
        <div
          style={{
            backgroundColor: '#f8d7da',
            color: '#721c24',
            padding: '12px',
            borderRadius: '4px',
            marginBottom: '20px',
            border: '1px solid #f5c6cb',
          }}
        >
          ❌ {error}
        </div>
      )}

      {/* Dashboard Result Summary */}
      {result && result.summary && (
        <div style={{ marginTop: '20px' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat( auto-fit, minmax(130px, 1fr) )',
              gap: '10px',
              marginBottom: '20px',
            }}
          >
            <div
              style={{
                backgroundColor: '#f8f9fa',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid #ddd',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '12px', color: '#666' }}>Mã trong Excel</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#007bff' }}>
                {result.summary.total_excel}
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#f8f9fa',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid #ddd',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '12px', color: '#666' }}>Quét thấy trong PDF</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#17a2b8' }}>
                {result.summary.total_pdf_detected}
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#d4edda',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid #c3e6cb',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '12px', color: '#155724' }}>Khớp thành công</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#28a745' }}>
                {result.summary.matched_count}
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#f8d7da',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid #f5c6cb',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '12px', color: '#721c24' }}>Mã bị Thiếu</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#dc3545' }}>
                {result.summary.missing_count}
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#fff3cd',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid #ffe8a1',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '12px', color: '#856404' }}>Mã Thừa / Lạ</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ffc107' }}>
                {result.summary.extra_count}
              </div>
            </div>

            <div
              style={{
                backgroundColor: '#e2e3e5',
                padding: '12px',
                borderRadius: '6px',
                border: '1px solid #d6d8db',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '12px', color: '#383d41' }}>Tỷ lệ hoàn thành</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#383d41' }}>
                {result.summary.match_rate}
              </div>
            </div>
          </div>

          {/* Sub Tabs Navigation */}
          <div style={{ display: 'flex', borderBottom: '2px solid #ddd', marginBottom: '15px' }}>
            <button
              onClick={() => setActiveSubTab('missing')}
              style={{
                padding: '10px 15px',
                border: 'none',
                backgroundColor: 'transparent',
                fontWeight: 'bold',
                cursor: 'pointer',
                borderBottom: activeSubTab === 'missing' ? '3px solid #dc3545' : 'none',
                color: activeSubTab === 'missing' ? '#dc3545' : '#555',
              }}
            >
              ❌ Danh sách Mã Thiếu ({result.details.missing.length})
            </button>
            <button
              onClick={() => setActiveSubTab('extra')}
              style={{
                padding: '10px 15px',
                border: 'none',
                backgroundColor: 'transparent',
                fontWeight: 'bold',
                cursor: 'pointer',
                borderBottom: activeSubTab === 'extra' ? '3px solid #ffc107' : 'none',
                color: activeSubTab === 'extra' ? '#d39e00' : '#555',
              }}
            >
              ⚠️ Danh sách Mã Thừa/Lạ ({result.details.extra.length})
            </button>
            <button
              onClick={() => setActiveSubTab('matched')}
              style={{
                padding: '10px 15px',
                border: 'none',
                backgroundColor: 'transparent',
                fontWeight: 'bold',
                cursor: 'pointer',
                borderBottom: activeSubTab === 'matched' ? '3px solid #28a745' : 'none',
                color: activeSubTab === 'matched' ? '#28a745' : '#555',
              }}
            >
              ✅ Danh sách Đã Khớp ({result.details.matched.length})
            </button>
          </div>

          {/* Content SubTab */}
          <div style={{ backgroundColor: '#fafafa', padding: '15px', borderRadius: '6px', border: '1px solid #eee' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontWeight: 'bold' }}>
                Chi tiết danh sách:
              </span>
              <button
                onClick={() => copyToClipboard(result.details[activeSubTab])}
                style={{
                  padding: '5px 12px',
                  backgroundColor: '#007bff',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                }}
              >
                {copied ? '✓ Đã chép!' : '📋 Copy danh sách này'}
              </button>
            </div>

            {result.details[activeSubTab].length === 0 ? (
              <p style={{ color: '#888', fontStyle: 'italic' }}>Không có dữ liệu trong mục này.</p>
            ) : (
              <div
                style={{
                  maxHeight: '250px',
                  overflowY: 'auto',
                  backgroundColor: '#fff',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  padding: '10px',
                }}
              >
                <ol style={{ margin: 0, paddingLeft: '25px' }}>
                  {result.details[activeSubTab].map((item, idx) => (
                    <li key={idx} style={{ padding: '3px 0', fontFamily: 'monospace', fontSize: '14px' }}>
                      {item}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CheckMissingTab;