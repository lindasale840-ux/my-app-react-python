import React, { useState } from 'react';
import { parseExcelColumnsApi, compareExcelVsPdfApi } from '../../services/comparePdfService';

export default function TabCompareExcelVsPdf() {
  const [excelFile, setExcelFile] = useState(null);
  const [pdfFiles, setPdfFiles] = useState([]);
  const [columns, setColumns] = useState([]);
  const [columnIndex, setColumnIndex] = useState(0);
  
  const [compareMode, setCompareMode] = useState('filename'); // 'filename' hoặc 'content'
  const [isScan, setIsScan] = useState(false);

  const [loadingCols, setLoadingCols] = useState(false);
  const [loadingProcess, setLoadingProcess] = useState(false);
  const [result, setResult] = useState(null);

  const handleExcelChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setExcelFile(file);
    setLoadingCols(true);
    setResult(null);

    try {
      const data = await parseExcelColumnsApi(file);
      setColumns(data.columns || []);
      setColumnIndex(0);
    } catch (err) {
      alert("Không thể đọc cấu trúc cột Excel: " + (err.response?.data?.detail || err.message));
      setColumns([]);
    } finally {
      setLoadingCols(false);
    }
  };

  const handlePdfChange = (e) => {
    if (e.target.files) {
      setPdfFiles(e.target.files);
      setResult(null);
    }
  };

  const handleCompare = async () => {
    if (!excelFile) {
      alert("Vui lòng chọn file Excel danh sách đối chiếu!");
      return;
    }
    if (!pdfFiles || pdfFiles.length === 0) {
      alert("Vui lòng chọn ít nhất 1 file PDF!");
      return;
    }

    setLoadingProcess(true);
    setResult(null);

    try {
      const res = await compareExcelVsPdfApi({
        excelFile,
        pdfFiles,
        columnIndex,
        compareMode,
        isScan,
      });
      setResult(res);
    } catch (err) {
      alert("Lỗi khi thực hiện đối chiếu: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingProcess(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '10px' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px', color: '#1e293b' }}>
        🔍 Đối chiếu danh sách Excel với File PDF Upload
      </h2>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '20px' }}>
        Kiểm tra danh sách Mã/Dữ liệu trong Excel có đầy đủ trong các File PDF (theo tên file hoặc nội dung bên trong).
      </p>

      {/* 1. UPLOAD INPUTS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontWeight: '600', fontSize: '13px', color: '#334155' }}>
            1. File Excel danh sách (.xlsx, .xls)
          </label>
          <input
            type="file"
            accept=".xlsx, .xls"
            onChange={handleExcelChange}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '13px',
            }}
          />
          {loadingCols && <p style={{ fontSize: '12px', color: '#0284c7', marginTop: '4px' }}>⏳ Đang đọc thông tin cột...</p>}
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontWeight: '600', fontSize: '13px', color: '#334155' }}>
            2. Danh sách file PDF Upload (Chọn nhiều file)
          </label>
          <input
            type="file"
            accept=".pdf"
            multiple
            onChange={handlePdfChange}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #cbd5e1',
              borderRadius: '6px',
              fontSize: '13px',
            }}
          />
          {pdfFiles.length > 0 && (
            <p style={{ fontSize: '12px', color: '#0284c7', marginTop: '4px', fontWeight: '500' }}>
              📁 Đã chọn {pdfFiles.length} file PDF
            </p>
          )}
        </div>
      </div>

      {/* 2. CẤU HÌNH ĐỐI CHIẾU */}
      <div style={{ padding: '16px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', marginBottom: '20px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 'bold', color: '#0f172a', marginBottom: '12px' }}>
          ⚙️ Cấu hình phương thức đối chiếu
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '12px' }}>
          {columns.length > 0 && (
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '12px', fontWeight: '500', color: '#475569' }}>
                Chọn Cột Excel chứa Mã/Dữ liệu cần kiểm tra:
              </label>
              <select
                value={columnIndex}
                onChange={(e) => setColumnIndex(parseInt(e.target.value))}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #cbd5e1',
                  fontSize: '13px',
                  backgroundColor: '#fff',
                }}
              >
                {columns.map((colLabel, idx) => (
                  <option key={idx} value={idx}>{colLabel}</option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '12px', fontWeight: '500', color: '#475569' }}>
              Chế độ đối chiếu:
            </label>
            <select
              value={compareMode}
              onChange={(e) => setCompareMode(e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                fontSize: '13px',
                backgroundColor: '#fff',
              }}
            >
              <option value="filename">⚡ Đối chiếu với TÊN FILE PDF (Siêu nhanh)</option>
              <option value="content">🔍 Đối chiếu với NỘI DUNG bên trong PDF</option>
            </select>
          </div>
        </div>

        {compareMode === 'content' && (
          <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px dashed #cbd5e1' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer', color: '#1e293b' }}>
              <input
                type="checkbox"
                checked={isScan}
                onChange={(e) => setIsScan(e.target.checked)}
              />
              <b>Bật chế độ OCR Scan</b> (Dành cho PDF dạng ảnh chụp/Scan - Tốc độ sẽ chậm hơn)
            </label>
          </div>
        )}
      </div>

      {/* 3. BUTTON BẮT ĐẦU */}
      <button
        onClick={handleCompare}
        disabled={loadingProcess || !excelFile || pdfFiles.length === 0}
        style={{
          width: '100%',
          padding: '12px',
          backgroundColor: loadingProcess || !excelFile || pdfFiles.length === 0 ? '#94a3b8' : '#0284c7',
          color: '#ffffff',
          border: 'none',
          borderRadius: '6px',
          fontWeight: 'bold',
          fontSize: '15px',
          cursor: loadingProcess || !excelFile || pdfFiles.length === 0 ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s',
        }}
      >
        {loadingProcess ? "⏳ Đang thực hiện đối chiếu..." : "🚀 Bắt Đầu Đối Chiếu"}
      </button>

      {/* 4. KẾT QUẢ ĐỐI CHIẾU */}
      {result && (
        <div style={{ marginTop: '24px' }}>
          {/* CARDS TỔNG QUAN */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div style={{ padding: '12px', backgroundColor: '#f1f5f9', borderRadius: '6px', textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: '#64748b' }}>Tổng mã trong Excel</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#0f172a' }}>{result.total_excel}</div>
            </div>
            <div style={{ padding: '12px', backgroundColor: '#f0fdf4', borderRadius: '6px', textAlign: 'center', border: '1px solid #bbf7d0' }}>
              <div style={{ fontSize: '12px', color: '#166534' }}>Khớp thành công</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#15803d' }}>{result.matched}</div>
            </div>
            <div style={{ padding: '12px', backgroundColor: result.missing.length > 0 ? '#fef2f2' : '#f8fafc', borderRadius: '6px', textAlign: 'center', border: result.missing.length > 0 ? '1px solid #fecaca' : '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '12px', color: result.missing.length > 0 ? '#991b1b' : '#64748b' }}>Còn thiếu</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: result.missing.length > 0 ? '#dc2626' : '#0f172a' }}>{result.missing.length}</div>
            </div>
          </div>

          {/* DANH SÁCH MÃ THIẾU */}
          {result.missing.length > 0 ? (
            <div style={{ padding: '16px', backgroundColor: '#fff', border: '1px solid #fca5a5', borderRadius: '8px' }}>
              <h4 style={{ fontSize: '14px', fontWeight: 'bold', color: '#991b1b', marginBottom: '8px' }}>
                ⚠️ Danh sách {result.missing.length} mã có trong Excel nhưng KHÔNG TÌM THẤY trong PDF:
              </h4>
              <div style={{ maxHeight: '200px', overflowY: 'auto', backgroundColor: '#fff5f5', padding: '10px', borderRadius: '4px', border: '1px solid #fee2e2' }}>
                <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#7f1d1d' }}>
                  {result.missing.map((item, idx) => (
                    <li key={idx} style={{ marginBottom: '4px' }}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div style={{ padding: '14px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', color: '#166534', fontSize: '14px', fontWeight: '500' }}>
              🎉 Tuyệt vời! Tất cả các mã trong Excel đều đã được tìm thấy trong danh sách PDF!
            </div>
          )}
        </div>
      )}
    </div>
  );
}