import React, { useState } from 'react';
import { mergeByNameService } from '../../services/pdfMergeService';

const MergeByNameTab = () => {
  const [filesA, setFilesA] = useState([]);
  const [filesB, setFilesB] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleFileAChange = (e) => {
    setFilesA(e.target.files);
  };

  const handleFileBChange = (e) => {
    setFilesB(e.target.files);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
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
      const response = await mergeByNameService(filesA, filesB);

      // Lấy thông tin count từ Header
      const mergedCount = response.headers['x-merged-count'] || 0;
      const skippedCount = response.headers['x-skipped-count'] || 0;

      // Xử lý download file ZIP
      const blob = new Blob([response.data], { type: 'application/zip' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', 'Merged_By_Name.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setMessage(`✅ Ghép thành công ${mergedCount} file | Bỏ qua ${skippedCount} file không trùng tên.`);
    } catch (err) {
      if (err.response && err.response.data instanceof Blob) {
        // Đọc thông báo lỗi từ Blob response
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
        📎 Ghép Hồ Sơ Theo Tên File (Trùng tên PDF)
      </h3>
      <p style={{ marginBottom: '20px', color: '#666', fontSize: '14px' }}>
        Tải lên danh sách File PDF của Bộ A và Bộ B. Các file có cùng tên sẽ được ghép liên tiếp vào nhau (Bộ A trước, Bộ B sau).
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
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
            1. Danh sách File Bộ A (PDF):
          </label>
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={handleFileAChange}
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

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
            2. Danh sách File Bộ B (PDF):
          </label>
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={handleFileBChange}
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
          {loading ? 'Đang ghép file PDF...' : 'Thực hiện ghép & Tải file ZIP'}
        </button>
      </form>
    </div>
  );
};

export default MergeByNameTab;