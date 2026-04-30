import { NavLink } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  BarChart2,
  DollarSign,
  FileText,
  Home,
  Image,
  Mic,
  Radio,
  Users,
  XCircle,
  Zap,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: Home },
  { to: '/users', label: 'Users', icon: Users },
  { to: '/requests', label: 'All Requests', icon: FileText },
  { to: '/requests/text', label: '↳ Text', icon: FileText, indent: true },
  { to: '/requests/photo', label: '↳ Photo', icon: Image, indent: true },
  { to: '/requests/voice', label: '↳ Voice', icon: Mic, indent: true },
  { to: '/requests/low', label: '↳ Low confidence', icon: Zap, indent: true },
  { to: '/requests/failed', label: '↳ Failed', icon: XCircle, indent: true },
  { to: '/usage/traffic', label: 'Traffic', icon: BarChart2 },
  { to: '/usage/costs', label: 'Costs', icon: DollarSign },
  { to: '/errors', label: 'Errors', icon: AlertTriangle },
  { to: '/broadcast', label: 'Broadcast', icon: Radio },
]

export default function Sidebar() {
  const { logout } = useAuth()

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Activity size={20} />
        <span>TNVED Admin</span>
      </div>
      <nav>
        {navItems.map(({ to, label, icon: Icon, indent }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx('sidebar-link', isActive && 'active', indent && 'indent')
            }
          >
            <Icon size={16} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <button className="sidebar-logout" onClick={logout}>
        Logout
      </button>
    </aside>
  )
}
