import { useState } from 'react'

const TIME_BUDGETS: readonly number[] = [2, 5, 10, 20]

export default function GetReadyCard() {
  const [budget, setBudget] = useState<number | null>(null)

  return (
    <section
      aria-label="Get ready"
      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
    >
      <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase">Get ready</h2>
      <p className="mt-2 text-sm text-slate-600">
        How much time do you have before the next lecture?
      </p>
      <div role="group" aria-label="Time budget" className="mt-3 flex flex-wrap gap-2">
        {TIME_BUDGETS.map((minutes) => {
          const selected = budget === minutes
          return (
            <button
              key={minutes}
              type="button"
              aria-pressed={selected}
              onClick={() => setBudget(minutes)}
              className={`rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors ${
                selected
                  ? 'border-sky-600 bg-sky-600 text-white'
                  : 'border-slate-300 bg-white text-slate-700 hover:border-sky-400 hover:text-sky-700'
              }`}
            >
              {minutes} min
            </button>
          )
        })}
      </div>
      <button
        type="button"
        disabled
        aria-describedby="get-ready-note"
        data-testid="get-ready-button"
        className="mt-4 w-full rounded-lg bg-sky-600 px-4 py-2.5 text-sm font-bold tracking-wide text-white uppercase opacity-50"
      >
        Get me ready
      </button>
      <p id="get-ready-note" className="mt-2 text-xs text-slate-500">
        The minimum knowledge bridge arrives in Stage 5. Stage 1 tracks your course and lecture
        positions.
      </p>
    </section>
  )
}
