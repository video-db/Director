import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export const textareaVariants = cva(
  [
    'block w-full resize-y rounded-xs border border-border-neutral-field bg-background-neutral-primary text-sm text-text-neutral-primary outline-none',
    'transition-[border-color,box-shadow] duration-150 placeholder:text-text-neutral-tertiary',
    // Hover only at rest: not while focused, invalid, read-only or disabled (a disabled textarea is read-only too).
    'not-read-only:not-aria-invalid:not-focus-visible:hover:border-border-neutral-field-hover',
    'focus-visible:border-border-brand-primary focus-visible:shadow-focus-ring',
    'aria-invalid:border-border-error-primary',
    // Read-only: the same fill as a read-only Input.
    'data-readonly:bg-background-neutral-subtle data-readonly:text-text-neutral-secondary',
    'disabled:cursor-not-allowed disabled:border-border-neutral-strong disabled:bg-background-neutral-secondary disabled:text-text-neutral-disabled disabled:placeholder:text-text-neutral-disabled',
  ],
  {
    variants: {
      size: {
        sm: 'min-h-80 px-12 py-8',
        md: 'min-h-104 px-16 py-12',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  },
)

export type TextareaVariants = VariantProps<typeof textareaVariants>
