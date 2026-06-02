import { useForm } from 'react-hook-form'

import { useCreateMeasurementMutation } from '../hooks/useMeasurements'

type MeasurementFormValues = {
  recorded_at: string
  body_weight_lbs: string
  waist_inches: string
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10)
}

export function MeasurementForm() {
  const createMeasurement = useCreateMeasurementMutation()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MeasurementFormValues>({
    defaultValues: {
      recorded_at: todayIsoDate(),
      body_weight_lbs: '',
      waist_inches: '',
    },
  })

  const onSubmit = handleSubmit((values) => {
    createMeasurement.mutate(
      {
        recorded_at: values.recorded_at,
        body_weight_lbs: Number(values.body_weight_lbs),
        waist_inches: Number(values.waist_inches),
      },
      {
        onSuccess: () => {
          reset({
            recorded_at: todayIsoDate(),
            body_weight_lbs: '',
            waist_inches: '',
          })
        },
      },
    )
  })

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label htmlFor="recorded_at" className="mb-1 block text-sm text-slate-400">
          Date
        </label>
        <input
          id="recorded_at"
          type="date"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          {...register('recorded_at', { required: 'Date is required' })}
        />
        {errors.recorded_at && (
          <p className="mt-1 text-sm text-red-400">{errors.recorded_at.message}</p>
        )}
      </div>

      <div>
        <label
          htmlFor="body_weight_lbs"
          className="mb-1 block text-sm text-slate-400"
        >
          Body weight (lb)
        </label>
        <input
          id="body_weight_lbs"
          type="number"
          step="0.1"
          min="0"
          placeholder="e.g. 180"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          {...register('body_weight_lbs', {
            required: 'Body weight is required',
            validate: (value) =>
              Number(value) > 0 || 'Enter a weight greater than 0',
          })}
        />
        {errors.body_weight_lbs && (
          <p className="mt-1 text-sm text-red-400">
            {errors.body_weight_lbs.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="waist_inches" className="mb-1 block text-sm text-slate-400">
          Waist circumference (in)
        </label>
        <input
          id="waist_inches"
          type="number"
          step="0.1"
          min="0"
          placeholder="e.g. 34"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
          {...register('waist_inches', {
            required: 'Waist measurement is required',
            validate: (value) =>
              Number(value) > 0 || 'Enter a measurement greater than 0',
          })}
        />
        {errors.waist_inches && (
          <p className="mt-1 text-sm text-red-400">{errors.waist_inches.message}</p>
        )}
      </div>

      {createMeasurement.isError && (
        <p className="text-sm text-red-400">
          {createMeasurement.error instanceof Error
            ? createMeasurement.error.message
            : 'Failed to save measurement'}
        </p>
      )}

      <button
        type="submit"
        disabled={createMeasurement.isPending}
        className="w-full rounded-lg bg-violet-600 px-4 py-2.5 font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {createMeasurement.isPending ? 'Saving…' : 'Save measurement'}
      </button>
    </form>
  )
}
