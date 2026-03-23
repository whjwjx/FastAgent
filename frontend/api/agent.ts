import client from './client';
import EventSource from 'react-native-sse';

export const sendChatMessage = async (message: string) => {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const response = await client.post('/assistant/', { message, timezone });
  return response.data;
};

export const createChatStream = (message: string, token: string) => {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  // Use client.defaults.baseURL to construct full URL
  const url = `${client.defaults.baseURL}/assistant/stream`;
  
  return new EventSource(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ message, timezone })
  });
};

export const getThoughts = async () => {
  const response = await client.get('/thoughts/');
  return response.data;
};

export const getSchedules = async () => {
  const response = await client.get('/schedules/');
  return response.data;
};
