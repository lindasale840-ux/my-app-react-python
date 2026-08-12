import React, { useState } from 'react';
import { parseExcelColumnsApi, groupByExcelApi } from '../../services/groupPdfService';

export default function TabGroupPdfByExcel() {
  const [excelFile, setExcelFile] = useState(null);
  const [pdfFiles, setPdfFiles] = useState([]);
  const [columns, setColumns] = useState([]);
  
  const [matchColIdx, setMatchColIdx] = useState(0);
  const [targetColIdx, setTargetColIdx] = useState(1);
  
  const [loadingCols, setLoadingCols] = useState(false);
  const [loadingProcess, setLoadingProcess] = useState(false);
  const [summary, setSummary] = useState('');

  // Xử lý khi Upload file Excel -> Tự phân tích cột
  const handleExcelChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setExcelFile(file);
    setLoadingCols(true);
    setSummary('');

    try {
      const data = await parseExcelColumnsApi(file);
      setColumns(data.columns || []);
      if (data.columns && data.columns.length > 0) {
        setMatchColIdx(0);
        setTargetColIdx(data.columns.length > 1 ? 1 : 0);
      }
    } catch (err) {
      alert("Không thể đọc danh sách cột từ Excel: " + (err.response?.data?.detail || err.message));
      setColumns([]);
    } finally {
      setLoadingCols(false);
    }
  };

  const handlePdfChange = (e) => {
    if (e.target.files) {
      setPdfFiles(e.target.files);
      setSummary('');
    }
  };

  const handleProcess = async () => {
    if (!excelFile) {
      alert("Vui lòng chọn file Excel danh mục đối chiếu!");
      return;
    }
    if (!pdfFiles || pdfFiles.length === 0) {
      alert("Vui lòng chọn ít nhất 1 file PDF!");
      return;
    }

    setLoadingProcess(true);
    setSummary('');

    try {
      const res = await groupByExcelApi(excelFile, pdfFiles, matchColIdx, targetColIdx);

      // Tự động tải file ZIP kết quả về
      const url = window.URL.createObjectURL(new Blob([res.blob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "Ket_Qua_Gom_Nhom_PDF.zip");
      document.body.appendChild(link);
      link.click();
      link.remove();

      setSummary(res.summary || "✅ Gom nhóm & nén ZIP hoàn tất!");
    } catch (err) {
      alert("Lỗi khi gom nhóm PDF: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingProcess(false);
    }
  };

  return (
    <div style={{ maxWidth: '750px', margin: '0 auto', padding: '10px' }}>
      <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px', color: '#1e293b' }}>
        📂 Phân loại & Gom nhóm PDF theo danh mục Excel
      </h2>
      <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '20px' }}>
        Đối chiếu tên file PDF (Mã GCN) với Excel để tự động nhóm vào từng Folder riêng biệt trong file nén ZIP.
      </p>

      {/* 1. UPLOAD SECTION */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontWeight: '600', fontSize: '13px', color: '#334155' }}>
            1. File Excel danh mục đối chiếu (.xlsx, .xls)
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
          {loadingCols && <p style={{ fontSize: '12px', color: '#0284c7', marginTop: '4px' }}>⏳ Đang phân tích cột Excel...</p>}
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontWeight: '600', fontSize: '13px', color: '#334155' }}>
            2. Các file PDF cần gom nhóm (Chọn nhiều file)
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

      {/* 2. CONFIG CỘT ĐỐI CHIẾU */}
      {columns.length > 0 && (
        <div style={{ padding: '16px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 'bold', color: '#0f172a', marginBottom: '12px' }}>
            🛠 Cấu hình cột đối chiếu
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '12px', fontWeight: '500', color: '#475569' }}>
                Cột khớp với Tên file PDF (Mã GCN):
              </label>
              <select
                value={matchColIdx}
                onChange={(e) => setMatchColIdx(parseInt(e.target.value))}
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

            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '12px', fontWeight: '500', color: '#475569' }}>
                Cột dùng làm Tên Thư Mục gom nhóm:
              </label>
              <select
                value={targetColIdx}
                onChange={(e) => setTargetColIdx(parseInt(e.target.value))}
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
          </div>
        </div>
      )}

      {/* 3. BUTTON THỰC HIỆN */}
      <button
        onClick={handleProcess}
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
        {loadingProcess ? "⏳ Đang đối chiếu & Gom nhóm vào file ZIP..." : "🚀 Tiến hành Gom nhóm & Nén ZIP"}
      </button>

      {/* 4. KẾT QUẢ SUMMARY */}
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
            lineHeight: '1.6',
          }}
        >
          <div style={{ fontWeight: 'bold', marginBottom: '4px', fontSize: '14px' }}>
            🎉 Kết quả xử lý:
          </div>
          {summary}
          <div style={{ marginTop: '6px', fontSize: '12px', color: '#15803d' }}>
            * File nén ZIP chứa cấu trúc các thư mục đã tự động tải xuống.
          </div>
        </div>
      )}
    </div>
  );
}