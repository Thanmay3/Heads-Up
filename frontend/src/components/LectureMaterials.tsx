import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { addNotes, deleteMaterial, listMaterials, uploadMaterial } from '../api/materials'
import type { Material, MaterialFileType, MaterialStatus } from '../api/types'

const ACCEPTED_TYPES = '.pdf,.pptx,.ppt,.txt'

const TYPE_LABELS: Record<MaterialFileType, string> = {
  pdf: 'PDF',
  pptx: 'PPTX',
  ppt: 'PPT',
  txt: 'TXT',
  notes: 'NOTES',
}

const STATUS_LABELS: Record<MaterialStatus, string> = {
  uploaded: 'Queued',
  processing: 'Processing',
  ready: 'Ready',
  failed: 'Failed',
}

const STATUS_STYLES: Record<MaterialStatus, string> = {
  uploaded: 'bg-amber-100 text-amber-800',
  processing: 'bg-amber-100 text-amber-800',
  ready: 'bg-emerald-100 text-emerald-800',
  failed: 'bg-rose-100 text-rose-800',
}

interface LectureMaterialsProps {
  lectureId: number
  lectureTitle: string
}

export default function LectureMaterials({ lectureId, lectureTitle }: LectureMaterialsProps) {
  const [materials, setMaterials] = useState<Material[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [notesTitle, setNotesTitle] = useState('')
  const [notesContent, setNotesContent] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const load = useCallback(async () => {
    try {
      setMaterials(await listMaterials(lectureId))
      setError(null)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Failed to load materials')
    }
  }, [lectureId])

  useEffect(() => {
    setMaterials(null)
    void load()
  }, [load])

  async function run(action: () => Promise<unknown>): Promise<boolean> {
    setBusy(true)
    try {
      await action()
      setError(null)
      setFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      await load()
      return true
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Material action failed')
      return false
    } finally {
      setBusy(false)
    }
  }

  function handleUpload(event: FormEvent) {
    event.preventDefault()
    if (file) void run(() => uploadMaterial(lectureId, file))
  }

  function handleNotes(event: FormEvent) {
    event.preventDefault()
    const title = notesTitle
    const content = notesContent
    void run(() => addNotes(lectureId, title, content)).then((ok) => {
      if (ok) {
        setNotesTitle('')
        setNotesContent('')
      }
    })
  }

  function handleDelete(material: Material) {
    if (!window.confirm(`Delete "${material.title}"?`)) return
    void run(() => deleteMaterial(material.id))
  }

  return (
    <section
      aria-label={`Materials for ${lectureTitle}`}
      className="mt-2 rounded-lg border border-slate-200 bg-white p-3"
    >
      <h4 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Materials</h4>

      {error && (
        <p role="alert" className="mt-2 rounded-md border border-rose-300 bg-rose-50 px-2 py-1 text-xs text-rose-800">
          {error}
        </p>
      )}

      {materials === null ? (
        <p className="mt-2 text-xs text-slate-500">Loading materials…</p>
      ) : materials.length === 0 ? (
        <p className="mt-2 text-xs text-slate-500">
          No materials yet. Upload slides or paste your own notes below.
        </p>
      ) : (
        <ul className="mt-2 space-y-1">
          {materials.map((material) => (
            <li key={material.id} className="rounded-md border border-slate-200 px-2 py-1.5">
              <div className="flex items-center gap-2">
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">
                  {TYPE_LABELS[material.file_type]}
                </span>
                <span className="min-w-0 flex-1 truncate text-xs font-medium text-slate-700">
                  {material.title}
                </span>
                <span className="text-[10px] text-slate-400">
                  {material.segment_count} {material.segment_count === 1 ? 'segment' : 'segments'}
                </span>
                <span className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${STATUS_STYLES[material.status]}`}>
                  {STATUS_LABELS[material.status]}
                </span>
                <button
                  type="button"
                  aria-label={`Delete ${material.title}`}
                  disabled={busy}
                  onClick={() => handleDelete(material)}
                  className="shrink-0 rounded px-1 py-0.5 text-[10px] font-medium text-slate-500 hover:bg-slate-100 hover:text-rose-700 disabled:opacity-50"
                >
                  Delete
                </button>
              </div>
              {material.status === 'failed' && material.error_message && (
                <p className="mt-1 text-[11px] text-rose-700">{material.error_message}</p>
              )}
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleUpload} className="mt-3 flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_TYPES}
          aria-label={`Upload material file for ${lectureTitle}`}
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="min-w-0 flex-1 text-xs text-slate-600 file:mr-2 file:rounded-md file:border-0 file:bg-slate-100 file:px-2 file:py-1 file:text-xs file:font-medium file:text-slate-700 hover:file:bg-slate-200"
        />
        <button
          type="submit"
          disabled={busy || !file}
          className="shrink-0 rounded-md bg-sky-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-sky-700 disabled:opacity-50"
        >
          Upload
        </button>
      </form>

      <form onSubmit={handleNotes} className="mt-2 space-y-1.5">
        <input
          type="text"
          value={notesTitle}
          onChange={(event) => setNotesTitle(event.target.value)}
          placeholder="Notes title"
          aria-label={`Notes title for ${lectureTitle}`}
          className="w-full rounded-md border border-slate-300 px-2 py-1 text-xs focus:outline-2 focus:outline-sky-500"
        />
        <textarea
          value={notesContent}
          onChange={(event) => setNotesContent(event.target.value)}
          placeholder="Paste your own notes for this lecture…"
          aria-label={`Notes content for ${lectureTitle}`}
          rows={2}
          className="w-full rounded-md border border-slate-300 px-2 py-1 text-xs focus:outline-2 focus:outline-sky-500"
        />
        <button
          type="submit"
          disabled={busy || notesTitle.trim() === '' || notesContent.trim() === ''}
          className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50"
        >
          Save notes
        </button>
      </form>
    </section>
  )
}
