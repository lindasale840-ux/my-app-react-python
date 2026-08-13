import React, { useState, useEffect } from 'react';
import { processGcnLocator } from '../../services/gcnLocatorService';

const GcnLocatorTab = () => {
  const [pdfFile, setPdfFile] = useState(null);
  const [requestedGcnText, setRequestedGcnText] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loadingStep, setLoadingStep] = useState(0);

  const steps = [
    'Đang tải file PDF lên hệ thống...',
    'Đang khởi tạo thuật toán Fast Skip Scan...',
    'Đang thực hiện quét OCR nhảy cóc trang...',
    'Đang xác định điểm biên trang bắt đầu...',
    'Đang tổng hợp báo cáo Excel vị trí...'
  ];

  useEffect(() => {
    let interval = null;
    if (loading) {
      setLoadingStep(0);
      interval = setInterval(() => {
        setLoadingStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!pdfFile) {
      setErrorMsg('Vui lòng chọn file PDF tổng cần quét định vị.');
      return;
    }
    if (!requestedGcnText.trim()) {
      setErrorMsg('Vui lòng nhập ít nhất một mã GCN cần tìm kiếm.');
      return;
    }

    setLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const blobData = await processGcnLocator(pdfFile, requestedGcnText);
      const url = window.URL.createObjectURL(new Blob([blobData]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'BaoCao_ViTri_GCN.xlsx');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      setSuccessMsg('⚡ Đã hoàn thành bản đồ định vị và xuất file Excel thành công!');
    } catch (err) {
      if (err.response && err.response.data instanceof Blob) {
        const text = await err.response.data.text();
        try {
          const json = JSON.parse(text);
          setErrorMsg(json.detail || 'Có lỗi xảy ra khi xử lý.');
        } catch {
          setErrorMsg('Lỗi không xác định từ hệ thống.');
        }
      } else {
        setErrorMsg(err.response?.data?.detail || 'Không thể kết nối đến máy chủ.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      {errorMsg && (
        <div style={{ padding: '10px 15px', marginBottom: '15px', borderRadius: '4px', backgroundColor: '#f8d7da', color: '#721c24', border: '1px solid #f5c6cb' }}>
          {errorMsg}
        </div>
      )}
      {successMsg && (
        <div style={{ padding: '10px 15px', marginBottom: '15px', borderRadius: '4px', backgroundColor: '#d4edda', color: '#155724', border: '1px solid #c3e6cb' }}>
          {successMsg}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
            File PDF Tổng (*):
          </label>
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setPdfFile(e.target.files[0])}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>
            Danh sách Mã Giấy Chứng Nhận cần tìm (Mỗi mã 1 dòng) (*):
          </label>
          <textarea
            rows={6}
            value={requestedGcnText}
            onChange={(e) => setRequestedGcnText(e.target.value)}
            placeholder={"GCN-2023-001\nGCN-2023-002\nGCN-2023-003"}
            style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontFamily: 'monospace', fontSize: '14px' }}
          />
        </div>

        {loading && (
          <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #b8daff', backgroundColor: '#d1ecf1', borderRadius: '4px', color: '#0c5460' }}>
            <div style={{ fontWeight: 'bold', marginBottom: '10px' }}>{steps[loadingStep]}...</div>
            <div style={{ width: '100%', backgroundColor: '#fff', height: '10px', borderRadius: '5px', overflow: 'hidden' }}>
              <div style={{ width: `${((loadingStep + 1) / steps.length) * 100}%`, height: '100%', backgroundColor: '#007bff', transition: 'width 0.5s' }}></div>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '10px 20px',
            borderRadius: '4px',
            border: 'none',
            backgroundColor: loading ? '#6c757d' : '#28a745',
            color: '#fff',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold',
            fontSize: '16px'
          }}
        >
          {loading ? 'Đang định vị vị trí...' : '📊 Xuất Báo Cáo Định Vị Excel'}
        </button>
      </form>
    </div>
  );
};

export default GcnLocatorTab;