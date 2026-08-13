import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/gcn_locator';

export const processGcnLocator = async (pdfFile, requestedGcnText) => {
  const formData = new FormData();
  formData.append('pdf_file', pdfFile);
  formData.append('requested_gcn_text', requestedGcnText);

  const response = await axios.post(`${API_BASE_URL}/locate`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob',
  });

  return response.data;
};