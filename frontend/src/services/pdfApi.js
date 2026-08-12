import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

export const mergePdfsApi = async (files) => {
  const formData = new FormData();
  
  // Đưa tất cả các file vào FormData với key 'files' (khớp với tham số backend)
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  const response = await axios.post(`${API_BASE_URL}/api/pdf/merge`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob', // Bắt buộc chọn 'blob' để nhận file binary trả về
  });

  return response.data;
};