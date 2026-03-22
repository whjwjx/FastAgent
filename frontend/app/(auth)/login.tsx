import { View, Text, TextInput, Button, StyleSheet, Alert } from 'react-native';
import { useState } from 'react';
import { router } from 'expo-router';
import { login } from '../../api/auth';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    try {
      const data = await login(username, password);
      await AsyncStorage.setItem('userToken', data.access_token);
      router.replace('/(tabs)');
    } catch (error) {
      Alert.alert('Login Failed', 'Incorrect username or password');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>FastAIStack</Text>
      <TextInput
        style={styles.input}
        placeholder="Username"
        value={username}
        onChangeText={setUsername}
        autoCapitalize="none"
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <Button title="Login" onPress={handleLogin} />
      <Button title="Register" onPress={() => router.push('/(auth)/register')} color="gray" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20, backgroundColor: '#fff' },
  title: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', marginBottom: 40, color: '#333' },
  input: { borderWidth: 1, borderColor: '#ccc', padding: 10, marginBottom: 20, borderRadius: 5, backgroundColor: '#f9f9f9', color: '#333' }
});
