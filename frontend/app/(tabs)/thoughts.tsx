import { useEffect, useState } from 'react';
import { StyleSheet, FlatList, Text, View, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getThoughts } from '../../api/agent';
import { useIsFocused } from '@react-navigation/native';

export default function ThoughtsScreen() {
  const [thoughts, setThoughts] = useState<{id: string, original_content: string, refined_content?: string, tags?: string[], created_at: string}[]>([]);
  const [loading, setLoading] = useState(true);
  const isFocused = useIsFocused();

  useEffect(() => {
    if (isFocused) {
      fetchThoughts();
    }
  }, [isFocused]);

  const fetchThoughts = async () => {
    try {
      setLoading(true);
      const data = await getThoughts();
      setThoughts(data);
    } catch (error) {
      console.error("Error fetching thoughts", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading && thoughts.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.header}>My Thoughts</Text>
      <FlatList
        data={thoughts}
        keyExtractor={item => item.id.toString()}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.content}>{item.original_content}</Text>
            {item.tags && item.tags.length > 0 ? <Text style={styles.tags}>Tags: {item.tags.join(', ')}</Text> : null}
            <Text style={styles.date}>{new Date(item.created_at).toLocaleString()}</Text>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.emptyText}>No thoughts recorded yet.</Text>}
        contentContainerStyle={styles.listContent}
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
  },
  listContent: {
    padding: 16,
  },
  card: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  content: {
    fontSize: 16,
    marginBottom: 8,
  },
  tags: {
    fontSize: 12,
    color: '#007AFF',
    marginBottom: 4,
  },
  date: {
    fontSize: 12,
    color: '#888',
  },
  emptyText: {
    textAlign: 'center',
    color: '#888',
    marginTop: 40,
  }
});
