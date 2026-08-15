import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/excel/multi-lookup';

export const excelService = {
  // Đọc thông tin sheets & columns của file
  inspectFile: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_BASE}/inspect`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Lấy cột khi đổi sheet
  getSheetColumns: async (file, sheetName) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('sheet_name', sheetName);
    const response = await axios.post(`${API_BASE}/get-columns`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Xem trước kết quả
  previewLookup: async (params) => {
    const formData = new FormData();
    formData.append('file', params.file);
    formData.append('sheet_name', params.sheetName);
    formData.append('lookup_column', params.lookupColumn);
    formData.append('lookup_values', params.lookupValues);
    formData.append('match_mode', params.matchMode);
    formData.append('case_sensitive', params.caseSensitive);

    const response = await axios.post(`${API_BASE}/preview-lookup`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Thực hiện lọc và tải file Excel kết quả
  processMultiLookup: async (params) => {
    const formData = new FormData();
    formData.append('file', params.file);
    formData.append('sheet_name', params.sheetName);
    formData.append('lookup_column', params.lookupColumn);
    formData.append('lookup_values', params.lookupValues);
    formData.append('match_mode', params.matchMode);
    formData.append('case_sensitive', params.caseSensitive);

    const response = await axios.post(`${API_BASE}/multi-lookup`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob'
    });
    return response;
  }
};