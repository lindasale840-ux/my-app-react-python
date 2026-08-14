import React, { useState } from 'react';
import { pdfRenameService } from '../../services/pdfRenameService';

export default function RenamePdfByExcelTab() {
  const [fileExcel, setFileExcel] = useState(null);
  const [pdfFiles, setPdfFiles] = useState([]);

  const [columns, setColumns] = useState([]);
  const [matchCol, setMatchCol] = useState('');
  const [primaryCol, setPrimaryCol] = useState('');
  const [fallbackCol, setFallbackCol] = useState('');

  const [loadingCols, setLoadingCols] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Tải file Excel & Đọc danh sách cột
  const handleExcelChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFileExcel(file);
    setErrorMessage('');
    setLoadingCols(true);

    try {
      const res = await pdfRenameService.getColumns(file);
      const cols = res.columns || [];
      setColumns(cols);

      if (cols.length > 0) {
        setMatchCol(cols[0]);
        setPrimaryCol(cols[Math.min(1, cols.length - 1)]);
        setFallbackCol(cols[Math.min(2, cols.length - 1)]);
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Không thể đọc danh sách cột từ File Excel!');
    } finally {
      setLoadingCols(false);
    }
  };

  const handleRunProcess = async () => {
    if (!fileExcel) {
      setErrorMessage('Vui lòng chọn File Excel dữ liệu!');
      return;
    }
    if (!pdfFiles || pdfFiles.length === 0) {
      setErrorMessage('Vui lòng chọn các tệp PDF cần đổi tên!');
      return;
    }
    if (!matchCol || !primaryCol || !fallbackCol) {
      setErrorMessage('Vui lòng chọn đầy đủ các cột tra cứu và tên mới!');
      return;
    }

    setErrorMessage('');
    setSuccessMessage('');
    setProcessing(true);

    try {
      const blob = await pdfRenameService.processRename(
        fileExcel,
        pdfFiles,
        matchCol,
        primaryCol,
        fallbackCol
      );

      // Tự động kích hoạt tải xuống file ZIP
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Danh_Sach_PDF_Da_Doi_Ten_${new Date().getTime()}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setSuccessMessage(`Đổi tên thành công! Đã xử lý ${pdfFiles.length} file PDF và tải xuống file ZIP.`);
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Đã xảy ra lỗi trong quá trình đổi tên file PDF!');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div style={{ padding: '10px 0' }}>
      <h3 style={{ marginTop: 0, marginBottom: '10px', color: '#333' }}>
        🏷️ Đổi Tên File PDF Theo Dữ Liệu Excel
      </h3>
      <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
        Hệ thống sẽ đối chiếu tên file PDF cũ với cột tra cứu trong Excel. Nếu trùng khớp, tên file mới sẽ được ghép theo <b>[Tên Ưu Tiên 1] _ [Tên File Cũ]</b> (nếu cột 1 rỗng sẽ tự lấy <b>Tên Dự Phòng</b>).
      </p>

      {/* THÔNG BÁO LỖI / THÀNH CÔNG */}
      {errorMessage && (
        <div style={{ backgroundColor: '#f8d7da', color: '#721c24', padding: '12px 15px', borderRadius: '4px', border: '1px solid #f5c6cb', marginBottom: '15px' }}>
          ⚠️ {errorMessage}
        </div>
      )}
      {successMessage && (
        <div style={{ backgroundColor: '#d4edda', color: '#155724', padding: '12px 15px', borderRadius: '4px', border: '1px solid #c3e6cb', marginBottom: '15px' }}>
          ✅ {successMessage}
        </div>
      )}

      {/* KHU VỰC UPLOAD FILE */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
        <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '6px', backgroundColor: '#fafafa' }}>
          <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
            1. Chọn File Excel Chứa Dữ Liệu (*):
          </label>
          <input
            type="file"
            accept=".xlsx, .xls"
            onChange={handleExcelChange}
            style={{ width: '100%' }}
          />
          {loadingCols && <small style={{ color: '#007bff', display: 'block', marginTop: '5px' }}>Đang nạp danh sách cột...</small>}
        </div>

        <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '6px', backgroundColor: '#fafafa' }}>
          <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
            2. Chọn Các File PDF Cần Đổi Tên (*):
          </label>
          <input
            type="file"
            accept=".pdf"
            multiple
            onChange={(e) => setPdfFiles(e.target.files)}
            style={{ width: '100%' }}
          />
          <small style={{ display: 'block', marginTop: '8px', color: '#666' }}>
            Đã chọn: <b>{pdfFiles.length}</b> tệp PDF
          </small>
        </div>
      </div>

      {/* KHU VỰC CẤU HÌNH CỘT MAPPING */}
      {columns.length > 0 && (
        <div style={{ border: '1px solid #e0e0e0', padding: '18px', borderRadius: '6px', backgroundColor: '#ffffff', marginBottom: '20px' }}>
          <h4 style={{ marginTop: 0, marginBottom: '15px', color: '#007bff' }}>⚙️ Đặt Quy Tắc Khớp Và Đổi Tên</h4>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
            <div>
              <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '6px' }}>
                🔑 Cột Khớp Với Tên File PDF Cũ:
              </label>
              <select
                value={matchCol}
                onChange={(e) => setMatchCol(e.target.value)}
                style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
              >
                {columns.map((c, idx) => (
                  <option key={idx} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '6px' }}>
                🥇 Cột Lấy Tên Ưu Tiên 1:
              </label>
              <select
                value={primaryCol}
                onChange={(e) => setPrimaryCol(e.target.value)}
                style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
              >
                {columns.map((c, idx) => (
                  <option key={idx} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontWeight: 'bold', fontSize: '13px', display: 'block', marginBottom: '6px' }}>
                🥈 Cột Lấy Tên Dự Phòng (Cột 2):
              </label>
              <select
                value={fallbackCol}
                onChange={(e) => setFallbackCol(e.target.value)}
                style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
              >
                {columns.map((c, idx) => (
                  <option key={idx} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* NÚT THỰC THI */}
      <button
        type="button"
        onClick={handleRunProcess}
        disabled={processing}
        style={{
          backgroundColor: processing ? '#6c757d' : '#28a745',
          color: '#ffffff',
          border: 'none',
          padding: '12px 24px',
          fontSize: '16px',
          fontWeight: 'bold',
          borderRadius: '4px',
          cursor: processing ? 'not-allowed' : 'pointer',
          width: '100%'
        }}
      >
        {processing ? '⏳ Đang đối chiếu & Đổi tên file PDF...' : '🚀 Bắt Đầu Đổi Tên PDF & Tải File ZIP'}
      </button>
    </div>
  );
}