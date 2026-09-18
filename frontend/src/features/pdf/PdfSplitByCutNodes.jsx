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

  // STATE MỚI: Quản lý tên file tương ứng cho từng dải trang { "1-3": "A", "4-8": "B" }
  const [rangeNames, setRangeNames] = useState({});

  // Chọn file PDF -> Tải ảnh Thumbnails
  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setCutPages([]);
    setRangeNames({});
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

  // Tự động tính danh sách các khoảng trang cắt dạng mảng [ "1-3", "4-8", "9-12" ]
  const computedRangesList = useMemo(() => {
    if (cutPages.length === 0 || thumbnails.length === 0) return [];
    
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

    return ranges;
  }, [cutPages, thumbnails.length]);

  // Cập nhật tên tùy chỉnh cho một dải trang cụ thể
  const handleRangeNameChange = (rangeStr, newName) => {
    setRangeNames(prev => ({
      ...prev,
      [rangeStr]: newName
    }));
  };

  // Chuỗi dải trang kiểm tra điều kiện kích hoạt nút bấm Tách PDF
  const generatedRangesText = useMemo(() => {
    return computedRangesList.join("\n");
  }, [computedRangesList]);

  // Thực hiện cắt PDF
  const handleSplitPdf = async () => {
    if (computedRangesList.length === 0) {
      alert("Vui lòng chọn ít nhất 1 điểm cắt!");
      return;
    }

    setProcessing(true);

    try {
      // Đóng gói mảng danh sách [{ range: "1-3", name: "A" }, ...] thành dạng chuỗi JSON
      const payloadData = computedRangesList.map((rangeStr, idx) => ({
        range: rangeStr,
        name: rangeNames[rangeStr] || `File_${idx + 1}`
      }));

      const rangesTextJson = JSON.stringify(payloadData);

      // Gọi API giữ nguyên tham số cũ
      const zipBlob = await splitPdfByRangesApi(file, rangesTextJson);

      const url = window.URL.createObjectURL(new Blob([zipBlob], { type: 'application/zip' }));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "Split_Results.zip");
      document.body.appendChild(link);
      link.click();
      
      // Dọn dẹp DOM và giải phóng RAM
      link.remove();
      window.URL.revokeObjectURL(url);

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

          {/* KHU VỰC NHẬP TÊN CHO TỪNG FILE PDF SAU Khi CẮT */}
          <div style={{ marginBottom: '20px', background: '#e6f7ff', padding: '15px', borderRadius: '5px' }}>
            <h4 style={{ margin: '0 0 10px 0' }}>📋 Danh sách dải trang và đặt tên file:</h4>
            {computedRangesList.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {computedRangesList.map((rangeStr, idx) => (
                  <div 
                    key={rangeStr} 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '10px', 
                      background: '#fff', 
                      padding: '8px 12px', 
                      borderRadius: '4px',
                      border: '1px solid #91d5ff' 
                    }}
                  >
                    <span style={{ fontWeight: 'bold', minWidth: '120px' }}>
                      Khoảng {idx + 1} ({rangeStr}):
                    </span>
                    <input
                      type="text"
                      placeholder={`Tên file (Mặc định: File_${idx + 1})`}
                      value={rangeNames[rangeStr] || ''}
                      onChange={(e) => handleRangeNameChange(rangeStr, e.target.value)}
                      style={{
                        flex: 1,
                        padding: '6px 10px',
                        border: '1px solid #ccc',
                        borderRadius: '4px'
                      }}
                    />
                    <span>.pdf</span>
                  </div>
                ))}
              </div>
            ) : (
              <span style={{ color: '#fa8c16' }}>⚠️ Chưa chọn điểm cắt nào! Hãy chọn nút "✂️ Cắt tại đây" bên trên.</span>
            )}
          </div>

          <button 
            onClick={handleSplitPdf} 
            disabled={processing || computedRangesList.length === 0}
            style={{ 
              padding: '10px 20px', 
              fontSize: '16px', 
              background: '#52c41a', 
              color: '#fff', 
              border: 'none', 
              borderRadius: '5px',
              cursor: processing ? 'not-allowed' : 'pointer'
            }}
          >
            {processing ? "⏳ Đang tách file..." : "🚀 Tiến hành Tách PDF & Tải về"}
          </button>
        </div>
      )}
    </div>
  );
}