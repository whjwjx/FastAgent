import React from 'react';
import { StyleSheet, FlatList, Text, View, TouchableOpacity, Share, Platform } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { updateThoughtPrivacy } from '../api/garden';

interface Thought {
  id: number;
  original_content: string;
  refined_content?: string;
  tags?: string[];
  is_public: boolean;
  created_at: string;
}

interface GardenFeedProps {
  thoughts: Thought[];
  mode: 'owner' | 'visitor';
  onRefresh?: () => void;
  ownerInfo?: {
    nickname: string;
    avatar?: string;
    bio?: string;
  };
  ListHeaderComponent?: React.ReactNode;
}

export const GardenFeed: React.FC<GardenFeedProps> = ({ 
  thoughts, 
  mode, 
  onRefresh, 
  ownerInfo,
  ListHeaderComponent 
}) => {
  const togglePrivacy = async (id: number, currentPublic: boolean) => {
    if (mode !== 'owner') return;
    try {
      await updateThoughtPrivacy(id, !currentPublic);
      onRefresh?.();
    } catch (error) {
      console.error("Failed to toggle privacy", error);
    }
  };

  const renderItem = ({ item }: { item: Thought }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.date}>{new Date(item.created_at).toLocaleDateString()}</Text>
        {mode === 'owner' && (
          <TouchableOpacity onPress={() => togglePrivacy(item.id, item.is_public)}>
            <MaterialCommunityIcons 
              name={item.is_public ? "earth" : "lock"} 
              size={20} 
              color={item.is_public ? "#4CAF50" : "#9E9E9E"} 
            />
          </TouchableOpacity>
        )}
      </View>
      
      <Text style={styles.content}>{item.original_content}</Text>
      
      {item.tags && item.tags.length > 0 && (
        <View style={styles.tagContainer}>
          {item.tags.map(tag => (
            <Text key={tag} style={styles.tag}>#{tag}</Text>
          ))}
        </View>
      )}
    </View>
  );

  return (
    <FlatList
      data={thoughts}
      keyExtractor={item => item.id.toString()}
      renderItem={renderItem}
      ListHeaderComponent={
        <View>
          {ListHeaderComponent}
          {mode === 'visitor' && ownerInfo && (
            <View style={styles.headerContainer}>
              <Text style={styles.headerTitle}>{ownerInfo.nickname}的数字花园</Text>
              {ownerInfo.bio && <Text style={styles.headerBio}>{ownerInfo.bio}</Text>}
            </View>
          )}
        </View>
      }
      ListEmptyComponent={<Text style={styles.emptyText}>这里还什么都没有...</Text>}
      contentContainerStyle={styles.listContent}
      onRefresh={onRefresh}
      refreshing={false}
    />
  );
};

const styles = StyleSheet.create({
  listContent: {
    padding: 16,
    paddingBottom: 40,
  },
  headerContainer: {
    paddingVertical: 24,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
  },
  headerBio: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  date: {
    fontSize: 12,
    color: '#999',
  },
  content: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
  tagContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 12,
  },
  tag: {
    fontSize: 12,
    color: '#007AFF',
    marginRight: 8,
    backgroundColor: '#F0F7FF',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    marginTop: 60,
    fontSize: 16,
  }
});
