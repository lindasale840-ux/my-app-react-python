import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// API 1: Lấy danh sách ảnh Thumbnail
export const getPdfThumbnailsApi = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(`${API_BASE_URL}/api/pdf/thumbnails`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  });

  return response.data;
};

// API 2: Gửi điểm cắt và tải file ZIP
export const splitPdfByRangesApi = async (file, rangesText) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('ranges_text', rangesText);

  const response = await axios.post(`${API_BASE_URL}/api/pdf/split-ranges`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
    timeout: 120000,
  });

  return response.data;
};