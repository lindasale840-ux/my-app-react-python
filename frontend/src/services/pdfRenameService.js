import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/pdf-rename';

export const pdfRenameService = {
  // Lấy danh sách cột từ File Excel
  getColumns: async (fileExcel) => {
    const formData = new FormData();
    formData.append('file_excel', fileExcel);

    const response = await axios.post(`${API_BASE_URL}/preview-columns`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Thực thi Đổi tên PDF & Nhận file ZIP
  processRename: async (fileExcel, pdfFiles, matchCol, primaryCol, fallbackCol) => {
    const formData = new FormData();
    formData.append('file_excel', fileExcel);

    if (pdfFiles && pdfFiles.length > 0) {
      Array.from(pdfFiles).forEach((file) => {
        formData.append('pdf_files', file);
      });
    }

    formData.append('match_col', matchCol);
    formData.append('primary_name_col', primaryCol);
    formData.append('fallback_name_col', fallbackCol);

    const response = await axios.post(`${API_BASE_URL}/process-rename`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob', // Bắt buộc để nhận File ZIP
    });

    return response.data;
  }
};