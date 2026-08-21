// src/services/pdfScanSplitService.js
import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/pdf_scan_split';

// 1. Hàm cũ dành cho Tab 1 (Giữ nguyên 100% tên và logic cũ)
export const processPdfScanSplit = async (pdfFile, excelFile, namingType) => {
  const formData = new FormData();
  formData.append('pdf_file', pdfFile);
  formData.append('excel_file', excelFile);
  formData.append('naming_type', namingType);

  const response = await axios.post(`${BASE_URL}/process`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob', // Xử lý nhận file zip
  });

  return response.data;
};

// 2. Hàm mới thêm vào dành cho Tab 2 (Kiểm tra GCN thiếu / thừa)
export const checkMissingGcn = async (pdfFile, excelFile) => {
  const formData = new FormData();
  formData.append('pdf_file', pdfFile);
  formData.append('excel_file', excelFile);

  const response = await axios.post(`${BASE_URL}/check_missing`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};