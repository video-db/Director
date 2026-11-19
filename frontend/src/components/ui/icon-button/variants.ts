import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export const iconButtonVariants = cva(
  [
    'inline-flex shrink-0 cursor-pointer items-center justify-center transition-colors duration-150 outline-none',
    'focus-visible:shadow-focus-ring disabled:cursor-not-allowed',
  ],
  {
    variants: {
      hierarchy: {
        primary: 'bg-background-brand-primary text-icon-brand-inverse not-disabled:hover:bg-background-brand-primary-hover not-disabled:active:bg-background-brand-primary-pressed disabled:bg-background-neutral-disabled disabled:text-icon-neutral-disabled',
        secondary: 'border border-border-neutral-primary bg-background-neutral-primary text-icon-neutral-primary not-disabled:hover:border-border-neutral-hover not-disabled:hover:bg-background-neutral-hover not-disabled:active:bg-background-neutral-pressed disabled:text-icon-neutral-disabled',
        tertiary: 'text-icon-neutral-primary not-disabled:hover:bg-background-neutral-hover not-disabled:active:bg-background-neutral-pressed disabled:text-icon-neutral-disabled aria-pressed:bg-background-neutral-secondary not-disabled:aria-pressed:hover:bg-background-neutral-tertiary',
        destructive: 'text-icon-error-primary not-disabled:hover:bg-background-error-subtle not-disabled:active:bg-background-error-subtle-hover disabled:text-icon-neutral-disabled',
        inverse: 'bg-background-overlay-glass text-icon-neutral-inverse-primary backdrop-blur-sm not-disabled:hover:bg-background-overlay-scrim disabled:text-icon-neutral-inverse-tertiary',
      },
      size: {
        xs: 'size-28',
        sm: 'size-control-sm',
        md: 'size-control-md',
        lg: 'size-control-lg',
      },
      shape: {
        square: 'rounded-xs',
        circle: 'rounded-full',
      },
    },
    defaultVariants: {
      hierarchy: 'tertiary',
      size: 'md',
      shape: 'square',
    },
  },
)

export type IconButtonVariants = VariantProps<typeof iconButtonVariants>

/** Icon size per button size: 16px at xs and sm, 24px at md and lg. */
export const iconButtonIconSize = { xs: 16, sm: 16, md: 24, lg: 24 } as const
