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

// Services mới cho Tab 2
export const getExcelColumnsService = async (excelFile) => {
  const formData = new FormData();
  formData.append('excel_file', excelFile);

  const response = await axios.post(`${BASE_URL}/get-excel-columns`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const mergeByExcelService = async (filesA, filesB, excelFile, columnA, columnB) => {
  const formData = new FormData();

  formData.append('column_a', columnA);
  formData.append('column_b', columnB);
  formData.append('excel_file', excelFile);

  Array.from(filesA).forEach((file) => {
    formData.append('files_a', file);
  });

  Array.from(filesB).forEach((file) => {
    formData.append('files_b', file);
  });

  const response = await axios.post(`${BASE_URL}/merge-by-excel`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob',
  });

  return response;
};