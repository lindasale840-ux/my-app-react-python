import React, { useState } from 'react';
import { pdfSplitService } from '../../services/pdfSplitService';

export default function PdfSplitTab() {
  const [mode, setMode] = useState('smart'); // 'smart' hoặc 'excel'
  const [pdfFile, setPdfFile] = useState(null);
  const [excelFile, setExcelFile] = useState(null);
  const [keyword, setKeyword] = useState('Giấy chứng nhận');
  const [namingType, setNamingType] = useState('ma_ql');
  const [includePageCount, setIncludePageCount] = useState(false); // <-- STATE MỚI
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const handleModeChange = (newMode) => {
    setMode(newMode);
    setMessage(null);
    if (newMode === 'excel') {
      setKeyword('Giấy chứng nhận, Certificate, Certificate of Calibration');
      setNamingType('ten_tb');
    } else {
      setKeyword('Giấy chứng nhận');
      setNamingType('ma_ql');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!pdfFile) {
      setMessage({ type: 'error', text: 'Vui lòng chọn file PDF!' });
      return;
    }
    if (mode === 'excel' && !excelFile) {
      setMessage({ type: 'error', text: 'Vui lòng chọn file Excel!' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      let blobData;
      if (mode === 'smart') {
        blobData = await pdfSplitService.splitSmart(pdfFile, keyword, namingType, includePageCount);
      } else {
        blobData = await pdfSplitService.splitExcel(pdfFile, excelFile, keyword, namingType, includePageCount);
      }

      const url = window.URL.createObjectURL(new Blob([blobData]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Tach_PDF_${namingType}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setMessage({ type: 'success', text: '🎉 Tách file PDF thành công! Đã tự động tải về file Zip.' });
    } catch (err) {
      let errText = 'Đã có lỗi xảy ra khi xử lý file!';
      if (err.response && err.response.data instanceof Blob) {
        const text = await err.response.data.text();
        try {
          const parsed = JSON.parse(text);
          errText = parsed.detail || errText;
        } catch {
          errText = text || errText;
        }
      }
      setMessage({ type: 'error', text: errText });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        <button
          type="button"
          onClick={() => handleModeChange('smart')}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            backgroundColor: mode === 'smart' ? '#007bff' : '#e0e0e0',
            color: mode === 'smart' ? '#fff' : '#333',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          🧠 Tách PDF Thông Minh (Tự động)
        </button>
        <button
          type="button"
          onClick={() => handleModeChange('excel')}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            backgroundColor: mode === 'excel' ? '#007bff' : '#e0e0e0',
            color: mode === 'excel' ? '#fff' : '#333',
            cursor: 'pointer',
            fontWeight: 'bold'
          }}
        >
          📊 Tách PDF & Đối Chiếu Excel
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
            File PDF cần tách (*):
          </label>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setPdfFile(e.target.files[0])}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
          />
        </div>

        {mode === 'excel' && (
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
              File Excel đối chiếu (*):
            </label>
            <input
              type="file"
              accept=".xlsx, .xls"
              onChange={(e) => setExcelFile(e.target.files[0])}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
            />
          </div>
        )}

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
            Từ khóa nhận diện điểm cắt (cách nhau bởi dấu phẩy):
          </label>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
            Quy tắc đặt tên file đầu ra:
          </label>
          <select
            value={namingType}
            onChange={(e) => setNamingType(e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
          >
            {mode === 'smart' ? (
              <>
                <option value="ma_ql">Mã Quản Lý (Mã QL)</option>
                <option value="so_gcn">Số Giấy Chứng Nhận (Số GCN)</option>
                <option value="ten_tb">Tên Thiết Bị & Kiểu Máy</option>
              </>
            ) : (
              <>
                <option value="ten_tb">Tên Thiết Bị & Kiểu Máy (Lấy từ Excel)</option>
                <option value="ma_ql">Mã Quản Lý (Lấy từ Excel)</option>
                <option value="so_gcn">Số Giấy Chứng Nhận (Số GCN)</option>
              </>
            )}
          </select>
        </div>

        {/* ============================================================================== */}
        {/* CHECKBOX BỔ SUNG SỐ TRANG VÀO TÊN FILE */}
        {/* ============================================================================== */}
        <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input
            type="checkbox"
            id="includePageCount"
            checked={includePageCount}
            onChange={(e) => setIncludePageCount(e.target.checked)}
            style={{ width: '18px', height: '18px', cursor: 'pointer' }}
          />
          <label htmlFor="includePageCount" style={{ cursor: 'pointer', userSelect: 'none', fontSize: '14px' }}>
            Thêm số trang vào cuối tên file (Ví dụ: <strong>TenFile_3Trang.pdf</strong>)
          </label>
        </div>

        {message && (
          <div
            style={{
              padding: '10px 15px',
              borderRadius: '4px',
              marginBottom: '15px',
              backgroundColor: message.type === 'error' ? '#f8d7da' : '#d4edda',
              color: message.type === 'error' ? '#721c24' : '#155724',
              border: `1px solid ${message.type === 'error' ? '#f5c6cb' : '#c3e6cb'}`
            }}
          >
            {message.text}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '10px 20px',
            borderRadius: '4px',
            border: 'none',
            backgroundColor: loading ? '#6c757d' : '#28a745',
            color: '#fff',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            fontSize: '16px'
          }}
        >
          {loading ? 'Đang xử lý...' : 'Thực Hiện Tách PDF'}
        </button>
      </form>
    </div>
  );
}