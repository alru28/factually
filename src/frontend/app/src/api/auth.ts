import axios from 'axios';

interface ApiKey {
  created_at: string;
  id: number;
  key: string;
  expires_at: string;
}

const apiClient = axios.create({
  baseURL: import.meta.env.API_GATEWAY_URL || "http://localhost:8000",
  headers: {
    'Content-Type': 'application/json',
  },
});

export const registerUser = async (email: string, password: string) => {
  return apiClient.post('/auth/register', { email, password });
};

export const loginUser = async (email: string, password: string) => {
  const response = await apiClient.post('/auth/login', { email, password });
  localStorage.setItem('token', response.data.access_token);
  return response;
};

export const requestPasswordReset = (email: string) => {
  return apiClient.post('/auth/password-reset/request', { email });
};

export const confirmPasswordReset = (token: string, new_password: string) => {
  return apiClient.post('/auth/password-reset/confirm', { token, new_password });
};

export const verifyEmail = (token: string) => {
  return apiClient.post('/auth/verify-email', { token });
};

export const getApiKeys = () => {
  return apiClient.get<{ api_keys: ApiKey[] }>('/auth/apikeys', {
    ...authHeader(),
    validateStatus: (status) => status === 200 || status === 404
  });
};

export const generateApiKey = () => {
  return apiClient.post('/auth/apikeys', {}, authHeader());
};

export const renewApiKey = (api_key_id: number) => {
  return apiClient.post(`/auth/apikeys/${api_key_id}/renew`, {}, authHeader());
};

export const revokeApiKey = (api_key_id: number) => {
  return apiClient.delete(`/auth/apikeys/${api_key_id}`, authHeader());
};

const authHeader = () => {
  const token = localStorage.getItem('token');
  return { headers: { Authorization: `Bearer ${token}` } };
};
