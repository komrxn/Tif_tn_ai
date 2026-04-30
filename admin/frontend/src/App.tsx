import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { useAuth } from './hooks/useAuth'
import Broadcast from './pages/Broadcast'
import Costs from './pages/Costs'
import Dashboard from './pages/Dashboard'
import Errors from './pages/Errors'
import Login from './pages/Login'
import Requests from './pages/Requests'
import Traffic from './pages/Traffic'
import Users from './pages/Users'

function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="users" element={<Users />} />
        <Route path="requests" element={<Requests defaultType="all" />} />
        <Route path="requests/text" element={<Requests defaultType="text" />} />
        <Route path="requests/photo" element={<Requests defaultType="photo" />} />
        <Route path="requests/voice" element={<Requests defaultType="voice" />} />
        <Route path="requests/low" element={<Requests defaultType="low_confidence" />} />
        <Route path="requests/failed" element={<Requests defaultType="failed" />} />
        <Route path="usage/traffic" element={<Traffic />} />
        <Route path="usage/costs" element={<Costs />} />
        <Route path="errors" element={<Errors />} />
        <Route path="broadcast" element={<Broadcast />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
