export type View = 'overview' | 'analyze' | 'freshness' | 'hygiene' | 'cook' | 'meal-plan'

export type FoodAnalysis = {
  dish: string
  confidence: number
  items: { name: string; confidence: number; portion: string; grams?: number | null; category?: string }[]
  nutrition: { calories: number; protein: number; carbs: number; fat: number; fiber: number } | null
  health_score: number | null
  freshness: 'Fresh' | 'Moderately Fresh' | 'Spoiled' | null
  freshness_confidence: number | null
  visual_signals: string[]
  insights: string[]
  limitations: string[]
  nutrition_source: string
  health_score_method: string
}

export type FreshnessAnalysis = {
  item_name: string
  level: 'Fresh' | 'Moderately Fresh' | 'Spoiled' | null
  confidence: number
  visual_signals: string[]
  features: { mean_brightness: number; color_variation: number; texture_variation: number; dark_pixel_ratio: number }
  recommendation: string
  warning: string
  limitations: string[]
}

export type HygieneAnalysis = {
  score: number | null
  status: string
  duration: string
  frames_analyzed: number
  checks: { label: string; score: number | null; status: string }[]
  alerts: { time: string; message: string }[]
  limitations: string[]
}

export type UserProfile = {
  age: number; height_cm: number; weight_kg: number
  activity: 'sedentary' | 'light' | 'moderate' | 'active'
  energy_basis: 'manual' | 'female_equation' | 'male_equation'
  goal: 'balanced' | 'weight-loss' | 'muscle-gain' | 'heart-health'
  diet: 'everything' | 'vegetarian' | 'vegan' | 'pescatarian'
  allergies: string[]; dislikes: string[]; health_notes: string
  pregnant_or_breastfeeding: boolean
}
export type MealPlanRequest = { profile: UserProfile; period: 'daily' | 'weekly'; manual_calories: number | null }
export type MacroTotals = { calories: number; protein: number; carbs: number; fat: number }
export type PlannedMeal = { slot: 'Breakfast' | 'Lunch' | 'Snack' | 'Dinner'; name: string; description: string; ingredients: string[]; portion: string; macros: MacroTotals; reason: string }
export type PlannedDay = { day: string; meals: PlannedMeal[]; totals: MacroTotals }
export type MealPlan = {
  period: 'daily' | 'weekly'
  profile_summary: string
  target: MacroTotals
  target_method: string
  days: PlannedDay[]
  alternatives: { day: string; replaces: PlannedMeal['slot']; meal: PlannedMeal }[]
  coach_note: string
  cautions: string[]
}

export type Recipe = {
  title: string
  subtitle: string
  time: string
  difficulty: string
  ingredients: string[]
  steps: string[]
  tip: string
  safety_note: string
}

export type CookingGuidance = { transcript: string; guidance: string; steps: string[]; safety_note: string }
export type Health = { status: string; ai_ready: boolean; provider: string | null; services: string[] }
export type ReportSummary = { id: number; kind: string; title: string; summary: string; created_at: string }

