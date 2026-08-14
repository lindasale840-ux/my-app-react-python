import React, { useState } from 'react';
import { excelFormService } from '../../services/excelFormService';

const TRANSFORM_OPTIONS = [
  "Nguyên bản (Direct)",
  "Cắt lấy phần sau dấu '/'",
  "Tạo mã 'M' (Prefix M)",
  "Định dạng Ngày (DD/MMM/YYYY)",
  "Tra cứu PDF theo Mã GCN",
  "Viết HOA toàn bộ",
  "Viết thường toàn bộ",
  "Đánh tích nhóm '6' (ü)"
];

export default function ExcelFillTab() {
  const [fileTong, setFileTong] = useState(null);
  const [fileForm, setFileForm] = useState(null);
  const [pdfFiles, setPdfFiles] = useState([]);
  
  const [columns, setColumns] = useState([]);
  const [idColumn, setIdColumn] = useState('');
  const [mappingPairs, setMappingPairs] = useState([]);
  
  const [r5Active, setR5Active] = useState(true);
  const [r5K, setR5K] = useState('K14');
  const [r5N, setR5N] = useState('N14');

  const [loadingColumns, setLoadingColumns] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Khi tải file Tổng lên -> Tự động gọi API lấy danh sách các Cột
  const handleFileTongChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setFileTong(file);
    setErrorMessage('');
    setLoadingColumns(true);

    try {
      const res = await excelFormService.getColumns(file);
      const cols = res.columns || [];
      setColumns(cols);

      if (cols.length > 0) {
        // Thiết lập vị trí cột mặc định chuẩn theo logic cũ
        const defaultIdCol = cols.length > 27 ? cols[27] : cols[0];
        setIdColumn(defaultIdCol);

        setMappingPairs([
          { excel_col: cols[Math.min(27, cols.length - 1)], transform_type: "Nguyên bản (Direct)", target_cell: "J11" },
          { excel_col: cols[Math.min(26, cols.length - 1)], transform_type: "Nguyên bản (Direct)", target_cell: "U11" },
          { excel_col: cols[Math.min(7, cols.length - 1)], transform_type: "Nguyên bản (Direct)", target_cell: "U9" },
          { excel_col: cols[Math.min(6, cols.length - 1)], transform_type: "Nguyên bản (Direct)", target_cell: "J10" },
          { excel_col: cols[Math.min(5, cols.length - 1)], transform_type: "Cắt lấy phần sau dấu '/'", target_cell: "J9" },
          { excel_col: cols[Math.min(27, cols.length - 1)], transform_type: "Tạo mã 'M' (Prefix M)", target_cell: "U10" },
          { excel_col: cols[Math.min(30, cols.length - 1)] || cols[0], transform_type: "Định dạng Ngày (DD/MMM/YYYY)", target_cell: "I18, G51" },
          { excel_col: cols[Math.min(31, cols.length - 1)] || cols[0], transform_type: "Định dạng Ngày (DD/MMM/YYYY)", target_cell: "I19" },
          { excel_col: cols[Math.min(25, cols.length - 1)] || cols[0], transform_type: "Tra cứu PDF theo Mã GCN", target_cell: "I20" },
        ]);
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Không thể lấy cấu trúc cột từ file Tổng Excel!');
    } finally {
      setLoadingColumns(false);
    }
  };

  const addMappingPair = () => {
    if (columns.length === 0) return;
    setMappingPairs([
      ...mappingPairs,
      { excel_col: columns[0], transform_type: "Nguyên bản (Direct)", target_cell: "" }
    ]);
  };

  const removeMappingPair = (index) => {
    const updated = mappingPairs.filter((_, i) => i !== index);
    setMappingPairs(updated);
  };

  const updateMappingPair = (index, field, value) => {
    const updated = [...mappingPairs];
    updated[index][field] = value;
    setMappingPairs(updated);
  };

  const handleRunProcess = async () => {
    if (!fileTong || !fileForm) {
      setErrorMessage('Vui lòng tải lên cả File Tổng và File Form Mẫu!');
      return;
    }

    setErrorMessage('');
    setSuccessMessage('');
    setProcessing(true);

    const config = {
      id_column: idColumn,
      dynamic_pairs: mappingPairs,
      special_rules: {
        checkmark_logic: { active: r5Active, cell_option1: r5K, cell_option2: r5N }
      }
    };

    try {
      const blob = await excelFormService.processForm(fileTong, fileForm, pdfFiles, config);
      
      // Tạo Link tải file ZIP
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Form_Excel_Completed_${new Date().getTime()}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setSuccessMessage('Đã xuất thành công gói file Form Excel và file Log!');
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Đã có lỗi xảy ra trong quá trình xử lý!');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div style={{ padding: '10px 0' }}>
      <h3 style={{ marginTop: 0, marginBottom: '10px', color: '#333' }}>📑 Điền Form Excel & Trích xuất PDF Tự Động</h3>
      <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
        Thêm linh hoạt các cặp mapping và chọn trực tiếp Kiểu xử lý dữ liệu ngay trên giao diện.
      </p>

      {/* ALERT BÁO LỖI / THÀNH CÔNG */}
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

      {/* SECTION 1: UPLOAD FILES */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
        <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '6px', backgroundColor: '#fafafa' }}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '6px' }}>1. Select File Tổng dữ liệu Excel (*):</label>
            <input type="file" accept=".xlsx, .xls" onChange={handleFileTongChange} style={{ width: '100%' }} />
            {loadingColumns && <small style={{ color: '#007bff' }}>Đang đọc cấu trúc các cột...</small>}
          </div>

          <div>
            <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '6px' }}>2. Select File Form Mẫu Excel (*):</label>
            <input type="file" accept=".xlsx, .xls" onChange={(e) => setFileForm(e.target.files[0])} style={{ width: '100%' }} />
          </div>
        </div>

        <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '6px', backgroundColor: '#fafafa' }}>
          <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '6px' }}>3. Select các tệp PDF đính kèm (nếu có):</label>
          <input type="file" accept=".pdf" multiple onChange={(e) => setPdfFiles(e.target.files)} style={{ width: '100%' }} />
          <small style={{ display: 'block', marginTop: '8px', color: '#777' }}>
            Đã chọn: <b>{pdfFiles.length}</b> file PDF
          </small>
        </div>
      </div>

      {columns.length > 0 && (
        <>
          <hr style={{ border: 'none', borderTop: '1px solid #eee', margin: '20px 0' }} />

          {/* SECTION 2: CHỌN MÃ QUẢN LÝ */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
              🔑 Chọn cột chứa Mã Quản Lý (Dùng làm tên File Excel xuất ra):
            </label>
            <select
              value={idColumn}
              onChange={(e) => setIdColumn(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              {columns.map((col, idx) => (
                <option key={idx} value={col}>{col}</option>
              ))}
            </select>
          </div>

          {/* SECTION 3: MAPPING DYNAMIC PAIRS */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h4 style={{ margin: 0, color: '#333' }}>⚙️ Danh sách các quy tắc Mapping</h4>
              <button
                type="button"
                onClick={addMappingPair}
                style={{ backgroundColor: '#28a745', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
              >
                ➕ Thêm Quy Tắc Mapping Mới
              </button>
            </div>

            {mappingPairs.map((pair, idx) => (
              <div key={idx} style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px', background: '#f9f9f9', padding: '10px', borderRadius: '4px', border: '1px solid #eee' }}>
                <div style={{ flex: 3 }}>
                  <label style={{ fontSize: '12px', color: '#555', display: 'block' }}>Cột File Tổng #{idx + 1}</label>
                  <select
                    value={pair.excel_col}
                    onChange={(e) => updateMappingPair(idx, 'excel_col', e.target.value)}
                    style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                  >
                    {columns.map((c, i) => (
                      <option key={i} value={c}>{c}</option>
                    ))}
                  </select>
                </div>

                <div style={{ flex: 3 }}>
                  <label style={{ fontSize: '12px', color: '#555', display: 'block' }}>Kiểu Xử Lý #{idx + 1}</label>
                  <select
                    value={pair.transform_type}
                    onChange={(e) => updateMappingPair(idx, 'transform_type', e.target.value)}
                    style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                  >
                    {TRANSFORM_OPTIONS.map((trans, i) => (
                      <option key={i} value={trans}>{trans}</option>
                    ))}
                  </select>
                </div>

                <div style={{ flex: 2 }}>
                  <label style={{ fontSize: '12px', color: '#555', display: 'block' }}>Ô Form Mẫu #{idx + 1}</label>
                  <input
                    type="text"
                    value={pair.target_cell}
                    placeholder="VD: J11 hoặc I18, G51"
                    onChange={(e) => updateMappingPair(idx, 'target_cell', e.target.value)}
                    style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box' }}
                  />
                </div>

                <div style={{ paddingTop: '18px' }}>
                  <button
                    type="button"
                    onClick={() => removeMappingPair(idx)}
                    style={{ backgroundColor: '#dc3545', color: '#fff', border: 'none', padding: '6px 10px', borderRadius: '4px', cursor: 'pointer' }}
                  >
                    ❌
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* SECTION 4: RULE CHECKMARK (Ü) */}
          <div style={{ border: '1px solid #e0e0e0', borderRadius: '6px', padding: '15px', marginBottom: '20px', backgroundColor: '#fdfdfd' }}>
            <label style={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', marginBottom: '10px' }}>
              <input
                type="checkbox"
                checked={r5Active}
                onChange={(e) => setR5Active(e.target.checked)}
              />
              🛠️ Bật quy tắc đánh dấu tích (ü) theo Mã Quản Lý
            </label>

            {r5Active && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '10px' }}>
                <div>
                  <label style={{ fontSize: '13px', display: 'block', marginBottom: '4px' }}>Ô đánh tích nếu chứa nhóm '6' (K14):</label>
                  <input
                    type="text"
                    value={r5K}
                    onChange={(e) => setR5K(e.target.value)}
                    style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '13px', display: 'block', marginBottom: '4px' }}>Ô đánh tích cho nhóm còn lại (N14):</label>
                  <input
                    type="text"
                    value={r5N}
                    onChange={(e) => setR5N(e.target.value)}
                    style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px', boxSizing: 'border-box' }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* NÚT THỰC THI */}
          <button
            type="button"
            onClick={handleRunProcess}
            disabled={processing}
            style={{
              backgroundColor: processing ? '#6c757d' : '#007bff',
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
            {processing ? '⏳ Đang xử lý dữ liệu và đóng gói ZIP...' : '🚀 Bắt đầu Tạo Form & Đóng Gói ZIP'}
          </button>
        </>
      )}
    </div>
  );
}