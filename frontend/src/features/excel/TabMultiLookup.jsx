import React, { useState } from 'react';
import { excelService } from '../../services/excelService';

const TabMultiLookup = () => {
  const [file, setFile] = useState(null);
  const [sheets, setSheets] = useState([]);
  const [selectedSheet, setSelectedSheet] = useState('');
  const [columns, setColumns] = useState([]);
  const [selectedColumn, setSelectedColumn] = useState('');

  const [lookupValues, setLookupValues] = useState('');
  const [matchMode, setMatchMode] = useState('Exact');
  const [caseSensitive, setCaseSensitive] = useState(false);

  const [loadingInspect, setLoadingInspect] = useState(false);
  const [loadingProcess, setLoadingProcess] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const [alert, setAlert] = useState({ type: '', message: '' });
  const [previewResult, setPreviewResult] = useState(null);

  // 1. Khi chọn file Excel
  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setAlert({ type: '', message: '' });
    setPreviewResult(null);
    setLoadingInspect(true);

    try {
      const data = await excelService.inspectFile(selectedFile);
      setSheets(data.sheets || []);
      if (data.sheets && data.sheets.length > 0) {
        setSelectedSheet(data.sheets[0]);
      }
      setColumns(data.columns || []);
      if (data.columns && data.columns.length > 0) {
        setSelectedColumn(data.columns[0]);
      }
      setAlert({
        type: 'success',
        message: `Đã nạp file "${selectedFile.name}" thành công! Tìm thấy ${data.sheets.length} sheet và ${data.columns.length} cột.`
      });
    } catch (err) {
      setAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Lỗi khi kiểm tra thông tin file Excel.'
      });
      setFile(null);
    } finally {
      setLoadingInspect(false);
    }
  };

  // 2. Khi thay đổi Sheet
  const handleSheetChange = async (e) => {
    const sheetName = e.target.value;
    setSelectedSheet(sheetName);
    if (!file) return;

    try {
      const data = await excelService.getSheetColumns(file, sheetName);
      setColumns(data.columns || []);
      if (data.columns && data.columns.length > 0) {
        setSelectedColumn(data.columns[0]);
      }
    } catch (err) {
      setAlert({
        type: 'error',
        message: 'Không thể đọc danh sách cột của sheet được chọn.'
      });
    }
  };

  // 3. Xử lý Xem trước
  const handlePreview = async () => {
    if (!file || !selectedSheet || !selectedColumn || !lookupValues.trim()) {
      setAlert({ type: 'error', message: 'Vui lòng điền đầy đủ các thông tin bắt buộc (*).' });
      return;
    }

    setLoadingPreview(true);
    setAlert({ type: '', message: '' });

    try {
      const res = await excelService.previewLookup({
        file,
        sheetName: selectedSheet,
        lookupColumn: selectedColumn,
        lookupValues,
        matchMode,
        caseSensitive
      });

      setPreviewResult(res);
      setAlert({
        type: 'success',
        message: `Xem trước hoàn tất! Tìm thấy ${res.total_rows_matched} dòng trùng khớp cho ${res.total_found}/${res.total_input} giá trị.`
      });
    } catch (err) {
      setAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Lỗi khi xem trước kết quả.'
      });
    } finally {
      setLoadingPreview(false);
    }
  };

  // 4. Xử lý Lọc & Tải File Excel
  const handleProcess = async () => {
    if (!file || !selectedSheet || !selectedColumn || !lookupValues.trim()) {
      setAlert({ type: 'error', message: 'Vui lòng điền đầy đủ các thông tin bắt buộc (*).' });
      return;
    }

    setLoadingProcess(true);
    setAlert({ type: '', message: '' });

    try {
      const response = await excelService.processMultiLookup({
        file,
        sheetName: selectedSheet,
        lookupColumn: selectedColumn,
        lookupValues,
        matchMode,
        caseSensitive
      });

      // Lấy headers thống kê
      const totalRows = response.headers['x-total-rows'] || '0';
      const summaryStatusRaw = response.headers['x-summary-status'] || '';
      const summaryStatus = decodeURIComponent(summaryStatusRaw);

      // Tải file xuống
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'KetQua_MultiLookup.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();

      setAlert({
        type: 'success',
        message: `Xuất file Excel thành công! ${summaryStatus}. Tổng cộng ${totalRows} dòng được trích xuất.`
      });
    } catch (err) {
      setAlert({
        type: 'error',
        message: err.response?.data?.detail || 'Lỗi khi lọc và xuất file Excel.'
      });
    } finally {
      setLoadingProcess(false);
    }
  };

  return (
    <div>
      {/* Alert Thông báo */}
      {alert.message && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '4px',
            marginBottom: '20px',
            backgroundColor: alert.type === 'error' ? '#f8d7da' : '#d4edda',
            color: alert.type === 'error' ? '#721c24' : '#155724',
            border: `1px solid ${alert.type === 'error' ? '#f5c6cb' : '#c3e6cb'}`,
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          {alert.message}
        </div>
      )}

      {/* 1. Chọn File Excel */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>
          1. Chọn File Excel Gốc (.xlsx, .xls, .csv) <span style={{ color: 'red' }}>*</span>
        </label>
        <input
          type="file"
          accept=".xlsx, .xls, .csv"
          onChange={handleFileChange}
          style={{
            display: 'block',
            width: '100%',
            padding: '8px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            boxSizing: 'border-box'
          }}
        />
        {loadingInspect && <p style={{ fontSize: '13px', color: '#007bff', marginTop: '5px' }}>Đang đọc thông tin cấu trúc file Excel...</p>}
      </div>

      {/* 2. Chọn Sheet và Cột Tra Cứu */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>
            2.1 Chọn Sheet <span style={{ color: 'red' }}>*</span>
          </label>
          <select
            value={selectedSheet}
            onChange={handleSheetChange}
            disabled={!file || sheets.length === 0}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              boxSizing: 'border-box'
            }}
          >
            {sheets.map((sh, idx) => (
              <option key={idx} value={sh}>
                {sh}
              </option>
            ))}
          </select>
        </div>

        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>
            2.2 Chọn Cột Lọc Tra Cứu (Lookup Column) <span style={{ color: 'red' }}>*</span>
          </label>
          <select
            value={selectedColumn}
            onChange={(e) => setSelectedColumn(e.target.value)}
            disabled={!file || columns.length === 0}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              boxSizing: 'border-box'
            }}
          >
            {columns.map((col, idx) => (
              <option key={idx} value={col}>
                {col}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 3. Danh sách Giá trị Cần Tìm */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>
          3. Nhập/Paste Danh Sách Giá Trị Cần Tìm (Mỗi mã 1 dòng) <span style={{ color: 'red' }}>*</span>
        </label>
        <textarea
          rows={6}
          value={lookupValues}
          onChange={(e) => setLookupValues(e.target.value)}
          placeholder={`Ví dụ:\nMA_KH_001\nMA_KH_002\nMA_KH_005`}
          style={{
            width: '100%',
            padding: '10px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            fontFamily: 'monospace',
            fontSize: '13px',
            boxSizing: 'border-box'
          }}
        />
      </div>

      {/* 4. Tùy Chọn Tra Cứu */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '4px', border: '1px solid #eee' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '10px', color: '#333' }}>
          4. Tùy Chọn Lọc Nâng Cao
        </label>
        <div style={{ display: 'flex', gap: '30px', alignItems: 'center' }}>
          <div>
            <span style={{ marginRight: '10px', fontSize: '14px', fontWeight: '500' }}>Chế độ khớp:</span>
            <label style={{ marginRight: '15px', cursor: 'pointer' }}>
              <input
                type="radio"
                name="matchMode"
                value="Exact"
                checked={matchMode === 'Exact'}
                onChange={() => setMatchMode('Exact')}
                style={{ marginRight: '5px' }}
              />
              Khớp chính xác (Exact)
            </label>
            <label style={{ cursor: 'pointer' }}>
              <input
                type="radio"
                name="matchMode"
                value="Contains"
                checked={matchMode === 'Contains'}
                onChange={() => setMatchMode('Contains')}
                style={{ marginRight: '5px' }}
              />
              Chứa từ khóa (Contains)
            </label>
          </div>

          <div>
            <label style={{ cursor: 'pointer', fontSize: '14px' }}>
              <input
                type="checkbox"
                checked={caseSensitive}
                onChange={(e) => setCaseSensitive(e.target.checked)}
                style={{ marginRight: '6px' }}
              />
              Phân biệt chữ hoa / chữ thường (Case-sensitive)
            </label>
          </div>
        </div>
      </div>

      {/* 5. Nút Thao Tác */}
      <div style={{ display: 'flex', gap: '15px', marginBottom: '20px' }}>
        <button
          onClick={handlePreview}
          disabled={loadingPreview || loadingProcess || !file}
          style={{
            padding: '11px 22px',
            backgroundColor: '#007bff',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            fontWeight: 'bold',
            cursor: loadingPreview || !file ? 'not-allowed' : 'pointer',
            opacity: loadingPreview || !file ? 0.6 : 1
          }}
        >
          {loadingPreview ? 'Đang kiểm tra...' : '🔍 Xem Trước Kết Quả'}
        </button>

        <button
          onClick={handleProcess}
          disabled={loadingProcess || loadingPreview || !file}
          style={{
            padding: '11px 22px',
            backgroundColor: '#28a745',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            fontWeight: 'bold',
            cursor: loadingProcess || !file ? 'not-allowed' : 'pointer',
            opacity: loadingProcess || !file ? 0.6 : 1
          }}
        >
          {loadingProcess ? 'Đang Lọc & Xuất File...' : '📥 Lọc & Tải Excel Kết Quả (.xlsx)'}
        </button>
      </div>

      {/* 6. Bảng Xem Trước Kết Quả */}
      {previewResult && (
        <div style={{ marginTop: '25px', paddingTop: '20px', borderTop: '2px solid #eee' }}>
          <h4 style={{ margin: '0 0 15px 0', color: '#333' }}>📊 Thống Kê Chi Tiết Tra Cứu:</h4>

          <div style={{ display: 'flex', gap: '15px', marginBottom: '15px' }}>
            <div style={{ flex: 1, padding: '10px 15px', backgroundColor: '#e9ecef', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: '#6c757d' }}>TỔNG MÃ TRA CỨU</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#333' }}>{previewResult.total_input}</div>
            </div>
            <div style={{ flex: 1, padding: '10px 15px', backgroundColor: '#d4edda', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: '#155724' }}>MÃ TÌM THẤY</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#28a745' }}>{previewResult.total_found}</div>
            </div>
            <div style={{ flex: 1, padding: '10px 15px', backgroundColor: '#f8d7da', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: '#721c24' }}>MÃ KHÔNG TÌM THẤY</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#dc3545' }}>{previewResult.total_missing}</div>
            </div>
            <div style={{ flex: 1, padding: '10px 15px', backgroundColor: '#cce5ff', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '12px', color: '#004085' }}>TỔNG DÒNG TRÙNG KHỚP</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#007bff' }}>{previewResult.total_rows_matched}</div>
            </div>
          </div>

          {/* Xem trước bảng dữ liệu */}
          {previewResult.preview_rows && previewResult.preview_rows.length > 0 && (
            <div>
              <p style={{ fontSize: '13px', color: '#666', fontStyle: 'italic', marginBottom: '8px' }}>
                Hiển thị tối đa 20 dòng đầu tiên của kết quả lọc:
              </p>
              <div style={{ overflowX: 'auto', border: '1px solid #ccc', borderRadius: '4px', maxHeight: '350px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f2f2f2', borderBottom: '2px solid #ddd' }}>
                      <th style={{ padding: '8px', borderRight: '1px solid #ddd', width: '40px' }}>#</th>
                      {previewResult.columns.map((col, idx) => (
                        <th key={idx} style={{ padding: '8px', borderRight: '1px solid #ddd', textAlign: 'left', whiteSpace: 'nowrap' }}>
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewResult.preview_rows.map((row, rIdx) => (
                      <tr key={rIdx} style={{ borderBottom: '1px solid #eee', backgroundColor: rIdx % 2 === 0 ? '#fff' : '#fafafa' }}>
                        <td style={{ padding: '8px', borderRight: '1px solid #ddd', textAlign: 'center', color: '#888' }}>{rIdx + 1}</td>
                        {previewResult.columns.map((col, cIdx) => (
                          <td key={cIdx} style={{ padding: '8px', borderRight: '1px solid #ddd', whiteSpace: 'nowrap' }}>
                            {String(row[col] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TabMultiLookup;