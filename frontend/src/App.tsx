import { Outlet } from 'react-router-dom'
import { Sidebar } from './components/layout/Sidebar'
import { TopBar } from './components/layout/TopBar'

/**
 * DashboardLayout — the shared shell for all dashboard sub-routes.
 * Sidebar (left rail, fixed) + TopBar (top, fixed) + scrollable content area.
 * Exported so router.tsx can reference it without a circular import.
 */
export function DashboardLayout() {
  return (
    <div
      className="flex h-screen overflow-hidden"
      style={{ backgroundColor: 'var(--bg-void)' }}
    >
      {/* Left rail — case index / folder tabs */}
      <Sidebar />

      {/* Main area: TopBar + scrollable page content */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar />
        <main
          className="flex-1 overflow-y-auto"
          style={{ backgroundColor: 'var(--bg-charcoal)' }}
        >
          <Outlet />
        </main>
      </div>
    </div>
  )
}
