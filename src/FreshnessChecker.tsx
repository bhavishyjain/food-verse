import { useEffect, useRef, useState } from 'react'
import { ArrowRight, Camera, Check, Leaf, Mic, ShieldCheck, Sparkles, Upload } from 'lucide-react'
import { analyzeFreshness } from './api'
import type { FreshnessAnalysis } from './types'

export function FreshnessChecker() {
  const imageRef = useRef<HTMLInputElement>(null)
  const audioRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [audio, setAudio] = useState<File | null>(null)
  const [preview, setPreview] = useState('')
  const [storageTime, setStorageTime] = useState('')
  const [storageType, setStorageType] = useState('')
  const [result, setResult] = useState<FreshnessAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])
  const choose = (next?: File) => {
    if (!next) return
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(next.type) || next.size > 10 * 1024 * 1024) { setError('Upload a JPG, PNG, or WebP image smaller than 10 MB.'); return }
    setFile(next); setPreview(URL.createObjectURL(next)); setResult(null); setError('')
  }
  const run = async () => {
    if (!file) return imageRef.current?.click()
    setLoading(true); setError('')
    try { setResult(await analyzeFreshness(file, storageTime, storageType, audio)) }
    catch (e) { setError(e instanceof Error ? e.message : 'Freshness review failed') }
    finally { setLoading(false) }
  }
  return <div className="tool-page"><div className="page-heading"><div><span className="mini-label">VISUAL FOOD QUALITY</span><h1>See the signs. Decide with care.</h1><p>Inspect visible color, texture and surface patterns, with storage context for better guidance.</p></div><span className="model-pill"><Leaf size={15}/> Freshness review</span></div>
    <div className="analyzer-layout"><div className="upload-panel">
      <input ref={imageRef} hidden type="file" accept="image/jpeg,image/png,image/webp" onChange={e=>choose(e.target.files?.[0])}/>
      <div className={`drop-zone ${preview ? 'has-preview' : ''}`} onClick={()=>imageRef.current?.click()} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();choose(e.dataTransfer.files[0])}}>{preview ? <img src={preview} alt="Food selected for visual freshness review"/> : <><span className="upload-icon"><Upload size={25}/></span><h3>Drop a clear food photo here</h3><p>or click to browse · JPG, PNG, or WebP up to 10 MB</p><span className="outline-button"><Camera size={17}/> Choose photo</span></>}{preview && <span className="replace-photo">Click to replace photo</span>}</div>
      <div className="freshness-fields"><label>How long has it been stored?<input value={storageTime} maxLength={100} onChange={e=>setStorageTime(e.target.value)} placeholder="e.g. 2 days"/></label><label>Where was it stored?<select value={storageType} onChange={e=>setStorageType(e.target.value)}><option value="">Select storage</option><option value="Refrigerated">Refrigerated</option><option value="Frozen">Frozen</option><option value="Room temperature">Room temperature</option><option value="Unknown">Unknown</option></select></label></div>
      <input ref={audioRef} hidden type="file" accept="audio/*" onChange={e=>setAudio(e.target.files?.[0] || null)}/><button className="audio-attach" onClick={()=>audioRef.current?.click()}><Mic size={16}/>{audio ? audio.name : 'Add a voice note'}</button>
      <button className="analyze-button" disabled={loading} onClick={run}>{loading ? 'Reviewing visible features…' : <>Check freshness <ArrowRight size={17}/></>}</button>{error && <p className="soft-error" role="alert">{error}</p>}<div className="privacy-note"><ShieldCheck size={16}/><span>Your photo and optional voice note are sent to the configured AI provider.</span></div>
    </div><div className={`result-panel ${result ? 'filled' : ''}`}>{result ? <div className="analysis-result"><div className="result-title"><div><span className="mini-label">FRESHNESS REPORT</span><h2>{result.item_name}</h2><p>{Math.round(result.confidence*100)}% model-stated confidence</p></div></div><div className="fresh-banner"><span className="fresh-icon"><Leaf size={20}/></span><div><small>VISIBLE ASSESSMENT</small><strong>{result.level || 'Insufficient evidence'}</strong></div></div><h4 className="subhead">Observed signals</h4><ul className="takeaways">{result.visual_signals.map((signal,i)=><li key={`${signal}-${i}`}><Check size={14}/>{signal}</li>)}</ul><h4 className="subhead">Image features</h4><div className="feature-grid"><span>Brightness <b>{Math.round(result.features.mean_brightness*100)}%</b></span><span>Color variation <b>{Math.round(result.features.color_variation*100)}%</b></span><span>Texture variation <b>{Math.round(result.features.texture_variation*100)}%</b></span><span>Dark area <b>{Math.round(result.features.dark_pixel_ratio*100)}%</b></span></div><div className="freshness-advice"><strong>Suggested action</strong><p>{result.recommendation}</p></div><p className="result-limitations"><strong>{result.warning}</strong> {result.limitations.join(' ')}</p></div> : <div className="empty-result"><div className="orb"><Sparkles size={25}/></div><h3>Your visual report will appear here</h3><p>See a freshness category, visible signals, image feature measurements, and a practical recommendation.</p></div>}</div></div>
  </div>
}
