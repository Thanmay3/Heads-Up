import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Material } from '../api/types'
import LectureMaterials from '../components/LectureMaterials'

vi.mock('../api/materials', () => ({
  listMaterials: vi.fn(),
  uploadMaterial: vi.fn(),
  addNotes: vi.fn(),
  deleteMaterial: vi.fn(),
}))

import { addNotes, deleteMaterial, listMaterials, uploadMaterial } from '../api/materials'

const mockedAddNotes = vi.mocked(addNotes)
const mockedDeleteMaterial = vi.mocked(deleteMaterial)
const mockedListMaterials = vi.mocked(listMaterials)
const mockedUploadMaterial = vi.mocked(uploadMaterial)

function materialFixture(overrides: Partial<Material> = {}): Material {
  return {
    id: 5,
    lecture_id: 2,
    kind: 'file',
    file_type: 'txt',
    title: 'dns-notes',
    original_filename: 'dns-notes.txt',
    file_size: 22,
    status: 'ready',
    error_message: null,
    segment_count: 1,
    created_at: '2026-10-07T00:00:00Z',
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockedListMaterials.mockResolvedValue([])
})

describe('LectureMaterials', () => {
  it('lists materials with type, status, and segment count', async () => {
    mockedListMaterials.mockResolvedValue([
      materialFixture(),
      materialFixture({
        id: 6,
        kind: 'notes',
        file_type: 'notes',
        title: 'typed notes',
        original_filename: null,
        status: 'failed',
        error_message: 'No text could be extracted from this PDF',
        segment_count: 0,
      }),
    ])

    render(<LectureMaterials lectureId={2} lectureTitle="DNS" />)

    expect(await screen.findByText('dns-notes')).toBeInTheDocument()
    expect(screen.getByText('Ready')).toBeInTheDocument()
    expect(screen.getByText('1 segment')).toBeInTheDocument()
    expect(screen.getByText('typed notes')).toBeInTheDocument()
    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(
      screen.getByText('No text could be extracted from this PDF'),
    ).toBeInTheDocument()
  })

  it('uploads the chosen file and reloads the list', async () => {
    const user = userEvent.setup()
    mockedUploadMaterial.mockResolvedValue(materialFixture())

    render(<LectureMaterials lectureId={2} lectureTitle="DNS" />)
    await screen.findByRole('button', { name: 'Upload' })

    const file = new File(['DNS maps names to IPs'], 'dns.txt', { type: 'text/plain' })
    await user.upload(screen.getByLabelText('Upload material file for DNS'), file)
    await user.click(screen.getByRole('button', { name: 'Upload' }))

    await waitFor(() => {
      expect(mockedUploadMaterial).toHaveBeenCalledWith(2, file)
    })
    await waitFor(() => {
      expect(mockedListMaterials).toHaveBeenCalledTimes(2)
    })
  })

  it('surfaces upload errors from the API', async () => {
    const user = userEvent.setup()
    mockedUploadMaterial.mockRejectedValue(
      new Error('This material is already attached to this lecture'),
    )

    render(<LectureMaterials lectureId={2} lectureTitle="DNS" />)
    await screen.findByRole('button', { name: 'Upload' })

    const file = new File(['same content'], 'dns.txt', { type: 'text/plain' })
    await user.upload(screen.getByLabelText('Upload material file for DNS'), file)
    await user.click(screen.getByRole('button', { name: 'Upload' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'This material is already attached to this lecture',
    )
  })

  it('saves typed notes and clears the form', async () => {
    const user = userEvent.setup()
    mockedAddNotes.mockResolvedValue(
      materialFixture({ kind: 'notes', file_type: 'notes', title: 'Class notes' }),
    )

    render(<LectureMaterials lectureId={2} lectureTitle="DNS" />)
    await screen.findByRole('button', { name: 'Save notes' })

    await user.type(screen.getByLabelText('Notes title for DNS'), 'Class notes')
    await user.type(screen.getByLabelText('Notes content for DNS'), 'TCP is reliable')
    await user.click(screen.getByRole('button', { name: 'Save notes' }))

    await waitFor(() => {
      expect(mockedAddNotes).toHaveBeenCalledWith(2, 'Class notes', 'TCP is reliable')
    })
    await waitFor(() => {
      expect(screen.getByLabelText('Notes title for DNS')).toHaveValue('')
    })
  })

  it('only deletes a material after confirmation', async () => {
    const user = userEvent.setup()
    mockedListMaterials.mockResolvedValue([materialFixture()])
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)

    render(<LectureMaterials lectureId={2} lectureTitle="DNS" />)
    await screen.findByText('dns-notes')

    await user.click(screen.getByLabelText('Delete dns-notes'))
    expect(confirm).toHaveBeenCalledWith('Delete "dns-notes"?')
    expect(mockedDeleteMaterial).not.toHaveBeenCalled()

    confirm.mockReturnValue(true)
    await user.click(screen.getByLabelText('Delete dns-notes'))
    await waitFor(() => {
      expect(mockedDeleteMaterial).toHaveBeenCalledWith(5)
    })

    confirm.mockRestore()
  })
})
