import { AlertCircle, Inbox, Loader2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { Alert } from './Alert'
import { Button } from './Button'

interface StateContainerProps {
  children: ReactNode
  className?: string
}

export function LoadingState({ label = 'Loading...' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-muted-foreground" role="status" aria-live="polite">
      <Loader2 className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}

export function EmptyState({
  title,
  description,
  icon = <Inbox className="h-6 w-6" aria-hidden="true" />,
}: {
  title: string
  description?: string
  icon?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-muted/30 p-10 text-center">
      <div className="rounded-full bg-muted p-3 text-muted-foreground">{icon}</div>
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      {description && <p className="max-w-md text-xs text-muted-foreground">{description}</p>}
    </div>
  )
}

export function ErrorState({
  message = 'We could not load this content.',
  onRetry,
}: {
  message?: string
  onRetry?: () => void
}) {
  return (
    <Alert variant="destructive" className="flex items-center justify-between gap-4" aria-live="assertive">
      <div className="flex items-start gap-2">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
        <span>{message}</span>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Retry
        </Button>
      )}
    </Alert>
  )
}

export function StateContainer({ children, className = '' }: StateContainerProps) {
  return <div className={`w-full ${className}`}>{children}</div>
}
