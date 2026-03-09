import { useEffect, useState } from 'react'
import { api } from '../utils/api'

interface ModuleInfo {
  name: string
  label: string
  description: string
  status: string
}

const MODULES: Omit<ModuleInfo, 'status'>[] = [
  { name: 'core', label: 'Core Orchestrator', description: '50+ agents, task decomposition, tool registry, and state management' },
  { name: 'visual_engine', label: 'Visual Engine', description: 'Image analysis, sketch-to-code, design extraction, and visual debugging' },
  { name: 'dev_env', label: 'Dev Environment', description: 'Project scaffolding, API builder, CI/CD generation, and Docker tooling' },
  { name: 'moe', label: 'Mixture of Experts', description: '64-expert routing, quantization, fine-tuning, and local inference' },
  { name: 'gamedev', label: 'Game Development', description: 'Unity, Unreal, and Godot code generation with physics and animation' },
]

export default function Modules() {
  const [modules, setModules] = useState<ModuleInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchModules() {
      const healthChecks: Record<string, () => Promise<{ status: string }>> = {
        core: () => api.getCoreHealth(),
        visual_engine: () => api.getVisualHealth(),
        dev_env: () => api.getDevHealth(),
        moe: () => api.getMoeHealth(),
        gamedev: () => api.getGamedevHealth(),
      }

      const results = await Promise.allSettled(
        MODULES.map(async (mod) => {
          try {
            const health = await healthChecks[mod.name]()
            return { ...mod, status: health.status }
          } catch {
            return { ...mod, status: 'unavailable' }
          }
        })
      )

      setModules(
        results.map((r) => (r.status === 'fulfilled' ? r.value : { ...MODULES[0], status: 'error' }))
      )
      setLoading(false)
    }

    fetchModules()
  }, [])

  if (loading) {
    return <div className="loading"><div className="spinner" />Loading modules...</div>
  }

  return (
    <div>
      <div className="page-header">
        <h2>Modules</h2>
        <p>Platform modules and their health status</p>
      </div>

      <div className="grid grid-2">
        {modules.map((mod) => (
          <div className="card" key={mod.name}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <h3 style={{ fontSize: '16px' }}>{mod.label}</h3>
              <span className={`badge badge-${mod.status}`}>
                <span className={`status-dot ${mod.status}`} />
                {mod.status}
              </span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
              {mod.description}
            </p>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Endpoint: <code>/api/v1/{mod.name === 'visual_engine' ? 'visual' : mod.name === 'dev_env' ? 'dev' : mod.name}</code>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
