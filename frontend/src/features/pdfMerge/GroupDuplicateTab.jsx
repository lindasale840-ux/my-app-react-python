import React, { useState } from 'react';
import { groupDuplicateFilesService } from '../../services/groupDuplicateService';

const GroupDuplicateTab = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [stats, setStats] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFiles(e.target.files);
      setErrorMessage('');
      setSuccessMessage('');
      setStats(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!files || files.length === 0) {
      setErrorMessage('Vui lòng chọn ít nhất một file để thực hiện gom hồ sơ.');
      return;
    }

    setLoading(true);
    setErrorMessage('');
    setSuccessMessage('');
    setStats(null);

    try {
      const response = await groupDuplicateFilesService(files);

      // Đọc thông số thống kê từ response headers
      const totalGroups = response.headers['x-total-groups'] || '0';
      const totalFiles = response.headers['x-total-files'] || '0';
      const largestGroup = response.headers['x-largest-group'] || '';
      const largestCount = response.headers['x-largest-count'] || '0';

      setStats({
        totalGroups,
        totalFiles,
        largestGroup,
        largestCount,
      });

      // Tạo link tự động tải file ZIP về máy
      const blob = new Blob([response.data], { type: 'application/zip' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', 'HoSo_Gom.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setSuccessMessage(`✅ Gom hồ sơ thành công! Đã tạo ${totalGroups} nhóm thư mục từ ${totalFiles} file.`);
    } catch (err) {
      if (err.response && err.response.data instanceof Blob) {
        try {
          const text = await err.response.data.text();
          const json = JSON.parse(text);
          setErrorMessage(json.detail || 'Có lỗi xảy ra khi xử lý gom hồ sơ!');
        } catch {
          setErrorMessage('Có lỗi xảy ra khi xử lý gom hồ sơ!');
        }
      } else {
        setErrorMessage(err.response?.data?.detail || err.message || 'Có lỗi xảy ra!');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3 style={{ marginTop: 0, marginBottom: '15px', color: '#333' }}>
        📂 Gom Hồ Sơ Trùng Tên Vào Thư Mục
      </h3>
      <p style={{ marginBottom: '20px', color: '#666', fontSize: '14px', lineHeight: '1.5' }}>
        Hệ thống sẽ tự động phân tích tên file (ví dụ: <code>ABC_1.pdf</code>, <code>ABC_2.pdf</code>, <code>ABC(1).pdf</code> thành nhóm <code>ABC</code>)
        và gom các file trùng tên gốc vào từng thư mục riêng biệt trong file ZIP kết quả.
      </p>

      {errorMessage && (
        <div style={{
          backgroundColor: '#f8d7da',
          color: '#721c24',
          padding: '12px 15px',
          borderRadius: '4px',
          marginBottom: '20px',
          border: '1px solid #f5c6cb'
        }}>
          {errorMessage}
        </div>
      )}

      {successMessage && (
        <div style={{
          backgroundColor: '#d4edda',
          color: '#155724',
          padding: '12px 15px',
          borderRadius: '4px',
          marginBottom: '20px',
          border: '1px solid #c3e6cb'
        }}>
          {successMessage}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>
            Chọn danh sách File cần gom:
          </label>
          <input
            type="file"
            multiple
            onChange={handleFileChange}
            style={{
              display: 'block',
              width: '100%',
              padding: '8px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              backgroundColor: '#fafafa'
            }}
          />
          {files.length > 0 && (
            <span style={{ fontSize: '13px', color: '#007bff', marginTop: '6px', display: 'block' }}>
              Đã chọn tổng cộng: <strong>{files.length}</strong> file
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
            padding: '10px 22px',
            fontSize: '15px',
            fontWeight: 'bold',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Đang phân nhóm & tạo ZIP...' : '🚀 Gom Hồ Sơ & Tải Về'}
        </button>
      </form>

      {stats && (
        <div style={{
          marginTop: '25px',
          padding: '15px',
          backgroundColor: '#f8f9fa',
          border: '1px solid #e9ecef',
          borderRadius: '6px'
        }}>
          <h4 style={{ marginTop: 0, marginBottom: '12px', color: '#333' }}>📊 Kết Quả Gom Hồ Sơ</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '14px' }}>
            <div>• Tổng số file xử lý: <strong>{stats.totalFiles}</strong></div>
            <div>• Tổng số nhóm đã tạo: <strong>{stats.totalGroups}</strong></div>
            <div>• Nhóm chứa nhiều file nhất: <strong>{stats.largestGroup || 'N/A'}</strong></div>
            <div>• Số file trong nhóm lớn nhất: <strong>{stats.largestCount}</strong></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GroupDuplicateTab;