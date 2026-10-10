import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCourse } from '../api/courses'
import { addLecture, deleteLecture, updateLecture } from '../api/lectures'
import type { CourseDetail, LectureStatus } from '../api/types'
import AddLectureForm from '../components/AddLectureForm'
import GetReadyCard from '../components/GetReadyCard'
import LectureRow from '../components/LectureRow'
import SituationPanel from '../components/SituationPanel'

export default function CoursePage() {
  const { courseId } = useParams()
  const id = Number(courseId)
  const [course, setCourse] = useState<CourseDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedMaterialsFor, setExpandedMaterialsFor] = useState<number | null>(null)

  const load = useCallback(async () => {
    try {
      setCourse(await getCourse(id))
      setError(null)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Failed to load course')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  async function handleStatusChange(lectureId: number, status: LectureStatus) {
    try {
      await updateLecture(lectureId, { status })
      await load()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Failed to update lecture')
    }
  }

  async function handleDelete(lectureId: number) {
    try {
      await deleteLecture(lectureId)
      await load()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Failed to delete lecture')
    }
  }

  async function handleAdd(title: string) {
    try {
      await addLecture(id, title)
      await load()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Failed to add lecture')
    }
  }

  function handleToggleMaterials(lectureId: number) {
    setExpandedMaterialsFor((current) => (current === lectureId ? null : lectureId))
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-8">
      <Link to="/" className="text-sm font-medium text-sky-700 hover:underline">
        ← All courses
      </Link>
      {loading ? (
        <p className="mt-6 text-sm text-slate-500">Loading course…</p>
      ) : error && course === null ? (
        <p role="alert" className="mt-6 rounded-lg border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {error}
        </p>
      ) : course === null ? null : (
        <>
          <h1 className="mt-2 text-2xl font-bold text-slate-900">{course.name}</h1>

          {error && (
            <p role="alert" className="mt-4 rounded-lg border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800">
              {error}
            </p>
          )}

          <div className="mt-4">
            <SituationPanel summary={course.summary} />
          </div>

          <section aria-label="Lectures" className="mt-6">
            <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase">
              Lectures
            </h2>
            {course.lectures.length === 0 ? (
              <p className="mt-3 text-sm text-slate-500">
                No lectures yet. Add them in the order the course teaches them.
              </p>
            ) : (
              <ul className="mt-3 space-y-2">
                {course.lectures.map((lecture) => (
                  <LectureRow
                    key={lecture.id}
                    lecture={lecture}
                    onStatusChange={handleStatusChange}
                    onDelete={handleDelete}
                    materialsExpanded={expandedMaterialsFor === lecture.id}
                    onToggleMaterials={handleToggleMaterials}
                  />
                ))}
              </ul>
            )}
            <div className="mt-4">
              <AddLectureForm onAdd={handleAdd} />
            </div>
          </section>

          <div className="mt-6">
            <GetReadyCard />
          </div>
        </>
      )}
    </main>
  )
}
