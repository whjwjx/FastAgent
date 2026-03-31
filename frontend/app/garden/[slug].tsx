import React, { useEffect, useState } from 'react';
import { StyleSheet, View, Text, ActivityIndicator } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { getSharedGardenBySlug, SharedGardenResponse } from '../../api/garden';
import { GardenFeed } from '../../components/GardenFeed';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function SharedGardenBySlug() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const [data, setData] = useState<SharedGardenResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (slug) {
      fetchGarden();
    }
  }, [slug]);

  const fetchGarden = async () => {
    try {
      setLoading(true);
      const res = await getSharedGardenBySlug(slug!);
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
