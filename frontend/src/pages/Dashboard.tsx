import { useEffect, useState } from 'react'
import { api } from '../utils/api'

interface HealthData {
  status: string
  modules: string[]
  uptime?: number
  version?: string
  timestamp?: number
}

interface ModuleHealth {
  name: string
  status: string
  label: string
}

const MODULE_LABELS: Record<string, string> = {
  core: 'Core Orchestrator',
  visual_engine: 'Visual Engine',
  dev_env: 'Dev Environment',
  moe: 'Mixture of Experts',
  gamedev: 'Game Development',
}

export default function Dashboard() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [modules, setModules] = useState<ModuleHealth[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const healthData = await api.getHealth()
        setHealth(healthData)

        // Check each module
        const moduleChecks = [
          { fn: () => api.getCoreHealth(), name: 'core' },
          { fn: () => api.getVisualHealth(), name: 'visual_engine' },
          { fn: () => api.getDevHealth(), name: 'dev_env' },
          { fn: () => api.getMoeHealth(), name: 'moe' },
          { fn: () => api.getGamedevHealth(), name: 'gamedev' },
        ]

        const results = await Promise.allSettled(moduleChecks.map((m) => m.fn()))
        const moduleStatuses = moduleChecks.map((m, i) => {
          const result = results[i]
          const data = result.status === 'fulfilled' ? result.value : null
          return {
            name: m.name,
            status: data?.status || 'unavailable',
            label: MODULE_LABELS[m.name] || m.name,
          }
        })
        setModules(moduleStatuses)
      } catch (err) {
        console.error('Failed to fetch health:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        Loading dashboard...
      </div>
    )
  }

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    return h > 0 ? `${h}h ${m}m` : `${m}m`
  }

  const healthyCount = modules.filter((m) => m.status === 'healthy').length

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>System overview and module health status</p>
      </div>

      {/* Stats */}
      <div className="grid grid-4" style={{ marginBottom: '24px' }}>
        <div className="card stat-card">
          <span className="stat-label">Status</span>
          <span className="stat-value" style={{ color: health?.status === 'healthy' ? 'var(--success)' : 'var(--error)' }}>
            {health?.status || 'Unknown'}
          </span>
          <span className="stat-detail">API server</span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Modules</span>
          <span className="stat-value">{healthyCount}/{modules.length}</span>
          <span className="stat-detail">Active modules</span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Uptime</span>
          <span className="stat-value">{health?.uptime ? formatUptime(health.uptime) : '-'}</span>
          <span className="stat-detail">Since last restart</span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Version</span>
          <span className="stat-value">{health?.version || '-'}</span>
          <span className="stat-detail">API version</span>
        </div>
      </div>

      {/* Modules */}
      <div className="card">
        <div className="card-header">
          <h3>Module Status</h3>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Module</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {modules.map((mod) => (
                <tr key={mod.name}>
                  <td>
                    <div className="module-card">
                      <div className="module-info">
                        <h4>{mod.label}</h4>
                        <p>{mod.name}</p>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`badge badge-${mod.status}`}>
                      <span className={`status-dot ${mod.status}`} />
                      {mod.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
