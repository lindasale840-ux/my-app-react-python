import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const collectAndZipPdf = async (formData) => {
  const response = await axios.post(`${API_BASE_URL}/api/pdf/collect-and-zip`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob', // Bắt buộc để tải về file binary ZIP
  });
  return response;
};