import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const reducePdfApi = async (file, dpi = 120, quality = 70) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("dpi", dpi);
  formData.append("quality", quality);

  const response = await axios.post(`${API_BASE_URL}/api/pdf/reduce`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    responseType: "blob",
  });

  const oldSize = response.headers["x-old-size"];
  const newSize = response.headers["x-new-size"];

  return {
    filename: file.name,
    blob: response.data,
    oldSize,
    newSize,
  };
};

// HÀM MỚI: Xử lý danh sách file
export const reducePdfBatchApi = async (files, dpi = 120, quality = 70, onProgress) => {
  const results = [];
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    try {
      const res = await reducePdfApi(file, dpi, quality);
      results.push({ success: true, ...res });
    } catch (err) {
      results.push({
        success: false,
        filename: file.name,
        error: err.response?.data?.detail || err.message
      });
    }

    // Callback báo tiến trình (ví dụ: đã xong 2/5 file)
    if (onProgress) {
      onProgress(i + 1, files.length);
    }
  }

  return results;
};