import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { useAuthStore } from '../store/authStore';

// 获取后端的 API Base URL，支持通过环境变量自定义，方便测试与部署
const getBaseUrl = () => {
  // 1. 如果通过环境变量显式指定了 API URL，优先级最高
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }

  // 2. 开发环境下的自动判断逻辑
  if (__DEV__) {
    // 尝试从 Expo Constants 获取当前局域网 IP（适用于真机通过 LAN 调试）
    const debuggerHost = Constants.expoConfig?.hostUri;
    if (debuggerHost) {
      const localhost = debuggerHost.split(':')[0];
      return `http://${localhost}:8000/api`;
    }
    
    // 降级方案：针对模拟器或默认本地环境
    if (Platform.OS === 'android') {
      return 'http://10.0.2.2:8000/api'; // Android 模拟器专属别名
    }
    return 'http://localhost:8000/api'; // iOS 模拟器或 Web
  }
  
  // 3. 生产环境默认 URL（如果没有配置环境变量）
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

// Add a response interceptor to handle 401 errors
client.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login
      await useAuthStore.getState().signOut();
    }
    return Promise.reject(error);
  }
);

export default client;
