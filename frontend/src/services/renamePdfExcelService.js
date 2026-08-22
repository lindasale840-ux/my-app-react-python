import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/rename-pdf-excel';

export const parseExcelColumnsApi = async (excelFile) => {
  const formData = new FormData();
  formData.append('excel_file', excelFile);
  const response = await axios.post(`${API_BASE_URL}/parse-excel-columns`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const previewRenameApi = async (excelFile, pdfFiles, keyColumn, targetColumns, separator) => {
  const formData = new FormData();
  formData.append('excel_file', excelFile);
  Array.from(pdfFiles).forEach((file) => {
    formData.append('pdf_files', file);
  });
  formData.append('key_column', keyColumn);
  formData.append('target_columns', JSON.stringify(targetColumns));
  formData.append('separator', separator);

  const response = await axios.post(`${API_BASE_URL}/preview-rename`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const executeRenameZipApi = async (excelFile, pdfFiles, keyColumn, targetColumns, separator) => {
  const formData = new FormData();
  formData.append('excel_file', excelFile);
  Array.from(pdfFiles).forEach((file) => {
    formData.append('pdf_files', file);
  });
  formData.append('key_column', keyColumn);
  formData.append('target_columns', JSON.stringify(targetColumns));
  formData.append('separator', separator);

  const response = await axios.post(`${API_BASE_URL}/execute-rename-zip`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
  });
  return response.data;
};