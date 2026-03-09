export default function Settings() {
  return (
    <div>
      <div className="page-header">
        <h2>Settings</h2>
        <p>Platform configuration and preferences</p>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <h3>API Configuration</h3>
          </div>
          <div className="form-group">
            <label>API Base URL</label>
            <input type="text" value="/api/v1" disabled />
          </div>
          <div className="form-group">
            <label>Server Port</label>
            <input type="text" value="8080" disabled />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>About</h3>
          </div>
          <table>
            <tbody>
              <tr><td style={{ color: 'var(--text-secondary)' }}>Platform</td><td>Mrki AI</td></tr>
              <tr><td style={{ color: 'var(--text-secondary)' }}>Version</td><td>1.0.0</td></tr>
              <tr><td style={{ color: 'var(--text-secondary)' }}>Framework</td><td>FastAPI + React</td></tr>
              <tr><td style={{ color: 'var(--text-secondary)' }}>License</td><td>Personal Use</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
