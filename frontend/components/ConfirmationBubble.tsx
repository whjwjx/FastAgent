import React, { useState } from 'react';
import { View, Text, TextInput, Button, StyleSheet, TouchableOpacity } from 'react-native';
import Checkbox from 'expo-checkbox';

export type ToolCall = {
  id?: string;
  function?: {
    name: string;
    arguments: string;
  };
};

type ConfirmationBubbleProps = {
  toolCalls: ToolCall[];
  onConfirm: (selectedToolCalls: ToolCall[]) => void;
  onCancel: () => void;
  status?: string;
  isConfirmed?: boolean;
  isCancelled?: boolean;
};

// 简单映射一下给前端展示的友好名称
const toolNameMapping: Record<string, string> = {
  "thought:crud:create": "记录想法",
  "thought:crud:read": "查询想法",
  "thought:crud:update": "更新想法",
  "thought:crud:delete": "删除想法",
  "create_schedule": "创建日程",
  "read_schedules": "查询日程",
  "update_schedule": "更新日程",
  "delete_schedule": "删除日程"
};

/**
 * 解析工具名，支持 namespace 格式，例如 thought:crud:create
 * 返回一个更友好的显示名称
 */
const getToolDisplayName = (name: string) => {
  if (toolNameMapping[name]) return toolNameMapping[name];
  
  if (name.includes(':')) {
    const parts = name.split(':');
    // 如果是 thought:crud:create，取最后一部分并首字母大写，或者根据前缀映射
    const lastPart = parts[parts.length - 1];
    const prefix = parts[0];
    
    const prefixMap: Record<string, string> = {
      'thought': '想法',
      'blog': '博客',
      'garden': '花园',
      'stats': '统计'
    };
    
    const actionMap: Record<string, string> = {
      'create': '新增',
      'update': '修改',
      'delete': '删除',
      'read': '查询',
      'list': '列表'
    };
    
    const prefixCn = prefixMap[prefix] || prefix;
    const actionCn = actionMap[lastPart] || lastPart;
    
    return `${prefixCn}-${actionCn}`;
  }
  
  return name;
};

export default function ConfirmationBubble({
  toolCalls,
  onConfirm,
  onCancel,
  status,
  isConfirmed,
  isCancelled
}: ConfirmationBubbleProps) {
  // 初始默认全部勾选，并尝试解析 arguments
  const [selectedStates, setSelectedStates] = useState<boolean[]>(toolCalls.map(() => true));
  const [parsedArgsList, setParsedArgsList] = useState<any[]>(
    toolCalls.map(tc => {
      try {
        return JSON.parse(tc.function?.arguments || '{}');
      } catch (e) {
        return {};
      }
    })
  );

  const toggleSelection = (index: number) => {
    const newStates = [...selectedStates];
    newStates[index] = !newStates[index];
    setSelectedStates(newStates);
  };

  const handleArgChange = (index: number, key: string, value: string) => {
    const newList = [...parsedArgsList];
    newList[index] = { ...newList[index], [key]: value };
    setParsedArgsList(newList);
  };

  const handleConfirmClick = () => {
    // 组装最终勾选并修改过的 toolCalls
    const finalToolCalls = toolCalls.filter((_, i) => selectedStates[i]).map((tc, i) => ({
      ...tc,
      function: {
        ...tc.function,
        name: tc.function?.name || '',
        arguments: JSON.stringify(parsedArgsList[i])
      }
    }));
    
    // 如果一个都没选但点了确认，相当于取消
    if (finalToolCalls.length === 0) {
      onCancel();
    } else {
      onConfirm(finalToolCalls);
    }
  };

  const isFinished = isConfirmed || isCancelled || status;

  return (
    <View style={styles.container}>
      <Text style={styles.headerTitle}>
        {isFinished ? '操作已处理' : '请确认以下操作'}
      </Text>

      {toolCalls.map((tc, index) => {
        const funcName = tc.function?.name || '';
        const displayName = getToolDisplayName(funcName);
        const args = parsedArgsList[index];

        return (
          <View key={index} style={[styles.itemContainer, isFinished && styles.itemDisabled]}>
            <View style={styles.itemHeader}>
              {!isFinished && (
                <Checkbox
                  value={selectedStates[index]}
                  onValueChange={() => toggleSelection(index)}
                  style={styles.checkbox}
                />
              )}
              <Text style={styles.itemName}>{displayName}</Text>
            </View>

            {/* 渲染参数输入框 */}
            <View style={styles.argsContainer}>
              {Object.keys(args).map((key) => {
                // 排除不需要展示或修改的内部 ID（根据业务需求可以调整）
                if (key === 'user_id') return null;
                
                return (
                  <View key={key} style={styles.argRow}>
                    <Text style={styles.argLabel}>{key}:</Text>
                    <TextInput
                      style={styles.argInput}
                      value={String(args[key])}
                      onChangeText={(val) => handleArgChange(index, key, val)}
                      editable={!isFinished && selectedStates[index]}
                      multiline={key.includes('content') || key === 'title'}
                    />
                  </View>
                );
              })}
            </View>
          </View>
        );
      })}

      {!isFinished ? (
        <View style={styles.actionButtons}>
          <TouchableOpacity style={styles.confirmBtn} onPress={handleConfirmClick}>
            <Text style={styles.btnText}>确认所选</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.cancelBtn} onPress={onCancel}>
            <Text style={styles.btnText}>全部取消</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <Text style={[styles.statusText, isCancelled ? styles.statusCancelled : styles.statusConfirmed]}>
          {status || (isCancelled ? '已取消' : '已确认')}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#333',
  },
  itemContainer: {
    marginBottom: 12,
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    padding: 8,
  },
  itemDisabled: {
    opacity: 0.6,
  },
  itemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  checkbox: {
    marginRight: 8,
    width: 18,
    height: 18,
  },
  itemName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
  argsContainer: {
    paddingLeft: 26,
  },
  argRow: {
    marginBottom: 6,
  },
  argLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  argInput: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    fontSize: 13,
    color: '#333',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  confirmBtn: {
    flex: 1,
    backgroundColor: '#007AFF',
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginRight: 6,
  },
  cancelBtn: {
    flex: 1,
    backgroundColor: '#FF3B30',
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginLeft: 6,
  },
  btnText: {
    color: '#fff',
    fontWeight: '600',
  },
  statusText: {
    marginTop: 8,
    textAlign: 'center',
    fontWeight: 'bold',
    fontStyle: 'italic',
  },
  statusConfirmed: {
    color: '#34C759',
  },
  statusCancelled: {
    color: '#FF3B30',
  },
});