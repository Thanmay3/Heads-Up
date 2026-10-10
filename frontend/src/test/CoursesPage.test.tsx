import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import CoursesPage from '../pages/CoursesPage'

vi.mock('../api/courses', () => ({
  listCourses: vi.fn(),
  getCourse: vi.fn(),
  createCourse: vi.fn(),
  deleteCourse: vi.fn(),
}))

import { createCourse, listCourses } from '../api/courses'

const mockedCourses = vi.mocked(listCourses)
const mockedCreate = vi.mocked(createCourse)

function renderPage() {
  return render(
    <MemoryRouter>
      <CoursesPage />
    </MemoryRouter>,
  )
}

describe('CoursesPage', () => {
  it('lists courses with their lecture and missed counts', async () => {
    mockedCourses.mockResolvedValue([
      {
        id: 1,
        name: 'Computer Networks',
        lecture_count: 11,
        missed_count: 2,
        created_at: '2026-10-07T00:00:00Z',
        updated_at: '2026-10-07T00:00:00Z',
      },
    ])

    renderPage()

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /Computer Networks/ })).toBeInTheDocument()
    })
    expect(screen.getByText('11 lectures')).toBeInTheDocument()
    expect(screen.getByText('2 missed')).toBeInTheDocument()
  })

  it('creates a course and reloads the list', async () => {
    const user = userEvent.setup()
    mockedCourses
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          id: 9,
          name: 'Operating Systems',
          lecture_count: 0,
          missed_count: 0,
          created_at: '2026-10-07T00:00:00Z',
          updated_at: '2026-10-07T00:00:00Z',
        },
      ])
    mockedCreate.mockResolvedValue({
      id: 9,
      name: 'Operating Systems',
      created_at: '2026-10-07T00:00:00Z',
      updated_at: '2026-10-07T00:00:00Z',
    })

    renderPage()
    await screen.findByText(/no courses yet/i)

    await user.type(screen.getByLabelText('Course name'), 'Operating Systems')
    await user.click(screen.getByRole('button', { name: 'Create course' }))

    await waitFor(() => {
      expect(mockedCreate).toHaveBeenCalledWith('Operating Systems')
    })
    expect(await screen.findByText('Operating Systems')).toBeInTheDocument()
  })

  it('shows an error message when loading fails', async () => {
    mockedCourses.mockRejectedValue(new Error('API is down'))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('API is down')
  })
})
