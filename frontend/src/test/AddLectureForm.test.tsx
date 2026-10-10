import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import AddLectureForm from '../components/AddLectureForm'

describe('AddLectureForm', () => {
  it('disables the submit button while the title is empty', () => {
    render(<AddLectureForm onAdd={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Add lecture' })).toBeDisabled()
  })

  it('submits the trimmed title and clears the input', async () => {
    const user = userEvent.setup()
    const onAdd = vi.fn().mockResolvedValue(undefined)
    render(<AddLectureForm onAdd={onAdd} />)

    const input = screen.getByLabelText('Lecture title')
    await user.type(input, '  Quality of Service  ')
    await user.click(screen.getByRole('button', { name: 'Add lecture' }))

    expect(onAdd).toHaveBeenCalledWith('Quality of Service')
    expect(input).toHaveValue('')
  })

  it('does not submit whitespace-only titles', async () => {
    const user = userEvent.setup()
    const onAdd = vi.fn()
    render(<AddLectureForm onAdd={onAdd} />)

    await user.type(screen.getByLabelText('Lecture title'), '   ')
    expect(screen.getByRole('button', { name: 'Add lecture' })).toBeDisabled()
    expect(onAdd).not.toHaveBeenCalled()
  })
})
