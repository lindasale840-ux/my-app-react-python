// src/services/pdfExcelService.js
import axios from 'axios';

const BASE_URL = 'http://localhost:8000/api/pdf-excel';

export const comparePdfExcel = async (pdfFiles, excelFile, compareType) => {
  const formData = new FormData();
  for (let i = 0; i < pdfFiles.length; i++) {
    formData.append('pdf_files', pdfFiles[i]);
  }
  formData.append('excel_file', excelFile);
  formData.append('compare_type', compareType);

  const response = await axios.post(`${BASE_URL}/compare`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const exportReportExcel = async (pdfFiles, excelFile, compareType) => {
  const formData = new FormData();
  for (let i = 0; i < pdfFiles.length; i++) {
    formData.append('pdf_files', pdfFiles[i]);
  }
  formData.append('excel_file', excelFile);
  formData.append('compare_type', compareType);

  try {
    const response = await axios.post(`${BASE_URL}/export-report`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      responseType: 'blob', // Nhận nhị phân file excel
    });

    // Tạo link tải file
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `BaoCao_DoiChieu_${compareType}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    // KỸ THUẬT QUAN TRỌNG: Nếu lỗi từ server trả về dạng Blob (do responseType: 'blob')
    if (err.response && err.response.data instanceof Blob) {
      const errorText = await err.response.data.text();
      try {
        const errorJson = JSON.parse(errorText);
        // Bắt và ném lại chuỗi lỗi cụ thể từ FastAPI
        throw new Error(errorJson.detail || 'Có lỗi xảy ra từ máy chủ.');
      } catch (parseErr) {
        throw new Error('Không thể đọc dữ liệu phản hồi từ máy chủ.');
      }
    }
    throw err;
  }
};