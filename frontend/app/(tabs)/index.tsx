import { useState, useRef } from 'react';
import { StyleSheet, TextInput, Button, FlatList, Text, View, KeyboardAvoidingView, Platform, SafeAreaView } from 'react-native';
import { createChatStream } from '../../api/agent';
import { useAuthStore } from '../../store/authStore';

export default function ChatScreen() {
  const [messages, setMessages] = useState<{id: string, text: string, sender: 'user'|'agent', status?: string}[]>([]);
  const [inputText, setInputText] = useState('');
  const { token } = useAuthStore();
  const flatListRef = useRef<FlatList>(null);

  const handleSend = () => {
    if (!inputText.trim()) return;

    const userMsg = { id: Date.now().toString(), text: inputText, sender: 'user' as const };
    const agentInitialMsgId = (Date.now() + 1).toString();
    const initialAgentMsg = { id: agentInitialMsgId, text: '', sender: 'agent' as const, status: '正在思考...' };
    
    setMessages(prev => [...prev, userMsg, initialAgentMsg]);
    setInputText('');

    if (!token) return;

    // Convert local messages to OpenAI history format (last 10 messages to save tokens)
    const history = messages.slice(-10).map(m => ({
      role: m.sender === 'user' ? 'user' : 'assistant',
      content: m.text
    })).filter(m => m.content); // Only keep messages with text content

    const es = createChatStream(userMsg.text, token, history);
    
    // Store the ID of the current text bubble being appended to
    let currentTextMsgId = agentInitialMsgId;
    
    es.addEventListener('message', (event) => {
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
                    // Update existing text bubble, clear its status
                    msgs[msgIndex] = { 
                        ...msgs[msgIndex], 
                        text: msgs[msgIndex].text + data.text,
                        status: ''
                    };
                }
                return msgs;
            });
        } 
        else if (data.type === 'tool_status') {
            const toolMsgId = data.tool_call_id || Date.now().toString();
            setMessages(prev => {
                const msgs = [...prev];
                // Check if this tool status already exists
                const existingIndex = msgs.findIndex(m => m.id === toolMsgId);
                if (existingIndex !== -1) {
                    msgs[existingIndex] = { ...msgs[existingIndex], status: data.status };
                } else {
                    // Create new tool status bubble
                    msgs.push({ id: toolMsgId, text: '', sender: 'agent' as const, status: data.status });
                }
                
                // When we start executing a tool, if we had a text bubble that was just "正在思考...",
                // we should clear its status or remove it if it's empty
                const initialMsgIndex = msgs.findIndex(m => m.id === agentInitialMsgId);
                if (initialMsgIndex !== -1 && msgs[initialMsgIndex].text === '' && msgs[initialMsgIndex].status === '正在思考...') {
                    msgs.splice(initialMsgIndex, 1);
                }
                
                // We need a new text bubble for any future text after a tool call
                currentTextMsgId = Date.now().toString() + '_text';
                const hasCurrentTextMsg = msgs.some(m => m.id === currentTextMsgId);
                if (!hasCurrentTextMsg) {
                    msgs.push({ id: currentTextMsgId, text: '', sender: 'agent' as const, status: '' });
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
        // Fallback for old protocol
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

    es.addEventListener('error', (event) => {
      console.error('SSE Error:', event);
      // In EventSource, an error event usually indicates a connection drop or server close.
      // We should close the stream to prevent automatic reconnection attempts which cause repeated messages.
      es.close();
      
      // Only set error message if we haven't received any text yet
      setMessages(prev => {
        const msg = prev.find(m => m.id === currentTextMsgId);
        if (msg && msg.text === '') {
          return prev.map(m => m.id === currentTextMsgId ? { ...m, text: "Error: Connection lost or server error" } : m);
        }
        return prev;
      });
    });
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={styles.container} 
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={90}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={item => item.id}
          renderItem={({ item }) => {
            // Only render bubble if it has either text or status
            if (!item.text && !item.status) {
              return null;
            }
            return (
              <View style={[styles.messageBubble, item.sender === 'user' ? styles.userBubble : styles.agentBubble]}>
                {item.text ? (
                  <Text style={[styles.messageText, item.sender === 'user' ? styles.userText : styles.agentText]}>
                    {item.text}
                  </Text>
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
    backgroundColor: '#fff',
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
