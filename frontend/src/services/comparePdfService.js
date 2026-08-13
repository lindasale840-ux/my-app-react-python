import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Đọc danh sách cột Excel để tạo Dropdown
export const parseExcelColumnsApi = async (excelFile) => {
  const formData = new FormData();
  formData.append('excel_file', excelFile);

  const response = await axios.post(`${API_BASE_URL}/api/pdf/parse-excel-cols`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// Gọi API Đối chiếu Excel vs PDF
export const compareExcelVsPdfApi = async ({
  excelFile,
  pdfFiles,
  columnIndex,
  compareMode,
  isScan,
}) => {
  const formData = new FormData();
  formData.append('excel_file', excelFile);

  Array.from(pdfFiles).forEach((file) => {
    formData.append('pdf_files', file);
  });

  formData.append('column_index', columnIndex);
  formData.append('compare_mode', compareMode);
  formData.append('is_scan', isScan ? 'true' : 'false');

  const response = await axios.post(`${API_BASE_URL}/api/pdf/compare-excel-vs-pdf`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return response.data;
};