import { apiPostForm } from './api'

export type StylingImageResult = {
  label: string
  b64_png: string
  media_type: string
}

export type StylingVisualization = {
  disclaimer: string
  current_weight_lbs: number
  target_weight_lbs: number
  lbs_to_lose: number
  images: StylingImageResult[]
}

export async function visualizeGoalAppearance(
  image: File,
  targetWeightLbs?: number,
): Promise<StylingVisualization> {
  const form = new FormData()
  form.append('image', image)
  if (targetWeightLbs != null && Number.isFinite(targetWeightLbs)) {
    form.append('target_weight_lbs', String(targetWeightLbs))
  }

  return apiPostForm<StylingVisualization>('/styling/visualize', form)
}
