import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/excel';

export const excelFormService = {
  // Lấy danh sách cột từ file Tổng Excel
  getColumns: async (fileTong) => {
    const formData = new FormData();
    formData.append('file_tong', fileTong);

    const response = await axios.post(`${API_BASE_URL}/preview-columns`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Thực thi xử lý Form & Nhận file ZIP
  processForm: async (fileTong, fileForm, pdfFiles, config) => {
    const formData = new FormData();
    formData.append('file_tong', fileTong);
    formData.append('file_form', fileForm);
    
    if (pdfFiles && pdfFiles.length > 0) {
      Array.from(pdfFiles).forEach((file) => {
        formData.append('pdf_files', file);
      });
    }

    formData.append('config', JSON.stringify(config));

    const response = await axios.post(`${API_BASE_URL}/process-form`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob', // Bắt buộc blob để nhận file nhị phân ZIP
    });

    return response.data;
  }
};