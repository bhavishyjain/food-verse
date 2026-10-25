import { useEffect, useRef, useState } from 'react'
import {
  Apple, ArrowRight, Bell, Camera, Check, ChefHat, ChevronRight, CircleUserRound,
  Clock3, Flame, HeartPulse, Leaf, Menu, Mic, Play, Plus, ScanLine, Search,
  ShieldCheck, Sparkles, Sprout, Upload, UtensilsCrossed, Video, WandSparkles, X,
} from 'lucide-react'
import { analyzeCookingAudio, analyzeFood, analyzeHygiene, createRecipe, createRecipeFromImage, getHealth } from './api'
import type { CookingGuidance, FoodAnalysis, Health, HygieneAnalysis, Recipe, View } from './types'
import { PlatformOverview } from './PlatformOverview'
import { FreshnessChecker } from './FreshnessChecker'
import { PersonalMealPlanner } from './PersonalMealPlanner'
import './overrides.css'

const navItems: { id: View; label: string; icon: typeof Apple }[] = [
  { id: 'overview', label: 'Overview', icon: Sprout },
  { id: 'analyze', label: 'Food analyzer', icon: ScanLine },
  { id: 'freshness', label: 'Freshness check', icon: Leaf },
  { id: 'hygiene', label: 'Kitchen hygiene', icon: ShieldCheck },
  { id: 'cook', label: 'Cooking assistant', icon: ChefHat },
  { id: 'meal-plan', label: 'Meal planner', icon: Apple },
]

const viewPaths: Record<View, string> = {
  overview: '/', analyze: '/food-recognition', freshness: '/freshness-detector',
  hygiene: '/hygiene-monitor', cook: '/kitchen-assistant', 'meal-plan': '/meal-planner',
}
const viewFromPath = (path: string): View => (Object.keys(viewPaths) as View[]).find(view => viewPaths[view] === path) || 'overview'

function App() {
  const [view, setView] = useState<View>(() => viewFromPath(window.location.pathname))
  const [mobileOpen, setMobileOpen] = useState(false)
  const [toast, setToast] = useState('')
  const [health, setHealth] = useState<Health | null>(null)

  useEffect(() => { getHealth().then(setHealth).catch(() => setHealth(null)) }, [])
  useEffect(() => {
    const onBack = () => setView(viewFromPath(window.location.pathname))
    window.addEventListener('popstate', onBack)
    return () => window.removeEventListener('popstate', onBack)
  }, [])

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(''), 2800)
    return () => window.clearTimeout(timer)
  }, [toast])

  const navigate = (next: View) => {
    setView(next)
    if (window.location.pathname !== viewPaths[next]) window.history.pushState({}, '', viewPaths[next])
    setMobileOpen(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <button className="mobile-close" onClick={() => setMobileOpen(false)} aria-label="Close menu"><X size={20} /></button>
        <button className="brand" onClick={() => navigate('overview')}>
          <span className="brand-mark"><Leaf size={20} fill="currentColor" /></span>
          <span>foodverse<span className="brand-dot">.</span></span>
        </button>
        <p className="nav-label">Workspace</p>
        <nav>
          {navItems.map(({ id, label, icon: Icon }) => (
            <button key={id} className={`nav-item ${view === id ? 'active' : ''}`} onClick={() => navigate(id)}>
              <Icon size={19} strokeWidth={1.8} /><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="upgrade-card service-card"><span className="spark"><Sparkles size={15} /></span><strong>AI service</strong><p>{health?.ai_ready ? `${health.provider} connected and ready.` : health ? 'Add an OpenAI or Groq API key to enable analysis.' : 'API is offline. Start FastAPI to continue.'}</p><span className={`service-state ${health?.ai_ready ? 'ready' : ''}`}>{health?.ai_ready ? 'Ready' : 'Setup needed'}</span></div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open menu"><Menu size={22} /></button>
          <div className="workspace-title"><span className="workspace-orbit"><Sparkles size={17}/></span><span><strong>Food intelligence workspace</strong><small>Image · Video · Audio · Text</small></span></div>
          <div className="top-actions">
            <span className={`top-status ${health?.ai_ready ? 'ready' : ''}`}><i />{health?.ai_ready ? 'AI ready' : 'Setup needed'}</span>
            <button className="ask-button" onClick={() => navigate('cook')}><WandSparkles size={17} /> Ask FoodVerse</button>
          </div>
        </header>

        <section className="page-wrap">
          {view === 'overview' && <PlatformOverview navigate={navigate} aiReady={!!health?.ai_ready} />}
          {view === 'analyze' && <FoodAnalyzer focus="analyze" />}
          {view === 'freshness' && <FreshnessChecker />}
          {view === 'hygiene' && <HygieneMonitor />}
          {view === 'cook' && <CookingAssistant />}
          {view === 'meal-plan' && <PersonalMealPlanner />}
        </section>
      </main>
      {toast && <div className="toast"><Check size={17} />{toast}</div>}
    </div>
  )
}

function FoodAnalyzer({ focus }: { focus: 'analyze' | 'freshness' }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const audioRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [context, setContext] = useState('')
  const [preview, setPreview] = useState('')
  const [analysis, setAnalysis] = useState<FoodAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])
  const choose = (next?: File) => {
    if (!next) return
    if (!['image/jpeg','image/png','image/webp'].includes(next.type) || next.size > 10 * 1024 * 1024) { setError('Upload a JPG, PNG, or WebP image smaller than 10 MB.'); return }
    if (preview) URL.revokeObjectURL(preview)
    setFile(next); setPreview(URL.createObjectURL(next)); setAnalysis(null); setError('')
  }
  const run = async () => {
    if ((focus === 'freshness' && !file) || (!file && !audioFile && !context.trim())) return inputRef.current?.click()
    setLoading(true); setError('')
    try { setAnalysis(await analyzeFood(file, context, audioFile)) }
    catch (e) { setError(e instanceof Error ? e.message : 'Analysis failed') }
    finally { setLoading(false) }
  }

  return <div className="tool-page">
    <div className="page-heading"><div><span className="mini-label">VISION INTELLIGENCE</span><h1>{focus === 'freshness' ? 'Is it still fresh?' : 'Understand what’s on your plate.'}</h1><p>{focus === 'freshness' ? 'Upload a clear photo to inspect visible color, texture, and surface quality signals.' : 'Upload a meal photo for recognition, nutrition estimates, and clear next steps.'}</p></div><span className="model-pill"><Sparkles size={15} /> Vision analysis</span></div>
    <div className="analyzer-layout">
      <div className="upload-panel">
        <input ref={inputRef} hidden type="file" accept="image/jpeg,image/png,image/webp" onChange={e => choose(e.target.files?.[0])} />
        <div className={`drop-zone ${preview ? 'has-preview' : ''}`} onClick={() => inputRef.current?.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); choose(e.dataTransfer.files[0]) }}>
          {preview ? <img src={preview} alt="Selected food" /> : <><span className="upload-icon"><Upload size={25} /></span><h3>Drop your food photo here</h3><p>or click to browse · JPG, PNG, or WebP up to 10 MB</p><span className="outline-button"><Camera size={17} /> Choose photo</span></>}
          {preview && <span className="replace-photo">Click to replace photo</span>}
        </div>
        <label className="context-label">Add context <span>optional</span><textarea value={context} onChange={e=>setContext(e.target.value)} maxLength={500} placeholder="What is this, how much did you eat, or what ingredients are hidden?" /></label>
        <input hidden ref={audioRef} type="file" accept="audio/*" onChange={e=>{setAudioFile(e.target.files?.[0] || null);setAnalysis(null)}}/><button className="audio-attach" onClick={()=>audioRef.current?.click()}><Mic size={16}/>{audioFile ? audioFile.name : 'Add a voice note'}</button>
        <button className="analyze-button" disabled={loading} onClick={run}>{loading ? <><span className="spinner" /> Analyzing your input...</> : <><ScanLine size={19} /> Analyze food <ArrowRight size={17} /></>}</button>
        {error && <p className="soft-error" role="alert">{error}</p>}
        <div className="privacy-note"><ShieldCheck size={16} /><span>Submitted images, text, and audio are sent to the configured AI provider. Review its data policy before sharing sensitive content.</span></div>
      </div>
      <div className={`result-panel ${analysis ? 'filled' : ''}`}>
        {!analysis ? <div className="empty-result"><div className="orb"><Sparkles size={25} /></div><h3>Your insights will appear here</h3><p>Food recognition, nutritional estimates, freshness, and recommendations — all in one clear view.</p><div className="empty-chips"><span>Recognition</span><span>Nutrition</span><span>Freshness</span></div></div> : <AnalysisResult data={analysis} focus={focus} />}
      </div>
    </div>
  </div>
}

function AnalysisResult({ data, focus }: { data: FoodAnalysis; focus: string }) {
  return <div className="analysis-result">
    <div className="result-title"><div><span className="mini-label">FOOD ANALYSIS</span><h2>{data.dish}</h2><p>{data.confidence ? `Model estimate · ${Math.round(data.confidence * 100)}% stated confidence` : 'Text or audio estimate · no visual confidence'}</p></div>{data.health_score !== null && <span className="health-score"><b>{data.health_score}</b><small>Heuristic<br />score</small></span>}</div>
    <div className="fresh-banner"><span className="fresh-icon"><Leaf size={20} /></span><div><small>VISIBLE FRESHNESS</small><strong>{data.freshness || 'Cannot determine'}</strong></div><span>{data.freshness_confidence !== null ? `${Math.round(data.freshness_confidence * 100)}% stated confidence` : 'Visual only'}</span></div>
    {focus === 'freshness' && <><h4 className="subhead">Visual signals</h4><ul className="takeaways">{data.visual_signals.map(item => <li key={item}><Check size={14}/>{item}</li>)}</ul></>}
    {focus !== 'freshness' && <><div className="nutrition-grid">
      <div className="calorie-box"><Flame size={18} /><strong>{data.nutrition?.calories ?? '—'}</strong><small>estimated kcal</small></div>
      <Nutrient value={data.nutrition ? `${data.nutrition.protein}g` : '—'} label="Protein" /><Nutrient value={data.nutrition ? `${data.nutrition.carbs}g` : '—'} label="Carbs" /><Nutrient value={data.nutrition ? `${data.nutrition.fat}g` : '—'} label="Fat" />
    </div><p className="nutrition-source">{data.nutrition_source}. {data.health_score_method}.</p>
    <h4 className="subhead">What we recognized</h4><div className="recognized-list">{data.items.map(item => <div key={item.name}><span><i />{item.name}</span><small>{item.portion}</small><b>{Math.round(item.confidence * 100)}%</b></div>)}</div></>}
    <h4 className="subhead">Recommended next steps</h4><ul className="takeaways">{data.insights.map(item => <li key={item}><Check size={14} />{item}</li>)}</ul><p className="result-limitations">{[...data.limitations, 'Appearance alone cannot confirm food safety.'].join(' ')}</p>
  </div>
}

function Nutrient({ value, label }: { value: string; label: string }) { return <div className="nutrient"><strong>{value}</strong><small>{label}</small></div> }

function HygieneMonitor() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<HygieneAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const run = async () => { if (!file) return inputRef.current?.click(); setLoading(true); setError(''); try { setResult(await analyzeHygiene(file)) } catch (e) { setError(e instanceof Error ? e.message : 'Video analysis failed') } finally { setLoading(false) } }
  return <div className="tool-page"><div className="page-heading"><div><span className="mini-label">FOOD SAFETY VISION</span><h1>Turn kitchen footage into safer habits.</h1><p>Sampled frames reveal visible glove use, hair restraints, handling practices, and surface cleanliness.</p></div><span className="model-pill"><Video size={15}/> Frame review</span></div>
    <div className="hygiene-layout">
      <div className="video-card"><input hidden ref={inputRef} type="file" accept="video/mp4,video/quicktime,video/webm" onChange={e => { setFile(e.target.files?.[0] || null); setResult(null); setError('') }} /><div className="video-stage" onClick={() => inputRef.current?.click()}><div className="video-grid" />{file ? <><span className="video-file"><Video size={27} /><b>{file.name}</b><small>Ready for frame analysis</small></span></> : <><span className="play-circle"><Play size={24} fill="currentColor" /></span><h3>Upload kitchen footage</h3><p>MP4, MOV, or WebM · up to 100 MB</p></>}</div><button className="analyze-button" onClick={run} disabled={loading}>{loading ? <><span className="spinner" /> Sampling key frames...</> : <><Video size={18} /> Analyze hygiene</>}</button>{error && <p className="soft-error" role="alert">{error}</p>}</div>
      <div className="hygiene-results">{result ? <><div className="score-head"><div className="big-score">{result.score ?? '—'}<small>/100</small></div><div><span className="mini-label">HYGIENE SCREENING</span><h3>{result.status}</h3><p>{result.frames_analyzed} sampled frames reviewed</p></div></div><div className="check-list">{result.checks.map(check => <div key={check.label}><span className={check.status === 'Pass' ? 'pass' : 'review'}>{check.status === 'Pass' ? <Check size={15}/> : '!'}</span><span><strong>{check.label}</strong><small>{check.status}</small></span><b>{check.score === null ? '—' : `${check.score}%`}</b></div>)}</div>{result.alerts.map(alert => <div className="alert-box" key={`${alert.time}-${alert.message}`}><Clock3 size={17}/><p><strong>Moment to review · {alert.time}</strong>{alert.message}</p></div>)}<p className="result-limitations">{[...result.limitations, 'Sampled video is not a formal hygiene inspection.'].join(' ')}</p></> : <div className="empty-result compact"><div className="orb"><ShieldCheck size={25}/></div><h3>Safety review ready when you are</h3><p>We’ll surface visible checks and approximate moments that need attention.</p></div>}</div>
    </div>
  </div>
}

function CookingAssistant() {
  const [prompt, setPrompt] = useState('I have chickpeas, tomatoes, spinach, and 30 minutes')
  const imageRef = useRef<HTMLInputElement>(null)
  const [image, setImage] = useState<File | null>(null)
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [guidance, setGuidance] = useState<CookingGuidance | null>(null)
  const [error, setError] = useState('')
  const audioRef = useRef<HTMLInputElement>(null)
  const [loading, setLoading] = useState(false)
  const ask = async () => { if (!prompt.trim() && !image) return; setLoading(true); setError(''); setGuidance(null); try { setRecipe(image ? await createRecipeFromImage(image, prompt) : await createRecipe(prompt)) } catch (e) { setError(e instanceof Error ? e.message : 'Recipe generation failed') } finally { setLoading(false) } }
  const askAudio = async (file?: File) => { if (!file) return; setLoading(true); setError(''); setRecipe(null); try { const result = await analyzeCookingAudio(file); setGuidance(result); setPrompt(result.transcript) } catch (e) { setError(e instanceof Error ? e.message : 'Audio analysis failed') } finally { setLoading(false) } }
  return <div className="tool-page cooking-page"><div className="cook-hero"><span className="mini-label">YOUR ADAPTIVE SOUS-CHEF</span><h1>What are we cooking?</h1><p>Describe your goal, add an ingredient photo, or upload a voice note for contextual cooking guidance.</p><div className="prompt-box"><textarea value={prompt} onChange={e => setPrompt(e.target.value)} aria-label="Cooking request" /><div><input ref={imageRef} hidden type="file" accept="image/jpeg,image/png,image/webp" onChange={e=>{const file=e.target.files?.[0];if(file){if(file.size>10*1024*1024){setError('Photo must be smaller than 10 MB.');return}setImage(file);setRecipe(null);setError('')}}}/><button className="voice-button" aria-label="Add ingredient photo" title="Add ingredient photo" onClick={()=>imageRef.current?.click()}><Camera size={18}/></button><input ref={audioRef} hidden type="file" accept="audio/*" onChange={e => askAudio(e.target.files?.[0])}/><button className="voice-button" aria-label="Upload voice note" title="Upload voice note" onClick={() => audioRef.current?.click()}><Mic size={18}/></button><button className="ask-button large" onClick={ask} disabled={loading}>{loading ? 'Thinking…' : 'Create my recipe'} <ArrowRight size={17}/></button></div></div>{image && <div className="ingredient-attachment"><Camera size={15}/><span>{image.name}</span><button aria-label="Remove ingredient photo" onClick={()=>setImage(null)}><X size={15}/></button></div>}{error && <p className="soft-error" role="alert">{error}</p>}<div className="prompt-chips"><button onClick={() => setPrompt('A high-protein vegetarian dinner in 20 minutes')}>High-protein dinner</button><button onClick={() => setPrompt('Use chickpeas and spinach, and avoid dairy')}>Use what I have</button><button onClick={() => setPrompt('A healthy comfort meal for a rainy evening')}>Healthy comfort food</button></div></div>
    {guidance && <div className="recipe-card audio-guidance"><span className="mini-label">VOICE GUIDANCE</span><h2>{guidance.guidance}</h2><p><strong>You said:</strong> {guidance.transcript}</p><ol>{guidance.steps.map((step,i)=><li key={step}><b>{i+1}.</b> {step}</li>)}</ol>{guidance.safety_note && <div className="chef-tip"><ShieldCheck size={18}/><p><strong>Safety note</strong>{guidance.safety_note}</p></div>}</div>}
    {recipe ? <div className="recipe-card"><div className="recipe-intro"><div className="recipe-visual"><span>🍋</span><i>🌿</i><b>●</b></div><div><span className="mini-label">RECIPE READY</span><h2>{recipe.title}</h2><p>{recipe.subtitle}</p><div className="recipe-meta"><span><Clock3 size={15}/>{recipe.time}</span><span><ChefHat size={15}/>{recipe.difficulty}</span></div></div></div><div className="recipe-columns"><div><h3>What you’ll need</h3><div className="ingredients">{recipe.ingredients.map(item => <span key={item}><Plus size={13}/>{item}</span>)}</div></div><div><h3>Let’s make it</h3><ol>{recipe.steps.map((step,i) => <li key={step}><span>{i+1}</span>{step}</li>)}</ol></div></div><div className="chef-tip"><Sparkles size={18}/><p><strong>Chef’s tip</strong>{recipe.tip}</p></div>{recipe.safety_note && <div className="chef-tip"><ShieldCheck size={18}/><p><strong>Safety note</strong>{recipe.safety_note}</p></div>}</div> : !guidance && <div className="suggestion-grid"><Suggestion emoji="🥗" title="Bright & balanced" text="Mediterranean meals in under 30 min" onClick={() => setPrompt('A Mediterranean meal in under 30 minutes')}/><Suggestion emoji="🍲" title="One-pot comfort" text="Less cleanup, all the flavor" onClick={() => setPrompt('A healthy one-pot comfort meal')}/><Suggestion emoji="🌮" title="Make it together" text="Fun, flexible family dinners" onClick={() => setPrompt('A flexible family dinner we can cook together')}/></div>}
  </div>
}

function Suggestion({emoji,title,text,onClick}:{emoji:string;title:string;text:string;onClick:()=>void}) { return <button className="suggestion" onClick={onClick}><span>{emoji}</span><div><h3>{title}</h3><p>{text}</p></div><ArrowRight size={17}/></button> }


export default App
