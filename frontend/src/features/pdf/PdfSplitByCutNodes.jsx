import React, { useState, useMemo, useRef } from 'react';
import { getPdfThumbnailsApi, splitPdfByRangesApi, extractCropTextApi } from '../../services/pdfSplitApi';

export default function PdfSplitByCutNodes() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  
  const [thumbnails, setThumbnails] = useState([]);
  const [cutPages, setCutPages] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 12;

  // STATE: Quản lý tên file tương ứng cho từng dải trang
  const [rangeNames, setRangeNames] = useState({});

  // STATE: Modal Zoom & Bôi đen (Crop)
  const [previewObj, setPreviewObj] = useState(null); // { imgSrc, pageNum }
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractedTextResult, setExtractedTextResult] = useState('');

  // STATE & REF cho việc bôi đen vùng ảnh (Crop ROI)
  const [cropRect, setCropRect] = useState(null); // { x, y, width, height }
  const isDraggingRef = useRef(false);
  const startPosRef = useRef({ x: 0, y: 0 });
  const imgRef = useRef(null);

  // STATE cho hiệu ứng Highlight khi Jump đến trang
  const [highlightedPage, setHighlightedPage] = useState(null);

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

  // Tính danh sách các khoảng trang cắt dạng mảng [ "1-3", "4-8", "9-12" ]
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

  // Cập nhật tên tùy chỉnh
  const handleRangeNameChange = (rangeStr, newName) => {
    setRangeNames(prev => ({
      ...prev,
      [rangeStr]: newName
    }));
  };

  // 🆕 TÍNH NĂNG 2: Jump (Cuộn & Chuyển trang preview đến vị trí đoạn cut)
  const handleJumpToPage = (targetPageNum) => {
    // 1. Tự động tính toán trang preview chứa trang targetPageNum
    const targetThumbPage = Math.ceil(targetPageNum / itemsPerPage);
    setCurrentPage(targetThumbPage);

    // 2. Tự động cuộn mượt và Highlight hiệu ứng chớp tắt
    setTimeout(() => {
      const el = document.getElementById(`pdf-page-card-${targetPageNum}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setHighlightedPage(targetPageNum);
        setTimeout(() => setHighlightedPage(null), 2000); // Tắt hiệu ứng sau 2 giây
      }
    }, 150);
  };

  // 🆕 TÍNH NĂNG 1: SỰ KIỆN KÉO CHUỘT BÔI ĐEN VÙNG CHỮ TÊN MODAL
  const handleMouseDown = (e) => {
    if (!imgRef.current) return;
    const rect = imgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    isDraggingRef.current = true;
    startPosRef.current = { x, y };
    setCropRect({ x, y, width: 0, height: 0 });
    setExtractedTextResult('');
  };

  const handleMouseMove = (e) => {
    if (!isDraggingRef.current || !imgRef.current) return;
    const rect = imgRef.current.getBoundingClientRect();
    const currentX = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    const currentY = Math.max(0, Math.min(e.clientY - rect.top, rect.height));

    const x = Math.min(startPosRef.current.x, currentX);
    const y = Math.min(startPosRef.current.y, currentY);
    const width = Math.abs(currentX - startPosRef.current.x);
    const height = Math.abs(currentY - startPosRef.current.y);

    setCropRect({ x, y, width, height });
  };

  const handleMouseUp = async () => {
    if (!isDraggingRef.current) return;
    isDraggingRef.current = false;

    if (!cropRect || cropRect.width < 10 || cropRect.height < 10 || !imgRef.current) {
      setCropRect(null);
      return;
    }

    setIsExtracting(true);

    try {
      const img = imgRef.current;

      // 1. Tính toán tỉ lệ chuẩn giữa Kích thước thật của ảnh (naturalWidth/Height) và Kích thước đang hiển thị
      const scaleX = img.naturalWidth / img.clientWidth;
      const scaleY = img.naturalHeight / img.clientHeight;

      const realX = cropRect.x * scaleX;
      const realY = cropRect.y * scaleY;
      const realW = cropRect.width * scaleX;
      const realH = cropRect.height * scaleY;

      // 2. Tạo Canvas ngầm để vẽ chính xác vùng chọn (chuẩn WeChat)
      const canvas = document.createElement('canvas');
      canvas.width = realW;
      canvas.height = realH;
      const ctx = canvas.getContext('2d');

      // Vẽ đúng vùng pixel được khoanh từ ảnh gốc sang Canvas
      ctx.drawImage(
        img,
        realX, realY, realW, realH, // Vùng cắt ở ảnh gốc
        0, 0, realW, realH          // Vùng vẽ lên Canvas
      );

      // 3. Chuyển Canvas thành tệp Blob PNG và gửi trực tiếp lên Backend
      canvas.toBlob(async (blob) => {
        if (!blob) {
          setIsExtracting(false);
          return;
        }

        try {
          const res = await extractCropTextApi(blob);
          if (res && res.text) {
            setExtractedTextResult(res.text);
          } else {
            setExtractedTextResult('Không tìm thấy chữ trong vùng chọn!');
          }
        } catch (err) {
          alert("Lỗi khi trích xuất chữ: " + err.message);
        } finally {
          setIsExtracting(false);
        }
      }, 'image/png');

    } catch (err) {
      alert("Lỗi tạo ảnh bôi đen: " + err.message);
      setIsExtracting(false);
    }
  };

  // Thực hiện cắt PDF
  const handleSplitPdf = async () => {
    if (computedRangesList.length === 0) {
      alert("Vui lòng chọn ít nhất 1 điểm cắt!");
      return;
    }

    setProcessing(true);

    try {
      const payloadData = computedRangesList.map((rangeStr, idx) => ({
        range: rangeStr,
        name: rangeNames[rangeStr] || `File_${idx + 1}`
      }));

      const rangesTextJson = JSON.stringify(payloadData);
      const zipBlob = await splitPdfByRangesApi(file, rangesTextJson);

      const url = window.URL.createObjectURL(new Blob([zipBlob], { type: 'application/zip' }));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "Split_Results.zip");
      document.body.appendChild(link);
      link.click();
      
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
              const isHighlighted = highlightedPage === pageNum;

              return (
                <div 
                  id={`pdf-page-card-${pageNum}`}
                  key={pageNum} 
                  style={{ 
                    border: isHighlighted ? '3px solid #ff4d4f' : (isCutPoint ? '2px solid red' : '1px solid #ddd'), 
                    padding: '8px', 
                    borderRadius: '5px',
                    textAlign: 'center',
                    background: isHighlighted ? '#fff2f0' : (isCutPoint ? '#fff0f0' : '#fff'),
                    transition: 'all 0.3s ease',
                    boxShadow: isHighlighted ? '0 0 12px rgba(255, 77, 79, 0.8)' : 'none'
                  }}
                >
                  <img 
                    src={imgSrc} 
                    alt={`Trang ${pageNum}`} 
                    onClick={() => {
                      setPreviewObj({ imgSrc, pageNum });
                      setCropRect(null);
                      setExtractedTextResult('');
                    }}
                    title="Click vào ảnh để phóng to & bôi đen trích xuất chữ"
                    style={{ 
                      width: '100%', 
                      height: 'auto', 
                      border: '1px solid #eee', 
                      cursor: 'zoom-in' 
                    }} 
                  />
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

          {/* KHU VỰC NHẬP TÊN CHO TỪNG FILE PDF SAU KHI CẮT */}
          <div style={{ marginBottom: '20px', background: '#e6f7ff', padding: '15px', borderRadius: '5px' }}>
            <h4 style={{ margin: '0 0 10px 0' }}>📋 Danh sách dải trang và đặt tên file:</h4>
            {computedRangesList.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {computedRangesList.map((rangeStr, idx) => {
                  const startPageOfRange = parseInt(rangeStr.split('-')[0], 10);

                  return (
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

                      {/* 🆕 NÚT JUMP CHUYỂN NHANH ĐẾN TRANG ĐẦU CỦA ĐOẠN */}
                      <button
                        type="button"
                        onClick={() => handleJumpToPage(startPageOfRange)}
                        title={`Cuộn đến Trang ${startPageOfRange}`}
                        style={{
                          padding: '4px 8px',
                          background: '#e6f7ff',
                          color: '#1890ff',
                          border: '1px solid #91d5ff',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '13px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}
                      >
                        🎯 Xem trang {startPageOfRange}
                      </button>

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
                  );
                })}
              </div>
            ) : (
              <span style={{ color: '#fa8c16' }}>⚠️️ Chưa chọn điểm cắt nào! Hãy chọn nút "✂️ Cắt tại đây" bên trên.</span>
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

      {/* 🆕 MODAL BÔI ĐEN LẤY CHỮ (EXTRACT ROI) */}
      {previewObj && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 9999,
            userSelect: 'none'
          }}
        >
          {/* NÚT ĐÓNG MODAL */}
          <button
            onClick={() => setPreviewObj(null)}
            style={{
              position: 'absolute',
              top: '15px',
              right: '20px',
              background: '#ff4d4f',
              color: '#fff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
              zIndex: 10000
            }}
          >
            ✕ Đóng Modal
          </button>

          <p style={{ color: '#fff', marginBottom: '10px', fontSize: '14px' }}>
            💡 <b>Hướng dẫn:</b> Nhấn giữ & kéo chuột bôi đen vùng chứa chữ trên Trang {previewObj.pageNum} để trích xuất text
          </p>

          {/* VÙNG CHỨA ẢNH & OVERLAY CROP */}
          <div 
            style={{ position: 'relative', display: 'inline-block', maxHeight: '70vh' }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          >
            <img 
              ref={imgRef}
              src={previewObj.imgSrc} 
              alt="Zoom Preview" 
              draggable={false}
              style={{ 
                maxHeight: '70vh', 
                maxWidth: '85vw', 
                borderRadius: '4px',
                border: '2px solid #fff',
                cursor: 'crosshair',
                display: 'block'
              }} 
            />

            {/* HỘP BÔI ĐEN HIỂN THỊ TRỰC QUAN */}
            {cropRect && (
              <div 
                style={{
                  position: 'absolute',
                  left: `${cropRect.x}px`,
                  top: `${cropRect.y}px`,
                  width: `${cropRect.width}px`,
                  height: `${cropRect.height}px`,
                  border: '2px dashed #00f0ff',
                  backgroundColor: 'rgba(0, 240, 255, 0.25)',
                  pointerEvents: 'none'
                }}
              />
            )}
          </div>

          {/* KHU VỰC HIỂN THỊ KẾT QUẢ TRÍCH XUẤT TEXT */}
          <div style={{ marginTop: '15px', width: '80%', maxWidth: '700px', textAlign: 'center' }}>
            {isExtracting && (
              <p style={{ color: '#1890ff', fontWeight: 'bold' }}>⏳ Đang trích xuất chữ từ vùng bôi đen...</p>
            )}

            {extractedTextResult && !isExtracting && (
              <div style={{ background: '#fff', padding: '10px 15px', borderRadius: '6px', textAlign: 'left', boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
                  <span style={{ fontWeight: 'bold', color: '#333' }}>📝 Kết quả chữ trích xuất:</span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(extractedTextResult);
                      alert("📋 Đã copy chữ vào bộ nhớ tạm!");
                    }}
                    style={{
                      background: '#52c41a',
                      color: '#fff',
                      border: 'none',
                      padding: '4px 10px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    📋 Copy Text
                  </button>
                </div>
                <textarea 
                  rows={3} 
                  value={extractedTextResult} 
                  readOnly 
                  style={{ width: '100%', padding: '6px', borderRadius: '4px', border: '1px solid #ddd', resize: 'vertical' }}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}