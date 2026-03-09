export default function Workflows() {
  return (
    <div>
      <div className="page-header">
        <h2>Workflows</h2>
        <p>Create and manage automation workflows</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Workflows</h3>
          <button className="btn btn-primary">New Workflow</button>
        </div>

        <div className="empty-state">
          <p>No workflows yet. Create your first workflow to get started.</p>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Workflows let you chain tasks together with dependencies, variables, and error handling.
          </p>
        </div>
      </div>
    </div>
  )
}
