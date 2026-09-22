import { useId, type ReactNode } from 'react'
import { Info } from 'lucide-react'
import { cn } from '../../lib/utils'

interface TooltipProps {
  content: string
  children: ReactNode
  className?: string
  side?: 'top' | 'bottom'
}

export function Tooltip({ content, children, className, side = 'top' }: TooltipProps) {
  const tooltipId = useId()
  const tooltipPosition = side === 'bottom'
    ? 'left-0 top-full mt-2'
    : 'bottom-full left-0 mb-2'

  return (
    <span className={cn('group relative inline-flex w-fit items-center gap-1', className)}>
      <span
        tabIndex={0}
        className="cursor-help rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-describedby={tooltipId}
      >
        {children}
      </span>
      <Info className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
      <span
        id={tooltipId}
        role="tooltip"
        className={cn(
          'pointer-events-none absolute z-50 hidden max-w-64 rounded-md bg-popover px-2.5 py-1.5 text-xs font-normal normal-case tracking-normal text-popover-foreground shadow-lg group-hover:block group-focus-within:block',
          tooltipPosition,
        )}
      >
        {content}
      </span>
    </span>
  )
}
