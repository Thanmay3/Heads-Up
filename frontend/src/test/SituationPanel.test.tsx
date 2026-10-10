import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { CourseSummary } from '../api/types'
import SituationPanel from '../components/SituationPanel'

const fullSummary: CourseSummary = {
  last_understood_lecture: { id: 1, order_index: 1, title: 'Introduction', status: 'understood' },
  upcoming_lecture: {
    id: 3,
    order_index: 3,
    title: 'Quality of Service',
    status: 'upcoming',
  },
  missed_lectures: [{ id: 2, order_index: 2, title: 'Congestion Control', status: 'missed' }],
  unmarked_before_upcoming: [],
}

describe('SituationPanel', () => {
  it('shows the understood frontier, the target lecture, and the missed gap', () => {
    render(<SituationPanel summary={fullSummary} />)
    expect(screen.getByLabelText('Your position')).toBeInTheDocument()
    expect(screen.getByText('L1 Introduction')).toBeInTheDocument()
    expect(screen.getByText('L3 Quality of Service')).toBeInTheDocument()
    expect(screen.getByText('L2 Congestion Control')).toBeInTheDocument()
  })

  it('surfaces an amber hint for unmarked lectures before the upcoming one', () => {
    render(
      <SituationPanel
        summary={{
          ...fullSummary,
          unmarked_before_upcoming: [
            { id: 4, order_index: 2, title: 'Reliable Data Transfer', status: 'unmarked' },
          ],
        }}
      />,
    )
    const hint = screen.getByText(/HeadsUp never assumes you know an unmarked lecture/i)
    expect(hint).toBeInTheDocument()
    expect(hint).toHaveTextContent('L2 Reliable Data Transfer')
  })

  it('asks the student to pick an upcoming lecture when none is marked', () => {
    render(
      <SituationPanel
        summary={{
          ...fullSummary,
          last_understood_lecture: null,
          upcoming_lecture: null,
          missed_lectures: [],
        }}
      />,
    )
    expect(screen.getByText(/mark one lecture as upcoming/i)).toBeInTheDocument()
    expect(screen.queryByText(/missed lecture/i)).not.toBeInTheDocument()
  })
})
