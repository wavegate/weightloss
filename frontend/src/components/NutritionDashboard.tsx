import { useState } from 'react'

import { DailyNutritionSummary } from './DailyNutritionSummary'
import {
  NutritionDateNav,
  type NutritionViewMode,
} from './NutritionDateNav'
import { WeeklyNutritionSummary } from './WeeklyNutritionSummary'
import { todayIsoDate } from '../lib/nutritionTargets'

export function NutritionDashboard() {
  const [selectedDate, setSelectedDate] = useState(todayIsoDate)
  const [viewMode, setViewMode] = useState<NutritionViewMode>('daily')

  return (
    <div className="flex flex-col gap-4">
      <NutritionDateNav
        selectedDate={selectedDate}
        onSelectedDateChange={setSelectedDate}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />
      {viewMode === 'daily' ? (
        <DailyNutritionSummary selectedDate={selectedDate} />
      ) : (
        <WeeklyNutritionSummary weekEndDate={selectedDate} />
      )}
    </div>
  )
}
