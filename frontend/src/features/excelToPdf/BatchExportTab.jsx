import React, { useState } from 'react';
import { convertExcelToPdf, inspectExcelSheets } from '../../services/excelToPdfService';

const BatchExportTab = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [fileSheetsMap, setFileSheetsMap] = useState({});
  const [selectedSheetsMap, setSelectedSheetsMap] = useState({});
  const [exportType, setExportType] = useState('zip');
  const [customFilename, setCustomFilename] = useState(''); // State lưu tên file tùy chỉnh
  const [isLoading, setIsLoading] = useState(false);
  const [isInspecting, setIsInspecting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const addFiles = async (newFiles) => {
    setErrorMessage('');
    setSuccessMessage('');

    const validFiles = newFiles.filter((file) => {
      const ext = file.name.split('.').pop().toLowerCase();
      return ext === 'xlsx' || ext === 'xls';
    });

    if (validFiles.length < newFiles.length) {
      setErrorMessage('Đã loại bỏ một số file không đúng định dạng Excel (.xlsx, .xls).');
    }

    if (validFiles.length === 0) return;

    const existingNames = new Set(selectedFiles.map((f) => f.name));
    const filteredNewFiles = validFiles.filter((f) => !existingNames.has(f.name));

    if (filteredNewFiles.length === 0) return;

    const updatedFiles = [...selectedFiles, ...filteredNewFiles];
    setSelectedFiles(updatedFiles);

    setIsInspecting(true);
    try {
      const res = await inspectExcelSheets(filteredNewFiles);
      if (res.success && res.data) {
        const newSheetsMap = { ...fileSheetsMap };
        const newSelectedSheets = { ...selectedSheetsMap };

        res.data.forEach((item) => {
          newSheetsMap[item.filename] = item.sheets;
          newSelectedSheets[item.filename] = [...item.sheets];
        });

        setFileSheetsMap(newSheetsMap);
        setSelectedSheetsMap(newSelectedSheets);
      }
    } catch (err) {
      console.error('Lỗi khi đọc danh sách sheet:', err);
      setErrorMessage('Không thể đọc danh sách Sheet từ file. Vẫn có thể tiến hành xuất toàn bộ.');
    } finally {
      setIsInspecting(false);
    }
  };

  const handleFileChange = (e) => {
    addFiles(Array.from(e.target.files));
  };

  const handleDragOver = (e) => e.preventDefault();

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleRemoveFile = (indexToRemove) => {
    const fileToRemove = selectedFiles[indexToRemove];
    setSelectedFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));

    if (fileToRemove) {
      setFileSheetsMap((prev) => {
        const copy = { ...prev };
        delete copy[fileToRemove.name];
        return copy;
      });
      setSelectedSheetsMap((prev) => {
        const copy = { ...prev };
        delete copy[fileToRemove.name];
        return copy;
      });
    }
  };

  // Toggle chọn sheet (Giữ nguyên thứ tự tích chọn của người dùng)
  const handleToggleSheet = (filename, sheetName) => {
    setSelectedSheetsMap((prev) => {
      const currentSelected = prev[filename] || [];
      const updated = currentSelected.includes(sheetName)
        ? currentSelected.filter((s) => s !== sheetName)
        : [...currentSelected, sheetName]; // Thêm mới vào cuối để giữ đúng thứ tự chọn
      return { ...prev, [filename]: updated };
    });
  };

  const handleToggleAllSheets = (filename) => {
    const allSheets = fileSheetsMap[filename] || [];
    const currentSelected = selectedSheetsMap[filename] || [];

    setSelectedSheetsMap((prev) => ({
      ...prev,
      [filename]: currentSelected.length === allSheets.length ? [] : [...allSheets],
    }));
  };

  // NĂNG MỚI: Áp dụng danh sách sheet của 1 file cho TẤT CẢ các file còn lại
  const handleApplySheetsToAll = (sourceFilename) => {
    const targetSheetsPattern = selectedSheetsMap[sourceFilename] || [];
    
    setSelectedSheetsMap((prev) => {
      const newMap = { ...prev };
      selectedFiles.forEach((file) => {
        const availableSheets = fileSheetsMap[file.name] || [];
        // Lọc lấy những sheet mà file này thực sự sở hữu dựa trên pattern mẫu
        const matchedSheets = targetSheetsPattern.filter((s) => availableSheets.includes(s));
        newMap[file.name] = matchedSheets;
      });
      return newMap;
    });

    setSuccessMessage(`Đã áp dụng cấu hình chọn Sheet của "${sourceFilename}" cho tất cả các file!`);
  };

  const handleStartConvert = async () => {
    if (selectedFiles.length === 0) {
      setErrorMessage('Vui lòng chọn ít nhất 1 file Excel.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const response = await convertExcelToPdf(selectedFiles, exportType, selectedSheetsMap, customFilename);

      const blob = new Blob([response.data], {
        type: exportType === 'zip' ? 'application/zip' : 'application/pdf',
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;

      // Đặt tên file xuất ra theo Custom Filename hoặc tên mặc định
      let defaultName = exportType === 'zip' ? 'Excel_Exported_PDFs.zip' : 'Excel_Merged_Export.pdf';
      if (customFilename.trim()) {
        const ext = exportType === 'zip' ? '.zip' : '.pdf';
        defaultName = customFilename.trim().endsWith(ext) ? customFilename.trim() : `${customFilename.trim()}${ext}`;
      }

      link.setAttribute('download', defaultName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setSuccessMessage('Xuất PDF thành công và đã tự động tải về!');
    } catch (err) {
      console.error(err);
      let msg = 'Đã xảy ra lỗi khi chuyển đổi file Excel sang PDF.';
      if (err.response && err.response.data instanceof Blob) {
        const text = await err.response.data.text();
        try {
          const parsed = JSON.parse(text);
          if (parsed.detail) msg = parsed.detail;
        } catch (_) {}
      }
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* KHU VỰC KÉO THẢ / CHỌN FILE */}
      <div
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        style={{
          border: '2px dashed #007bff',
          borderRadius: '8px',
          padding: '30px',
          textAlign: 'center',
          backgroundColor: '#f8f9fa',
          cursor: 'pointer',
        }}
      >
        <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#333', marginBottom: '10px' }}>
          Kéo & Thả các file Excel (.xlsx, .xls) vào đây
        </p>
        <p style={{ fontSize: '14px', color: '#6c757d', marginBottom: '15px' }}>hoặc</p>
        <label
          htmlFor="file-upload-input"
          style={{
            backgroundColor: '#007bff',
            color: '#ffffff',
            padding: '10px 20px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold',
            display: 'inline-block',
          }}
        >
          Chọn file từ máy tính
        </label>
        <input
          id="file-upload-input"
          type="file"
          multiple
          accept=".xlsx, .xls"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </div>

      {/* ERROR / SUCCESS MESSAGES */}
      {errorMessage && (
        <div style={{ backgroundColor: '#f8d7da', color: '#721c24', padding: '12px 15px', borderRadius: '4px', border: '1px solid #f5c6cb' }}>
          {errorMessage}
        </div>
      )}

      {successMessage && (
        <div style={{ backgroundColor: '#d4edda', color: '#155724', padding: '12px 15px', borderRadius: '4px', border: '1px solid #c3e6cb' }}>
          {successMessage}
        </div>
      )}

      {isInspecting && (
        <div style={{ color: '#007bff', fontSize: '14px', fontStyle: 'italic' }}>
          ⏳ Đang đọc danh sách Sheet từ các file...
        </div>
      )}

      {/* DANH SÁCH FILE VÀ CHỌN SHEET */}
      {selectedFiles.length > 0 && (
        <div>
          <h4 style={{ marginBottom: '10px', color: '#333' }}>
            Danh sách file đã chọn ({selectedFiles.length}):
          </h4>
          <ul style={{ listStyleType: 'none', padding: 0, margin: 0 }}>
            {selectedFiles.map((file, idx) => {
              const sheets = fileSheetsMap[file.name] || [];
              const selectedSheets = selectedSheetsMap[file.name] || [];

              return (
                <li
                  key={idx}
                  style={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    padding: '12px',
                    marginBottom: '10px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: sheets.length > 0 ? '8px' : '0' }}>
                    <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#333' }}>
                      📊 {file.name} <small style={{ color: '#888', fontWeight: 'normal' }}>({(file.size / 1024).toFixed(1)} KB)</small>
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(idx)}
                      style={{ backgroundColor: '#dc3545', color: '#ffffff', border: 'none', borderRadius: '4px', padding: '4px 10px', cursor: 'pointer', fontSize: '12px' }}
                    >
                      Xóa
                    </button>
                  </div>

                  {/* KHU VỰC CHỌN SHEET */}
                  {sheets.length > 0 && (
                    <div style={{ backgroundColor: '#f9f9f9', padding: '10px', borderRadius: '4px', border: '1px solid #eee' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '12px', fontWeight: 'bold', color: '#555' }}>Tích chọn Sheet cần xuất (Thứ tự xuất sẽ theo thứ tự tích):</span>
                        <div style={{ display: 'flex', gap: '10px' }}>
                          {selectedFiles.length > 1 && (
                            <button
                              type="button"
                              onClick={() => handleApplySheetsToAll(file.name)}
                              style={{ background: 'none', border: 'none', color: '#28a745', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', padding: 0 }}
                            >
                              ⚡ Áp dụng danh sách Sheet này cho tất cả các file
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleToggleAllSheets(file.name)}
                            style={{ background: 'none', border: 'none', color: '#007bff', cursor: 'pointer', fontSize: '12px', padding: 0 }}
                          >
                            {selectedSheets.length === sheets.length ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
                          </button>
                        </div>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                        {sheets.map((sheet, sIdx) => (
                          <label key={sIdx} style={{ fontSize: '13px', display: 'flex', alignItems: 'center', cursor: 'pointer', backgroundColor: '#fff', padding: '3px 8px', borderRadius: '3px', border: '1px solid #ccc' }}>
                            <input
                              type="checkbox"
                              checked={selectedSheets.includes(sheet)}
                              onChange={() => handleToggleSheet(file.name, sheet)}
                              style={{ marginRight: '5px' }}
                            />
                            {sheet}
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* CẤU HÌNH TÙY CHỌN ĐẦU RA VÀ ĐỔI TÊN FILE */}
      <div style={{ backgroundColor: '#ffffff', border: '1px solid #ddd', borderRadius: '6px', padding: '15px' }}>
        <h4 style={{ marginBottom: '12px', color: '#333' }}>Tùy chọn xuất đầu ra:</h4>
        
        {/* ĐỔI TÊN FILE TÙY CHỈNH */}
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: 'bold', marginBottom: '5px', color: '#555' }}>
            ✏️ Đổi tên file tải về (Tùy chọn):
          </label>
          <input
            type="text"
            placeholder={exportType === 'zip' ? 'Ví dụ: Bao_Cao_Thang_10.zip' : 'Ví dụ: Tong_Hop_Bao_Cao.pdf'}
            value={customFilename}
            onChange={(e) => setCustomFilename(e.target.value)}
            style={{ width: '100%', padding: '8px 12px', borderRadius: '4px', border: '1px solid #ccc', fontSize: '14px', boxSizing: 'border-box' }}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', fontSize: '14px' }}>
            <input
              type="radio"
              name="exportType"
              value="zip"
              checked={exportType === 'zip'}
              onChange={(e) => setExportType(e.target.value)}
              style={{ marginRight: '8px' }}
            />
            <strong>Option A:</strong> Tải về file .ZIP (Mỗi file Excel xuất thành 1 file PDF riêng)
          </label>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', fontSize: '14px' }}>
            <input
              type="radio"
              name="exportType"
              value="single_pdf"
              checked={exportType === 'single_pdf'}
              onChange={(e) => setExportType(e.target.value)}
              style={{ marginRight: '8px' }}
            />
            <strong>Option B:</strong> Gộp tất cả các file/sheet thành 1 file PDF duy nhất
          </label>
        </div>
      </div>

      {/* NÚT XUẤT PDF */}
      <button
        type="button"
        onClick={handleStartConvert}
        disabled={isLoading || selectedFiles.length === 0}
        style={{
          backgroundColor: isLoading || selectedFiles.length === 0 ? '#6c757d' : '#28a745',
          color: '#ffffff',
          padding: '12px 25px',
          border: 'none',
          borderRadius: '4px',
          fontSize: '16px',
          fontWeight: 'bold',
          cursor: isLoading || selectedFiles.length === 0 ? 'not-allowed' : 'pointer',
          width: '100%',
        }}
      >
        {isLoading ? 'Đang chuyển đổi PDF...' : '🚀 Bắt đầu chuyển đổi ngay'}
      </button>
    </div>
  );
};

export default BatchExportTab;