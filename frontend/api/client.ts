import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// For local development, Android emulator needs 10.0.2.2 instead of localhost
// iOS simulator and Web can use localhost
const getBaseUrl = () => {
  if (__DEV__) {
    if (Platform.OS === 'android') {
      return 'http://10.0.2.2:8000/api';
    }
    return 'http://localhost:8000/api';
  }
  // Production URL here
  return 'https://api.yourdomain.com/api';
};

const client = axios.create({
  baseURL: getBaseUrl(),
  timeout: 10000,
});

// Add a request interceptor to inject the token
client.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('userToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default client;
