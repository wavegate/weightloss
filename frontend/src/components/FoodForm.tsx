import { useForm } from 'react-hook-form'

import { useCreateFoodMutation } from '../hooks/useFoods'

type FoodFormValues = {
  recorded_at: string
  name: string
  description: string
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10)
}

export function FoodForm() {
  const createFood = useCreateFoodMutation()

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

  const onSubmit = handleSubmit((values) => {
    createFood.mutate(values, {
      onSuccess: () => {
        reset({
          recorded_at: todayIsoDate(),
          name: '',
          description: '',
        })
      },
    })
  })

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
        <label htmlFor="food_name" className="mb-1 block text-sm text-slate-400">
          Food name
        </label>
        <input
          id="food_name"
          type="text"
          placeholder="e.g. Grilled chicken salad"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          {...register('name', { required: 'Food name is required' })}
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
          Description
        </label>
        <textarea
          id="food_description"
          rows={3}
          placeholder="Portion size, ingredients, preparation…"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          {...register('description', { required: 'Description is required' })}
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
