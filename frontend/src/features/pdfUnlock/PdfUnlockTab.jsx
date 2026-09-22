import React, { useState } from 'react';
import { unlockPdfApi } from '../../services/pdfUnlockService';

export default function PdfUnlockTab() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.lowerCase?.() && !selectedFile.name.endsWith('.pdf')) {
        setErrorMsg('Vui lòng chọn file có định dạng PDF!');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setErrorMsg('');
      setSuccessMsg('');
    }
  };

  const handleUnlock = async () => {
    if (!file) {
      setErrorMsg('Vui lòng chọn 1 file PDF cần mở khóa!');
      return;
    }

    setLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const blobData = await unlockPdfApi(file);

      // Tự động kích hoạt tải xuống file đã mở khóa
      const downloadUrl = window.URL.createObjectURL(new Blob([blobData], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', `Unlocked_${file.name}`);
      document.body.appendChild(link);
      link.click();

      // Dọn dẹp DOM
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setSuccessMsg('🚀 Mở khóa PDF thành công! File đã được tự động tải về.');
    } catch (err) {
      // Đọc thông tin lỗi từ Blob nếu backend trả về JSON lỗi
      if (err.response && err.response.data instanceof Blob) {
        const errorText = await err.response.data.text();
        try {
          const parsed = JSON.parse(errorText);
          setErrorMsg(parsed.detail || 'Lỗi khi mở khóa PDF.');
        } catch {
          setErrorMsg('Lỗi máy chủ khi xử lý file!');
        }
      } else {
        setErrorMsg(err.message || 'Lỗi kết nối máy chủ!');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <p style={{ margin: '0 0 10px 0', color: '#555', fontSize: '14px' }}>
          Tải lên file PDF bị khóa quyền (Secured / Owner Password). Hệ thống sẽ loại bỏ giới hạn chỉnh sửa, in ấn, copy mà vẫn bảo toàn 100% chất lượng định dạng gốc.
        </p>
      </div>

      {errorMsg && (
        <div style={{ padding: '12px 15px', backgroundColor: '#f8d7da', color: '#721c24', borderRadius: '4px', marginBottom: '15px', border: '1px solid #f5c6cb' }}>
          ❌ {errorMsg}
        </div>
      )}

      {successMsg && (
        <div style={{ padding: '12px 15px', backgroundColor: '#d4edda', color: '#155724', borderRadius: '4px', marginBottom: '15px', border: '1px solid #c3e6cb' }}>
          {successMsg}
        </div>
      )}

      <div style={{ marginBottom: '20px', padding: '15px', border: '1px dashed #ccc', borderRadius: '6px', backgroundColor: '#fafafa' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '10px' }}>
          📁 Chọn file PDF bị khóa:
        </label>
        <input 
          type="file" 
          accept="application/pdf" 
          onChange={handleFileChange}
          style={{ padding: '6px 0' }}
        />
        {file && (
          <div style={{ marginTop: '10px', fontSize: '13px', color: '#007bff' }}>
            📄 File đã chọn: <b>{file.name}</b> ({(file.size / 1024 / 1024).toFixed(2)} MB)
          </div>
        )}
      </div>

      <button
        onClick={handleUnlock}
        disabled={loading || !file}
        style={{
          padding: '10px 24px',
          fontSize: '15px',
          fontWeight: 'bold',
          color: '#ffffff',
          backgroundColor: loading || !file ? '#6c757d' : '#28a745',
          border: 'none',
          borderRadius: '4px',
          cursor: loading || !file ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s'
        }}
      >
        {loading ? '⏳ Đang mở khóa PDF...' : '🔓 Tiến hành Mở khóa PDF'}
      </button>
    </div>
  );
}