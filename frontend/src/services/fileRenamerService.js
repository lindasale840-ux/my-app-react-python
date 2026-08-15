import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/file-renamer';

export const previewFileRename = async (files, ruleMode, ruleConfig) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  formData.append('rule_mode', ruleMode);
  formData.append('rule_config', JSON.stringify(ruleConfig));

  const response = await axios.post(`${API_BASE_URL}/preview`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const processFileRename = async (files, ruleMode, ruleConfig) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  formData.append('rule_mode', ruleMode);
  formData.append('rule_config', JSON.stringify(ruleConfig));

  const response = await axios.post(`${API_BASE_URL}/process`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
  });
  return response.data;
};