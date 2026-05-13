import { useEffect, useRef } from 'react'

export default function MediaPlayer({ file, activeTimestamp }) {
  const mediaRef = useRef(null)

  useEffect(() => {
    if (activeTimestamp !== null && mediaRef.current) {
      mediaRef.current.currentTime = activeTimestamp
      mediaRef.current.play().catch(e => console.log('Autoplay prevented', e))
    }
  }, [activeTimestamp])

  if (!file || !['audio', 'video'].includes(file.file_type)) return null

  // Assuming static serving of files or an API endpoint that streams the file
  const mediaUrl = `http://localhost:8000/api/files/download/${file.id}`

  return (
    <div className="media-player-container">
      {file.file_type === 'video' ? (
        <video 
          ref={mediaRef} 
          src={mediaUrl} 
          controls 
          className="media-player"
          style={{ maxHeight: '300px' }}
        />
      ) : (
        <audio 
          ref={mediaRef} 
          src={mediaUrl} 
          controls 
          className="media-player"
        />
      )}
    </div>
  )
}
