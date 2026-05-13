import { FileText, Music, Video, Clock } from 'lucide-react'

export default function FileList({ files, activeFile, onSelectFile }) {
  const getIcon = (type) => {
    if (type === 'pdf') return <FileText size={20} />
    if (type === 'audio') return <Music size={20} />
    if (type === 'video') return <Video size={20} />
    return <FileText size={20} />
  }

  const getStatusClass = (status) => {
    if (status === 'processing') return 'status-processing'
    if (status === 'ready') return 'status-ready'
    return 'status-error'
  }

  const formatSize = (bytes) => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  if (files.length === 0) {
    return <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', padding: '1rem' }}>No files uploaded yet</div>
  }

  return (
    <div>
      {files.map(file => (
        <div 
          key={file.id} 
          className={`file-item ${activeFile?.id === file.id ? 'active' : ''}`}
          onClick={() => onSelectFile(file)}
        >
          <div className="file-icon">
            {getIcon(file.file_type)}
          </div>
          <div className="file-info">
            <div className="file-name" title={file.filename}>{file.filename}</div>
            <div className="file-meta">
              <span>{formatSize(file.file_size)}</span>
              <span className={`status-badge ${getStatusClass(file.status)}`}>
                {file.status}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
