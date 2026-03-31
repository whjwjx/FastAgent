import React, { useEffect, useState, useCallback } from 'react';
import { StyleSheet, View, Text, Switch, TextInput, TouchableOpacity, ScrollView, Alert, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getGardenConfig, updateGardenConfig, resetShareToken, GardenConfig } from '../../api/garden';
import { getThoughts } from '../../api/agent';
import { GardenFeed } from '../../components/GardenFeed';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useIsFocused } from '@react-navigation/native';
import * as Clipboard from 'expo-clipboard';

export default function GardenScreen() {
  const [config, setConfig] = useState<GardenConfig | null>(null);
  const [thoughts, setThoughts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [slug, setSlug] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const isFocused = useIsFocused();

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [configData, thoughtsData] = await Promise.all([
        getGardenConfig(),
        getThoughts()
      ]);
      setConfig(configData);
      setThoughts(thoughtsData);
      setSlug(configData.slug || '');
    } catch (error) {
      console.error("Failed to fetch garden data", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isFocused) {
      fetchData();
    }
  }, [isFocused, fetchData]);

  const handleToggleShare = async (value: boolean) => {
    if (!config) return;
    try {
      const updated = await updateGardenConfig({ is_share_open: value });
      setConfig(updated);
    } catch (error) {
      Alert.alert("Error", "Failed to update sharing status");
    }
  };

  const handleUpdateSlug = async () => {
    if (!config || slug === config.slug) return;
    try {
      setIsSaving(true);
      const updated = await updateGardenConfig({ slug });
      setConfig(updated);
      Alert.alert("Success", "Slug updated successfully");
    } catch (error: any) {
      const msg = error.response?.data?.detail || "Failed to update slug";
      Alert.alert("Error", msg);
    } finally {
      setIsSaving(false);
    }
  };

  const copyLink = async (type: 'token' | 'slug') => {
    if (!config) return;
    const baseUrl = Platform.OS === 'web' ? window.location.origin : 'http://localhost:8081';
    const path = type === 'token' ? `/share/${config.share_token}` : `/garden/${config.slug}`;
    const url = `${baseUrl}${path}`;
    await Clipboard.setStringAsync(url);
    Alert.alert("Success", "Link copied to clipboard");
  };

  const handleResetToken = async () => {
    Alert.alert(
      "Reset Token",
      "This will invalidate your current private sharing link. Are you sure?",
      [
        { text: "Cancel", style: "cancel" },
        { 
          text: "Reset", 
          style: "destructive",
          onPress: async () => {
            try {
              const updated = await resetShareToken();
              setConfig(updated);
              Alert.alert("Success", "Token reset successfully");
            } catch (error) {
              Alert.alert("Error", "Failed to reset token");
            }
          }
        }
      ]
    );
  };

  if (loading && !config) {
    return (
      <View style={styles.center}>
        <Text>Loading...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <GardenFeed 
        thoughts={thoughts} 
        mode="owner" 
        onRefresh={fetchData}
        ListHeaderComponent={
          <View>
            <View style={styles.section}>
              <View style={styles.row}>
                <View>
                  <Text style={styles.sectionTitle}>开启分享</Text>
                  <Text style={styles.sectionDesc}>开启后，访客可通过链接查看公开内容</Text>
                </View>
                <Switch 
                  value={config?.is_share_open} 
                  onValueChange={handleToggleShare}
                  trackColor={{ false: "#D1D1D1", true: "#4CAF50" }}
                />
              </View>
            </View>

            {config?.is_share_open && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>分享管理</Text>
                
                <View style={styles.linkCard}>
                  <View style={styles.linkHeader}>
                    <Text style={styles.linkLabel}>私密 Token 链接</Text>
                    <TouchableOpacity onPress={handleResetToken}>
                      <Text style={styles.linkAction}>重置</Text>
                    </TouchableOpacity>
                  </View>
                  <TouchableOpacity style={styles.linkBox} onPress={() => copyLink('token')}>
                    <Text style={styles.linkText} numberOfLines={1}>/share/{config.share_token}</Text>
                    <MaterialCommunityIcons name="content-copy" size={16} color="#007AFF" />
                  </TouchableOpacity>
                </View>

                <View style={styles.linkCard}>
                  <Text style={styles.linkLabel}>个性化 Slug 后缀</Text>
                  <View style={styles.slugInputRow}>
                    <View style={styles.slugPrefixBox}>
                      <Text style={styles.slugPrefix}>/garden/</Text>
                    </View>
                    <TextInput 
                      style={styles.slugInput}
                      value={slug}
                      onChangeText={setSlug}
                      autoCapitalize="none"
                      placeholder="your-garden-name"
                    />
                    <TouchableOpacity 
                      style={[styles.saveBtn, slug === config.slug && styles.saveBtnDisabled]} 
                      onPress={handleUpdateSlug}
                      disabled={slug === config.slug || isSaving}
                    >
                      <Text style={styles.saveBtnText}>{isSaving ? '...' : '保存'}</Text>
                    </TouchableOpacity>
                  </View>
                  <TouchableOpacity style={styles.linkBox} onPress={() => copyLink('slug')}>
                    <Text style={styles.linkText} numberOfLines={1}>/garden/{config.slug}</Text>
                    <MaterialCommunityIcons name="content-copy" size={16} color="#007AFF" />
                  </TouchableOpacity>
                </View>
              </View>
            )}

            <View style={styles.section}>
              <Text style={styles.sectionTitle}>花园预览 (主人视角)</Text>
              <Text style={styles.sectionDesc}>点击图标切换想法的公开/私密状态</Text>
            </View>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  scrollContent: {
    paddingBottom: 20,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  section: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  sectionDesc: {
    fontSize: 13,
    color: '#999',
    marginTop: 4,
  },
  linkCard: {
    marginTop: 20,
  },
  linkHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  linkLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  linkAction: {
    fontSize: 12,
    color: '#FF3B30',
  },
  linkBox: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F0F0F0',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E5E5',
  },
  linkText: {
    fontSize: 13,
    color: '#007AFF',
    flex: 1,
    marginRight: 10,
  },
  slugInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  slugPrefixBox: {
    backgroundColor: '#F0F0F0',
    padding: 10,
    borderTopLeftRadius: 8,
    borderBottomLeftRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E5E5',
    borderRightWidth: 0,
  },
  slugPrefix: {
    fontSize: 14,
    color: '#999',
  },
  slugInput: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 10,
    borderWidth: 1,
    borderColor: '#E5E5E5',
    fontSize: 14,
  },
  saveBtn: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 15,
    paddingVertical: 10,
    borderTopRightRadius: 8,
    borderBottomRightRadius: 8,
  },
  saveBtnDisabled: {
    backgroundColor: '#B4D7FF',
  },
  saveBtnText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
});
