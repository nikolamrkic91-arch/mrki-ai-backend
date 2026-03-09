import { useState } from 'react'
import { api } from '../utils/api'

export default function Tasks() {
  const [taskName, setTaskName] = useState('')
  const [taskDescription, setTaskDescription] = useState('')
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await api.executeTask({
        name: taskName,
        description: taskDescription,
      })
      setResult(JSON.stringify(response, null, 2))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Task execution failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Tasks</h2>
        <p>Execute tasks through the core orchestrator</p>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <h3>Execute Task</h3>
          </div>

          <form onSubmit={handleExecute}>
            <div className="form-group">
              <label>Task Name</label>
              <input
                type="text"
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
                placeholder="e.g. data-processing"
                required
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                placeholder="Describe what this task should do..."
                rows={4}
                style={{ resize: 'vertical' }}
              />
            </div>

            {error && <p className="form-error">{error}</p>}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ marginTop: '8px' }}
            >
              {loading ? 'Executing...' : 'Execute Task'}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Result</h3>
          </div>

          {result ? (
            <pre style={{
              background: 'var(--bg-primary)',
              padding: '16px',
              borderRadius: 'var(--radius)',
              fontSize: '13px',
              overflow: 'auto',
              maxHeight: '400px',
              lineHeight: '1.5',
            }}>
              {result}
            </pre>
          ) : (
            <div className="empty-state">
              <p>Execute a task to see results here.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
