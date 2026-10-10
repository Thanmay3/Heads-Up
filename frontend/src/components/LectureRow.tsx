import type { Lecture, LectureStatus } from '../api/types'
import LectureMaterials from './LectureMaterials'

const STATUS_OPTIONS: ReadonlyArray<{ value: LectureStatus; label: string }> = [
  { value: 'unmarked', label: 'Unmarked' },
  { value: 'understood', label: 'Understood' },
  { value: 'missed', label: 'Missed' },
  { value: 'upcoming', label: 'Upcoming' },
]

const ROW_STYLES: Record<LectureStatus, string> = {
  unmarked: 'border-slate-300 bg-white text-slate-700',
  understood: 'border-emerald-300 bg-emerald-50 text-emerald-900',
  missed: 'border-rose-300 bg-rose-50 text-rose-900',
  upcoming: 'border-sky-300 bg-sky-50 text-sky-900',
}

interface LectureRowProps {
  lecture: Lecture
  onStatusChange: (id: number, status: LectureStatus) => void
  onDelete: (id: number) => void
  materialsExpanded?: boolean
  onToggleMaterials?: (id: number) => void
}

export default function LectureRow({
  lecture,
  onStatusChange,
  onDelete,
  materialsExpanded = false,
  onToggleMaterials,
}: LectureRowProps) {
  return (
    <li className={`rounded-lg border px-3 py-2 ${ROW_STYLES[lecture.status]}`}>
      <div className="flex items-center gap-2 sm:gap-3">
        <span className="w-9 shrink-0 text-sm font-semibold tabular-nums">
          L{lecture.order_index}
        </span>
        <span className="min-w-0 flex-1 truncate text-sm font-medium">{lecture.title}</span>
        <button
          type="button"
          aria-expanded={materialsExpanded}
          aria-label={`Materials for ${lecture.title}`}
          onClick={() => onToggleMaterials?.(lecture.id)}
          className={`shrink-0 rounded-md px-2 py-1 text-xs font-medium focus:outline-2 focus:outline-sky-500 ${
            materialsExpanded
              ? 'bg-slate-900 text-white'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          }`}
        >
          Materials
        </button>
        <select
          aria-label={`Status for ${lecture.title}`}
          value={lecture.status}
          onChange={(event) => onStatusChange(lecture.id, event.target.value as LectureStatus)}
          className="shrink-0 rounded-md border border-current/30 bg-white px-2 py-1 text-xs font-medium text-slate-700 focus:outline-2 focus:outline-sky-500"
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          aria-label={`Delete ${lecture.title}`}
          onClick={() => {
            if (window.confirm(`Delete "L${lecture.order_index} ${lecture.title}"?`)) {
              onDelete(lecture.id)
            }
          }}
          className="shrink-0 rounded-md px-2 py-1 text-xs font-medium text-slate-500 hover:bg-slate-200/70 hover:text-rose-700 focus:outline-2 focus:outline-rose-500"
        >
          Delete
        </button>
      </div>
      {materialsExpanded && <LectureMaterials lectureId={lecture.id} lectureTitle={lecture.title} />}
    </li>
  )
}
