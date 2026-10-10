import { request } from './client'
import type { Course, CourseDetail, CourseListItem } from './types'

export function listCourses(): Promise<CourseListItem[]> {
  return request<CourseListItem[]>('/courses')
}

export function getCourse(id: number): Promise<CourseDetail> {
  return request<CourseDetail>(`/courses/${id}`)
}

export function createCourse(name: string): Promise<Course> {
  return request<Course>('/courses', { method: 'POST', body: JSON.stringify({ name }) })
}

export function deleteCourse(id: number): Promise<void> {
  return request<void>(`/courses/${id}`, { method: 'DELETE' })
}
