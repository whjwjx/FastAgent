import { useState } from 'react';
import { StyleSheet, TextInput, Button, FlatList, Text, View, KeyboardAvoidingView, Platform, SafeAreaView } from 'react-native';
import { sendChatMessage } from '../../api/agent';

export default function ChatScreen() {
  const [messages, setMessages] = useState<{id: string, text: string, sender: 'user'|'agent'}[]>([]);
  const [inputText, setInputText] = useState('');

  const handleSend = async () => {
    if (!inputText.trim()) return;

    const userMsg = { id: Date.now().toString(), text: inputText, sender: 'user' as const };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');

    try {
      const response = await sendChatMessage(userMsg.text);
      const agentMsg = { id: (Date.now() + 1).toString(), text: response.reply, sender: 'agent' as const };
      setMessages(prev => [...prev, agentMsg]);
    } catch (error) {
      const errorMsg = { id: (Date.now() + 1).toString(), text: "Error: Could not connect to AI", sender: 'agent' as const };
      setMessages(prev => [...prev, errorMsg]);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={styles.container} 
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={90}
      >
        <FlatList
          data={messages}
          keyExtractor={item => item.id}
          renderItem={({ item }) => (
            <View style={[styles.messageBubble, item.sender === 'user' ? styles.userBubble : styles.agentBubble]}>
              <Text style={[styles.messageText, item.sender === 'user' ? styles.userText : styles.agentText]}>
                {item.text}
              </Text>
            </View>
          )}
          contentContainerStyle={styles.listContent}
        />
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Talk to your AI Assistant..."
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
