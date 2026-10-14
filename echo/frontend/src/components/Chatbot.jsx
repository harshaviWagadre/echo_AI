import React, {useState} from 'react'
import { api } from '../api'

export default function Chatbot(){
  const [message, setMessage] = useState('')
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [error, setError] = useState('')

  async function send(e){
    e.preventDefault()
    const text = message.trim()
    if(!text || loading) return
    setLoading(true)
    setError('')
    try{
      const res = await api.post('/chat', { message: text, conversation_id: conversationId })
      setHistory(h => [...h, { from: 'me', text }, { from: 'bot', text: res.data.response }])
      setConversationId(res.data.conversation_id)
      setMessage('')
    }catch(err){
      setError(err.response?.data?.detail || 'The assistant could not respond. Check that the backend is running.')
    }finally{ setLoading(false) }
  }

  function newChat(){
    setHistory([])
    setConversationId(null)
    setMessage('')
    setError('')
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark">e</span><span>echo</span></div>
        <button className="new-chat" type="button" onClick={newChat}>+ New chat</button>
      </header>

      <section className="chat-layout">
        <div className="welcome">
          <p className="eyebrow">PERSONAL AI ASSISTANT</p>
          <h1>How can I help<br /><em>today?</em></h1>
          <p className="welcome-copy">Ask anything, explore an idea, or get help turning a thought into a plan.</p>
        </div>

        <div className="conversation" aria-live="polite">
          {history.length === 0 && (
            <div className="empty-state">
              <span className="spark">✦</span>
              <p>Your conversation will appear here.</p>
            </div>
          )}
          {history.map((m,i)=>(
            <div className={`message-row ${m.from === 'me' ? 'user-row' : 'assistant-row'}`} key={`${m.from}-${i}`}>
              <div className="message-label">{m.from === 'me' ? 'You' : 'Echo'}</div>
              <div className="message-text">{m.text}</div>
            </div>
          ))}
          {loading && <div className="message-row assistant-row"><div className="message-label">Echo</div><div className="typing"><span /><span /><span /></div></div>}
        </div>

        {error && <div className="error-message" role="alert">{error}</div>}

        <form className="composer" onSubmit={send}>
          <textarea value={message} onChange={e=>setMessage(e.target.value)} placeholder="Message Echo..." rows="1" aria-label="Message Echo" onKeyDown={e=>{ if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); send(e) } }} />
          <button className="send-button" type="submit" disabled={loading || !message.trim()} aria-label="Send message">↑</button>
        </form>
        <p className="composer-note">Echo can make mistakes. Check important information.</p>
      </section>
    </main>
  )
}
