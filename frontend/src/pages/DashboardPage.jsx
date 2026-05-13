import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import api from '../api'
import FileUpload from '../components/FileUpload'
import FileList from '../components/FileList'
import ChatPanel from '../components/ChatPanel'
import MediaPlayer from '../components/MediaPlayer'
import SummaryView from '../components/SummaryView'
import { LogOut } from 'lucide-react'

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const [files, setFiles] = useState([])
  const [activeFile, setActiveFile] = useState(null)
  const [activeTimestamp, setActiveTimestamp] = useState(null)

  const fetchFiles = async () => {
    try {
      const response = await api.get('/files')
      setFiles(response.data)
    } catch (err) {
      console.error('Failed to fetch files', err)
    }
  }

  useEffect(() => {
    fetchFiles()
    const interval = setInterval(fetchFiles, 5000) // Poll for status updates
    return () => clearInterval(interval)
  }, [])

  const handleUploadSuccess = () => {
    fetchFiles()
  }

  return (
    <div className="dashboard">
      {/* Sidebar: Files */}
      <div className="sidebar">
        <div className="sidebar-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ marginBottom: '0.25rem' }}>My Documents</h2>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Logged in as {user?.username}</div>
          </div>
          <button onClick={logout} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }} title="Logout">
            <LogOut size={20} />
          </button>
        </div>
        
        <div className="sidebar-content">
          <FileUpload onUploadSuccess={handleUploadSuccess} />
          <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', margin: '1.5rem 0 0.5rem 0', textTransform: 'uppercase' }}>
            Uploaded Files
          </h3>
          <FileList 
            files={files} 
            activeFile={activeFile} 
            onSelectFile={setActiveFile} 
          />
        </div>
      </div>

      {/* Main Content: Chat & Media */}
      <div className="main-content">
        {activeFile ? (
          <>
            {['audio', 'video'].includes(activeFile.file_type) && (
              <MediaPlayer 
                file={activeFile} 
                activeTimestamp={activeTimestamp} 
              />
            )}
            
            <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
              <div style={{ flex: 2, display: 'flex', flexDirection: 'column' }}>
                <ChatPanel 
                  activeFile={activeFile} 
                  onTimestampClick={setActiveTimestamp} 
                />
              </div>
              <div style={{ flex: 1, borderLeft: '1px solid var(--border-color)', background: 'rgba(15, 23, 42, 0.6)' }}>
                <SummaryView activeFile={activeFile} />
              </div>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-muted)', flexDirection: 'column' }}>
            <h2 style={{ color: 'var(--text-main)' }}>Welcome to ProjectAced</h2>
            <p>Select or upload a file to start analyzing</p>
          </div>
        )}
      </div>
    </div>
  )
}
