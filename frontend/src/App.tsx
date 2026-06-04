import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ApiAuthProvider } from './components/ApiAuthProvider'
import { Layout } from './components/Layout'
import { RequireAuth } from './components/RequireAuth'
import { FoodLogPage } from './pages/FoodLogPage'
import { MeasurementsPage } from './pages/MeasurementsPage'
import { MetabolismPage } from './pages/MetabolismPage'
import { EventManagerPage } from './pages/EventManagerPage'
import { VisionPage } from './pages/VisionPage'
import { SignInPage } from './pages/SignInPage'
import { SignUpPage } from './pages/SignUpPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/sign-in/*" element={<SignInPage />} />
        <Route path="/sign-up/*" element={<SignUpPage />} />

        <Route element={<RequireAuth />}>
          <Route path="event-manager" element={<EventManagerPage />} />
          <Route
            element={
              <ApiAuthProvider>
                <Layout />
              </ApiAuthProvider>
            }
          >
            <Route index element={<Navigate to="/measurements" replace />} />
            <Route path="measurements" element={<MeasurementsPage />} />
            <Route path="food" element={<FoodLogPage />} />
            <Route path="metabolism" element={<MetabolismPage />} />
            <Route path="vision" element={<VisionPage />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
