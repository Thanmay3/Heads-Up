import { BrowserRouter, Route, Routes } from 'react-router-dom'
import CoursePage from './pages/CoursePage'
import CoursesPage from './pages/CoursesPage'

export default function App() {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<CoursesPage />} />
          <Route path="/courses/:courseId" element={<CoursePage />} />
        </Routes>
      </BrowserRouter>
    </div>
  )
}
