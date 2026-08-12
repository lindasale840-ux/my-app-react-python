import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const compressPdfApi = async (file, mode = 'normal') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mode', mode);

  const response = await axios.post(`${API_BASE_URL}/api/pdf/compress`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
    timeout: 120000, // Chờ tối đa 2 phút khi nén file lớn
  });

  return {
    blob: response.data,
    message: response.headers['x-compress-message'],
    oldSize: response.headers['x-old-size'],
    newSize: response.headers['x-new-size']
  };
};