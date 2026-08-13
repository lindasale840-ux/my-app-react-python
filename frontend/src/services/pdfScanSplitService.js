// src/services/pdfScanSplitService.js
import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/pdf_scan_split';

export const processPdfScanSplit = async (pdfFile, excelFile, namingType) => {
  const formData = new FormData();
  formData.append('pdf_file', pdfFile);
  formData.append('excel_file', excelFile);
  formData.append('naming_type', namingType);

  const response = await axios.post(`${BASE_URL}/process`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob', // Để xử lý nhận file zip trả về dạng stream
  });

  return response.data;
};