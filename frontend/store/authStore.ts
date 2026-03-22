import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface User {
  id: number;
  username: string;
  email: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  signIn: (token: string, user?: User) => Promise<void>;
  signOut: () => Promise<void>;
  restoreToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isLoading: true,
  
  signIn: async (token: string, user?: User) => {
    try {
      await AsyncStorage.setItem('userToken', token);
      if (user) {
        await AsyncStorage.setItem('userInfo', JSON.stringify(user));
      }
      set({ token, user: user || null });
    } catch (e) {
      console.error('Failed to save token', e);
    }
  },
  
  signOut: async () => {
    try {
      await AsyncStorage.removeItem('userToken');
      await AsyncStorage.removeItem('userInfo');
      set({ token: null, user: null });
    } catch (e) {
      console.error('Failed to remove token', e);
    }
  },
  
  restoreToken: async () => {
    try {
      const token = await AsyncStorage.getItem('userToken');
      const userInfoString = await AsyncStorage.getItem('userInfo');
      let user = null;
      if (userInfoString) {
        user = JSON.parse(userInfoString);
      }
      set({ token, user, isLoading: false });
    } catch (e) {
      console.error('Failed to restore token', e);
      set({ isLoading: false });
    }
  }
}));
