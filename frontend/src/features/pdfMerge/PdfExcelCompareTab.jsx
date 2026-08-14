// src/features/pdfMerge/PdfExcelCompareTab.jsx
import React, { useState } from 'react';
import { comparePdfExcel, exportReportExcel } from '../../services/pdfExcelService';

const COMPARE_OPTIONS = [
  { label: 'GCN (Cột Z - Index 25)', value: 'GCN' },
  { label: 'Số seri (Cột AA - Index 26)', value: 'Số seri' },
  { label: 'Mã quản lý (Cột AB - Index 27)', value: 'Mã quản lý' },
  { label: 'Tên thiết bị (Cột F - Index 5)', value: 'Tên thiết bị' },
  { label: 'Model (Cột G - Index 6)', value: 'Model' },
];

export default function PdfExcelCompareTab() {
  const [pdfFiles, setPdfFiles] = useState([]);
  const [excelFile, setExcelFile] = useState(null);
  const [compareType, setCompareType] = useState('GCN');

  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [resultData, setResultData] = useState(null);

  const handlePdfChange = (e) => {
    if (e.target.files) {
      setPdfFiles(Array.from(e.target.files));
      setErrorMessage('');
    }
  };

  const handleExcelChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setExcelFile(e.target.files[0]);
      setErrorMessage('');
    }
  };

  const handleCompare = async () => {
    if (pdfFiles.length === 0) {
      setErrorMessage('Vui lòng chọn ít nhất một file PDF.');
      return;
    }
    if (!excelFile) {
      setErrorMessage('Vui lòng chọn file Excel để đối chiếu.');
      return;
    }

    setLoading(true);
    setErrorMessage('');
    setSuccessMessage('');
    setResultData(null);

    try {
      const data = await comparePdfExcel(pdfFiles, excelFile, compareType);
      setResultData(data);
      setSuccessMessage('Đối chiếu thành công! Dưới đây là kết quả chi tiết.');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Có lỗi xảy ra trong quá trình đối chiếu.';
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (pdfFiles.length === 0 || !excelFile) {
      setErrorMessage('Vui lòng chọn đầy đủ file PDF và Excel trước khi xuất báo cáo.');
      return;
    }

    setExporting(true);
    setErrorMessage('');
    try {
      await exportReportExcel(pdfFiles, excelFile, compareType);
      setSuccessMessage('Đã tải xuống báo cáo Excel thành công.');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Có lỗi khi xuất báo cáo Excel.';
      setErrorMessage(msg);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      <h3 style={{ marginTop: 0, marginBottom: '20px', color: '#333' }}>
        📊 Đối chiếu danh sách PDF với dữ liệu Excel
      </h3>

      {errorMessage && (
        <div
          style={{
            backgroundColor: '#f8d7da',
            color: '#721c24',
            padding: '12px 20px',
            borderRadius: '4px',
            marginBottom: '20px',
            border: '1px solid #f5c6cb',
          }}
        >
          {errorMessage}
        </div>
      )}

      {successMessage && (
        <div
          style={{
            backgroundColor: '#d4edda',
            color: '#155724',
            padding: '12px 20px',
            borderRadius: '4px',
            marginBottom: '20px',
            border: '1px solid #c3e6cb',
          }}
        >
          {successMessage}
        </div>
      )}

      {/* Form cấu hình */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '20px',
          marginBottom: '20px',
        }}
      >
        {/* Chọn File PDF */}
        <div
          style={{
            border: '1px border #ccc',
            padding: '15px',
            borderRadius: '6px',
            backgroundColor: '#fafafa',
          }}
        >
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
            1. Chọn Danh sách File PDF ({pdfFiles.length} file)
          </label>
          <input
            type="file"
            multiple
            accept="application/pdf"
            onChange={handlePdfChange}
            style={{ display: 'block', width: '100%', marginBottom: '10px' }}
          />
          {pdfFiles.length > 0 && (
            <div style={{ maxHeight: '100px', overflowY: 'auto', fontSize: '13px', color: '#555' }}>
              {pdfFiles.map((f, idx) => (
                <div key={idx}>• {f.name}</div>
              ))}
            </div>
          )}
        </div>

        {/* Chọn File Excel & Cột đối chiếu */}
        <div
          style={{
            border: '1px border #ccc',
            padding: '15px',
            borderRadius: '6px',
            backgroundColor: '#fafafa',
          }}
        >
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
              2. Chọn File Excel
            </label>
            <input
              type="file"
              accept=".xlsx, .xls"
              onChange={handleExcelChange}
              style={{ display: 'block', width: '100%' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
              3. Loại Cột Excel Đối Chiếu
            </label>
            <select
              value={compareType}
              onChange={(e) => setCompareType(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '4px',
                border: '1px solid #ccc',
              }}
            >
              {COMPARE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Hành động */}
      <div style={{ marginBottom: '25px', display: 'flex', gap: '15px' }}>
        <button
          onClick={handleCompare}
          disabled={loading}
          style={{
            backgroundColor: '#007bff',
            color: '#fff',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? 'Đang đối chiếu...' : '🔍 Thực hiện Đối Chiếu'}
        </button>

        <button
          onClick={handleExport}
          disabled={exporting}
          style={{
            backgroundColor: '#28a745',
            color: '#fff',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '4px',
            cursor: exporting ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            opacity: exporting ? 0.7 : 1,
          }}
        >
          {exporting ? 'Đang tạo Excel...' : '📊 Xuất Báo Cáo Excel'}
        </button>
      </div>

      {/* Hiển thị kết quả */}
      {resultData && (
        <div style={{ marginTop: '20px' }}>
          <h4 style={{ marginBottom: '15px', color: '#333' }}>📈 Kết Quả Thống Kê</h4>

          {/* Cards tổng quan */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '15px',
              marginBottom: '20px',
            }}
          >
            <div style={{ padding: '15px', backgroundColor: '#e6f4ea', borderRadius: '6px', border: '1px solid #b7e1cd' }}>
              <div style={{ fontSize: '12px', color: '#137333' }}>Khớp (OK)</div>
              <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#137333' }}>
                {resultData.summary.matched_count}
              </div>
            </div>

            <div style={{ padding: '15px', backgroundColor: '#fce8e6', borderRadius: '6px', border: '1px solid #f5c2c7' }}>
              <div style={{ fontSize: '12px', color: '#c5221f' }}>Thiếu file PDF</div>
              <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#c5221f' }}>
                {resultData.summary.missing_pdf_count}
              </div>
            </div>

            <div style={{ padding: '15px', backgroundColor: '#fef7e0', borderRadius: '6px', border: '1px solid #fce8b2' }}>
              <div style={{ fontSize: '12px', color: '#b06000' }}>Thiếu trên Excel</div>
              <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#b06000' }}>
                {resultData.summary.missing_excel_count}
              </div>
            </div>

            <div style={{ padding: '15px', backgroundColor: '#f1f3f4', borderRadius: '6px', border: '1px solid #dadce0' }}>
              <div style={{ fontSize: '12px', color: '#3c4043' }}>File PDF Trùng lap</div>
              <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#3c4043' }}>
                {resultData.summary.duplicates_count}
              </div>
            </div>
          </div>

          {/* Chi tiết bảng */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Cột Thiếu PDF */}
            <div style={{ border: '1px solid #eee', borderRadius: '4px', padding: '10px' }}>
              <h5 style={{ marginTop: 0, color: '#c5221f' }}>
                ❌ Giá trị Excel không có file PDF ({resultData.missing_pdf.length})
              </h5>
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                {resultData.missing_pdf.length === 0 ? (
                  <p style={{ fontSize: '13px', color: '#888' }}>Không có</p>
                ) : (
                  <ul style={{ paddingLeft: '20px', margin: 0, fontSize: '13px' }}>
                    {resultData.missing_pdf.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Cột Thiếu Excel */}
            <div style={{ border: '1px solid #eee', borderRadius: '4px', padding: '10px' }}>
              <h5 style={{ marginTop: 0, color: '#b06000' }}>
                ⚠️ File PDF không có trong Excel ({resultData.missing_excel.length})
              </h5>
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                {resultData.missing_excel.length === 0 ? (
                  <p style={{ fontSize: '13px', color: '#888' }}>Không có</p>
                ) : (
                  <ul style={{ paddingLeft: '20px', margin: 0, fontSize: '13px' }}>
                    {resultData.missing_excel.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}