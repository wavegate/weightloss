import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { FoodLogPage } from './pages/FoodLogPage'
import { MeasurementsPage } from './pages/MeasurementsPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Navigate to="/measurements" replace />} />
          <Route path="measurements" element={<MeasurementsPage />} />
          <Route path="food" element={<FoodLogPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
