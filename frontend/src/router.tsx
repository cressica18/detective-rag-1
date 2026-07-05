import { createBrowserRouter } from 'react-router-dom'
import { LandingPage } from './pages/LandingPage'
import { UploadPage } from './pages/UploadPage'
import { DashboardHome } from './pages/DashboardHome'
import { ChatPage } from './pages/ChatPage'
import { TimelinePage } from './pages/TimelinePage'
import { SuspectBoardPage } from './pages/SuspectBoardPage'
import { EvidenceViewerPage } from './pages/EvidenceViewerPage'
import { CaseSummaryPage } from './pages/CaseSummaryPage'
import { DashboardLayout } from './App'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/upload',
    element: <UploadPage />,
  },
  {
    // Dashboard shell — all sub-routes share Sidebar + TopBar
    element: <DashboardLayout />,
    children: [
      { path: '/dashboard', element: <DashboardHome /> },
      { path: '/chat', element: <ChatPage /> },
      { path: '/timeline', element: <TimelinePage /> },
      { path: '/suspects', element: <SuspectBoardPage /> },
      { path: '/evidence', element: <EvidenceViewerPage /> },
      { path: '/summary', element: <CaseSummaryPage /> },
    ],
  },
])
