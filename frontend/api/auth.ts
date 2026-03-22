import client from './client';

export const login = async (username, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  const response = await client.post('/auth/login', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const register = async (username, email, password) => {
  const response = await client.post('/auth/register', { username, email, password });
  return response.data;
};
