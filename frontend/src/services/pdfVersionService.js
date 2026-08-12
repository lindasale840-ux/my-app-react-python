import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const downgradePdfVersionApi = async (file, compatibility = "1.4") => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("compatibility", compatibility);

  const response = await axios.post(`${API_BASE_URL}/api/pdf/downgrade-version`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    responseType: "blob",
  });

  return response.data;
};