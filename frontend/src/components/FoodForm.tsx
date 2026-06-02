import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'

import { useCreateFoodMutation } from '../hooks/useFoods'
import { todayIsoDate } from '../lib/nutritionTargets'

const MAX_IMAGE_BYTES = 5 * 1024 * 1024
const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']

type FoodFormValues = {
  recorded_at: string
  name: string
  description: string
}

function validateImageFile(file: File): string | null {
  if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    return 'Use a JPEG, PNG, WebP, or GIF image'
  }
  if (file.size > MAX_IMAGE_BYTES) {
    return 'Image must be 5 MB or smaller'
  }
  return null
}

export function FoodForm() {
  const createFood = useCreateFoodMutation()
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null)
  const [imageError, setImageError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FoodFormValues>({
    defaultValues: {
      recorded_at: todayIsoDate(),
      name: '',
      description: '',
    },
  })

  useEffect(() => {
    if (!imageFile) {
      setImagePreviewUrl(null)
      return
    }
    const url = URL.createObjectURL(imageFile)
    setImagePreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [imageFile])

  const clearImage = () => {
    setImageFile(null)
    setImageError(null)
  }

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
  }

  const onSubmit = handleSubmit((values) => {
    const hasText = values.name.trim() && values.description.trim()
    if (!imageFile && !hasText) {
      setImageError('Add a photo or fill in food name and description')
      return
    }

    createFood.mutate(
      {
        ...values,
        image: imageFile,
      },
      {
        onSuccess: () => {
          reset({
            recorded_at: todayIsoDate(),
            name: '',
            description: '',
          })
          clearImage()
        },
      },
    )
  })

  const hasImage = imageFile !== null

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label htmlFor="food_date" className="mb-1 block text-sm text-slate-400">
          Date
        </label>
        <input
          id="food_date"
          type="date"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          {...register('recorded_at', { required: 'Date is required' })}
        />
        {errors.recorded_at && (
          <p className="mt-1 text-sm text-red-400">{errors.recorded_at.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="food_image" className="mb-1 block text-sm text-slate-400">
          Photo (optional)
        </label>
        <input
          id="food_image"
          type="file"
          accept={ACCEPTED_IMAGE_TYPES.join(',')}
          capture="environment"
          onChange={onImageChange}
          className="w-full text-sm text-slate-300 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-2 file:text-slate-100"
        />
        <p className="mt-1 text-xs text-slate-500">
          Upload a meal photo for AI analysis, or describe the food below.
        </p>
        {imagePreviewUrl && (
          <div className="mt-3 flex items-start gap-3">
            <img
              src={imagePreviewUrl}
              alt="Selected meal"
              className="h-24 w-24 rounded-lg border border-slate-700 object-cover"
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
        <label htmlFor="food_name" className="mb-1 block text-sm text-slate-400">
          Food name{hasImage ? ' (optional)' : ''}
        </label>
        <input
          id="food_name"
          type="text"
          placeholder="e.g. Grilled chicken salad"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          {...register('name', {
            validate: (value) => {
              if (hasImage) {
                return true
              }
              return value.trim() ? true : 'Food name is required without a photo'
            },
          })}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-400">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label
          htmlFor="food_description"
          className="mb-1 block text-sm text-slate-400"
        >
          Description{hasImage ? ' (optional)' : ''}
        </label>
        <textarea
          id="food_description"
          rows={3}
          placeholder="Portion size, ingredients, preparation…"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          {...register('description', {
            validate: (value) => {
              if (hasImage) {
                return true
              }
              return value.trim()
                ? true
                : 'Description is required without a photo'
            },
          })}
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-400">
            {errors.description.message}
          </p>
        )}
      </div>

      {createFood.isError && (
        <p className="text-sm text-red-400">
          {createFood.error instanceof Error
            ? createFood.error.message
            : 'Failed to save food entry'}
        </p>
      )}

      <button
        type="submit"
        disabled={createFood.isPending}
        className="w-full rounded-lg bg-violet-600 px-4 py-2.5 font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {createFood.isPending
          ? 'Estimating nutrition with AI…'
          : 'Add food & estimate macros'}
      </button>
    </form>
  )
}
