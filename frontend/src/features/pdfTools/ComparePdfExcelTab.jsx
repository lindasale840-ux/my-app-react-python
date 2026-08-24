import React, { useState } from 'react';
import { pdfToolsService } from '../../services/pdfToolsService';

export const ComparePdfExcelTab = () => {
  const [excelFile, setExcelFile] = useState(null);
  const [columns, setColumns] = useState([]);
  const [selectedColumn, setSelectedColumn] = useState('');
  const [pdfFiles, setPdfFiles] = useState([]);
  
  const [loadingColumns, setLoadingColumns] = useState(false);
  const [loadingCompare, setLoadingCompare] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Tải file Excel và đọc danh sách cột
  const handleExcelChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setExcelFile(file);
    setColumns([]);
    setSelectedColumn('');
    setError('');
    setSuccess('');
    setLoadingColumns(true);

    try {
      const res = await pdfToolsService.getExcelColumns(file);
      setColumns(res.columns || []);
      if (res.columns && res.columns.length > 0) {
        setSelectedColumn(res.columns[0]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể đọc file Excel.');
    } finally {
      setLoadingColumns(false);
    }
  };

  const handlePdfChange = (e) => {
    const files = Array.from(e.target.files);
    setPdfFiles(files);
    setError('');
    setSuccess('');
  };

  const handleCompare = async () => {
    if (!excelFile) {
      setError('Vui lòng chọn file Excel Tổng.');
      return;
    }
    if (!selectedColumn) {
      setError('Vui lòng chọn cột đối chiếu.');
      return;
    }
    if (pdfFiles.length === 0) {
      setError('Vui lòng chọn danh sách file PDF.');
      return;
    }

    setLoadingCompare(true);
    setError('');
    setSuccess('');

    try {
      const blobData = await pdfToolsService.comparePdfWithExcel(excelFile, selectedColumn, pdfFiles);

      const url = window.URL.createObjectURL(new Blob([blobData]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Bao_Cao_Doi_Chieu_PDF.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();

      setSuccess('Đã hoàn tất đối chiếu và xuất file Báo Cáo Excel thành công!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Có lỗi xảy ra khi đối chiếu dữ liệu.');
    } finally {
      setLoadingCompare(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '15px', color: '#555', fontSize: '14px' }}>
        So sánh danh sách mã trong 1 cột Excel Tổng với danh sách các file PDF thực tế được upload để lọc ra danh sách thiếu file PDF.
      </div>

      {/* Bước 1: Chọn Excel */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
          1. Chọn File Excel Tổng:
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
        {loadingColumns && (
          <div style={{ marginTop: '5px', fontSize: '13px', color: '#007bff' }}>
            Đang đọc danh sách cột...
          </div>
        )}
      </div>

      {/* Chọn cột đối chiếu */}
      {columns.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
            2. Chọn Cột Chứa Mã/Tên File Cần Đối Chiếu:
          </label>
          <select
            value={selectedColumn}
            onChange={(e) => setSelectedColumn(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              backgroundColor: '#fff'
            }}
          >
            {columns.map((col, idx) => (
              <option key={idx} value={col}>
                {col}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Bước 2: Chọn danh sách PDF */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
          3. Chọn Các File PDF Thực Tế Tải Lên:
        </label>
        <input
          type="file"
          multiple
          accept=".pdf"
          onChange={handlePdfChange}
          style={{
            display: 'block',
            width: '100%',
            padding: '8px',
            border: '1px solid #ccc',
            borderRadius: '4px'
          }}
        />
        {pdfFiles.length > 0 && (
          <div style={{ marginTop: '8px', fontSize: '13px', color: '#28a745', fontWeight: 'bold' }}>
            Đã chọn: {pdfFiles.length} file PDF
          </div>
        )}
      </div>

      {error && (
        <div style={{
          backgroundColor: '#f8d7da',
          color: '#721c24',
          padding: '10px 15px',
          borderRadius: '4px',
          marginBottom: '20px',
          border: '1px solid #f5c6cb'
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{
          backgroundColor: '#d4edda',
          color: '#155724',
          padding: '10px 15px',
          borderRadius: '4px',
          marginBottom: '20px',
          border: '1px solid #c3e6cb'
        }}>
          {success}
        </div>
      )}

      <button
        onClick={handleCompare}
        disabled={loadingCompare || !excelFile || pdfFiles.length === 0}
        style={{
          backgroundColor: (loadingCompare || !excelFile || pdfFiles.length === 0) ? '#cccccc' : '#007bff',
          color: '#ffffff',
          border: 'none',
          padding: '10px 20px',
          fontSize: '15px',
          fontWeight: 'bold',
          borderRadius: '4px',
          cursor: (loadingCompare || !excelFile || pdfFiles.length === 0) ? 'not-allowed' : 'pointer'
        }}
      >
        {loadingCompare ? 'Đang đối chiếu dữ liệu...' : 'Thực Hiện Đối Chiếu & Xuất Báo Cáo'}
      </button>
    </div>
  );
};