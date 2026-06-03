import { useEffect, useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { useWeightLossPlan } from '../hooks/useWeightLossPlan'
import { useMeasurementsQuery } from '../hooks/useMeasurements'
import { ApiError } from '../services/api'
import { visualizeGoalAppearance } from '../services/stylingService'

const MAX_IMAGE_BYTES = 5 * 1024 * 1024
const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']

function validateImageFile(file: File): string | null {
  if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    return 'Use a JPEG, PNG, WebP, or GIF image'
  }
  if (file.size > MAX_IMAGE_BYTES) {
    return 'Image must be 5 MB or smaller'
  }
  return null
}

export function VisionPage() {
  const { data: plan } = useWeightLossPlan()
  const { data: measurements } = useMeasurementsQuery()
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null)
  const [imageError, setImageError] = useState<string | null>(null)
  const [targetWeight, setTargetWeight] = useState('')

  const latestWeight = measurements?.[0]?.body_weight_lbs
  const defaultTarget = plan?.target_weight_lbs

  useEffect(() => {
    if (targetWeight === '' && defaultTarget != null) {
      setTargetWeight(String(Math.round(defaultTarget)))
    }
  }, [defaultTarget, targetWeight])

  useEffect(() => {
    if (!imageFile) {
      setImagePreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(imageFile)
    setImagePreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [imageFile])

  const visualize = useMutation({
    mutationFn: () => {
      if (!imageFile) {
        throw new Error('Photo is required')
      }
      const parsed = targetWeight.trim() ? Number(targetWeight) : undefined
      if (parsed != null && (!Number.isFinite(parsed) || parsed <= 0)) {
        throw new Error('Enter a valid target weight in lbs')
      }
      return visualizeGoalAppearance(imageFile, parsed)
    },
  })

  const resultImage = visualize.data?.images[0]
  const generatedSrc = resultImage
    ? `data:${resultImage.media_type};base64,${resultImage.b64_png}`
    : null

  const weightSummary = useMemo(() => {
    if (visualize.data) {
      return `${Math.round(visualize.data.current_weight_lbs)} lbs → ${Math.round(visualize.data.target_weight_lbs)} lbs (${Math.round(visualize.data.lbs_to_lose)} lbs)`
    }
    if (latestWeight != null && defaultTarget != null) {
      return `${Math.round(latestWeight)} lbs → ${Math.round(defaultTarget)} lbs`
    }
    return null
  }, [visualize.data, latestWeight, defaultTarget])

  const onImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) {
      return
    }
    const error = validateImageFile(file)
    if (error) {
      setImageError(error)
      setImageFile(null)
      return
    }
    setImageError(null)
    setImageFile(file)
    visualize.reset()
  }

  const clearImage = () => {
    setImageFile(null)
    setImageError(null)
    visualize.reset()
  }

  const mutationError =
    visualize.error instanceof ApiError
      ? visualize.error.message
      : visualize.error instanceof Error
        ? visualize.error.message
        : null

  return (
    <div className="flex flex-col gap-8">
      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-slate-400">
          Goal preview
        </h2>
        <p className="mb-4 text-sm text-slate-400">
          Upload a clear full-body or mirror selfie (head to toe, good light, plain
          background). AI will illustrate how you might look at your goal weight.
          Photos are not stored.
        </p>
        <ul className="mb-4 list-inside list-disc text-xs text-slate-500">
          <li>Face and body both visible — face-only photos produce poor results</li>
          <li>Stand straight, arms slightly away from torso, neutral pose</li>
          <li>Avoid filters, heavy shadows, or baggy layers that hide your shape</li>
        </ul>
        <p className="mb-6 text-xs text-amber-200/90">
          Illustration only — not a guarantee of results and not medical advice.
        </p>

        {weightSummary && (
          <p className="mb-4 text-sm text-slate-300">
            Previewing: <span className="font-medium text-slate-100">{weightSummary}</span>
          </p>
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="vision_image" className="mb-1 block text-sm text-slate-400">
              Your photo
            </label>
            <input
              id="vision_image"
              type="file"
              accept={ACCEPTED_IMAGE_TYPES.join(',')}
              onChange={onImageChange}
              className="w-full text-sm text-slate-300 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-2 file:text-slate-100"
            />
            <p className="mt-1 text-xs text-slate-500">
              Front-facing, good lighting, head-to-toe if possible. Max 5 MB.
            </p>
            {imagePreviewUrl && (
              <div className="mt-3 flex items-start gap-3">
                <img
                  src={imagePreviewUrl}
                  alt="Your upload"
                  className="max-h-48 rounded-lg border border-slate-700 object-contain"
                />
                <button
                  type="button"
                  onClick={clearImage}
                  className="text-sm text-slate-400 underline-offset-2 hover:text-slate-200 hover:underline"
                >
                  Remove photo
                </button>
              </div>
            )}
            {imageError && <p className="mt-1 text-sm text-red-400">{imageError}</p>}
          </div>

          <div>
            <label htmlFor="target_weight" className="mb-1 block text-sm text-slate-400">
              Goal weight (lbs)
            </label>
            <input
              id="target_weight"
              type="number"
              min={1}
              step={0.1}
              value={targetWeight}
              onChange={(e) => setTargetWeight(e.target.value)}
              placeholder={defaultTarget != null ? String(Math.round(defaultTarget)) : 'e.g. 165'}
              className="w-full max-w-xs rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
            />
            <p className="mt-1 text-xs text-slate-500">
              Uses your saved plan goal when set. Log weight on the measurements page first.
            </p>
          </div>

          {mutationError && (
            <p className="text-sm text-red-400">{mutationError}</p>
          )}

          <button
            type="button"
            disabled={!imageFile || visualize.isPending}
            onClick={() => visualize.mutate()}
            className="w-full max-w-md rounded-lg bg-violet-600 px-4 py-2.5 font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {visualize.isPending
              ? 'Generating preview (high quality — may take 1–2 minutes)…'
              : 'Generate goal preview'}
          </button>
        </div>
      </section>

      {visualize.data && generatedSrc && imagePreviewUrl && (
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-slate-400">
            Before & after (AI)
          </h2>
          <div className="grid gap-6 sm:grid-cols-2">
            <figure>
              <figcaption className="mb-2 text-xs uppercase tracking-wide text-slate-500">
                Your photo
              </figcaption>
              <img
                src={imagePreviewUrl}
                alt="Before"
                className="w-full rounded-lg border border-slate-700 object-contain"
              />
            </figure>
            <figure>
              <figcaption className="mb-2 text-xs uppercase tracking-wide text-slate-500">
                Goal preview
              </figcaption>
              <img
                src={generatedSrc}
                alt="AI goal weight preview"
                className="w-full rounded-lg border border-slate-700 object-contain"
              />
            </figure>
          </div>
          <p className="mt-4 text-xs text-slate-500">{visualize.data.disclaimer}</p>
        </section>
      )}
    </div>
  )
}
