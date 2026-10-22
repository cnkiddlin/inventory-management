import type { ReactNode } from 'react'


const toneStyles = {
  blue: 'bg-blue-50 text-blue-600',
  green: 'bg-emerald-50 text-emerald-600',
  amber: 'bg-amber-50 text-amber-600',
  red: 'bg-rose-50 text-rose-600',
  slate: 'bg-slate-100 text-slate-600',
}

interface StatCardProps {
  label: string
  value: string
  helper?: string
  icon: ReactNode
  tone?: keyof typeof toneStyles
}

export function StatCard({ label, value, helper, icon, tone = 'blue' }: StatCardProps) {
  return (
    <div className="panel panel-hover flex items-center gap-4 p-5">
      <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${toneStyles[tone]}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <div className="text-xs font-medium text-slate-500">{label}</div>
        <div className="mt-1 truncate text-[23px] font-semibold leading-tight tracking-tight text-slate-900">
          {value}
        </div>
        {helper && <div className="mt-1 text-[11px] text-slate-400">{helper}</div>}
      </div>
    </div>
  )
}

