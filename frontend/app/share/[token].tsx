import React, { useEffect, useState } from 'react';
import { StyleSheet, View, Text, ActivityIndicator } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { getSharedGardenByToken, SharedGardenResponse } from '../../api/garden';
import { GardenFeed } from '../../components/GardenFeed';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function SharedGardenByToken() {
  const { token } = useLocalSearchParams<{ token: string }>();
  const [data, setData] = useState<SharedGardenResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      fetchGarden();
    }
  }, [token]);

  const fetchGarden = async () => {
    try {
      setLoading(true);
      const res = await getSharedGardenByToken(token!);
      setData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Garden not found");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error || "Not Found"}</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <GardenFeed 
        thoughts={data.thoughts} 
        mode="visitor" 
        ownerInfo={{
          nickname: data.owner_nickname,
          avatar: data.owner_avatar,
          bio: data.owner_bio
        }}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#FF3B30',
  }
});
