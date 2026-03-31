import { useEffect, useState, useCallback } from 'react';
import { StyleSheet, View, Text, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getThoughts } from '../../api/agent';
import { useIsFocused } from '@react-navigation/native';
import { GardenFeed } from '../../components/GardenFeed';

export default function ThoughtsScreen() {
  const [thoughts, setThoughts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const isFocused = useIsFocused();

  const fetchThoughts = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getThoughts();
      setThoughts(data);
    } catch (error) {
      console.error("Error fetching thoughts", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isFocused) {
      fetchThoughts();
    }
  }, [isFocused, fetchThoughts]);

  if (loading && thoughts.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.header}>My Thoughts</Text>
      <GardenFeed 
        thoughts={thoughts} 
        mode="owner" 
        onRefresh={fetchThoughts} 
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    padding: 20,
    backgroundColor: '#fff',
  }
});
