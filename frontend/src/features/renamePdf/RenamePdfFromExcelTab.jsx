import React, { useState } from 'react';
import {
  parseExcelColumnsApi,
  previewRenameApi,
  executeRenameZipApi,
} from '../../services/renamePdfExcelService';

const RenamePdfFromExcelTab = () => {
  const [excelFile, setExcelFile] = useState(null);
  const [columns, setColumns] = useState([]);
  const [keyColumn, setKeyColumn] = useState('');
  const [selectedTargetColumns, setSelectedTargetColumns] = useState([]);
  const [separator, setSeparator] = useState('_');
  const [pdfFiles, setPdfFiles] = useState([]);
  
  const [previewData, setPreviewData] = useState([]);
  const [loadingParse, setLoadingParse] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingDownload, setLoadingDownload] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Xử lý Upload Excel & Lấy Cột
  const handleExcelChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setExcelFile(file);
    setErrorMsg('');
    setSuccessMsg('');
    setLoadingParse(true);

    try {
      const res = await parseExcelColumnsApi(file);
      if (res.status === 'success' && res.columns.length > 0) {
        setColumns(res.columns);
        setKeyColumn(res.columns[0]);
        setSelectedTargetColumns([res.columns[0]]);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Không thể đọc danh sách cột từ file Excel!');
    } finally {
      setLoadingParse(false);
    }
  };

  // Chọn/Bỏ chọn cột ghép tên mới
  const handleToggleTargetColumn = (col) => {
    if (selectedTargetColumns.includes(col)) {
      if (selectedTargetColumns.length === 1) return; // Bắt buộc chọn ít nhất 1 cột
      setSelectedTargetColumns(selectedTargetColumns.filter((c) => c !== col));
    } else {
      setSelectedTargetColumns([...selectedTargetColumns, col]);
    }
  };

  // Xem trước Bảng Đối Chiếu
  const handlePreview = async () => {
    if (!excelFile || pdfFiles.length === 0 || !keyColumn || selectedTargetColumns.length === 0) {
      setErrorMsg('Vui lòng chọn đầy đủ File Excel, Danh sách PDF, Cột Khóa và Cột Đổi Tên!');
      return;
    }
    setErrorMsg('');
    setSuccessMsg('');
    setLoadingPreview(true);

    try {
      const res = await previewRenameApi(excelFile, pdfFiles, keyColumn, selectedTargetColumns, separator);
      if (res.status === 'success') {
        setPreviewData(res.data);
        setSuccessMsg(`Đã đối chiếu thành công ${res.data.length} file PDF!`);
      }
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Lỗi trong quá trình đối chiếu!');
    } finally {
      setLoadingPreview(false);
    }
  };

  // Thực thi Đổi Tên & Tải Zip
  const handleDownloadZip = async () => {
    if (!excelFile || pdfFiles.length === 0) return;
    setLoadingDownload(true);
    setErrorMsg('');

    try {
      const blob = await executeRenameZipApi(excelFile, pdfFiles, keyColumn, selectedTargetColumns, separator);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'PDF_Doi_Ten_Theo_Excel.zip');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      setSuccessMsg('Đã nén và tải xuống file ZIP thành công!');
    } catch (err) {
      setErrorMsg('Lỗi khi nén và tải về file ZIP!');
    } finally {
      setLoadingDownload(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
      {/* Alert Thông Báo */}
      {errorMsg && (
        <div style={{ backgroundColor: '#f8d7da', color: '#721c24', padding: '12px 15px', borderRadius: '4px', border: '1px solid #f5c6cb' }}>
          ⚠️ {errorMsg}
        </div>
      )}
      {successMsg && (
        <div style={{ backgroundColor: '#d4edda', color: '#155724', padding: '12px 15px', borderRadius: '4px', border: '1px solid #c3e6cb' }}>
          ✅ {successMsg}
        </div>
      )}

      {/* Bước 1: Upload Excel & Chọn Cột */}
      <div style={{ border: '1px solid #ccc', borderRadius: '6px', padding: '15px', backgroundColor: '#ffffff' }}>
        <h4 style={{ margin: '0 0 12px 0', color: '#007bff' }}>1. Chọn File Excel Tổng & Đội Tên Cột</h4>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '6px' }}>File Excel Tổng (.xlsx, .xls):</label>
          <input type="file" accept=".xlsx, .xls" onChange={handleExcelChange} style={{ display: 'block' }} />
          {loadingParse && <span style={{ color: '#007bff', fontSize: '13px', marginTop: '5px', display: 'block' }}>Đang đọc dữ liệu cột Excel...</span>}
        </div>

        {columns.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '10px' }}>
            <div>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '6px' }}>Cột Khóa (Dùng để khớp với Tên File PDF hiện tại):</label>
              <select
                value={keyColumn}
                onChange={(e) => setKeyColumn(e.target.value)}
                style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', minWidth: '250px' }}
              >
                {columns.map((col) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '6px' }}>Chọn Cột Làm Tên Mới (Có thể chọn nhiều cột để ghép):</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', maxHeight: '120px', overflowY: 'auto', padding: '8px', border: '1px solid #eee', borderRadius: '4px' }}>
                {columns.map((col) => {
                  const isChecked = selectedTargetColumns.includes(col);
                  return (
                    <button
                      key={col}
                      type="button"
                      onClick={() => handleToggleTargetColumn(col)}
                      style={{
                        padding: '5px 10px',
                        borderRadius: '4px',
                        border: isChecked ? '1px solid #007bff' : '1px solid #ccc',
                        backgroundColor: isChecked ? '#007bff' : '#f8f9fa',
                        color: isChecked ? '#ffffff' : '#333333',
                        cursor: 'pointer',
                        fontSize: '13px',
                      }}
                    >
                      {isChecked ? '✓ ' : '+ '}{col}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '6px' }}>Ký tự nối giữa các cột:</label>
              <input
                type="text"
                value={separator}
                onChange={(e) => setSeparator(e.target.value)}
                style={{ padding: '6px 10px', borderRadius: '4px', border: '1px solid #ccc', width: '80px', textAlign: 'center' }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Bước 2: Upload Danh Sách PDF */}
      <div style={{ border: '1px solid #ccc', borderRadius: '6px', padding: '15px', backgroundColor: '#ffffff' }}>
        <h4 style={{ margin: '0 0 12px 0', color: '#007bff' }}>2. Upload Danh Sách File PDF Cần Đổi Tên</h4>
        <input
          type="file"
          accept=".pdf"
          multiple
          onChange={(e) => setPdfFiles(e.target.files)}
          style={{ display: 'block' }}
        />
        {pdfFiles.length > 0 && (
          <div style={{ marginTop: '8px', color: '#28a745', fontSize: '14px', fontWeight: 'bold' }}>
            📁 Đã chọn {pdfFiles.length} file PDF.
          </div>
        )}
      </div>

      {/* Bước 3: Thao tác & Preview */}
      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={handlePreview}
          disabled={loadingPreview || pdfFiles.length === 0 || !excelFile}
          style={{
            backgroundColor: '#007bff',
            color: '#ffffff',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '4px',
            fontWeight: 'bold',
            cursor: loadingPreview ? 'not-allowed' : 'pointer',
            opacity: loadingPreview || pdfFiles.length === 0 || !excelFile ? 0.6 : 1,
          }}
        >
          {loadingPreview ? 'Đang Đối Chiếu...' : '🔍 Đối Chiếu Xem Trước'}
        </button>

        {previewData.length > 0 && (
          <button
            onClick={handleDownloadZip}
            disabled={loadingDownload}
            style={{
              backgroundColor: '#28a745',
              color: '#ffffff',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '4px',
              fontWeight: 'bold',
              cursor: loadingDownload ? 'not-allowed' : 'pointer',
            }}
          >
            {loadingDownload ? 'Đang Nén ZIP...' : '📦 Xác Nhận & Tải File ZIP'}
          </button>
        )}
      </div>

      {/* Bảng Preview Đối Chiếu */}
      {previewData.length > 0 && (
        <div style={{ border: '1px solid #ccc', borderRadius: '6px', padding: '15px', backgroundColor: '#ffffff' }}>
          <h4 style={{ margin: '0 0 12px 0' }}>Bảng Kết Quả Xem Trước ({previewData.length} files)</h4>
          <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f2f2f2', borderBottom: '2px solid #ddd' }}>
                  <th style={{ padding: '8px', border: '1px solid #ddd' }}>STT</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd' }}>Tên File PDF Gốc</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd' }}>Tên File Mới Sẽ Đổi</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd' }}>Trạng Thái</th>
                </tr>
              </thead>
              <tbody>
                {previewData.map((item, idx) => (
                  <tr key={idx} style={{ backgroundColor: idx % 2 === 0 ? '#ffffff' : '#f9f9f9' }}>
                    <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'center' }}>{idx + 1}</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{item.original_name}</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd', fontWeight: 'bold', color: item.status === 'success' ? '#155724' : '#333' }}>
                      {item.new_name}
                    </td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{item.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default RenamePdfFromExcelTab;