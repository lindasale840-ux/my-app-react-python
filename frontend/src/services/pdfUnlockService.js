import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/pdf-unlock';

export const unlockPdfApi = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(`${BASE_URL}/unlock`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob', // Bắt buộc để nhận luồng Stream/Blob tải file
  });

  return response.data;
};