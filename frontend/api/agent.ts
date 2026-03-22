import client from './client';

export const sendChatMessage = async (message: string) => {
  const response = await client.post('/assistant/', { message });
  return response.data;
};

export const getThoughts = async () => {
  const response = await client.get('/thoughts/');
  return response.data;
};

export const getSchedules = async () => {
  const response = await client.get('/schedules/');
  return response.data;
};
