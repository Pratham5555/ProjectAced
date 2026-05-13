import { useState, useRef } from 'react'
import { UploadCloud, Loader } from 'lucide-react'
import api from '../api'

export default function FileUpload({ onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = async (e) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0])
    }
  }

  const uploadFile = async (file) => {
    setUploading(true)
    setError(null)
    const formData = new FormData()
    formData.append('file', file)

    try {
      await api.post('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      onUploadSuccess()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const triggerSelect = () => {
    if (inputRef.current) inputRef.current.click()
  }

  return (
    <div 
      className={`upload-area ${dragActive ? 'drag-active' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={triggerSelect}
    >
      <input 
        ref={inputRef}
        type="file" 
        style={{ display: 'none' }} 
        onChange={handleChange}
        accept=".pdf,audio/*,video/*"
      />
      
      {uploading ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Loader className="spinner upload-icon" size={32} />
          <span>Uploading...</span>
        </div>
      ) : (
        <>
          <UploadCloud className="upload-icon" size={32} />
          <div style={{ fontWeight: 500 }}>Click or Drag file to upload</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Supports PDF, Audio, Video
          </div>
        </>
      )}
      
      {error && <div style={{ color: 'var(--error)', marginTop: '0.5rem', fontSize: '0.85rem' }}>{error}</div>}
    </div>
  )
}
