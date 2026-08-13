import React, { useState } from 'react';
import { getExcelColumnsService, mergeByExcelService } from '../../services/pdfMergeService';

const MergeByExcelTab = () => {
  const [filesA, setFilesA] = useState([]);
  const [filesB, setFilesB] = useState([]);
  const [excelFile, setExcelFile] = useState(null);
  const [columns, setColumns] = useState([]);
  const [columnA, setColumnA] = useState('');
  const [columnB, setColumnB] = useState('');

  const [loading, setLoading] = useState(false);
  const [loadingExcel, setLoadingExcel] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleExcelChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setExcelFile(file);
    setLoadingExcel(true);
    setError(null);

    try {
      const res = await getExcelColumnsService(file);
      const cols = res.columns || [];
      setColumns(cols);

      if (cols.length > 0) {
        setColumnA(cols[0]);
        setColumnB(cols[1] || cols[0]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể đọc các cột từ file Excel!');
      setColumns([]);
    } finally {
      setLoadingExcel(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!excelFile) {
      setError('Vui lòng chọn file Excel cấu hình!');
      return;
    }
    if (!columnA || !columnB) {
      setError('Vui lòng chọn cột tương ứng cho File A và File B!');
      return;
    }
    if (!filesA || filesA.length === 0) {
      setError('Vui lòng chọn danh sách File Bộ A!');
      return;
    }
    if (!filesB || filesB.length === 0) {
      setError('Vui lòng chọn danh sách File Bộ B!');
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const response = await mergeByExcelService(filesA, filesB, excelFile, columnA, columnB);

      const successCount = response.headers['x-success-count'] || 0;
      const totalCount = response.headers['x-total-count'] || 0;

      const blob = new Blob([response.data], { type: 'application/zip' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', 'Merge_By_Excel.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setMessage(`✅ Ghép thành công ${successCount}/${totalCount} hồ sơ. File ZIP bao gồm cả file báo cáo Merge_Report.xlsx.`);
    } catch (err) {
      if (err.response && err.response.data instanceof Blob) {
        const text = await err.response.data.text();
        try {
          const json = JSON.parse(text);
          setError(json.detail || 'Có lỗi xảy ra khi ghép file!');
        } catch {
          setError('Có lỗi xảy ra khi ghép file!');
        }
      } else {
        setError(err.response?.data?.detail || err.message || 'Có lỗi xảy ra!');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3 style={{ marginTop: 0, marginBottom: '15px', color: '#333' }}>
        📊 Ghép Hồ Sơ Theo Cấu Hình Excel
      </h3>
      <p style={{ marginBottom: '20px', color: '#666', fontSize: '14px' }}>
        Tải lên file Excel định nghĩa cặp ghép (Cột File A & Cột File B) cùng các tập tin PDF tương ứng để xử lý ghép hàng loạt.
      </p>

      {error && (
        <div style={{
          backgroundColor: '#f8d7da',
          color: '#721c24',
          padding: '12px 15px',
          borderRadius: '4px',
          marginBottom: '20px',
          border: '1px solid #f5c6cb'
        }}>
          {error}
        </div>
      )}

      {message && (
        <div style={{
          backgroundColor: '#d4edda',
          color: '#155724',
          padding: '12px 15px',
          borderRadius: '4px',
          marginBottom: '20px',
          border: '1px solid #c3e6cb'
        }}>
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* 1. Chọn File Excel */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
            1. File Excel Cấu Hình (.xlsx, .xls):
          </label>
          <input
            type="file"
            accept=".xlsx, .xls"
            onChange={handleExcelChange}
            style={{
              display: 'block',
              width: '100%',
              padding: '8px',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
          />
          {loadingExcel && (
            <span style={{ fontSize: '13px', color: '#007bff', marginTop: '5px', display: 'block' }}>
              Đang phân tích các cột trong file Excel...
            </span>
          )}
        </div>

        {/* Cấu hình chọn Cột A và B */}
        {columns.length > 0 && (
          <div style={{
            display: 'flex',
            gap: '20px',
            marginBottom: '20px',
            backgroundColor: '#f8f9fa',
            padding: '15px',
            borderRadius: '4px',
            border: '1px solid #e9ecef'
          }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
                Chọn Cột Chứa Tên File A:
              </label>
              <select
                value={columnA}
                onChange={(e) => setColumnA(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #ccc'
                }}
              >
                {columns.map((col, idx) => (
                  <option key={idx} value={col}>{col}</option>
                ))}
              </select>
            </div>

            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
                Chọn Cột Chứa Tên File B:
              </label>
              <select
                value={columnB}
                onChange={(e) => setColumnB(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #ccc'
                }}
              >
                {columns.map((col, idx) => (
                  <option key={idx} value={col}>{col}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* 2. File Bộ A */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
            2. Danh sách File Bộ A (PDF):
          </label>
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={(e) => setFilesA(e.target.files)}
            style={{
              display: 'block',
              width: '100%',
              padding: '8px',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
          />
          {filesA.length > 0 && (
            <span style={{ fontSize: '13px', color: '#007bff', marginTop: '5px', display: 'block' }}>
              Đã chọn {filesA.length} file Bộ A
            </span>
          )}
        </div>

        {/* 3. File Bộ B */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
            3. Danh sách File Bộ B (PDF):
          </label>
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={(e) => setFilesB(e.target.files)}
            style={{
              display: 'block',
              width: '100%',
              padding: '8px',
              border: '1px solid #ccc',
              borderRadius: '4px'
            }}
          />
          {filesB.length > 0 && (
            <span style={{ fontSize: '13px', color: '#007bff', marginTop: '5px', display: 'block' }}>
              Đã chọn {filesB.length} file Bộ B
            </span>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            backgroundColor: loading ? '#6c757d' : '#28a745',
            color: '#ffffff',
            border: 'none',
            padding: '10px 20px',
            fontSize: '15px',
            fontWeight: 'bold',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Đang thực hiện ghép file...' : 'Ghép Hồ Sơ & Tải Kết Quả'}
        </button>
      </form>
    </div>
  );
};

export default MergeByExcelTab;