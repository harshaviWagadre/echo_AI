import React, {useState} from 'react'
import { api } from '../api'

export default function VideoEditor(){
  const [clipId, setClipId] = useState('')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [clip, setClip] = useState(null)
  const [music, setMusic] = useState(null)

  async function submit(e){
    e.preventDefault()
    if(!clip) return
    setLoading(true)
    try{
      const form = new FormData()
      form.append('clip', clip)
      if (music) form.append('music', music)
      const res = await api.post('/video/edit', form)
      setStatus(res.data)
    }catch(err){
      console.error(err)
      alert('Error queuing video edit')
    }finally{ setLoading(false) }
  }

  return (
    <div>
      <form onSubmit={submit}>
        <div>
          <input type="file" accept="video/*" onChange={e=>setClip(e.target.files[0])} />
        </div>
        <div style={{marginTop:8}}>
          <input type="file" accept="audio/*" onChange={e=>setMusic(e.target.files[0])} />
        </div>
        <div style={{marginTop:8}}>
          <button type="submit" disabled={loading}>{loading? 'Queuing...':'Edit Video'}</button>
        </div>
      </form>

      {status && (
        <div style={{marginTop:12}}>
          <div>Job ID: {status.id}</div>
          <div>Status: {status.status}</div>
        </div>
      )}
    </div>
  )
}
