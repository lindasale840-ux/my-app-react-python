import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/pdf_merge';

export const mergeByNameService = async (filesA, filesB) => {
  const formData = new FormData();

  Array.from(filesA).forEach((file) => {
    formData.append('files_a', file);
  });

  Array.from(filesB).forEach((file) => {
    formData.append('files_b', file);
  });

  const response = await axios.post(`${BASE_URL}/merge-by-name`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob', // Bắt buộc nhận dạng blob để tải file ZIP
  });

  return response;
};