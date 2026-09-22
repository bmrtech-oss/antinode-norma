import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

export const Skeleton = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      role="status"
      aria-label="Loading"
      className={cn('animate-pulse rounded-md bg-muted', className)}
      {...props}
    />
  ),
)

Skeleton.displayName = 'Skeleton'
