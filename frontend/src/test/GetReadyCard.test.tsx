import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import GetReadyCard from '../components/GetReadyCard'

describe('GetReadyCard', () => {
  it('offers the four time budgets and disables the action until an engine exists', () => {
    render(<GetReadyCard />)
    expect(screen.getByRole('button', { name: '2 min' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '5 min' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '10 min' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '20 min' })).toBeInTheDocument()
    expect(screen.getByTestId('get-ready-button')).toBeDisabled()
    expect(screen.getByText(/arrives in Stage 5/i)).toBeInTheDocument()
  })

  it('marks the chosen budget as pressed', async () => {
    const user = userEvent.setup()
    render(<GetReadyCard />)
    const tenMinutes = screen.getByRole('button', { name: '10 min' })
    expect(tenMinutes).toHaveAttribute('aria-pressed', 'false')
    await user.click(tenMinutes)
    expect(tenMinutes).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '2 min' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('keeps the get-ready action disabled even with a budget selected', async () => {
    const user = userEvent.setup()
    render(<GetReadyCard />)
    await user.click(screen.getByRole('button', { name: '5 min' }))
    expect(screen.getByTestId('get-ready-button')).toBeDisabled()
  })
})
