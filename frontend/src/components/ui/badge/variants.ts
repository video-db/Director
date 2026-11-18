import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export const pillVariants = cva(
  'inline-flex w-fit shrink-0 items-center justify-center gap-4 font-medium whitespace-nowrap',
  {
    variants: {
      size: {
        sm: 'h-22 px-8 text-xs',
        md: 'h-28 px-12 text-sm',
      },
    },
    defaultVariants: { size: 'md' },
  },
)

// Badge: colour × emphasis. Rendered as a link (as="a" / render={<a />}), it underlines on hover and shows
// the focus ring.
export const badgeVariants = cva('rounded-xs [a&]:outline-none [a&]:underline-offset-2 [a&]:hover:underline [a&]:focus-visible:shadow-focus-ring', {
  variants: {
    colour: {
      neutral: '',
      brand: '',
      success: '',
      warning: '',
      error: '',
      info: '',
    },
    emphasis: {
      subtle: '',
      bold: '',
      outline: 'border bg-background-neutral-primary',
      // No fill or border: the text alone, e.g. in a dense row of badges
      ghost: '',
    },
  },
  compoundVariants: [
    { emphasis: 'subtle', colour: 'neutral', class: 'bg-background-neutral-secondary text-text-neutral-secondary' },
    { emphasis: 'subtle', colour: 'brand', class: 'bg-background-brand-tertiary text-text-brand-primary' },
    { emphasis: 'subtle', colour: 'success', class: 'bg-background-success-subtle text-text-success-primary' },
    { emphasis: 'subtle', colour: 'warning', class: 'bg-background-warning-subtle text-text-warning-primary' },
    { emphasis: 'subtle', colour: 'error', class: 'bg-background-error-subtle text-text-error-primary' },
    { emphasis: 'subtle', colour: 'info', class: 'bg-background-info-subtle text-text-info-primary' },

    { emphasis: 'bold', colour: 'neutral', class: 'bg-background-neutral-inverse-primary text-text-neutral-inverse-primary' },
    { emphasis: 'bold', colour: 'brand', class: 'bg-background-brand-primary text-text-brand-inverse' },
    { emphasis: 'bold', colour: 'success', class: 'bg-background-success-bold text-text-success-inverse' },
    { emphasis: 'bold', colour: 'warning', class: 'bg-background-warning-bold text-text-warning-inverse' },
    { emphasis: 'bold', colour: 'error', class: 'bg-background-error-bold text-text-error-inverse' },
    { emphasis: 'bold', colour: 'info', class: 'bg-background-info-bold text-text-info-inverse' },

    { emphasis: 'outline', colour: 'neutral', class: 'border-border-neutral-primary text-text-neutral-secondary' },
    { emphasis: 'outline', colour: 'brand', class: 'border-border-brand-primary text-text-brand-primary' },
    { emphasis: 'outline', colour: 'success', class: 'border-border-success-primary text-text-success-primary' },
    { emphasis: 'outline', colour: 'warning', class: 'border-border-warning-primary text-text-warning-primary' },
    { emphasis: 'outline', colour: 'error', class: 'border-border-error-primary text-text-error-primary' },
    { emphasis: 'outline', colour: 'info', class: 'border-border-info-primary text-text-info-primary' },

    { emphasis: 'ghost', colour: 'neutral', class: 'text-text-neutral-primary' },
    { emphasis: 'ghost', colour: 'brand', class: 'text-text-brand-primary' },
    { emphasis: 'ghost', colour: 'success', class: 'text-text-success-primary' },
    { emphasis: 'ghost', colour: 'warning', class: 'text-text-warning-primary' },
    { emphasis: 'ghost', colour: 'error', class: 'text-text-error-primary' },
    { emphasis: 'ghost', colour: 'info', class: 'text-text-info-primary' },
  ],
  defaultVariants: {
    colour: 'neutral',
    emphasis: 'subtle',
  },
})

// Leading dot, icon and remove button, sized with the pill.
export const pillDotClasses = 'shrink-0 rounded-full bg-current'
export const pillDotSize = { sm: 'size-6', md: 'size-8' } as const
export const pillIconSize = { sm: 12, md: 16 } as const
/** loading: a Spinner in the icon's place, at the icon's size, in the text colour */
export const badgeSpinnerSize = { sm: 'xs', md: 'sm' } as const

// The remove (×) button. Its hit area (after:) reaches at least 24px around the 12 or 16px icon.
export const badgeRemoveClasses = 'relative flex cursor-pointer items-center justify-center rounded-full opacity-70 outline-none after:absolute hover:opacity-100 focus-visible:shadow-focus-ring'
export const badgeRemoveHitArea = { sm: 'after:-inset-6', md: 'after:-inset-4' } as const

// StatusPill: a fully rounded subtle badge with a status dot.
export const statusPillColours = {
  active: 'success',
  paid: 'success',
  invited: 'info',
  pending: 'warning',
  rejected: 'error',
  failed: 'error',
} as const satisfies Record<string, NonNullable<BadgeVariants['colour']>>
export type StatusPillStatus = keyof typeof statusPillColours
/** "pending" → "Pending" */
export const statusPillLabel = (status: StatusPillStatus) => status.charAt(0).toUpperCase() + status.slice(1)

// Counter: a fully rounded count, e.g. next to a section title.
export const counterClasses = 'rounded-full tabular-nums'
export const counterTones = {
  'neutral-subtle': 'bg-background-neutral-secondary text-text-neutral-tertiary',
  'neutral-bold': 'bg-background-neutral-inverse-primary text-text-neutral-inverse-primary',
  'brand-subtle': 'bg-background-brand-tertiary text-text-brand-primary',
  'brand-bold': 'bg-background-brand-primary text-text-brand-inverse',
} as const

export type PillVariants = VariantProps<typeof pillVariants>
export type BadgeVariants = VariantProps<typeof badgeVariants>
