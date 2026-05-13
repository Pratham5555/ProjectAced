import { useState, useEffect } from 'react'
import { FileText, Loader } from 'lucide-react'
import api from '../api'

export default function SummaryView({ activeFile }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (activeFile && activeFile.status === 'ready') {
      fetchSummary()
    } else {
      setSummary(null)
    }
  }, [activeFile])

  const fetchSummary = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/files/${activeFile.id}`)
      if (res.data.summary) {
        setSummary(res.data.summary)
      } else {
        setSummary("Summary not generated yet.")
      }
    } catch (err) {
      console.error('Failed to fetch summary', err)
      setSummary("Failed to load summary.")
    } finally {
      setLoading(false)
    }
  }

  if (!activeFile) return null

  return (
    <div style={{ padding: '1.5rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', color: 'var(--text-main)' }}>
        <FileText size={20} className="text-primary" />
        Document Summary
      </h3>
      
      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.5rem' }}>
        {activeFile.status !== 'ready' ? (
          <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
            Processing document to generate summary...
          </div>
        ) : loading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
            <Loader size={16} className="spinner" /> Loading summary...
          </div>
        ) : (
          <div style={{ lineHeight: 1.6, color: 'var(--text-muted)', whiteSpace: 'pre-wrap' }}>
            {summary}
          </div>
        )}
      </div>
    </div>
  )
}
