import { useEffect, useState } from 'react'
import { ArrowRight, AudioLines, Camera, ChefHat, CircleHelp, Leaf, ScanLine, ShieldCheck, Sparkles, Trash2, UtensilsCrossed, Video } from 'lucide-react'
import { clearHistory, getHistory } from './api'
import type { ReportSummary, View } from './types'
import './platform.css'

const capabilities: { view: View; icon: typeof Camera; number: string; title: string; description: string; tags: string[]; tone: string }[] = [
  { view: 'analyze', icon: ScanLine, number: '01', title: 'Food recognition', description: 'Identify visible dishes and estimate portions, macros, calories and a health score.', tags: ['IMAGE', 'NUTRITION'], tone: 'sage' },
  { view: 'freshness', icon: Leaf, number: '02', title: 'Freshness signals', description: 'Review visible quality cues with storage context and careful safety advice.', tags: ['IMAGE', 'SAFETY'], tone: 'mint' },
  { view: 'hygiene', icon: ShieldCheck, number: '03', title: 'Kitchen hygiene', description: 'Sample video frames for gloves, hair restraints, handling and surfaces.', tags: ['VIDEO', 'ALERTS'], tone: 'sand' },
  { view: 'cook', icon: ChefHat, number: '04', title: 'Cooking assistant', description: 'Turn ingredient photos, typed requests or voice notes into practical guidance.', tags: ['IMAGE', 'TEXT', 'AUDIO'], tone: 'peach' },
  { view: 'meal-plan', icon: UtensilsCrossed, number: '05', title: 'Personal meal plans', description: 'Build a day or week around your profile, dietary limits and nutrition goals.', tags: ['PROFILE', 'PLANNING'], tone: 'lavender' },
]

export function PlatformOverview({ navigate, aiReady }: { navigate: (view: View) => void; aiReady: boolean }) {
  const [reports, setReports] = useState<ReportSummary[]>([])
  const [historyError, setHistoryError] = useState('')
  useEffect(() => { getHistory().then(setReports).catch(() => setHistoryError('Recent reports are unavailable while the API is offline.')) }, [])
  const erase = async () => {
    if (!window.confirm('Delete all saved FoodVerse reports for this browser?')) return
    try { await clearHistory(); setReports([]); setHistoryError('') }
    catch { setHistoryError('Could not clear reports. Please try again.') }
  }
  return <div className="platform-overview">
    <div className="overview-kicker"><span className="pulse-mark" /> FOODVERSE AI / CONTROL CENTER <span>01 — 05 CAPABILITIES</span></div>
    <section className="platform-hero">
      <div className="platform-hero-copy"><span className="hero-overline"><Sparkles size={15}/> MULTIMODAL FOOD INTELLIGENCE</span><h1>Every food decision,<br/><em>more informed.</em></h1><p>One place to understand what you eat, how fresh it looks, how safely it is prepared, and what to cook next.</p><div className="hero-actions"><button className="platform-primary" onClick={() => navigate('analyze')}><Camera size={18}/> Analyze a food photo <ArrowRight size={17}/></button><button className="platform-secondary" onClick={() => navigate('cook')}>Ask the cooking assistant <ArrowRight size={16}/></button></div><div className="hero-status"><span className={aiReady ? 'status-dot on' : 'status-dot'}/>{aiReady ? 'Model connected · Ready for input' : 'Connect an AI model to start analysis'}</div></div>
      <div className="intelligence-map" aria-label="FoodVerse processes image, video, audio and text into actionable insights"><div className="map-center"><span><Sparkles size={26}/></span><strong>FoodVerse</strong><small>AI ENGINE</small></div><div className="map-inputs"><span><Camera size={16}/> Image</span><span><Video size={16}/> Video</span><span><AudioLines size={16}/> Audio</span><span><CircleHelp size={16}/> Text</span></div><div className="map-output out-one">Nutrition <ArrowRight size={14}/></div><div className="map-output out-two">Freshness <ArrowRight size={14}/></div><div className="map-output out-three">Safety <ArrowRight size={14}/></div><div className="map-output out-four">Guidance <ArrowRight size={14}/></div><span className="map-loop loop-one"/><span className="map-loop loop-two"/><span className="map-loop loop-three"/><span className="map-loop loop-four"/></div>
    </section>
    <section className="platform-section"><div className="platform-section-head"><div><span className="section-eyebrow">THE PLATFORM</span><h2>One workspace. Five ways to see more.</h2></div><p>Choose an input. FoodVerse turns model output into estimates, visual observations, alerts and next steps.</p></div><div className="platform-capabilities">{capabilities.map(({ view, icon: Icon, number, title, description, tags, tone }) => <button key={view} className={`platform-capability ${tone}`} onClick={() => navigate(view)}><span className="cap-top"><span className="cap-icon"><Icon size={23}/></span><span className="cap-number">{number} / 05</span></span><span className="cap-body"><strong>{title}</strong><span>{description}</span></span><span className="cap-footer"><span>{tags.map(tag => <i key={tag}>{tag}</i>)}</span><ArrowRight size={19}/></span></button>)}</div></section>
    <section className="recent-reports"><div className="recent-head"><div><span className="section-eyebrow">YOUR REPORTS</span><h2>Recent insights</h2></div>{reports.length > 0 && <button onClick={erase}><Trash2 size={15}/> Clear history</button>}</div>{historyError ? <p className="recent-empty">{historyError}</p> : reports.length ? <div className="recent-grid">{reports.slice(0, 3).map(report => <article key={report.id}><span>{report.kind.replace('-', ' ')} · {new Date(report.created_at).toLocaleDateString()}</span><strong>{report.title}</strong><p>{report.summary}</p></article>)}</div> : <p className="recent-empty">Your reports will appear here after your first analysis. Uploaded media is not saved.</p>}</section>
    <section className="platform-trust"><div className="trust-icon"><ShieldCheck size={22}/></div><div><strong>Evidence first, estimates clearly labeled.</strong><p>Visual freshness is a screening signal, not a microbiological test. Nutrition depends on visible portions and ingredients; kitchen video reviews sampled frames.</p></div><button onClick={() => navigate('freshness')}>Explore the analysis <ArrowRight size={16}/></button></section>
  </div>
}
