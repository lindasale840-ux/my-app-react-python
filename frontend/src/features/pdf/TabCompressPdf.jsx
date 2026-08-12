import React, { useState } from 'react';
import { compressPdfApi } from '../../services/pdfCompressApi';

export default function TabCompressPdf() {
  const [file, setFile] = useState(null);
  const [mode, setMode] = useState('normal');
  const [loading, setLoading] = useState(false);
  const [resultInfo, setResultInfo] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResultInfo(null);
    }
  };

  const handleCompress = async () => {
    if (!file) {
      alert("Vui lòng chọn 1 file PDF!");
      return;
    }

    setLoading(true);
    setResultInfo(null);

    try {
      const res = await compressPdfApi(file, mode);

      // Tự động tải file nén về
      const url = window.URL.createObjectURL(new Blob([res.blob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `compressed_${file.name}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setResultInfo({
        message: `✅ Nén thành công: ${res.oldSize || 0} MB → ${res.newSize || 0} MB`,
        oldSize: res.oldSize,
        newSize: res.newSize
      });
    } catch (err) {
      alert("Lỗi khi nén file PDF: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '600px' }}>
      <h3 style={{ marginBottom: '15px', color: '#0f172a' }}>🗜️ Nén File PDF</h3>

      {/* CHỌN FILE */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
          Chọn file PDF cần nén:
        </label>
        <input 
          type="file" 
          accept="application/pdf" 
          onChange={handleFileChange} 
          style={{ padding: '8px', border: '1px solid #cbd5e1', borderRadius: '4px', width: '100%' }}
        />
      </div>

      {/* CHỌN MỨC ĐỘ NÉN */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
          Chế độ nén:
        </label>
        <div style={{ display: 'flex', gap: '20px' }}>
          <label style={{ cursor: 'pointer' }}>
            <input 
              type="radio" 
              name="compress_mode" 
              value="normal" 
              checked={mode === 'normal'} 
              onChange={(e) => setMode(e.target.value)} 
            /> {' '}
            <b>Nén Tiêu Chuẩn</b> (Nhanh, giữ nguyên chất lượng ảnh/font)
          </label>
          
          <label style={{ cursor: 'pointer' }}>
            <input 
              type="radio" 
              name="compress_mode" 
              value="strong" 
              checked={mode === 'strong'} 
              onChange={(e) => setMode(e.target.value)} 
            /> {' '}
            <b>Nén Thượng Hạng</b> (Nén cả Ảnh & Font chữ, file nhỏ hơn nữa)
          </label>
        </div>
      </div>

      {/* NÚT THỰC HIỆN */}
      <button
        onClick={handleCompress}
        disabled={loading || !file}
        style={{
          padding: '10px 24px',
          fontSize: '15px',
          fontWeight: 'bold',
          color: '#fff',
          backgroundColor: loading || !file ? '#94a3b8' : '#0284c7',
          border: 'none',
          borderRadius: '6px',
          cursor: loading || !file ? 'not-allowed' : 'pointer',
          marginBottom: '20px'
        }}
      >
        {loading ? "⏳ Đang nén file..." : "⚡ Tiến Hành Nén PDF"}
      </button>

      {/* KẾT QUẢ */}
      {resultInfo && (
        <div style={{ background: '#f0fdf4', border: '1px solid #86efac', padding: '15px', borderRadius: '6px' }}>
          <p style={{ margin: 0, color: '#166534', fontWeight: 'bold' }}>
            {resultInfo.message}
          </p>
        </div>
      )}
    </div>
  );
}