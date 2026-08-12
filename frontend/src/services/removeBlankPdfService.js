import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const removeBlankPagesApi = async (files, threshold = 0.98) => {
  const formData = new FormData();
  
  // Appends danh sách nhiều file
  Array.from(files).forEach((file) => {
    formData.append("files", file);
  });
  
  formData.append("threshold", threshold);

  const response = await axios.post(`${API_BASE_URL}/api/pdf/remove-blank-pages`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    responseType: "blob",
  });

  const rawSummary = response.headers["x-remove-summary"];
  const summary = rawSummary ? decodeURIComponent(rawSummary) : "";
  const isZip = response.headers["content-type"] === "application/zip";

  return {
    blob: response.data,
    summary,
    isZip,
  };
};