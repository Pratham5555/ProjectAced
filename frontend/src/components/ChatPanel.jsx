import { useState, useEffect, useRef } from 'react'
import { Send, Clock } from 'lucide-react'
import api from '../api'

// Simple helper to parse [MM:SS] timestamps in text
const parseTextWithTimestamps = (text, onTimestampClick) => {
  if (!text) return []
  const regex = /\[(\d{1,2}:\d{2})\]/g
  const parts = []
  let lastIndex = 0
  let match

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: 'text', content: text.substring(lastIndex, match.index) })
    }
    const timeStr = match[1]
    const [mins, secs] = timeStr.split(':').map(Number)
    const timeInSeconds = mins * 60 + secs
    
    parts.push({ 
      type: 'timestamp', 
      content: timeStr, 
      seconds: timeInSeconds 
    })
    lastIndex = regex.lastIndex
  }

  if (lastIndex < text.length) {
    parts.push({ type: 'text', content: text.substring(lastIndex) })
  }

  return parts.map((part, i) => {
    if (part.type === 'timestamp') {
      return (
        <span 
          key={i} 
          className="timestamp-badge"
          onClick={() => onTimestampClick(part.seconds)}
        >
          <Clock size={12} /> {part.content}
        </span>
      )
    }
    return <span key={i}>{part.content}</span>
  })
}

export default function ChatPanel({ activeFile, onTimestampClick }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (activeFile) {
      loadHistory()
    }
  }, [activeFile])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadHistory = async () => {
    try {
      const res = await api.get(`/chat/history/${activeFile.id}`)
      setMessages(res.data)
    } catch (err) {
      console.error('Failed to load history', err)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading || activeFile.status !== 'ready') return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    // Add empty AI message placeholder
    setMessages(prev => [...prev, { role: 'ai', content: '' }])

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`http://localhost:8000/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          file_id: activeFile.id,
          prompt: input
        })
      })

      if (!response.ok) throw new Error('Chat request failed')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        setMessages(prev => {
          const newMessages = [...prev]
          const lastMsg = newMessages[newMessages.length - 1]
          if (lastMsg.role === 'ai') {
            lastMsg.content += chunk
          }
          return newMessages
        })
      }
    } catch (err) {
      console.error('Chat stream error', err)
      setMessages(prev => {
        const newMsgs = [...prev]
        newMsgs[newMsgs.length - 1].content = "Sorry, an error occurred while generating the response."
        return newMsgs
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-content">
              {parseTextWithTimestamps(msg.content, onTimestampClick)}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        {activeFile?.status !== 'ready' ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
            Wait until file processing is complete to chat.
          </div>
        ) : (
          <form onSubmit={handleSend} className="chat-form">
            <input
              type="text"
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask a question about this document..."
              disabled={loading}
            />
            <button type="submit" className="send-btn" disabled={loading || !input.trim()}>
              <Send size={18} />
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
