import React, { useState, useEffect } from 'react';
import { processPdfScanSplit } from '../../services/pdfScanSplitService';

const AutoSplitTab = () => {
  const [pdfFile, setPdfFile] = useState(null);
  const [excelFile, setExcelFile] = useState(null);
  const [namingType, setNamingType] = useState('ten_tb');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loadingStep, setLoadingStep] = useState(0);

  const steps = [
    'Đang tải file lên...',
    'Đang trích xuất dữ liệu...',
    'Đang quét OCR nội dung PDF...',
    'Đang đối chiếu dữ liệu...',
    'Đang đóng gói file ZIP...'
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

  const namingOptions = [
    { value: 'ten_tb', label: 'Tên thiết bị + Model' },
    { value: 'ten_ma_ql', label: 'Tên thiết bị + Mã quản lý' },
    { value: 'ten_truoc_slash_ma_ql', label: 'Tên (trước /) + Mã quản lý' },
    { value: 'ten_sau_slash_ma_ql', label: 'Tên (sau /) + Mã quản lý' },
    { value: 'ten_ma_ql_hoac_ten_ma_xx', label: 'Tên + Mã QL (Ưu tiên) HOẶC Tên + Mã XX' },
    { value: 'ten_ma_xx_hoac_ten_ma_ql', label: 'Tên + Mã XX (Ưu tiên) HOẶC Tên + Mã QL' },
    { value: 'ma_ql_hoac_ma_xx', label: 'Mã QL (Ưu tiên) HOẶC Mã XX' },
    { value: 'ma_xx_hoac_ma_ql', label: 'Mã XX (Ưu tiên) HOẶC Mã QL' },
    { value: 'ten_va_so_gcn', label: 'Tên thiết bị + Số GCN' },
    { value: 'ten_khong_model', label: 'Tên thiết bị (Không Model)' },
    { value: 'model_khong_ten', label: 'Model (Không Tên)' },
    { value: 'ma_xuat_xuong', label: 'Mã xuất xưởng' },
    { value: 'ten_ma_xuat_xuong', label: 'Tên thiết bị + Mã xuất xưởng' },
    { value: 'ten_dac_trung', label: 'Tên + Đặc tính kỹ thuật' },
    { value: 'ten_model_nsx', label: 'Tên + Model + Nhà sản xuất' },
    { value: 'ten_model_dac_trung', label: 'Tên + Model + Đặc tính KT' },
    { value: 'ma_ql', label: 'Mã quản lý' },
    { value: 'so_gcn', label: 'Số GCN' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!pdfFile || !excelFile) {
      setErrorMsg('Vui lòng chọn đầy đủ file PDF Scan và file Excel đối chiếu.');
      return;
    }
    setLoading(true); setErrorMsg(''); setSuccessMsg('');
    try {
      const blobData = await processPdfScanSplit(pdfFile, excelFile, namingType);
      const url = window.URL.createObjectURL(new Blob([blobData]));
      const link = document.createElement('a');
      link.href = url; link.setAttribute('download', 'Result.zip');
      document.body.appendChild(link); link.click(); link.parentNode.removeChild(link);
      setSuccessMsg('⚡ Xử lý thành công!');
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Có lỗi xảy ra.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      {errorMsg && <div style={{ padding: '10px', marginBottom: '15px', borderRadius: '4px', backgroundColor: '#f8d7da', color: '#721c24' }}>{errorMsg}</div>}
      {successMsg && <div style={{ padding: '10px', marginBottom: '15px', borderRadius: '4px', backgroundColor: '#d4edda', color: '#155724' }}>{successMsg}</div>}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>File PDF cần tách (*):</label>
          <input type="file" accept=".pdf" onChange={(e) => setPdfFile(e.target.files[0])} style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }} />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>File Excel đối chiếu (*):</label>
          <input type="file" accept=".xlsx, .xls" onChange={(e) => setExcelFile(e.target.files[0])} style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }} />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px' }}>Quy tắc đặt tên file:</label>
          <select value={namingType} onChange={(e) => setNamingType(e.target.value)} style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}>
            {namingOptions.map((opt) => (<option key={opt.value} value={opt.value}>{opt.label}</option>))}
          </select>
        </div>

        {loading && (
          <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #b8daff', backgroundColor: '#d1ecf1', borderRadius: '4px', color: '#0c5460' }}>
            <div style={{ fontWeight: 'bold', marginBottom: '10px' }}>{steps[loadingStep]}...</div>
            <div style={{ width: '100%', backgroundColor: '#fff', height: '10px', borderRadius: '5px', overflow: 'hidden' }}>
              <div style={{ width: `${((loadingStep + 1) / steps.length) * 100}%`, height: '100%', backgroundColor: '#007bff', transition: 'width 0.5s' }}></div>
            </div>
          </div>
        )}

        <button type="submit" disabled={loading} style={{ width: '100%', padding: '10px', border: 'none', borderRadius: '4px', backgroundColor: loading ? '#6c757d' : '#28a745', color: '#fff', fontWeight: 'bold', cursor: loading ? 'not-allowed' : 'pointer' }}>
          {loading ? 'Đang xử lý...' : '🚀 Thực hiện tách PDF'}
        </button>
      </form>
    </div>
  );
};

export default AutoSplitTab;