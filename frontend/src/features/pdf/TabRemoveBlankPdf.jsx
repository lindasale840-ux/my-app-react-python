import React, { useState } from 'react';
import { removeBlankPagesApi } from '../../services/removeBlankPdfService';

export default function TabRemoveBlankPdf() {
  const [files, setFiles] = useState([]);
  const [threshold, setThreshold] = useState(0.98);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(e.target.files);
      setSummary('');
    }
  };

  const handleProcess = async () => {
    if (!files || files.length === 0) {
      alert("Vui lòng chọn ít nhất 1 file PDF!");
      return;
    }

    setLoading(true);
    setSummary('');

    try {
      const res = await removeBlankPagesApi(files, threshold);

      // Tự động tải file về (PDF hoặc ZIP)
      const downloadName = res.isZip
        ? "cleaned_pdfs.zip"
        : `cleaned_${files[0].name}`;

      const url = window.URL.createObjectURL(new Blob([res.blob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", downloadName);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setSummary(res.summary || "✅ Đã xử lý xong!");
    } catch (err) {
      alert("Lỗi khi lọc trang trắng: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '650px', margin: '0 auto', padding: '10px' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px', color: '#1e293b' }}>
        🧹 Xóa Trang Trắng Hàng Loạt (Lọc thông minh qua RAM)
      </h2>

      {/* Upload File */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#334155' }}>
          Chọn một hoặc nhiều file PDF:
        </label>
        <input
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileChange}
          style={{
            display: 'block',
            width: '100%',
            padding: '8px',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '14px',
          }}
        />
        {files.length > 0 && (
          <p style={{ marginTop: '6px', fontSize: '13px', color: '#0284c7', fontWeight: '500' }}>
            📁 Đã chọn {files.length} file PDF
          </p>
        )}
      </div>

      {/* Độ nhạy Threshold */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#334155' }}>
          Độ nhạy nhận diện trang trắng (Threshold): <strong>{threshold}</strong>
        </label>
        <input
          type="range"
          min="0.90"
          max="0.99"
          step="0.01"
          value={threshold}
          onChange={(e) => setThreshold(parseFloat(e.target.value))}
          style={{ width: '100%', cursor: 'pointer' }}
        />
        <span style={{ fontSize: '12px', color: '#64748b' }}>
          * Mặc định 0.98 (Khuyên dùng). Ngưỡng càng cao yêu cầu trang càng phải trắng hoàn toàn.
        </span>
      </div>

      {/* Nút Thực Hiện */}
      <button
        onClick={handleProcess}
        disabled={loading || files.length === 0}
        style={{
          width: '100%',
          padding: '12px',
          backgroundColor: loading || files.length === 0 ? '#94a3b8' : '#0284c7',
          color: '#ffffff',
          border: 'none',
          borderRadius: '6px',
          fontWeight: 'bold',
          fontSize: '15px',
          cursor: loading || files.length === 0 ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s',
        }}
      >
        {loading ? "Đang quét và xóa trang trắng..." : "Thực Hiện Xóa Trang Trắng"}
      </button>

      {/* Khối Báo Báo Báo Kết Quả */}
      {summary && (
        <div
          style={{
            marginTop: '20px',
            padding: '14px',
            borderRadius: '6px',
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0',
            color: '#166534',
            fontSize: '13px',
            whiteSpace: 'pre-line',
            lineHeight: '1.6',
          }}
        >
          <div style={{ fontWeight: 'bold', marginBottom: '6px', fontSize: '14px' }}>
            🎉 Báo cáo kết quả xử lý:
          </div>
          {summary}
        </div>
      )}
    </div>
  );
}