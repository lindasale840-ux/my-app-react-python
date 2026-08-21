import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/excel-to-pdf';

export const convertExcelToPdf = async (files, exportType) => {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append('files', file);
  });
  formData.append('export_type', exportType);

  const response = await axios.post(`${API_BASE_URL}/convert`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob', // Bắt buộc blob để nhận file nhị phân (ZIP/PDF)
  });

  return response;
};