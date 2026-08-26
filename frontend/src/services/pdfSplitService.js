import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/pdfsplit';

export const pdfSplitService = {
  splitSmart: async (pdfFile, keyword, namingType, includePageCount = false) => {
    const formData = new FormData();
    formData.append('pdf_file', pdfFile);
    formData.append('keyword', keyword);
    formData.append('naming_type', namingType);
    formData.append('include_page_count', includePageCount); // <-- THÊM THAM SỐ NÀY

    const response = await axios.post(`${BASE_URL}/split-smart`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob'
    });
    return response.data;
  },

  splitExcel: async (pdfFile, excelFile, keyword, namingType, includePageCount = false) => {
    const formData = new FormData();
    formData.append('pdf_file', pdfFile);
    formData.append('excel_file', excelFile);
    formData.append('keyword', keyword);
    formData.append('naming_type', namingType);
    formData.append('include_page_count', includePageCount); // <-- THÊM THAM SỐ NÀY

    const response = await axios.post(`${BASE_URL}/split-excel`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob'
    });
    return response.data;
  }
};