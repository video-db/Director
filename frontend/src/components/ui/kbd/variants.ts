import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export const kbdVariants = cva(
  [
    'inline-flex h-20 min-w-20 shrink-0 items-center justify-center gap-2 rounded-xxs border px-4',
    'font-mono text-xs font-medium whitespace-nowrap select-none',
  ],
  {
    variants: {
      variant: {
        default: 'border-border-neutral-strong bg-background-neutral-subtle text-text-neutral-secondary',
        // For dark surfaces such as Tooltip content.
        inverse: 'border-border-neutral-inverse-primary bg-background-neutral-inverse-secondary text-text-neutral-inverse-primary',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export type KbdVariants = VariantProps<typeof kbdVariants>

/** Keys pressed together or in sequence, e.g. ⌘ + K. */
export const kbdGroupClass = 'inline-flex items-center gap-4'
