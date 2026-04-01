import { useEffect, useState, useCallback } from 'react';
import { StyleSheet, View, Text, ActivityIndicator, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getThoughts } from '../../api/agent';
import { useIsFocused } from '@react-navigation/native';
import { GardenFeed } from '../../components/GardenFeed';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';

type TabType = 'idea' | 'blog';

export default function ThoughtsScreen() {
  const [thoughts, setThoughts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('idea');
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  
  const isFocused = useIsFocused();
  const router = useRouter();

  const fetchThoughts = useCallback(async (type: TabType) => {
    try {
      setLoading(true);
      const data = await getThoughts(type);
      setThoughts(data);
    } catch (error) {
      console.error(`Error fetching ${type}s`, error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isFocused) {
      fetchThoughts(activeTab);
      setIsSelectionMode(false);
      setSelectedIds([]);
    }
  }, [isFocused, activeTab, fetchThoughts]);

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    setIsSelectionMode(false);
    setSelectedIds([]);
  };

  const toggleSelectionMode = () => {
    setIsSelectionMode(!isSelectionMode);
    if (isSelectionMode) {
      setSelectedIds([]);
    }
  };

  const handleToggleSelect = (id: number) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const handleGenerateBlog = () => {
    if (selectedIds.length === 0) return;
    
    // Pass the selected IDs as a parameter to the Chat tab
    // Since we're using expo-router, we can use setParams or just pass it in the URL
    const message = `请根据我选中的这些想法 (ID: ${selectedIds.join(', ')}) 帮我合成一篇博客长文，并保存。`;
    router.push({
      pathname: '/(tabs)/',
      params: { initialMessage: message }
    });
  };

  const renderContent = () => {
    if (loading && thoughts.length === 0) {
      return (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#007AFF" />
        </View>
      );
    }

    return (
      <View style={{ flex: 1 }}>
        <GardenFeed 
          thoughts={thoughts} 
          mode="owner" 
          onRefresh={() => fetchThoughts(activeTab)} 
          selectable={isSelectionMode}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
        />
        
        {isSelectionMode && selectedIds.length > 0 && (
          <TouchableOpacity 
            style={styles.generateButton}
            onPress={handleGenerateBlog}
          >
            <MaterialCommunityIcons name="magic-staff" size={20} color="#fff" />
            <Text style={styles.generateButtonText}>
              合成博客 ({selectedIds.length})
            </Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.headerContainer}>
        <View style={styles.headerRow}>
          <Text style={styles.header}>My Space</Text>
          {activeTab === 'idea' && (
            <TouchableOpacity onPress={toggleSelectionMode} style={styles.selectionToggle}>
              <Text style={styles.selectionToggleText}>
                {isSelectionMode ? 'Cancel' : 'Select'}
              </Text>
            </TouchableOpacity>
          )}
        </View>
        <View style={styles.tabContainer}>
          <TouchableOpacity 
            style={[styles.tabButton, activeTab === 'idea' && styles.activeTabButton]} 
            onPress={() => handleTabChange('idea')}
          >
            <Text style={[styles.tabText, activeTab === 'idea' && styles.activeTabText]}>Thoughts</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.tabButton, activeTab === 'blog' && styles.activeTabButton]} 
            onPress={() => handleTabChange('blog')}
          >
            <Text style={[styles.tabText, activeTab === 'blog' && styles.activeTabText]}>Blogs & Reports</Text>
          </TouchableOpacity>
        </View>
      </View>
      {renderContent()}
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
  headerContainer: {
    backgroundColor: '#fff',
    paddingTop: 20,
    paddingHorizontal: 20,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  header: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  selectionToggle: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#F0F7FF',
    borderRadius: 16,
  },
  selectionToggleText: {
    color: '#007AFF',
    fontWeight: '600',
    fontSize: 14,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    padding: 4,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 6,
  },
  activeTabButton: {
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
    elevation: 2,
  },
  tabText: {
    fontSize: 14,
    color: '#666',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#000',
    fontWeight: 'bold',
  },
  generateButton: {
    position: 'absolute',
    bottom: 20,
    alignSelf: 'center',
    backgroundColor: '#007AFF',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 8,
  },
  generateButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  }
});
