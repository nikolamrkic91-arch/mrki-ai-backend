import { NavLink } from 'react-router-dom'

interface SidebarProps {
  onLogout: () => void
}

export default function Sidebar({ onLogout }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h1>Mrki AI</h1>
        <span className="version">v1.0</span>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end>
          Dashboard
        </NavLink>
        <NavLink to="/modules">
          Modules
        </NavLink>
        <NavLink to="/workflows">
          Workflows
        </NavLink>
        <NavLink to="/tasks">
          Tasks
        </NavLink>
        <NavLink to="/settings">
          Settings
        </NavLink>
      </nav>

      <div style={{ padding: '12px' }}>
        <button className="btn btn-outline btn-full" onClick={onLogout}>
          Logout
        </button>
      </div>
    </aside>
  )
}
