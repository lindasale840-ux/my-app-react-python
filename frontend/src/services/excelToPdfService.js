import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/excel-to-pdf';

// API 1: Đọc danh sách Sheet của các file đã chọn
export const inspectExcelSheets = async (files) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await axios.post(`${API_BASE_URL}/inspect-sheets`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data; // Trả về { success: true, data: [...] }
};

// API 2: Chuyển đổi Excel sang PDF (Cập nhật hỗ trợ sheet_selection_map)
export const convertExcelToPdf = async (files, exportType, selectedSheetsMap = {}, customFilename = '') => {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append('files', file);
  });
  formData.append('export_type', exportType);

  // Đóng gói cấu hình file_configs khớp với cách parse ở Backend
  const fileConfigs = {};
  files.forEach((file, index) => {
    fileConfigs[file.name] = {
      sheets: selectedSheetsMap[file.name] || [],
    };
  });

  const options = {
    global_custom_name: customFilename,
    file_configs: fileConfigs,
  };

  formData.append('options', JSON.stringify(options));

  const response = await axios.post(`${API_BASE_URL}/convert`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob',
  });

  return response;
};