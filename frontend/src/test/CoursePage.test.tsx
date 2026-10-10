import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import type { CourseDetail } from '../api/types'
import CoursePage from '../pages/CoursePage'

vi.mock('../api/courses', () => ({
  getCourse: vi.fn(),
}))

vi.mock('../api/lectures', () => ({
  addLecture: vi.fn(),
  updateLecture: vi.fn(),
  deleteLecture: vi.fn(),
}))

vi.mock('../api/materials', () => ({
  listMaterials: vi.fn(),
}))

import { getCourse } from '../api/courses'
import { updateLecture } from '../api/lectures'
import { listMaterials } from '../api/materials'

const mockedGetCourse = vi.mocked(getCourse)
const mockedUpdateLecture = vi.mocked(updateLecture)
const mockedListMaterials = vi.mocked(listMaterials)

const courseFixture: CourseDetail = {
  id: 1,
  name: 'Computer Networks',
  created_at: '2026-10-07T00:00:00Z',
  updated_at: '2026-10-07T00:00:00Z',
  lectures: [
    {
      id: 11,
      order_index: 1,
      title: 'Introduction',
      status: 'understood',
      created_at: '2026-10-07T00:00:00Z',
      updated_at: '2026-10-07T00:00:00Z',
    },
    {
      id: 12,
      order_index: 2,
      title: 'Congestion Control',
      status: 'missed',
      created_at: '2026-10-07T00:00:00Z',
      updated_at: '2026-10-07T00:00:00Z',
    },
    {
      id: 13,
      order_index: 3,
      title: 'Quality of Service',
      status: 'upcoming',
      created_at: '2026-10-07T00:00:00Z',
      updated_at: '2026-10-07T00:00:00Z',
    },
  ],
  summary: {
    last_understood_lecture: {
      id: 11,
      order_index: 1,
      title: 'Introduction',
      status: 'understood',
    },
    upcoming_lecture: {
      id: 13,
      order_index: 3,
      title: 'Quality of Service',
      status: 'upcoming',
    },
    missed_lectures: [{ id: 12, order_index: 2, title: 'Congestion Control', status: 'missed' }],
    unmarked_before_upcoming: [],
  },
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/courses/1']}>
      <Routes>
        <Route path="/courses/:courseId" element={<CoursePage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('CoursePage', () => {
  it('shows the course, its lectures, and the derived situation', async () => {
    mockedGetCourse.mockResolvedValue(courseFixture)
    renderPage()

    expect(await screen.findByRole('heading', { name: 'Computer Networks' })).toBeInTheDocument()
    expect(screen.getByText('L1 Introduction')).toBeInTheDocument()
    expect(screen.getByText('L2 Congestion Control')).toBeInTheDocument()
    expect(screen.getByText('L3 Quality of Service')).toBeInTheDocument()
    expect(screen.getByLabelText('Your position')).toBeInTheDocument()
    expect(screen.getByText('L2 Congestion Control')).toBeInTheDocument()
  })

  it('persists a status change and reloads the course', async () => {
    const user = userEvent.setup()
    mockedGetCourse.mockResolvedValue(courseFixture)
    mockedUpdateLecture.mockResolvedValue({
      ...courseFixture.lectures[1],
      status: 'understood',
    })

    renderPage()
    await screen.findByRole('heading', { name: 'Computer Networks' })

    await user.selectOptions(screen.getByLabelText('Status for Congestion Control'), 'understood')

    await waitFor(() => {
      expect(mockedUpdateLecture).toHaveBeenCalledWith(12, { status: 'understood' })
    })
    await waitFor(() => {
      expect(mockedGetCourse).toHaveBeenCalledTimes(2)
    })
  })

  it('shows an error when the course does not exist', async () => {
    mockedGetCourse.mockRejectedValue(new Error('Course 999 not found'))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('Course 999 not found')
  })

  it('expands materials for one lecture at a time', async () => {
    const user = userEvent.setup()
    mockedGetCourse.mockResolvedValue(courseFixture)
    mockedListMaterials.mockResolvedValue([])

    renderPage()
    await screen.findByRole('heading', { name: 'Computer Networks' })

    await user.click(screen.getByRole('button', { name: 'Materials for Introduction' }))
    expect(await screen.findByLabelText('Materials for Introduction')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Materials for Quality of Service' }))
    expect(screen.getByLabelText('Materials for Quality of Service')).toBeInTheDocument()
    expect(screen.queryByLabelText('Materials for Introduction')).not.toBeInTheDocument()
  })
})
