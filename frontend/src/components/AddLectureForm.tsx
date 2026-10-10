import { useState } from 'react'
import type { FormEvent } from 'react'

interface AddLectureFormProps {
  onAdd: (title: string) => void | Promise<void>
}

export default function AddLectureForm({ onAdd }: AddLectureFormProps) {
  const [title, setTitle] = useState('')
  const trimmed = title.trim()

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!trimmed) return
    await onAdd(trimmed)
    setTitle('')
  }

  return (
    <form aria-label="Add lecture" onSubmit={handleSubmit} className="flex gap-2">
      <input
        aria-label="Lecture title"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder="Add the next lecture, e.g. Quality of Service"
        maxLength={200}
        className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-2 focus:outline-sky-500"
      />
      <button
        type="submit"
        disabled={!trimmed}
        className="shrink-0 rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
      >
        Add lecture
      </button>
    </form>
  )
}
