import type { CourseSummary } from '../api/types'

interface SituationPanelProps {
  summary: CourseSummary
}

function lectureLabel(lecture: { order_index: number; title: string }): string {
  return `L${lecture.order_index} ${lecture.title}`
}

export default function SituationPanel({ summary }: SituationPanelProps) {
  const {
    last_understood_lecture: lastUnderstood,
    upcoming_lecture: upcoming,
    missed_lectures: missed,
    unmarked_before_upcoming: unmarked,
  } = summary

  return (
    <section
      aria-label="Your position"
      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
    >
      <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase">
        Your position
      </h2>
      <dl className="mt-3 space-y-2 text-sm">
        <div className="flex flex-wrap items-baseline gap-x-2">
          <dt className="text-slate-500">Understood through</dt>
          <dd className="font-semibold text-emerald-700">
            {lastUnderstood ? (
              lectureLabel(lastUnderstood)
            ) : (
              <span className="font-normal text-slate-500">nothing marked understood yet</span>
            )}
          </dd>
        </div>
        <div className="flex flex-wrap items-baseline gap-x-2">
          <dt className="text-slate-500">Preparing for</dt>
          <dd className="font-semibold text-sky-700">
            {upcoming ? (
              lectureLabel(upcoming)
            ) : (
              <span className="font-normal text-slate-500">
                mark one lecture as Upcoming to set your target
              </span>
            )}
          </dd>
        </div>
        {missed.length > 0 && (
          <div className="flex flex-wrap items-baseline gap-x-2">
            <dt className="text-slate-500">
              {missed.length === 1 ? 'Missed lecture' : 'Missed lectures'}
            </dt>
            <dd className="font-semibold text-rose-700">
              {missed.map((lecture) => lectureLabel(lecture)).join(', ')}
            </dd>
          </div>
        )}
      </dl>
      {unmarked.length > 0 && (
        <p className="mt-3 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          HeadsUp never assumes you know an unmarked lecture. Mark{' '}
          {unmarked.length === 1
            ? lectureLabel(unmarked[0])
            : unmarked.map((lecture) => lectureLabel(lecture)).join(', ')}{' '}
          as understood or missed so your position stays accurate.
        </p>
      )}
    </section>
  )
}
