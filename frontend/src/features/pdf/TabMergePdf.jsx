import React, { useState } from 'react';
import { mergePdfsApi } from '../../services/pdfApi';

export default function TabMergePdf() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    setSelectedFiles(e.target.files);
  };

  const handleMerge = async () => {
    if (selectedFiles.length < 2) {
      alert('Vui lòng chọn từ 2 file PDF trở lên!');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const pdfBlob = await mergePdfsApi(selectedFiles);
      
      // Tạo đường dẫn tải file về từ Blob nhận được
      const url = window.URL.createObjectURL(new Blob([pdfBlob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Merged_${Date.now()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      setMessage('✅ Ghép file thành công và đã tự động tải về!');
    } catch (error) {
      console.error(error);
      setMessage('❌ Có lỗi xảy ra khi ghép file!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3>Ghép nhiều file PDF thành 1</h3>
      
      <input 
        type="file" 
        multiple 
        accept=".pdf" 
        onChange={handleFileChange} 
      />
      
      <p>Đã chọn: {selectedFiles.length} file</p>

      <button 
        onClick={handleMerge} 
        disabled={loading || selectedFiles.length === 0}
        style={{ padding: '10px 20px', cursor: 'pointer', backgroundColor: '#007bff', color: '#fff', border: 'none', borderRadius: '4px' }}
      >
        {loading ? 'Đang xử lý...' : 'Thực hiện Ghép PDF'}
      </button>

      {message && <p style={{ marginTop: '15px', fontWeight: 'bold' }}>{message}</p>}
    </div>
  );
}