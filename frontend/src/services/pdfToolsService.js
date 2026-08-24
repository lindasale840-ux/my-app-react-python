import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/pdf-tools';

export const pdfToolsService = {
  // Trích xuất tên file PDF ra Excel
  extractPdfNames: async (files) => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await axios.post(`${BASE_URL}/extract-names`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob'
    });
    return response.data;
  },

  // Đọc danh sách tiêu đề cột từ file Excel
  getExcelColumns: async (excelFile) => {
    const formData = new FormData();
    formData.append('excel_file', excelFile);

    const response = await axios.post(`${BASE_URL}/get-columns`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Đối chiếu PDF với Excel
  comparePdfWithExcel: async (excelFile, columnName, pdfFiles) => {
    const formData = new FormData();
    formData.append('excel_file', excelFile);
    formData.append('column_name', columnName);
    pdfFiles.forEach((file) => {
      formData.append('pdf_files', file);
    });

    const response = await axios.post(`${BASE_URL}/compare-with-excel`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob'
    });
    return response.data;
  }
};