import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { Lecture } from '../api/types'
import LectureRow from '../components/LectureRow'

const lecture: Lecture = {
  id: 7,
  order_index: 3,
  title: 'Congestion Control',
  status: 'unmarked',
  created_at: '2026-10-07T00:00:00Z',
  updated_at: '2026-10-07T00:00:00Z',
}

describe('LectureRow', () => {
  it('renders the lecture number and title', () => {
    render(<LectureRow lecture={lecture} onStatusChange={vi.fn()} onDelete={vi.fn()} />)
    expect(screen.getByText('L3')).toBeInTheDocument()
    expect(screen.getByText('Congestion Control')).toBeInTheDocument()
  })

  it('reports status changes with the lecture id', async () => {
    const user = userEvent.setup()
    const onStatusChange = vi.fn()
    render(<LectureRow lecture={lecture} onStatusChange={onStatusChange} onDelete={vi.fn()} />)

    await user.selectOptions(
      screen.getByLabelText('Status for Congestion Control'),
      'understood',
    )
    expect(onStatusChange).toHaveBeenCalledWith(7, 'understood')
  })

  it('only deletes after the confirmation dialog is accepted', async () => {
    const user = userEvent.setup()
    const onDelete = vi.fn()
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    render(<LectureRow lecture={lecture} onStatusChange={vi.fn()} onDelete={onDelete} />)

    await user.click(screen.getByLabelText('Delete Congestion Control'))
    expect(confirm).toHaveBeenCalledWith('Delete "L3 Congestion Control"?')
    expect(onDelete).not.toHaveBeenCalled()

    confirm.mockReturnValue(true)
    await user.click(screen.getByLabelText('Delete Congestion Control'))
    expect(onDelete).toHaveBeenCalledWith(7)

    confirm.mockRestore()
  })
})
