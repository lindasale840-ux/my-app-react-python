import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/pdf-to-excel';

export const analyzeBatchPdfApi = async (fileList) => {
  const formData = new FormData();
  Array.from(fileList).forEach((file) => {
    formData.append('files', file);
  });

  const response = await axios.post(`${API_BASE_URL}/analyze-batch`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  });
  return response.data;
};

export const exportExcelApi = async (exportMode, matrices) => {
  const response = await axios.post(
    `${API_BASE_URL}/export-excel`,
    {
      export_mode: exportMode,
      matrices: matrices,
    },
    {
      responseType: 'blob',
      timeout: 120000,
    }
  );
  return response.data;
};