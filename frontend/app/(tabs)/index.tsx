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
    const agentMsgId = (Date.now() + 1).toString();
    const agentMsg = { id: agentMsgId, text: '', sender: 'agent' as const, status: '正在思考...' };
    
    setMessages(prev => [...prev, userMsg, agentMsg]);
    setInputText('');

    if (!token) return;

    // Convert local messages to OpenAI history format (last 10 messages to save tokens)
    const history = messages.slice(-10).map(m => ({
      role: m.sender === 'user' ? 'user' : 'assistant',
      content: m.text
    }));

    const es = createChatStream(userMsg.text, token, history);
    
    es.addEventListener('message', (event) => {
      if (event.data === '[DONE]') {
        setMessages(prev => prev.map(msg => 
          msg.id === agentMsgId ? { ...msg, status: '' } : msg
        ));
        es.close();
        return;
      }
      try {
        const data = JSON.parse(event.data || '{}');
        if (data.text !== undefined) {
          setMessages(prev => prev.map(msg => 
            msg.id === agentMsgId ? { ...msg, text: msg.text + data.text, status: data.text ? '' : msg.status } : msg
          ));
        }
        if (data.status !== undefined) {
          setMessages(prev => prev.map(msg => 
            msg.id === agentMsgId ? { ...msg, status: data.status } : msg
          ));
        }
        if (data.error) {
          setMessages(prev => prev.map(msg => 
            msg.id === agentMsgId ? { ...msg, text: msg.text + "\nError: " + data.error, status: '' } : msg
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
        const msg = prev.find(m => m.id === agentMsgId);
        if (msg && msg.text === '') {
          return prev.map(m => m.id === agentMsgId ? { ...m, text: "Error: Connection lost or server error" } : m);
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
          renderItem={({ item }) => (
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
          )}
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
