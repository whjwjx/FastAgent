import { View, Text, TextInput, Button, StyleSheet, Alert } from 'react-native';
import { useState } from 'react';
import { router } from 'expo-router';
import { register } from '../../api/auth';

export default function RegisterScreen() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleRegister = async () => {
    try {
      await register(username, email, password);
      Alert.alert('Success', 'Registration successful, please login');
      router.back();
    } catch (error) {
      Alert.alert('Registration Failed', 'Could not register. Please try again.');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Register</Text>
      <TextInput
        style={styles.input}
        placeholder="Username"
        value={username}
        onChangeText={setUsername}
        autoCapitalize="none"
      />
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <Button title="Register" onPress={handleRegister} />
      <Button title="Back to Login" onPress={() => router.back()} color="gray" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20, backgroundColor: '#fff' },
  title: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', marginBottom: 40, color: '#333' },
  input: { borderWidth: 1, borderColor: '#ccc', padding: 10, marginBottom: 20, borderRadius: 5, backgroundColor: '#f9f9f9', color: '#333' }
});
