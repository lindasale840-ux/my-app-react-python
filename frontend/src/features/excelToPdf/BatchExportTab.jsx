import React, { useState } from 'react';
import { convertExcelToPdf } from '../../services/excelToPdfService';

const BatchExportTab = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [exportType, setExportType] = useState('zip'); // 'zip' hoặc 'single_pdf'
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Xử lý khi chọn file từ máy tính
  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    addFiles(files);
  };

  // Lọc lấy các file Excel
  const addFiles = (newFiles) => {
    setErrorMessage('');
    setSuccessMessage('');

    const validFiles = newFiles.filter((file) => {
      const ext = file.name.split('.').pop().toLowerCase();
      return ext === 'xlsx' || ext === 'xls';
    });

    if (validFiles.length < newFiles.length) {
      setErrorMessage('Đã loại bỏ một số file không đúng định dạng Excel (.xlsx, .xls).');
    }

    // Tránh trùng lặp tên file
    setSelectedFiles((prevFiles) => {
      const existingNames = new Set(prevFiles.map((f) => f.name));
      const filteredNewFiles = validFiles.filter((f) => !existingNames.has(f.name));
      return [...prevFiles, ...filteredNewFiles];
    });
  };

  // Kéo thả file (Drag & Drop)
  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  // Xóa file khỏi danh sách chọn
  const handleRemoveFile = (indexToRemove) => {
    setSelectedFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  };

  // Xử lý gọi API xuất PDF
  const handleStartConvert = async () => {
    if (selectedFiles.length === 0) {
      setErrorMessage('Vui lòng chọn ít nhất 1 file Excel.');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const response = await convertExcelToPdf(selectedFiles, exportType);

      // Tạo URL download file nhị phân
      const blob = new Blob([response.data], {
        type: exportType === 'zip' ? 'application/zip' : 'application/pdf',
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;

      const defaultFileName = exportType === 'zip' ? 'Excel_Exported_PDFs.zip' : 'Excel_Merged_Export.pdf';
      link.setAttribute('download', defaultFileName);

      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setSuccessMessage('Xuất PDF hàng loạt thành công và đã tự động tải về!');
    } catch (err) {
      console.error(err);
      let msg = 'Đã xảy ra lỗi khi chuyển đổi file Excel sang PDF.';
      if (err.response && err.response.data instanceof Blob) {
        // Đọc thông báo lỗi từ Blob nếu backend trả về JSON Error
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
          marginBottom: '10px',
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

      {/* HIỂN THỊ THÔNG BÁO ERROR / SUCCESS */}
      {errorMessage && (
        <div
          style={{
            backgroundColor: '#f8d7da',
            color: '#721c24',
            padding: '12px 15px',
            borderRadius: '4px',
            border: '1px solid #f5c6cb',
            marginBottom: '10px',
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
            padding: '12px 15px',
            borderRadius: '4px',
            border: '1px solid #c3e6cb',
            marginBottom: '10px',
          }}
        >
          {successMessage}
        </div>
      )}

      {/* DANH SÁCH FILE ĐÃ CHỌN */}
      {selectedFiles.length > 0 && (
        <div style={{ marginBottom: '15px' }}>
          <h4 style={{ marginBottom: '10px', color: '#333' }}>
            Danh sách file đã chọn ({selectedFiles.length}):
          </h4>
          <ul style={{ listStyleType: 'none', padding: 0, margin: 0 }}>
            {selectedFiles.map((file, idx) => (
              <li
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 12px',
                  backgroundColor: '#ffffff',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  marginBottom: '8px',
                }}
              >
                <span style={{ fontSize: '14px', color: '#333' }}>
                  📊 {file.name} <small style={{ color: '#888' }}>({(file.size / 1024).toFixed(1)} KB)</small>
                </span>
                <button
                  type="button"
                  onClick={() => handleRemoveFile(idx)}
                  style={{
                    backgroundColor: '#dc3545',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '4px 10px',
                    cursor: 'pointer',
                    fontSize: '12px',
                  }}
                >
                  Xóa
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* CẤU HÌNH TÙY CHỌN ĐẦU RA */}
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid #ddd',
          borderRadius: '6px',
          padding: '15px',
          marginBottom: '15px',
        }}
      >
        <h4 style={{ marginBottom: '12px', color: '#333' }}>Tùy chọn xuất đầu ra:</h4>
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
            <strong>Option B:</strong> Gộp tất cả thành 1 file PDF duy nhất
          </label>
        </div>
      </div>

      {/* NÚT BẮT ĐẦU CHUYỂN ĐỔI */}
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
        {isLoading ? 'Đang gọi MS Excel chuyển đổi PDF...' : '🚀 Bắt đầu chuyển đổi ngay'}
      </button>
    </div>
  );
};

export default BatchExportTab;