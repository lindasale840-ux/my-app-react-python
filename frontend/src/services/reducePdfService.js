import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const reducePdfApi = async (file, dpi = 120, quality = 70) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("dpi", dpi);
  formData.append("quality", quality);

  // SỬA: Dùng backtick `...` thay vì nháy đơn '...' và bỏ prefix /api thừa
  const response = await axios.post(`${API_BASE_URL}/api/pdf/reduce`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    responseType: "blob",
  });

  const oldSize = response.headers["x-old-size"];
  const newSize = response.headers["x-new-size"];

  return {
    blob: response.data,
    oldSize,
    newSize,
  };
};