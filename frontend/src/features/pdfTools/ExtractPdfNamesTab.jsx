import React, { useState } from 'react';
import { pdfToolsService } from '../../services/pdfToolsService';

export const ExtractPdfNamesTab = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
    setError('');
    setSuccess('');
  };

  const handleExtract = async () => {
    if (files.length === 0) {
      setError('Vui lòng chọn ít nhất một file PDF.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const blobData = await pdfToolsService.extractPdfNames(files);
      
      // Tạo link download
      const url = window.URL.createObjectURL(new Blob([blobData]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Danh_Sach_File_PDF.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();

      setSuccess(`Trích xuất thành công ${files.length} file PDF ra Excel!`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Có lỗi xảy ra khi trích xuất tên file PDF.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '15px', color: '#555', fontSize: '14px' }}>
        Tải lên danh sách các file PDF. Hệ thống sẽ trích xuất tên file, STT và dung lượng vào một file Excel.
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
          Chọn các file PDF:
        </label>
        <input
          type="file"
          multiple
          accept=".pdf"
          onChange={handleFileChange}
          style={{
            display: 'block',
            width: '100%',
            padding: '8px',
            border: '1px solid #ccc',
            borderRadius: '4px'
          }}
        />
        {files.length > 0 && (
          <div style={{ marginTop: '8px', fontSize: '13px', color: '#28a745', fontWeight: 'bold' }}>
            Đã chọn: {files.length} file PDF
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
        onClick={handleExtract}
        disabled={loading || files.length === 0}
        style={{
          backgroundColor: loading ? '#cccccc' : '#28a745',
          color: '#ffffff',
          border: 'none',
          padding: '10px 20px',
          fontSize: '15px',
          fontWeight: 'bold',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? 'Đang trích xuất Excel...' : 'Trích Xuất Ra File Excel'}
      </button>
    </div>
  );
};