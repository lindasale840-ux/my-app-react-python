import React, { useState, useEffect } from 'react';
import { previewFileRename, processFileRename } from '../../services/fileRenamerService';

export default function BatchRenameTab() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [ruleMode, setRuleMode] = useState('SPLIT_SEPARATOR');
  const [ruleConfig, setRuleConfig] = useState({
    separator: '_',
    action: 'BEFORE_FIRST',
    index_n: 1,
    search_text: '',
    replace_text: '',
    match_case: false,
    prefix: '',
    suffix: '',
    base_name: '',
    start_number: 1,
    padding_digits: 2,
    position: 'SUFFIX',
    case_type: 'UPPER'
  });

  const [previewData, setPreviewData] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingProcess, setLoadingProcess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Tự động gọi Preview mỗi khi người dùng thay đổi file hoặc cấu hình
  useEffect(() => {
    if (selectedFiles.length > 0) {
      handlePreview();
    } else {
      setPreviewData(null);
    }
  }, [selectedFiles, ruleMode, ruleConfig]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(Array.from(e.target.files));
      setErrorMessage('');
      setSuccessMessage('');
    }
  };

  const handleConfigChange = (key, value) => {
    setRuleConfig((prev) => ({ ...prev, [key]: value }));
  };

  const handlePreview = async () => {
    if (selectedFiles.length === 0) return;
    setLoadingPreview(true);
    setErrorMessage('');
    try {
      const res = await previewFileRename(selectedFiles, ruleMode, ruleConfig);
      if (res.success) {
        setPreviewData(res);
      } else {
        setErrorMessage('Không thể tạo bản xem trước');
      }
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Lỗi kết nối khi gọi API Preview');
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleExecuteRename = async () => {
    if (selectedFiles.length === 0) {
      setErrorMessage('Vui lòng chọn ít nhất 1 file!');
      return;
    }
    setLoadingProcess(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const blobData = await processFileRename(selectedFiles, ruleMode, ruleConfig);
      
      // Tải file ZIP xuống
      const url = window.URL.createObjectURL(new Blob([blobData]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'DanhSachFile_DaDoiTen.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();

      setSuccessMessage('Đổi tên file và tải về thành công!');
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Lỗi khi thực hiện đổi tên file!');
    } finally {
      setLoadingProcess(false);
    }
  };

  return (
    <div style={{ width: '100%' }}>
      {/* Thông báo Alert */}
      {errorMessage && (
        <div style={{ padding: '12px 15px', backgroundColor: '#f8d7da', color: '#721c24', border: '1px solid #f5c6cb', borderRadius: '4px', marginBottom: '15px' }}>
          {errorMessage}
        </div>
      )}
      {successMessage && (
        <div style={{ padding: '12px 15px', backgroundColor: '#d4edda', color: '#155724', border: '1px solid #c3e6cb', borderRadius: '4px', marginBottom: '15px' }}>
          {successMessage}
        </div>
      )}

      {/* 1. KHOẢNG UPLOAD FILE */}
      <div style={{ marginBottom: '20px', padding: '15px', border: '1px dashed #007bff', borderRadius: '6px', backgroundColor: '#f8f9fa', textAlign: 'center' }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '10px', color: '#333' }}>
          Chọn các file cần đổi tên (PDF, Word, Excel, Hình ảnh, ZIP...):
        </label>
        <input 
          type="file" 
          multiple 
          onChange={handleFileChange}
          style={{ cursor: 'pointer' }}
        />
        {selectedFiles.length > 0 && (
          <div style={{ marginTop: '10px', fontSize: '14px', color: '#28a745', fontWeight: 'bold' }}>
            Đã chọn {selectedFiles.length} file.
          </div>
        )}
      </div>

      {/* 2. CẤU HÌNH QUY TẮC ĐỔI TÊN */}
      <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '6px', backgroundColor: '#fff' }}>
        <h4 style={{ marginTop: 0, marginBottom: '15px', color: '#007bff' }}>Cấu hình Quy tắc Đổi tên</h4>

        <div style={{ marginBottom: '15px' }}>
          <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '5px' }}>Chế độ Đổi tên (Mode):</label>
          <select 
            value={ruleMode} 
            onChange={(e) => setRuleMode(e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
          >
            <option value="SPLIT_SEPARATOR">1. Tách/Cắt theo Ký tự phân cách (Separator)</option>
            <option value="REPLACE_REMOVE">2. Tìm kiếm, Thay thế & Xóa chuỗi</option>
            <option value="PREFIX_SUFFIX">3. Thêm Tiền tố / Hậu tố (Prefix/Suffix)</option>
            <option value="SEQUENCE_NUMBERING">4. Đánh số thứ tự tự động (Auto-Index)</option>
            <option value="CASE_CONVERSION">5. Đổi kiểu chữ & Xóa dấu tiếng Việt</option>
          </select>
        </div>

        {/* Cấu hình chi tiết theo từng Mode */}
        {ruleMode === 'SPLIT_SEPARATOR' && (
          <div style={{ padding: '10px', backgroundColor: '#f1f8ff', borderRadius: '4px' }}>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'block', marginBottom: '3px' }}>Ký tự phân cách (Separator):</label>
              <input 
                type="text" 
                value={ruleConfig.separator} 
                onChange={(e) => handleConfigChange('separator', e.target.value)}
                style={{ width: '100px', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                placeholder="Vd: _ hoặc -"
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'block', marginBottom: '3px' }}>Hành động vị trí cắt:</label>
              <select 
                value={ruleConfig.action} 
                onChange={(e) => handleConfigChange('action', e.target.value)}
                style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
              >
                <option value="BEFORE_FIRST">Lấy phần TRƯỚC ký tự xuất hiện ĐẦU TIÊN</option>
                <option value="AFTER_FIRST">Lấy phần SAU ký tự xuất hiện ĐẦU TIÊN</option>
                <option value="BEFORE_LAST">Lấy phần TRƯỚC ký tự xuất hiện CUỐI CÙNG</option>
                <option value="AFTER_LAST">Lấy phần SAU ký tự xuất hiện CUỐI CÙNG</option>
                <option value="INDEX_N">Lấy đoạn thứ N cụ thể</option>
              </select>
            </div>
            {ruleConfig.action === 'INDEX_N' && (
              <div style={{ marginBottom: '10px' }}>
                <label style={{ display: 'block', marginBottom: '3px' }}>Vị trí đoạn N (Bắt đầu từ 1):</label>
                <input 
                  type="number" 
                  min="1"
                  value={ruleConfig.index_n} 
                  onChange={(e) => handleConfigChange('index_n', e.target.value)}
                  style={{ width: '80px', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                />
              </div>
            )}
          </div>
        )}

        {ruleMode === 'REPLACE_REMOVE' && (
          <div style={{ padding: '10px', backgroundColor: '#f1f8ff', borderRadius: '4px' }}>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'block', marginBottom: '3px' }}>Chuỗi cần tìm:</label>
              <input 
                type="text" 
                value={ruleConfig.search_text} 
                onChange={(e) => handleConfigChange('search_text', e.target.value)}
                style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                placeholder="Nhập từ cần tìm/xóa..."
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'block', marginBottom: '3px' }}>Chuỗi thay thế (Để rỗng nếu muốn XÓA):</label>
              <input 
                type="text" 
                value={ruleConfig.replace_text} 
                onChange={(e) => handleConfigChange('replace_text', e.target.value)}
                style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                placeholder="Chuỗi thay thế..."
              />
            </div>
            <div>
              <label style={{ cursor: 'pointer' }}>
                <input 
                  type="checkbox" 
                  checked={ruleConfig.match_case} 
                  onChange={(e) => handleConfigChange('match_case', e.target.checked)}
                  style={{ marginRight: '6px' }}
                />
                Phân biệt Hoa / Thường
              </label>
            </div>
          </div>
        )}

        {ruleMode === 'PREFIX_SUFFIX' && (
          <div style={{ padding: '10px', backgroundColor: '#f1f8ff', borderRadius: '4px' }}>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'block', marginBottom: '3px' }}>Tiền tố (Chèn vào ĐẦU tên file):</label>
              <input 
                type="text" 
                value={ruleConfig.prefix} 
                onChange={(e) => handleConfigChange('prefix', e.target.value)}
                style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                placeholder="Vd: [2026]_"
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'block', marginBottom: '3px' }}>Hậu tố (Chèn vào CUỐI tên file):</label>
              <input 
                type="text" 
                value={ruleConfig.suffix} 
                onChange={(e) => handleConfigChange('suffix', e.target.value)}
                style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                placeholder="Vd: _Final"
              />
            </div>
          </div>
        )}

        {ruleMode === 'SEQUENCE_NUMBERING' && (
          <div style={{ padding: '10px', backgroundColor: '#f1f8ff', borderRadius: '4px' }}>
            <div style={{ marginBottom: '10px' }}>
              <label style={{ display: 'block', marginBottom: '3px' }}>Tên gốc chung (Tùy chọn):</label>
              <input 
                type="text" 
                value={ruleConfig.base_name} 
                onChange={(e) => handleConfigChange('base_name', e.target.value)}
                style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                placeholder="Vd: BaoGia"
              />
            </div>
            <div style={{ display: 'flex', gap: '15px', marginBottom: '10px' }}>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '3px' }}>Số bắt đầu:</label>
                <input 
                  type="number" 
                  value={ruleConfig.start_number} 
                  onChange={(e) => handleConfigChange('start_number', parseInt(e.target.value) || 1)}
                  style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ display: 'block', marginBottom: '3px' }}>Số chữ số định dạng:</label>
                <select 
                  value={ruleConfig.padding_digits} 
                  onChange={(e) => handleConfigChange('padding_digits', parseInt(e.target.value))}
                  style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
                >
                  <option value={1}>1 (1, 2, 3...)</option>
                  <option value={2}>2 (01, 02, 03...)</option>
                  <option value={3}>3 (001, 002, 003...)</option>
                  <option value={4}>4 (0001, 0002...)</option>
                </select>
              </div>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '3px' }}>Vị trí chèn số thứ tự:</label>
              <select 
                value={ruleConfig.position} 
                onChange={(e) => handleConfigChange('position', e.target.value)}
                style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
              >
                <option value="SUFFIX">Chèn vào CUỐI tên file cũ</option>
                <option value="PREFIX">Chèn vào ĐẦU tên file cũ</option>
                <option value="REPLACE_ALL">Thay thế HOÀN TOÀN tên cũ bằng Tên gốc + Số</option>
              </select>
            </div>
          </div>
        )}

        {ruleMode === 'CASE_CONVERSION' && (
          <div style={{ padding: '10px', backgroundColor: '#f1f8ff', borderRadius: '4px' }}>
            <label style={{ display: 'block', marginBottom: '3px' }}>Kiểu chuyển đổi:</label>
            <select 
              value={ruleConfig.case_type} 
              onChange={(e) => handleConfigChange('case_type', e.target.value)}
              style={{ width: '100%', padding: '6px', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              <option value="UPPER">IN HOA TOÀN BỘ (UPPERCASE)</option>
              <option value="LOWER">in thường toàn bộ (lowercase)</option>
              <option value="TITLE">Viết Hoa Chữ Cái Đầu (Title Case)</option>
              <option value="REMOVE_ACCENTS">Xóa dấu Tiếng Việt (Báo giá ➔ Bao gia)</option>
            </select>
          </div>
        )}
      </div>

      {/* 3. BẢNG PREVIEW DỰ KIẾN */}
      {selectedFiles.length > 0 && (
        <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '6px', backgroundColor: '#fff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h4 style={{ margin: 0, color: '#007bff' }}>Xem trước kết quả đổi tên (Preview)</h4>
            {loadingPreview && <span style={{ fontSize: '13px', color: '#666' }}>Đang tính toán...</span>}
          </div>

          {previewData && previewData.has_conflict && (
            <div style={{ padding: '8px 12px', backgroundColor: '#f8d7da', color: '#721c24', borderRadius: '4px', marginBottom: '10px', fontSize: '13px' }}>
              ⚠️ Cảnh báo: Phát hiện xung đột trùng tên giữa các file! Vui lòng điều chỉnh quy tắc.
            </div>
          )}

          <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #eee' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f2f2f2', borderBottom: '2px solid #ddd' }}>
                  <th style={{ padding: '8px', textAlign: 'left' }}>STT</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Tên file gốc</th>
                  <th style={{ padding: '8px', textAlign: 'center' }}>➔</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Tên file mới dự kiến</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {previewData?.items?.map((item, idx) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #eee', backgroundColor: item.status === 'CONFLICT' ? '#fff3cd' : 'transparent' }}>
                    <td style={{ padding: '8px' }}>{idx + 1}</td>
                    <td style={{ padding: '8px', color: '#555' }}>{item.original_name}</td>
                    <td style={{ padding: '8px', textAlign: 'center', color: '#007bff' }}>➔</td>
                    <td style={{ padding: '8px', fontWeight: 'bold', color: item.status === 'CONFLICT' ? '#dc3545' : '#28a745' }}>
                      {item.new_name}
                    </td>
                    <td style={{ padding: '8px', fontSize: '12px' }}>
                      {item.status === 'OK' ? (
                        <span style={{ color: '#28a745' }}>✓ Hợp lệ</span>
                      ) : (
                        <span style={{ color: '#dc3545', fontWeight: 'bold' }}>{item.message}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. NÚT THỰC HIỆN ĐỔI TÊN & TẢI ZIP */}
      <div style={{ textAlign: 'right' }}>
        <button
          onClick={handleExecuteRename}
          disabled={loadingProcess || selectedFiles.length === 0}
          style={{
            padding: '12px 25px',
            backgroundColor: loadingProcess || selectedFiles.length === 0 ? '#ccc' : '#28a745',
            color: '#fff',
            border: 'none',
            borderRadius: '5px',
            fontSize: '16px',
            fontWeight: 'bold',
            cursor: loadingProcess || selectedFiles.length === 0 ? 'not-allowed' : 'pointer',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
        >
          {loadingProcess ? 'Đang đóng gói ZIP...' : 'Xác nhận Đổi tên & Tải về ZIP'}
        </button>
      </div>
    </div>
  );
}