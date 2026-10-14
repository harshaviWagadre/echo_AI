import React, {useState} from 'react'
import { api, API_URL } from '../api'

export default function ImageCreator(){
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit(e){
    e.preventDefault()
    setLoading(true)
    try{
      const form = new FormData()
      form.append('prompt', prompt)
      const res = await api.post('/image/create', form)
      if (res.data.url.startsWith('/')) res.data.url = `${API_URL}${res.data.url}`
      setResult(res.data)
    }catch(err){
      console.error(err)
      alert('Error creating image (check backend)')
    }finally{ setLoading(false) }
  }

  return (
    <div>
      <form onSubmit={submit}>
        <div>
          <input value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder="Describe the image" style={{width:'100%'}} />
        </div>
        <div style={{marginTop:8}}>
          <button type="submit" disabled={loading}>{loading? 'Creating...':'Create Image'}</button>
        </div>
      </form>

      {result && (
        <div style={{marginTop:12}}>
          <div>Image ID: {result.id}</div>
          <div>URL: {result.url}</div>
          <div>Prompt: {result.prompt}</div>
        </div>
      )}
    </div>
  )
}
