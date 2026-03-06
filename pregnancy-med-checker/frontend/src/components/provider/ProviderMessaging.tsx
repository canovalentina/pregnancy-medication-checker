import { useState, useEffect, useRef } from 'react';
import { getMessages, sendMessage, getPatientUnreadCount, type Message } from '../../services/messagesApi';
import { getUser } from '../../utils/auth';
import './ProviderMessaging.css';

interface ProviderMessagingProps {
  patientId: string;
  patientName?: string;
}

export function ProviderMessaging({ patientId, patientName }: ProviderMessagingProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const user = getUser();

  useEffect(() => {
    loadMessages();
    loadUnreadCount();
    // Poll for new messages every 30 seconds
    const interval = setInterval(() => {
      loadMessages();
      loadUnreadCount();
    }, 30000);
    return () => clearInterval(interval);
  }, [patientId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadMessages = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getMessages(patientId);
      if (response.status === 'success') {
        setMessages(response.data.messages);
        setUnreadCount(response.data.unread_count);
      } else {
        setError(response.error || 'Failed to load messages');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const response = await getPatientUnreadCount(patientId);
      if (response.status === 'success') {
        setUnreadCount(response.data.unread_count);
      }
    } catch (err) {
      // Silently fail for unread count
      console.error('Failed to load unread count:', err);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || isSending) return;

    setIsSending(true);
    setError(null);
    try {
      const response = await sendMessage(patientId, newMessage.trim());
      if (response.status === 'success') {
        setNewMessage('');
        await loadMessages();
      } else {
        setError(response.error || 'Failed to send message');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} min ago`;
      if (diffMins < 1440) {
        const hours = Math.floor(diffMins / 60);
        return `${hours} hr${hours !== 1 ? 's' : ''} ago`;
      }

      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const isOwnMessage = (message: Message) => {
    return message.sender_username === user?.username;
  };

  return (
    <div className="provider-messaging">
      <div className="messaging-header">
        <div className="header-top">
          <h3>💬 Messages with {patientName || 'Patient'}</h3>
          {unreadCount > 0 && (
            <div className="unread-badge">
              {unreadCount} unread
            </div>
          )}
        </div>
        <p className="messaging-description">
          Communicate directly with your patient. Messages are secure and private.
        </p>
      </div>

      {error && (
        <div className="messaging-error">
          <span>⚠️</span>
          <span>{error}</span>
          <button onClick={() => setError(null)} className="error-dismiss">
            ×
          </button>
        </div>
      )}

      {loading && messages.length === 0 ? (
        <div className="messaging-loading">
          <div className="loading-spinner" />
          <p>Loading messages...</p>
        </div>
      ) : (
        <>
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="messages-empty">
                <div className="empty-icon">💬</div>
                <p>No messages yet. Start a conversation with your patient!</p>
              </div>
            ) : (
              <div className="messages-list">
                {messages.map((message) => {
                  const ownMessage = isOwnMessage(message);
                  return (
                    <div
                      key={message.id}
                      className={`message-item ${ownMessage ? 'own-message' : 'other-message'} ${
                        !message.read && !ownMessage ? 'unread' : ''
                      }`}
                    >
                      <div className="message-bubble">
                        <div className="message-header">
                          <span className="message-sender">
                            {ownMessage ? 'You' : message.sender_name}
                            {message.sender_role === 'patient' && (
                              <span className="sender-role-badge">Patient</span>
                            )}
                          </span>
                          <span className="message-time">{formatDate(message.created_at)}</span>
                        </div>
                        <div className="message-content">{message.content}</div>
                        {!message.read && ownMessage && (
                          <div className="message-status">Sent</div>
                        )}
                        {message.read && ownMessage && (
                          <div className="message-status read">Read</div>
                        )}
                      </div>
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          <div className="message-input-container">
            <textarea
              className="message-input"
              placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              rows={3}
              disabled={isSending}
            />
            <button
              className="send-button"
              onClick={handleSendMessage}
              disabled={isSending || !newMessage.trim()}
            >
              {isSending ? 'Sending...' : 'Send'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

