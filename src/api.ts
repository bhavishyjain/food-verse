import type { CookingGuidance, FoodAnalysis, FreshnessAnalysis, Health, HygieneAnalysis, MealPlan, MealPlanRequest, Recipe, ReportSummary } from './types'

function browserSession(): string {
  let value = localStorage.getItem('foodverse-session')
  if (!value || !/^[a-f0-9]{32}$/.test(value)) {
    value = crypto.randomUUID().replaceAll('-', '')
    localStorage.setItem('foodverse-session', value)
  }
  return value
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers)
  headers.set('X-FoodVerse-Session', browserSession())
  const response = await fetch(path, { ...options, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    throw new Error(Array.isArray(detail) ? detail.map(item => item.msg || 'Invalid input').join('; ') : typeof detail === 'string' ? detail : 'Something went wrong. Please try again.')
  }
  return response.json() as Promise<T>
}

export function analyzeFood(file?: File | null, textContext = '', audioFile?: File | null) {
  const body = new FormData()
  if (file) body.append('file', file)
  if (textContext.trim()) body.append('text_context', textContext.trim())
  if (audioFile) body.append('audio_file', audioFile)
  return request<FoodAnalysis>('/api/analyze/food', { method: 'POST', body })
}

export function analyzeFreshness(file: File, storageTime: string, storageType: string, audioFile?: File | null) {
  const body = new FormData()
  body.append('file', file)
  body.append('storage_time', storageTime)
  body.append('storage_type', storageType)
  if (audioFile) body.append('audio_file', audioFile)
  return request<FreshnessAnalysis>('/api/analyze/freshness', { method: 'POST', body })
}

export function analyzeHygiene(file: File) {
  const body = new FormData()
  body.append('file', file)
  return request<HygieneAnalysis>('/api/analyze/hygiene', { method: 'POST', body })
}

export function getHealth() { return request<Health>('/api/health') }
export function getHistory() { return request<ReportSummary[]>('/api/history') }
export function clearHistory() { return request<{ deleted: number }>('/api/history', { method: 'DELETE' }) }

export function analyzeCookingAudio(file: File) {
  const body = new FormData()
  body.append('file', file)
  return request<CookingGuidance>('/api/cooking/audio', { method: 'POST', body })
}

export function createMealPlan(data: MealPlanRequest) {
  return request<MealPlan>('/api/meal-plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export function createRecipe(prompt: string) {
  return request<Recipe>('/api/recipe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  })
}

export function createRecipeFromImage(file: File, prompt: string) {
  const body = new FormData()
  body.append('file', file)
  body.append('prompt', prompt)
  return request<Recipe>('/api/recipe/from-image', { method: 'POST', body })
}

