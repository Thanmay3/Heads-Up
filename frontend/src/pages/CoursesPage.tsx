import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { createCourse, listCourses } from '../api/courses'
import type { CourseListItem } from '../api/types'

export default function CoursesPage() {
  const [courses, setCourses] = useState<CourseListItem[]>([])
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      setCourses(await listCourses())
      setError(null)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Failed to load courses')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    try {
      await createCourse(trimmed)
      setName('')
      await load()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Failed to create course')
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">HeadsUp</h1>
        <p className="mt-1 text-sm text-slate-600">
          Track your courses so you never walk into a lecture lost. Pick a course to mark where
          you stand.
        </p>
      </header>

      <form aria-label="Create course" onSubmit={handleCreate} className="mt-6 flex gap-2">
        <input
          aria-label="Course name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="New course name, e.g. Computer Networks"
          maxLength={120}
          className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-2 focus:outline-sky-500"
        />
        <button
          type="submit"
          disabled={!name.trim()}
          className="shrink-0 rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Create course
        </button>
      </form>

      {error && (
        <p role="alert" className="mt-4 rounded-lg border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {error}
        </p>
      )}

      {loading ? (
        <p className="mt-6 text-sm text-slate-500">Loading courses…</p>
      ) : courses.length === 0 ? (
        <p className="mt-6 text-sm text-slate-500">
          No courses yet. Create one above to start tracking lectures.
        </p>
      ) : (
        <ul className="mt-6 space-y-2">
          {courses.map((course) => (
            <li key={course.id}>
              <Link
                to={`/courses/${course.id}`}
                className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm hover:border-sky-400"
              >
                <span className="font-semibold text-slate-900">{course.name}</span>
                <span className="text-xs text-slate-500">
                  {course.lecture_count}{' '}
                  {course.lecture_count === 1 ? 'lecture' : 'lectures'}
                  {course.missed_count > 0 && (
                    <span className="ml-2 rounded-full bg-rose-100 px-2 py-0.5 font-semibold text-rose-700">
                      {course.missed_count} missed
                    </span>
                  )}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}
