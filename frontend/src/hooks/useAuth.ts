import { useState, useCallback } from 'react'
import { api } from '../utils/api'

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!api.getToken())
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const login = useCallback(async (username: string, password: string) => {
    setLoading(true)
    setError(null)
    try {
      await api.login(username, password)
      setIsAuthenticated(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }, [])

  const register = useCallback(async (username: string, password: string) => {
    setLoading(true)
    setError(null)
    try {
      await api.register(username, password)
      await api.login(username, password)
      setIsAuthenticated(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    api.logout()
    setIsAuthenticated(false)
  }, [])

  return { isAuthenticated, error, loading, login, register, logout }
}
