import React, { useState, useMemo } from 'react';
import { getPdfThumbnailsApi, splitPdfByRangesApi } from '../../services/pdfSplitApi';

export default function PdfSplitByCutNodes() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  
  const [thumbnails, setThumbnails] = useState([]);
  const [cutPages, setCutPages] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  // Chọn file PDF -> Tải ảnh Thumbnails
  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setCutPages([]);
    setCurrentPage(1);
    setLoading(true);

    try {
      const data = await getPdfThumbnailsApi(selectedFile);
      setThumbnails(data.thumbnails || []);
    } catch (err) {
      alert("Lỗi khi tải ảnh xem trước PDF: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Click nút Chọn/Hủy điểm cắt
  const toggleCutPoint = (pageNumber) => {
    if (cutPages.includes(pageNumber)) {
      setCutPages(cutPages.filter(p => p !== pageNumber));
    } else {
      setCutPages([...cutPages, pageNumber].sort((a, b) => a - b));
    }
  };

  // Tự động tính chuỗi khoảng trang cắt
  const generatedRangesText = useMemo(() => {
    if (cutPages.length === 0 || thumbnails.length === 0) return "";
    
    const ranges = [];
    let startPage = 1;
    const sortedCuts = [...cutPages].sort((a, b) => a - b);

    sortedCuts.forEach((endPage) => {
      ranges.push(`${startPage}-${endPage}`);
      startPage = endPage + 1;
    });

    if (startPage <= thumbnails.length) {
      ranges.push(`${startPage}-${thumbnails.length}`);
    }

    return ranges.join("\n");
  }, [cutPages, thumbnails.length]);

  // Thực hiện cắt PDF
  const handleSplitPdf = async () => {
    if (!generatedRangesText) {
      alert("Vui lòng chọn ít nhất 1 điểm cắt!");
      return;
    }

    setProcessing(true);

    try {
      const zipBlob = await splitPdfByRangesApi(file, generatedRangesText);

      const url = window.URL.createObjectURL(new Blob([zipBlob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "Split_Results.zip");
      document.body.appendChild(link);
      link.click();
      link.remove();

      alert("🚀 Tách PDF thành công và đã tải file ZIP!");
    } catch (err) {
      alert("Lỗi khi tách file: " + err.message);
    } finally {
      setProcessing(false);
    }
  };

  const totalPagesCount = thumbnails.length;
  const totalThumbPages = Math.ceil(totalPagesCount / itemsPerPage) || 1;
  const startIdx = (currentPage - 1) * itemsPerPage;
  const currentThumbnails = thumbnails.slice(startIdx, startIdx + itemsPerPage);

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', background: '#fff' }}>
      <h3>✂️ Tách PDF theo điểm cắt</h3>
      
      <div style={{ marginBottom: '15px' }}>
        <label><b>Chọn file PDF: </b></label>
        <input type="file" accept="application/pdf" onChange={handleFileChange} />
      </div>

      {loading && <p style={{ color: 'blue' }}>⏳ Đang tải toàn bộ ảnh preview của PDF...</p>}

      {thumbnails.length > 0 && (
        <div>
          <p><b>Tổng số trang:</b> {thumbnails.length}</p>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '15px', background: '#f5f5f5', padding: '10px', borderRadius: '5px' }}>
            <button disabled={currentPage <= 1} onClick={() => setCurrentPage(prev => prev - 1)}>
              ⬅ Trang preview trước
            </button>
            <span> Xem trang <b>{currentPage}</b> / {totalThumbPages} </span>
            <button disabled={currentPage >= totalThumbPages} onClick={() => setCurrentPage(prev => prev + 1)}>
              Trang preview sau ➡
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', marginBottom: '20px' }}>
            {currentThumbnails.map((imgSrc, index) => {
              const pageNum = startIdx + index + 1;
              const isCutPoint = cutPages.includes(pageNum);

              return (
                <div 
                  key={pageNum} 
                  style={{ 
                    border: isCutPoint ? '2px solid red' : '1px solid #ddd', 
                    padding: '8px', 
                    borderRadius: '5px',
                    textAlign: 'center',
                    background: isCutPoint ? '#fff0f0' : '#fff'
                  }}
                >
                  <img src={imgSrc} alt={`Trang ${pageNum}`} style={{ width: '100%', height: 'auto', border: '1px solid #eee' }} />
                  <div style={{ marginTop: '5px', fontWeight: 'bold' }}>Trang {pageNum}</div>
                  
                  <button 
                    onClick={() => toggleCutPoint(pageNum)}
                    style={{
                      marginTop: '5px',
                      padding: '4px 8px',
                      cursor: 'pointer',
                      background: isCutPoint ? '#ff4d4f' : '#1890ff',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '4px'
                    }}
                  >
                    {isCutPoint ? '❌ Hủy điểm cắt' : '✂️ Cắt tại đây'}
                  </button>
                </div>
              );
            })}
          </div>

          <div style={{ marginBottom: '20px', background: '#e6f7ff', padding: '12px', borderRadius: '5px' }}>
            <h4 style={{ margin: '0 0 8px 0' }}>📋 Khoảng trang tự sinh:</h4>
            {generatedRangesText ? (
              <pre style={{ background: '#fff', padding: '8px', border: '1px solid #b7eb8f', borderRadius: '4px' }}>
                {generatedRangesText}
              </pre>
            ) : (
              <span style={{ color: '#fa8c16' }}>⚠️ Chưa chọn điểm cắt nào! Hãy chọn nút "✂️ Cắt tại đây" bên trên.</span>
            )}
          </div>

          <button 
            onClick={handleSplitPdf} 
            disabled={processing || !generatedRangesText}
            style={{ 
              padding: '10px 20px', 
              fontSize: '16px', 
              background: '#52c41a', 
              color: '#fff', 
              border: 'none', 
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            {processing ? "⏳ Đang tách file..." : "🚀 Tiến hành Tách PDF"}
          </button>
        </div>
      )}
    </div>
  );
}