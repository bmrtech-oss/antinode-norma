import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

type AlertVariant = 'default' | 'destructive' | 'warning' | 'success'

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant
}

const variants: Record<AlertVariant, string> = {
  default: 'border-border bg-card text-card-foreground',
  destructive: 'border-destructive/40 bg-destructive/10 text-destructive',
  warning: 'border-warning/40 bg-warning/10 text-warning',
  success: 'border-success/40 bg-success/10 text-success',
}

export const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'default', role = 'alert', ...props }, ref) => (
    <div
      ref={ref}
      role={role}
      className={cn('relative w-full rounded-lg border p-4 text-sm', variants[variant], className)}
      {...props}
    />
  ),
)

Alert.displayName = 'Alert'
