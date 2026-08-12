import React, { useState } from 'react';
import { downgradePdfVersionApi } from '../../services/pdfVersionService';

export default function TabVersionPdf() {
  const [file, setFile] = useState(null);
  const [compatibility, setCompatibility] = useState("1.4");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setMessage('');
    }
  };

  const handleDowngrade = async () => {
    if (!file) {
      alert("Vui lòng chọn 1 file PDF!");
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const blobData = await downgradePdfVersionApi(file, compatibility);

      // Tự động tải file về
      const url = window.URL.createObjectURL(new Blob([blobData]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `v${compatibility}_${file.name}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setMessage(`✅ Đã hạ PDF về phiên bản ${compatibility} thành công!`);
    } catch (err) {
      setMessage(`❌ Lỗi: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '10px' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px', color: '#1e293b' }}>
        Hạ Phiên Bản PDF (Compatibility)
      </h2>

      {/* Chọn File */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#334155' }}>
          Chọn file PDF:
        </label>
        <input
          type="file"
          accept=".pdf"
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
      </div>

      {/* Chọn phiên bản PDF */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#334155' }}>
          Chọn phiên bản PDF muốn hạ về:
        </label>
        <select
          value={compatibility}
          onChange={(e) => setCompatibility(e.target.value)}
          style={{
            width: '100%',
            padding: '10px',
            border: '1px solid #cbd5e1',
            borderRadius: '6px',
            fontSize: '14px',
            backgroundColor: '#fff',
            outline: 'none',
          }}
        >
          <option value="1.3">PDF 1.3 (Acrobat 4.0)</option>
          <option value="1.4">PDF 1.4 (Acrobat 5.0 - Khuyên dùng)</option>
          <option value="1.5">PDF 1.5 (Acrobat 6.0)</option>
          <option value="1.6">PDF 1.6 (Acrobat 7.0)</option>
          <option value="1.7">PDF 1.7 (Acrobat 8.0/ISO)</option>
        </select>
      </div>

      {/* Nút Thực hiện */}
      <button
        onClick={handleDowngrade}
        disabled={loading || !file}
        style={{
          width: '100%',
          padding: '12px',
          backgroundColor: loading || !file ? '#94a3b8' : '#0284c7',
          color: '#ffffff',
          border: 'none',
          borderRadius: '6px',
          fontWeight: 'bold',
          fontSize: '15px',
          cursor: loading || !file ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s',
        }}
      >
        {loading ? "Đang xử lý hạ phiên bản..." : "Thực Hiện Hạ Phiên Bản"}
      </button>

      {/* Thông báo kết quả */}
      {message && (
        <div
          style={{
            marginTop: '16px',
            padding: '12px',
            borderRadius: '6px',
            textAlign: 'center',
            fontSize: '14px',
            fontWeight: '500',
            backgroundColor: message.startsWith('✅') ? '#f0fdf4' : '#fef2f2',
            color: message.startsWith('✅') ? '#166534' : '#991b1b',
            border: message.startsWith('✅') ? '1px solid #bbf7d0' : '1px solid #fecaca',
          }}
        >
          {message}
        </div>
      )}
    </div>
  );
}