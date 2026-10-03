import React, { useState } from 'react';
import { analyzeBatchPdfApi, exportExcelApi } from '../../services/excelExportService';

export default function ExportPdfToExcelTab() {
  const [files, setFiles] = useState([]);
  const [analyzedData, setAnalyzedData] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [exportMode, setExportMode] = useState('single_file'); // 'single_file' | 'zip_archive'
  const [isLoading, setIsLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });
  const [selectedCellCoords, setSelectedCellCoords] = useState([]); // Chứa mảng [{r, c}] được chọn để merge
  const [isSelecting, setIsSelecting] = useState(false);
  const [startCell, setStartCell] = useState(null); // { r, c }
  const [historyStack, setHistoryStack] = useState([]);

  // Hàm ghi nhận trạng thái vào lịch sử trước khi thay đổi dữ liệu
  const pushToHistory = () => {
    if (!analyzedData || analyzedData.length === 0) return;
    // Lưu bản sao sâu (Deep copy) của analyzedData
    const snapshot = JSON.parse(JSON.stringify(analyzedData));
    setHistoryStack((prev) => [...prev, snapshot]);
  };

  // [Cập nhật 1]: Hàm quy đổi số cột sang chữ cái A, B, C...
  const getColumnLabel = (colIdx) => {
    let label = '';
    let tempCol = colIdx;
    while (tempCol > 0) {
      let remainder = (tempCol - 1) % 26;
      label = String.fromCharCode(65 + remainder) + label;
      tempCol = Math.floor((tempCol - 1) / 26);
    }
    return label;
  };

  // [Cập nhật 2]: Hàm chọn cột khi Click (Hỗ trợ CTRL / CMD)
  const handleSelectColumn = (colNum, event) => {
    if (!currentItem) return;

    const colCells = [];
    for (let r = 1; r <= currentItem.rows; r++) {
      colCells.push({ r, c: colNum });
    }

    const isCtrlPressed = event.ctrlKey || event.metaKey;

    if (isCtrlPressed) {
      const isColAlreadySelected = selectedCellCoords.some((item) => item.c === colNum);

      if (isColAlreadySelected) {
        setSelectedCellCoords((prev) => prev.filter((item) => item.c !== colNum));
      } else {
        setSelectedCellCoords((prev) => [...prev, ...colCells]);
      }
    } else {
      setSelectedCellCoords(colCells);
    }
  };

  // Hàm UNDO: Khôi phục lại trạng thái gần nhất
  const handleUndo = () => {
    if (historyStack.length === 0) {
      alert('Không có thao tác nào để hoàn tác!');
      return;
    }
    const previousState = historyStack[historyStack.length - 1];
    setAnalyzedData(previousState);
    setHistoryStack((prev) => prev.slice(0, prev.length - 1));
    setSelectedCellCoords([]);
  };
  // Xử lý khi Upload Files
  const handleFileChange = async (e) => {
    const uploadedFiles = e.target.files;
    if (!uploadedFiles || uploadedFiles.length === 0) return;

    setFiles(uploadedFiles);
    setIsLoading(true);
    setStatusMsg({ type: '', text: '' });

    try {
      const res = await analyzeBatchPdfApi(uploadedFiles);
      if (res && res.status === 'success') {
        setAnalyzedData(res.data);
        setSelectedIndex(0);
        setStatusMsg({ type: 'success', text: `Phân tích thành công ${res.data.length} file PDF!` });
      }
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Lỗi phân tích file: ' + (err.response?.data?.detail || err.message) });
    } finally {
      setIsLoading(false);
    }
  };

  // Lấy file hiện tại đang xem
  const currentItem = analyzedData[selectedIndex] || null;

  // Cập nhật text ô trực tiếp
  const handleCellTextChange = (r, c, newText) => {
    if (!currentItem) return;
    const updatedAnalyzed = [...analyzedData];
    const cellObj = updatedAnalyzed[selectedIndex].cells.find(cell => cell.row === r && cell.col === c);
    if (cellObj) {
      cellObj.text = newText;
      setAnalyzedData(updatedAnalyzed);
    }
  };

  // Chọn ô để Gộp (Merge)
  const toggleCellSelect = (r, c) => {
    const exists = selectedCellCoords.some(coord => coord.r === r && coord.c === c);
    if (exists) {
      setSelectedCellCoords(selectedCellCoords.filter(coord => !(coord.r === r && coord.c === c)));
    } else {
      setSelectedCellCoords([...selectedCellCoords, { r, c }]);
    }
  };

  // 1. Khi nhấn chuột xuống một ô (Bắt đầu chọn)
  const handleMouseDown = (r, c) => {
    setIsSelecting(true);
    setStartCell({ r, c });
    setSelectedCellCoords([{ r, c }]);
  };

  // 2. Khi di chuyển chuột qua các ô khác trong khi đang giữ chuột trái
  const handleMouseEnter = (r, c) => {
    if (!isSelecting || !startCell) return;

    // Tính toán vùng hình chữ nhật từ startCell đến ô hiện tại (r, c)
    const minR = Math.min(startCell.r, r);
    const maxR = Math.max(startCell.r, r);
    const minC = Math.min(startCell.c, c);
    const maxC = Math.max(startCell.c, c);

    const newSelection = [];
    for (let row = minR; row <= maxR; row++) {
      for (let col = minC; col <= maxC; col++) {
        newSelection.push({ r: row, c: col });
      }
    }
    setSelectedCellCoords(newSelection);
  };

  // 3. Khi thả chuột ra (Kết thúc bôi đen)
  const handleMouseUp = () => {
    setIsSelecting(false);
  };
  // Thực hiện Gộp các ô đã chọn (Merge Cells)
  const handleMergeSelected = () => {
  if (selectedCellCoords.length < 2 || !currentItem) {
    alert('Vui lòng bôi đen chọn ít nhất 2 ô để gộp!');
    return;
  }

  pushToHistory(); // Lưu Undo trước khi gộp

  const rows = selectedCellCoords.map((item) => item.r);
  const cols = selectedCellCoords.map((item) => item.c);
  const minR = Math.min(...rows);
  const maxR = Math.max(...rows);
  const minC = Math.min(...cols);
  const maxC = Math.max(...cols);

  const rSpan = maxR - minR + 1;
  const cSpan = maxC - minC + 1;

  const updatedAnalyzed = [...analyzedData];
  const targetCells = updatedAnalyzed[selectedIndex].cells;

  // Gom toàn bộ chữ của các ô được chọn
  const mergedText = targetCells
    .filter((cell) => selectedCellCoords.some((sc) => sc.r === cell.row && sc.c === cell.col))
    .map((cell) => cell.text)
    .filter(Boolean)
    .join(' ');

  // Loại bỏ các ô nằm trong vùng gộp (trừ ô góc trên cùng bên trái)
  const filteredCells = targetCells.filter((cell) => {
    const inRegion = cell.row >= minR && cell.row <= maxR && cell.col >= minC && cell.col <= maxC;
    return !inRegion || (cell.row === minR && cell.col === minC);
  });

  // Cập nhật ô gốc (Root Cell)
  const rootCell = filteredCells.find((cell) => cell.row === minR && cell.col === minC);
  if (rootCell) {
    rootCell.rowspan = rSpan;
    rootCell.colspan = cSpan;
    rootCell.text = mergedText;
  }

  updatedAnalyzed[selectedIndex].cells = filteredCells;
  setAnalyzedData(updatedAnalyzed);
  setSelectedCellCoords([]);
};

  // 1. XÓA HÀNG CHUẨN
  const handleDeleteSelectedRows = () => {
    if (selectedCellCoords.length === 0 || !currentItem) return;

    pushToHistory(); // Lưu Undo trước khi xóa

    const rowsToDelete = [...new Set(selectedCellCoords.map((c) => c.r))].sort((a, b) => b - a);
    const updatedAnalyzed = [...analyzedData];
    const target = updatedAnalyzed[selectedIndex];

    let newCells = target.cells.filter((cell) => !rowsToDelete.includes(cell.row));

    rowsToDelete.forEach((deletedRow) => {
      newCells = newCells.map((cell) => {
        if (cell.row > deletedRow) {
          return { ...cell, row: cell.row - 1 };
        }
        if (cell.row <= deletedRow && cell.row + cell.rowspan - 1 >= deletedRow) {
          return { ...cell, rowspan: Math.max(1, cell.rowspan - 1) };
        }
        return cell;
      });
    });

    target.rows = Math.max(1, target.rows - rowsToDelete.length);
    target.cells = newCells;

    setAnalyzedData(updatedAnalyzed);
    setSelectedCellCoords([]);
  };

 // 2. XÓA CỘT CHUẨN (Bảo toàn dữ liệu các cột khác)
  const handleDeleteSelectedCols = () => {
    if (selectedCellCoords.length === 0 || !currentItem) return;

    pushToHistory(); // Lưu Undo trước khi xóa

    const colsToDelete = [...new Set(selectedCellCoords.map((c) => c.c))].sort((a, b) => b - a);
    const updatedAnalyzed = [...analyzedData];
    const target = updatedAnalyzed[selectedIndex];

    // Lọc ô không nằm trong cột bị xóa
    let newCells = target.cells.filter((cell) => !colsToDelete.includes(cell.col));

    // Điều chỉnh lại chỉ số cột cho các ô nằm sau cột bị xóa
    colsToDelete.forEach((deletedCol) => {
      newCells = newCells.map((cell) => {
        if (cell.col > deletedCol) {
          return { ...cell, col: cell.col - 1 };
        }
        // Điều chỉnh colspan nếu ô gộp bị cắt qua cột xóa
        if (cell.col <= deletedCol && cell.col + cell.colspan - 1 >= deletedCol) {
          return { ...cell, colspan: Math.max(1, cell.colspan - 1) };
        }
        return cell;
      });
    });

    target.cols = Math.max(1, target.cols - colsToDelete.length);
    target.cells = newCells;

    setAnalyzedData(updatedAnalyzed);
    setSelectedCellCoords([]);
  };

  // 3. Chỉ Xuất VÙNG ĐANG CHỌN (Selection Only)
  const handleExportSelectedRangeOnly = async () => {
    if (selectedCellCoords.length === 0 || !currentItem) {
      alert('Vui lòng bôi đen chọn vùng dữ liệu bạn muốn xuất!');
      return;
    }

    const rows = selectedCellCoords.map((item) => item.r);
    const cols = selectedCellCoords.map((item) => item.c);
    const minR = Math.min(...rows);
    const maxR = Math.max(...rows);
    const minC = Math.min(...cols);
    const maxC = Math.max(...cols);

    // Trích xuất ma trận con thu nhỏ đúng theo vùng bôi đen
    const extractedCells = currentItem.cells
      .filter((cell) => cell.row >= minR && cell.row <= maxR && cell.col >= minC && cell.col <= maxC)
      .map((cell) => ({
        ...cell,
        row: cell.row - minR + 1,
        col: cell.col - minC + 1,
      }));

    const payloadMatrix = [
      {
        filename: `Selected_Range_${currentItem.filename}`,
        rows: maxR - minR + 1,
        cols: maxC - minC + 1,
        cells: extractedCells,
      },
    ];

    setIsLoading(true);
    try {
      const blob = await exportExcelApi('single_file', payloadMatrix);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Vung_Lua_Chon_${currentItem.filename}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Lỗi xuất vùng chọn: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Áp dụng khung lưới hiện tại cho TẤT CẢ các file còn lại (Template Mode)
  const handleApplyGridToAll = () => {
    if (!currentItem) return;
    const templateCells = JSON.parse(JSON.stringify(currentItem.cells));
    const templateRows = currentItem.rows;
    const templateCols = currentItem.cols;

    const updatedAnalyzed = analyzedData.map((item) => ({
      ...item,
      rows: templateRows,
      cols: templateCols,
      cells: JSON.parse(JSON.stringify(templateCells)),
    }));

    setAnalyzedData(updatedAnalyzed);
    alert('Đã áp dụng khung lưới hiện tại cho toàn bộ danh sách file!');
  };

  // Trigger Xuất Excel
  const handleExport = async () => {
    if (analyzedData.length === 0) return;
    setIsLoading(true);
    setStatusMsg({ type: '', text: '' });

    try {
      const blob = await exportExcelApi(exportMode, analyzedData);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        exportMode === 'single_file' ? 'PDF_Export_Data.xlsx' : 'PDF_Export_Files.zip'
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      setStatusMsg({ type: 'success', text: 'Tải file Excel thành công!' });
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Lỗi xuất Excel: ' + err.message });
    } finally {
      setIsLoading(false);
    }
  };

  // 1. Thêm useEffect đăng ký phím tắt Ctrl + Z
  React.useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault();
        handleUndo();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [historyStack]);
  

  return (
    <div>
      {/* Alert Thông Báo */}
      {statusMsg.text && (
        <div
          style={{
            padding: '12px 15px',
            borderRadius: '4px',
            marginBottom: '15px',
            backgroundColor: statusMsg.type === 'error' ? '#f8d7da' : '#d4edda',
            color: statusMsg.type === 'error' ? '#721c24' : '#155724',
            border: `1px solid ${statusMsg.type === 'error' ? '#f5c6cb' : '#c3e6cb'}`,
          }}
        >
          {statusMsg.text}
        </div>
      )}

      {/* Control Panel: Upload & Config */}
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid #ccc',
          borderRadius: '6px',
          padding: '20px',
          marginBottom: '20px',
        }}
      >
        <div style={{ marginBottom: '15px' }}>
          <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
            1. Chọn danh sách file PDF (Hỗ trợ chọn nhiều file cùng lúc):
          </label>
          <input
            type="file"
            multiple
            accept="application/pdf"
            onChange={handleFileChange}
            disabled={isLoading}
            style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', width: '100%' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>
            2. Chế độ Xuất Đầu Ra (Output Strategy):
          </label>
          <div style={{ display: 'flex', gap: '20px' }}>
            <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <input
                type="radio"
                name="export_mode"
                value="single_file"
                checked={exportMode === 'single_file'}
                onChange={(e) => setExportMode(e.target.value)}
              />
              Gộp tất cả vào 1 File Excel (Mỗi PDF = 1 Sheet)
            </label>
            <label style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <input
                type="radio"
                name="export_mode"
                value="zip_archive"
                checked={exportMode === 'zip_archive'}
                onChange={(e) => setExportMode(e.target.value)}
              />
              Mỗi PDF ra 1 File Excel riêng (Tải về tệp .ZIP)
            </label>
          </div>
        </div>

        {analyzedData.length > 0 && (
          <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
            <button
              onClick={handleExport}
              disabled={isLoading}
              style={{
                backgroundColor: '#28a745',
                color: '#ffffff',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '4px',
                fontWeight: 'bold',
                cursor: isLoading ? 'not-allowed' : 'pointer',
              }}
            >
              {isLoading ? 'Đang xuất Excel...' : '🚀 XUẤT FILE EXCEL NGAY'}
            </button>
            <button
              onClick={handleApplyGridToAll}
              style={{
                backgroundColor: '#17a2b8',
                color: '#ffffff',
                border: 'none',
                padding: '10px 15px',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              📋 Áp Dụng Lưới Này Cho Tất Cả File (Template)
            </button>
          </div>
        )}
      </div>

      {/* Workspace Reviewer: Sidebar + Canvas Grid */}
      {analyzedData.length > 0 && (
        <div style={{ display: 'flex', gap: '20px' }}>
          {/* Sidebar Danh Sách File */}
          <div
            style={{
              width: '280px',
              backgroundColor: '#ffffff',
              border: '1px solid #ccc',
              borderRadius: '6px',
              padding: '15px',
              maxHeight: '600px',
              overflowY: 'auto',
            }}
          >
            <h4 style={{ marginTop: 0, marginBottom: '10px' }}>Danh Sách File ({analyzedData.length})</h4>
            {analyzedData.map((item, idx) => (
              <div
                key={idx}
                onClick={() => {
                  setSelectedIndex(idx);
                  setSelectedCellCoords([]);
                }}
                style={{
                  padding: '10px',
                  borderRadius: '4px',
                  marginBottom: '8px',
                  cursor: 'pointer',
                  border: selectedIndex === idx ? '2px solid #007bff' : '1px solid #eee',
                  backgroundColor: selectedIndex === idx ? '#e7f1ff' : '#f8f9fa',
                }}
              >
                <div style={{ fontWeight: 'bold', fontSize: '13px', wordBreak: 'break-all' }}>
                  {item.filename}
                </div>
                <div style={{ fontSize: '12px', marginTop: '4px', color: '#666' }}>
                  Trạng thái: {item.status === 'Ready' ? '🟢 Ready' : '🔴 Error'}
                </div>
              </div>
            ))}
          </div>

          {/* Main Reviewer & Interactive Grid */}
          <div
            style={{
              flex: 1,
              backgroundColor: '#ffffff',
              border: '1px solid #ccc',
              borderRadius: '6px',
              padding: '15px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px', alignItems: 'center' }}>
              <h4 style={{ margin: 0 }}>Xem Trực Quan & Tinh Chỉnh Lưới: {currentItem?.filename}</h4>
              <button
                onClick={handleMergeSelected}
                style={{
                  backgroundColor: '#007bff',
                  color: '#ffffff',
                  border: 'none',
                  padding: '8px 15px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 'bold'
                }}
              >
                🔗 Gộp Các Ô Đã Chọn ({selectedCellCoords.length})
              </button>
            </div>

            {currentItem && currentItem.rows > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                {/* PDF Background Preview Image */}
                {currentItem.bg_image && (
                  <div style={{ marginBottom: '15px' }}>
                    <p style={{ margin: '0 0 5px 0', fontSize: '12px', color: '#666' }}>Ảnh xem trước file PDF:</p>
                    <img
                      src={currentItem.bg_image}
                      alt="PDF Preview"
                      style={{ maxWidth: '100%', maxHeight: '400px', border: '1px solid #ddd', borderRadius: '4px', objectFit: 'contain' }}
                    />
                  </div>
                )}

                {/* Toolbar Thao Tác Cấu Trúc Bảng */}
                <div style={{ display: 'flex', gap: '10px', marginBottom: '12px', flexWrap: 'wrap' }}>
                  <button
                    onClick={handleUndo}
                    disabled={historyStack.length === 0}
                    style={{
                      backgroundColor: historyStack.length > 0 ? '#6c757d' : '#cccccc',
                      color: '#fff',
                      border: 'none',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      cursor: historyStack.length > 0 ? 'pointer' : 'not-allowed',
                      fontSize: '13px',
                      fontWeight: 'bold',
                    }}
                  >
                    ↩️ Undo (Ctrl+Z) [{historyStack.length}]
                  </button>

                  <button
                    onClick={handleMergeSelected}
                    style={{
                      backgroundColor: '#007bff',
                      color: '#fff',
                      border: 'none',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: 'bold',
                    }}
                  >
                    🔗 Gộp Ô ({selectedCellCoords.length})
                  </button>
                
                  <button
                    onClick={handleDeleteSelectedRows}
                    style={{
                      backgroundColor: '#dc3545',
                      color: '#fff',
                      border: 'none',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '13px',
                    }}
                  >
                    🗑️ Xóa Hàng Chọn
                  </button>

                  <button
                    onClick={handleDeleteSelectedCols}
                    style={{
                      backgroundColor: '#fd7e14',
                      color: '#fff',
                      border: 'none',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '13px',
                    }}
                  >
                    ✂️ Xóa Cột Chọn
                  </button>

                  <button
                    onClick={handleExportSelectedRangeOnly}
                    style={{
                      backgroundColor: '#28a745',
                      color: '#fff',
                      border: 'none',
                      padding: '6px 12px',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: 'bold',
                    }}
                  >
                    🎯 Chỉ Xuất Vùng Đang Bôi Đen
                  </button>
                </div>
                {/* Interactive Matrix Grid */}
                <p style={{ fontWeight: 'bold', marginBottom: '8px', fontSize: '13px', color: '#333' }}>
                  Ma Trận Dữ Liệu (Click chọn nhiều ô để Gộp / Nhập trực tiếp vào ô để sửa chữ):
                </p>
                
                <table 
  style={{ 
    borderCollapse: 'collapse', 
    width: '100%', 
    backgroundColor: '#fff', 
    border: '2px solid #007bff',
    userSelect: 'none'
  }}
  onMouseUp={handleMouseUp}
  onMouseLeave={handleMouseUp}
>
  {/* TIÊU ĐỀ CỘT DẠNG EXCEL (A, B, C...) */}
  <thead>
    <tr style={{ backgroundColor: '#e9ecef', textAlign: 'center', fontWeight: 'bold' }}>
      {/* Ô góc trống */}
      <th style={{ border: '1px solid #ccc', width: '40px', padding: '4px', fontSize: '12px', color: '#666' }}>
        #
      </th>
      {Array.from({ length: currentItem.cols || 0 }).map((_, cIdx) => {
        const colNum = cIdx + 1;
        const colLabel = getColumnLabel(colNum);
        const isColumnSelected = selectedCellCoords.some((sc) => sc.c === colNum);

        return (
          <th
            key={colNum}
            onClick={(e) => handleSelectColumn(colNum, e)}
            title="Bấm để chọn cột này. Giữ CTRL + Click để chọn nhiều cột!"
            style={{
              border: '1px solid #ccc',
              padding: '6px',
              fontSize: '12px',
              cursor: 'pointer',
              backgroundColor: isColumnSelected ? '#ffe082' : '#f1f3f5', // Đổi màu header nếu cột được chọn
              color: isColumnSelected ? '#000' : '#495057',
              transition: 'background-color 0.15s ease'
            }}
          >
            {colLabel}
          </th>
        );
      })}
    </tr>
  </thead>

  <tbody>
    {Array.from({ length: currentItem.rows || 0 }).map((_, rIdx) => {
      const rowNum = rIdx + 1;
      return (
        <tr key={rowNum}>
          {/* Cột chỉ số hàng 1, 2, 3... */}
          <td style={{ border: '1px solid #ccc', textAlign: 'center', backgroundColor: '#f1f3f5', fontSize: '11px', color: '#666', fontWeight: 'bold' }}>
            {rowNum}
          </td>

          {Array.from({ length: currentItem.cols || 0 }).map((_, cIdx) => {
            const colNum = cIdx + 1;
            const cellObj = (currentItem.cells || []).find(
              (c) => c.row === rowNum && c.col === colNum
            );

            if (!cellObj) return null;

            const isSelected = selectedCellCoords.some(
              (sc) => sc.r === rowNum && sc.c === colNum
            );

            return (
              <td
                key={colNum}
                rowSpan={cellObj.rowspan || 1}
                colSpan={cellObj.colspan || 1}
                onMouseDown={() => handleMouseDown(rowNum, colNum)}
                onMouseEnter={() => handleMouseEnter(rowNum, colNum)}
                style={{
                  border: '1px solid #007bff',
                  padding: '4px',
                  backgroundColor: isSelected ? '#fff3cd' : '#ffffff',
                  minWidth: '80px',
                  cursor: 'cell'
                }}
              >
                <input
                  type="text"
                  value={cellObj.text || ''}
                  onChange={(e) => handleCellTextChange(rowNum, colNum, e.target.value)}
                  onMouseDown={(e) => e.stopPropagation()}
                  style={{
                    width: '95%',
                    border: 'none',
                    outline: 'none',
                    backgroundColor: 'transparent',
                    fontSize: '13px',
                  }}
                />
              </td>
            );
          })}
        </tr>
      );
    })}
  </tbody>
</table>
              </div>
            ) : (
              <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                Chưa có dữ liệu bảng hoặc file đang được tải...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}