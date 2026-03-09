import { Routes, Route } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Modules from './pages/Modules'
import Workflows from './pages/Workflows'
import Tasks from './pages/Tasks'
import Settings from './pages/Settings'

export default function App() {
  const { isAuthenticated, error, loading, login, register, logout } = useAuth()

  if (!isAuthenticated) {
    return <Login onLogin={login} onRegister={register} error={error} loading={loading} />
  }

  return (
    <div className="app">
      <Sidebar onLogout={logout} />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/modules" element={<Modules />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
