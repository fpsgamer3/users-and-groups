import React, { useState } from 'react';
import './MessageInput.css';
import { useLanguage } from '../LanguageContext';

function MessageInput({ onSendMessage, isMuted = false }) {
  const { t } = useLanguage();
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!message.trim()) return;

    setSending(true);
    await onSendMessage(message);
    setMessage('');
    setSending(false);
  };

  if (isMuted) {
    return (
      <div className="message-input-form muted">
        <input
          type="text"
          className="message-input"
          placeholder="You have been muted and cannot send messages"
          disabled
        />
        <button 
          type="submit" 
          className="btn-send"
          disabled
        >
          {t('message_send')}
        </button>
      </div>
    );
  }

  return (
    <form className="message-input-form" onSubmit={handleSubmit}>
      <input
        type="text"
        className="message-input"
        placeholder={t('message_placeholder')}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={sending}
      />
      <button 
        type="submit" 
        className="btn-send"
        disabled={sending || !message.trim()}
      >
        {sending ? 'Sending...' : t('message_send')}
      </button>
    </form>
  );
}

export default MessageInput;
