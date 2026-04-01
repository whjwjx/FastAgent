import client from './client';
import EventSource from 'react-native-sse';

export const sendChatMessage = async (message: string) => {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const response = await client.post('/assistant/', { message, timezone });
  return response.data;
};

export const createChatStream = (message: string, token: string, history: any[] = []) => {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  // Use client.defaults.baseURL to construct full URL
  const url = `${client.defaults.baseURL}/assistant/stream`;
  
  return new EventSource(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ message, timezone, history })
  });
};

export const createConfirmStream = (actionId: string, toolCalls: any[], isCancelled: boolean, token: string, history: any[] = []) => {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const url = `${client.defaults.baseURL}/assistant/stream`;
  
  return new EventSource(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ 
      is_confirmation: true,
      action_id: actionId,
      tool_calls: toolCalls,
      is_cancelled: isCancelled,
      timezone, 
      history 
    })
  });
};

export const getThoughts = async (thought_type?: string) => {
  const params = thought_type ? { thought_type } : {};
  const response = await client.get('/thoughts/', { params });
  return response.data;
};

export const getSchedules = async () => {
  const response = await client.get('/schedules/');
  return response.data;
};
