import { useState, useRef, useEffect } from 'react';
import { StyleSheet, TextInput, Button, FlatList, Text, View, KeyboardAvoidingView, Platform, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createChatStream, createConfirmStream } from '../../api/agent';
import { useAuthStore } from '../../store/authStore';
import ConfirmationBubble from '../../components/ConfirmationBubble';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Markdown from 'react-native-markdown-display';

export type Message = {
  id: string;
  text: string;
  sender: 'user' | 'agent';
  status?: string;
  isConfirmation?: boolean;
  actionId?: string;
  toolCalls?: any[];
  isConfirmed?: boolean;
  isCancelled?: boolean;
};

const CHAT_HISTORY_KEY = 'chat_history_messages';

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const { token } = useAuthStore();
  const flatListRef = useRef<FlatList>(null);
  
  // Load chat history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const savedHistory = await AsyncStorage.getItem(CHAT_HISTORY_KEY);
        if (savedHistory) {
          setMessages(JSON.parse(savedHistory));
        }
      } catch (e) {
        console.error('Failed to load chat history', e);
      }
    };
    loadHistory();
  }, []);

  // Save chat history whenever messages change
  useEffect(() => {
    const saveHistory = async () => {
      try {
        // Only save the last 50 messages to prevent storage overflow
        const messagesToSave = messages.slice(-50);
        await AsyncStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messagesToSave));
      } catch (e) {
        console.error('Failed to save chat history', e);
      }
    };
    if (messages.length > 0) {
      saveHistory();
    }
  }, [messages]);

  const handleStreamEvents = (es: any, agentInitialMsgId: string) => {
    let currentTextMsgId = agentInitialMsgId;
    
    es.addEventListener('message', (event: any) => {
      if (event.data === '[DONE]') {
        setMessages(prev => prev.map(msg => 
          msg.id === currentTextMsgId ? { ...msg, status: '' } : msg
        ));
        es.close();
        return;
      }
      try {
        const data = JSON.parse(event.data || '{}');
        
        if (data.type === 'text') {
            setMessages(prev => {
                const msgs = [...prev];
                const msgIndex = msgs.findIndex(m => m.id === currentTextMsgId);
                
                if (msgIndex !== -1) {
                    msgs[msgIndex] = { 
                        ...msgs[msgIndex], 
                        text: msgs[msgIndex].text + data.text,
                        status: ''
                    };
                }
                return msgs;
            });
        } 
        else if (data.type === 'tool_confirmation_required') {
            setMessages(prev => {
                const msgs = [...prev];
                // Add a confirmation bubble
                msgs.push({
                    id: data.action_id,
                    text: '',
                    sender: 'agent',
                    isConfirmation: true,
                    actionId: data.action_id,
                    toolCalls: data.tool_calls
                });
                return msgs;
            });
        }
        else if (data.type === 'tool_status') {
            const toolMsgId = data.tool_call_id || Date.now().toString();
            setMessages(prev => {
                const msgs = [...prev];
                const existingIndex = msgs.findIndex(m => m.id === toolMsgId);
                if (existingIndex !== -1) {
                    msgs[existingIndex] = { ...msgs[existingIndex], status: data.status };
                } else {
                    msgs.push({ id: toolMsgId, text: '', sender: 'agent', status: data.status });
                }
                
                const initialMsgIndex = msgs.findIndex(m => m.id === agentInitialMsgId);
                if (initialMsgIndex !== -1 && msgs[initialMsgIndex].text === '' && msgs[initialMsgIndex].status === '正在思考...') {
                    msgs.splice(initialMsgIndex, 1);
                }
                
                currentTextMsgId = Date.now().toString() + '_text';
                const hasCurrentTextMsg = msgs.some(m => m.id === currentTextMsgId);
                if (!hasCurrentTextMsg) {
                    msgs.push({ id: currentTextMsgId, text: '', sender: 'agent', status: '' });
                }
                
                return msgs;
            });
        }
        else if (data.type === 'tool_status_done') {
            const toolMsgId = data.tool_call_id;
            setMessages(prev => {
                const msgs = [...prev];
                const msgIndex = msgs.findIndex(m => m.id === toolMsgId);
                if (msgIndex !== -1) {
                    msgs[msgIndex] = { ...msgs[msgIndex], status: data.status };
                }
                return msgs;
            });
        }
        else {
            if (data.text !== undefined) {
              setMessages(prev => prev.map(msg => 
                msg.id === currentTextMsgId ? { ...msg, text: msg.text + data.text, status: data.text ? '' : msg.status } : msg
              ));
            }
            if (data.status !== undefined) {
              setMessages(prev => prev.map(msg => 
                msg.id === currentTextMsgId ? { ...msg, status: data.status } : msg
              ));
            }
        }
        
        if (data.error) {
          setMessages(prev => prev.map(msg => 
            msg.id === currentTextMsgId ? { ...msg, text: msg.text + "\nError: " + data.error, status: '' } : msg
          ));
          es.close();
        }
      } catch (e) {
        console.error("Parse stream error", e);
      }
    });

    es.addEventListener('error', (event: any) => {
      console.error('SSE Error:', event);
      es.close();
      
      // Handle 401 Unauthorized for SSE
      if (event.xhrStatus === 401) {
        useAuthStore.getState().signOut();
        return;
      }

      setMessages(prev => {
        const msg = prev.find(m => m.id === currentTextMsgId);
        if (msg && msg.text === '') {
          return prev.map(m => m.id === currentTextMsgId ? { ...m, text: "Error: Connection lost or server error" } : m);
        }
        return prev;
      });
    });
  };

  const handleSend = () => {
    if (!inputText.trim()) return;

    // 处理遗留的未确认表单（置为已失效）
    setMessages(prev => {
      let changed = false;
      const newMsgs = prev.map(msg => {
        if (msg.isConfirmation && !msg.isConfirmed && !msg.isCancelled && !msg.status) {
          changed = true;
          return { ...msg, status: '已失效', isCancelled: true };
        }
        return msg;
      });
      
      // 注意：这里我们仅在前端将状态置灰，
      // 由于没有真正的回传后端，所以对于 LLM 的上下文来说，这等同于没有发生过。
      // 这正是我们期望的：如果用户不理会确认框直接说新话，就等于直接开启了新话题。
      return changed ? newMsgs : prev;
    });

    const userMsg: Message = { id: Date.now().toString(), text: inputText, sender: 'user' };
    const agentInitialMsgId = (Date.now() + 1).toString();
    const initialAgentMsg: Message = { id: agentInitialMsgId, text: '', sender: 'agent', status: '正在思考...' };
    
    setMessages(prev => [...prev, userMsg, initialAgentMsg]);
    setInputText('');

    if (!token) return;

    const history = messages.slice(-10).map(m => ({
      role: m.sender === 'user' ? 'user' : 'assistant',
      content: m.text
    })).filter(m => m.content);

    const es = createChatStream(userMsg.text, token, history);
    handleStreamEvents(es, agentInitialMsgId);
  };

  const handleConfirmAction = (msgId: string, actionId: string, toolCalls: any[], isCancelled: boolean) => {
    // 确保我们发送回后端的 toolCalls 包含 id
    const processedToolCalls = toolCalls.map((tc, idx) => ({
      ...tc,
      id: tc.id || `call_${idx}_${Date.now()}`
    }));

    // Update local UI state
    setMessages(prev => prev.map(msg => {
      if (msg.id === msgId) {
        return { ...msg, isConfirmed: !isCancelled, isCancelled: isCancelled, status: isCancelled ? '已取消' : '正在执行...' };
      }
      return msg;
    }));

    if (!token) return;

    const history = messages.slice(-10).map(m => ({
      role: m.sender === 'user' ? 'user' : 'assistant',
      content: m.text
    })).filter(m => m.content);

    // Provide a temporary ID for any text the agent will stream back after confirmation
    const agentInitialMsgId = (Date.now() + 1).toString();
    const initialAgentMsg: Message = { id: agentInitialMsgId, text: '', sender: 'agent', status: '正在处理...' };
    setMessages(prev => [...prev, initialAgentMsg]);

    const es = createConfirmStream(actionId, processedToolCalls, isCancelled, token, history);
    handleStreamEvents(es, agentInitialMsgId);
  };

  const handleClearHistory = async () => {
    try {
      await AsyncStorage.removeItem(CHAT_HISTORY_KEY);
      setMessages([]);
    } catch (e) {
      console.error('Failed to clear chat history', e);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>FastAIStack Assistant</Text>
        <TouchableOpacity onPress={handleClearHistory} style={styles.clearBtn}>
          <Text style={styles.clearBtnText}>Clear</Text>
        </TouchableOpacity>
      </View>
      <KeyboardAvoidingView 
        style={styles.keyboardView} 
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={item => item.id}
          renderItem={({ item }) => {
            if (item.isConfirmation) {
              return (
                <ConfirmationBubble
                  toolCalls={item.toolCalls || []}
                  onConfirm={(selectedToolCalls) => handleConfirmAction(item.id, item.actionId!, selectedToolCalls, false)}
                  onCancel={() => handleConfirmAction(item.id, item.actionId!, item.toolCalls || [], true)}
                  status={item.status}
                  isConfirmed={item.isConfirmed}
                  isCancelled={item.isCancelled}
                />
              );
            }

            // Only render bubble if it has either text or status
            if (!item.text && !item.status) {
              return null;
            }
            const markdownStyles = {
    body: {
      fontSize: 16,
      color: item.sender === 'user' ? '#fff' : '#333',
      lineHeight: 24,
    },
    code_inline: {
      backgroundColor: item.sender === 'user' ? 'rgba(255,255,255,0.2)' : '#f0f0f0',
      color: item.sender === 'user' ? '#fff' : '#333',
      borderRadius: 4,
      padding: 2,
      fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    },
    code_block: {
      backgroundColor: item.sender === 'user' ? 'rgba(255,255,255,0.2)' : '#f0f0f0',
      color: item.sender === 'user' ? '#fff' : '#333',
      borderRadius: 8,
      padding: 10,
      fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    },
    paragraph: {
      marginTop: 0,
      marginBottom: 0,
    }
  };

  return (
    <View style={[styles.messageBubble, item.sender === 'user' ? styles.userBubble : styles.agentBubble]}>
      {item.text ? (
        // 使用 react-native-markdown-display 渲染 Markdown
        <Markdown style={markdownStyles}>
          {item.text}
        </Markdown>
      ) : null}
                {item.status ? (
                  <Text style={[styles.statusText, item.text ? styles.statusTextWithMargin : null]}>
                    {item.status}
                  </Text>
                ) : null}
              </View>
            );
          }}
          contentContainerStyle={styles.listContent}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
          onLayout={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Talk to your AI Assistant..."
            onSubmitEditing={handleSend}
            returnKeyType="send"
            blurOnSubmit={false}
          />
          <Button title="Send" onPress={handleSend} />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  clearBtn: {
    padding: 6,
  },
  clearBtnText: {
    color: '#FF3B30',
    fontSize: 14,
  },
  listContent: {
    padding: 16,
  },
  messageBubble: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 10,
    maxWidth: '80%',
  },
  userBubble: {
    backgroundColor: '#007AFF',
    alignSelf: 'flex-end',
  },
  agentBubble: {
    backgroundColor: '#E5E5EA',
    alignSelf: 'flex-start',
  },
  messageText: {
    fontSize: 16,
  },
  userText: {
    color: '#fff',
  },
  agentText: {
    color: '#000',
  },
  statusText: {
    fontSize: 14,
    color: '#666',
    fontStyle: 'italic',
  },
  statusTextWithMargin: {
    marginTop: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    borderTopWidth: 1,
    borderColor: '#ccc',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 10,
    marginRight: 10,
  }
});
