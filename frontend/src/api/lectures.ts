import { request } from './client'
import type { Lecture, LectureStatus } from './types'

export function addLecture(courseId: number, title: string): Promise<Lecture> {
  return request<Lecture>(`/courses/${courseId}/lectures`, {
    method: 'POST',
    body: JSON.stringify({ title }),
  })
}

export function updateLecture(
  id: number,
  patch: { title?: string; status?: LectureStatus },
): Promise<Lecture> {
  return request<Lecture>(`/lectures/${id}`, { method: 'PATCH', body: JSON.stringify(patch) })
}

export function deleteLecture(id: number): Promise<void> {
  return request<void>(`/lectures/${id}`, { method: 'DELETE' })
}
