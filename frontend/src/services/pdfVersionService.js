import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const downgradePdfBatchApi = async (files, compatibility = "1.4") => {
  const formData = new FormData();
  
  // Đính kèm danh sách nhiều file vào FormData
  files.forEach((file) => {
    formData.append("files", file);
  });
  
  formData.append("compatibility", compatibility);

  const response = await axios.post(`${API_BASE_URL}/api/pdf-version/downgrade-batch`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    responseType: "blob", // Nhận về file ZIP dạng Blob
  });

  return response.data;
};