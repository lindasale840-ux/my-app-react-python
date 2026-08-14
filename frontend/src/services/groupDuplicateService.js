import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/group-duplicate';

export const groupDuplicateFilesService = async (files) => {
  const formData = new FormData();
  Array.from(files).forEach((file) => {
    formData.append('files', file);
  });

  const response = await axios.post(`${BASE_URL}/process`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob',
  });

  return response;
};