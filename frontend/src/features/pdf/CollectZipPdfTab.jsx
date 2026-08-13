import React, { useState } from 'react';
import * as XLSX from 'xlsx';
import { collectAndZipPdf } from '../../services/collectZipPdfService';

const CollectZipPdfTab = ({ getTabStyle }) => {
  const [excelFile, setExcelFile] = useState(null);
  const [pdfFiles, setPdfFiles] = useState([]);
  const [columns, setColumns] = useState([]);
  const [selectedCol, setSelectedCol] = useState('');
  const [zipName, setZipName] = useState('Ket_Qua_Gom_PDF');
  
  const [advancedMode, setAdvancedMode] = useState(false);
  const [cutLength, setCutLength] = useState(9);
  
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [missingCodes, setMissingCodes] = useState([]);

  // Đọc danh sách cột từ file Excel
  const handleExcelChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setExcelFile(file);

    const reader = new FileReader();
    reader.onload = (evt) => {
      const bstr = evt.target.result;
      const wb = XLSX.read(bstr, { type: 'binary' });
      const wsname = wb.SheetNames[0];
      const ws = wb.Sheets[wsname];
      const data = XLSX.utils.sheet_to_json(ws, { header: 1 });
      if (data && data.length > 0) {
        setColumns(data[0]);
        setSelectedCol(data[0][0] || '');
      }
    };
    reader.readAsBinaryString(file);
  };

  const handlePdfChange = (e) => {
    setPdfFiles(Array.from(e.target.files));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!excelFile || pdfFiles.length === 0 || !selectedCol) {
      alert('Vui lòng chọn file Excel, các file PDF và chọn cột tương ứng!');
      return;
    }

    setLoading(true);
    setStatusMessage(null);
    setMissingCodes([]);

    const formData = new FormData();
    formData.append('excel_file', excelFile);
    pdfFiles.forEach((file) => formData.append('pdf_files', file));
    formData.append('selected_col', selectedCol);
    formData.append('zip_name', zipName);
    formData.append('advanced_mode', advancedMode);
    formData.append('cut_length', cutLength);

    try {
      const response = await collectAndZipPdf(formData);
      
      // Kiểm tra nếu server trả về JSON lỗi thay vì Blob ZIP
      if (response.data.type === 'application/json') {
        const text = await response.data.text();
        const json = JSON.parse(text);
        setStatusMessage({ type: 'error', text: json.message });
        if (json.missing_codes) setMissingCodes(json.missing_codes);
        setLoading(false);
        return;
      }

      // Xử lý đọc missing codes từ Header nếu có
      const missing = response.headers['x-missing-codes'];
      if (missing) {
        setMissingCodes(missing.split(',').filter(Boolean));
      }

      // Tải file ZIP xuống máy người dùng
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${zipName}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setStatusMessage({ type: 'success', text: '🎉 Đã gom và nén file ZIP thành công!' });
    } catch (error) {
      setStatusMessage({ type: 'error', text: `❌ Lỗi xử lý: ${error.message}` });
    } finally {
      setLoading(false);
    }
  };

  const currentStyle = getTabStyle ? getTabStyle() : {};

  return (
    <div style={{ padding: '20px', backgroundColor: '#fff', borderRadius: '8px', ...currentStyle }}>
      <h2>📦 Gom & Nén PDF Theo Danh Sách Excel (như Ryder)</h2>
      <p style={{ color: '#666' }}>
        Tìm các file PDF có tên nằm trong danh sách Excel, gộp lại và đóng gói thành file ZIP.
      </p>

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'flex', gap: '20px', marginBottom: '15px' }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
              👉 Chọn file Excel danh sách:
            </label>
            <input type="file" accept=".xlsx, .xls" onChange={handleExcelChange} style={{ width: '100%' }} required />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
              📁 Chọn các file PDF cần gom:
            </label>
            <input type="file" accept=".pdf" multiple onChange={handlePdfChange} style={{ width: '100%' }} required />
          </div>
        </div>

        {columns.length > 0 && (
          <div style={{ display: 'flex', gap: '20px', marginBottom: '15px' }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                🎯 Chọn cột chứa Mã Giấy Chứng Nhận:
              </label>
              <select
                value={selectedCol}
                onChange={(e) => setSelectedCol(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
              >
                {columns.map((col, idx) => (
                  <option key={idx} value={col}>{col}</option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>
                📝 Tên file nén ZIP đầu ra:
              </label>
              <input
                type="text"
                value={zipName}
                onChange={(e) => setZipName(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
              />
            </div>
          </div>
        )}

        <hr style={{ margin: '20px 0', borderColor: '#eee' }} />

        <div style={{ marginBottom: '15px' }}>
          <label style={{ cursor: 'pointer', fontWeight: 'bold' }}>
            <input
              type="checkbox"
              checked={advancedMode}
              onChange={(e) => setAdvancedMode(e.target.checked)}
              style={{ marginRight: '8px' }}
            />
            ⚙️ Kích hoạt chế độ phân loại thư mục chuyên sâu trước khi nén
          </label>
        </div>

        {advancedMode && (
          <div style={{ padding: '15px', backgroundColor: '#eef6ff', borderRadius: '6px', marginBottom: '15px' }}>
            <p style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#0056b3' }}>
              💡 Hệ thống sẽ dựa vào Mã Chứng Nhận trong Excel để tạo các thư mục con tương ứng bên trong file ZIP.
            </p>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
              ✂️ Nhập số ký tự đầu của mã để đặt tên thư mục gốc:
            </label>
            <input
              type="number"
              min="1"
              max="50"
              value={cutLength}
              onChange={(e) => setCutLength(parseInt(e.target.value) || 1)}
              style={{ width: '100px', padding: '6px', borderRadius: '4px', border: '1px solid #ccc' }}
            />
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold',
          }}
        >
          {loading ? '⏳ Đang Gom và Nén File...' : '🚀 Tiến hành Gom và Nén File'}
        </button>
      </form>

      {statusMessage && (
        <div
          style={{
            marginTop: '20px',
            padding: '15px',
            borderRadius: '6px',
            backgroundColor: statusMessage.type === 'success' ? '#d4edda' : '#f8d7da',
            color: statusMessage.type === 'success' ? '#155724' : '#721c24',
          }}
        >
          {statusMessage.text}
        </div>
      )}

      {missingCodes.length > 0 && (
        <div style={{ marginTop: '15px', padding: '15px', backgroundColor: '#fff3cd', borderRadius: '6px' }}>
          <strong style={{ color: '#856404' }}>
            ⚠️ Có {missingCodes.length} mã trong Excel KHÔNG tìm thấy file PDF tương ứng:
          </strong>
          <ul style={{ marginTop: '10px', color: '#856404' }}>
            {missingCodes.map((code, idx) => (
              <li key={idx}>{code}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CollectZipPdfTab;