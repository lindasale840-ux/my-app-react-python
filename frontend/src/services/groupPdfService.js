import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// API 1: Đọc xem danh sách cột trong Excel
export const parseExcelColumnsApi = async (excelFile) => {
  const formData = new FormData();
  formData.append('excel_file', excelFile);

  const response = await axios.post(`${API_BASE_URL}/api/pdf/parse-excel-cols`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// API 2: Thực hiện Gom nhóm & nhận file ZIP
export const groupByExcelApi = async (excelFile, pdfFiles, matchColIdx, targetColIdx) => {
  const formData = new FormData();
  formData.append('excel_file', excelFile);
  
  Array.from(pdfFiles).forEach((file) => {
    formData.append('pdf_files', file);
  });
  
  formData.append('match_col_idx', matchColIdx);
  formData.append('target_col_idx', targetColIdx);

  const response = await axios.post(`${API_BASE_URL}/api/pdf/group-by-excel`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
  });

  const rawSummary = response.headers['x-group-summary'];
  const summary = rawSummary ? decodeURIComponent(rawSummary) : '';

  return {
    blob: response.data,
    summary,
  };
};