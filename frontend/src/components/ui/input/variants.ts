import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

/** Heights and side padding per size: 36 / 40 / 44px. Select's trigger uses the same. */
export const inputSizeClasses = {
  sm: 'h-control-sm px-12',
  md: 'h-control-md px-12',
  lg: 'h-control-lg px-16',
} as const

/** Disabled field: Border/Neutral/Strong on Background/Neutral/Secondary. Select's trigger uses the same. */
export const inputDisabledClasses = 'data-disabled:cursor-not-allowed data-disabled:border-border-neutral-strong data-disabled:bg-background-neutral-secondary data-disabled:text-text-neutral-disabled'

// Styles live on the wrapper so icons and the clear button sit inside the field.
export const inputVariants = cva(
  [
    'group/input flex w-full items-center gap-8 rounded-xs border border-border-neutral-field bg-background-neutral-primary',
    'text-sm text-text-neutral-primary transition-[border-color,box-shadow] duration-150',
    // Hover only in the plain resting state, so focus, error, disabled and read-only keep their borders.
    'not-data-disabled:not-data-readonly:not-data-invalid:not-focus-within:hover:border-border-neutral-field-hover',
    // Focus styles follow the text control only, so a focused button inside shows just its own ring.
    // :where() keeps the specificity low, so the error border still wins over the focus border.
    'has-[:where([data-slot=input-control],[data-slot=input-group-control]):focus-visible]:border-border-brand-primary',
    'has-[:where([data-slot=input-control],[data-slot=input-group-control]):focus-visible]:shadow-focus-ring',
    'data-invalid:border-border-error-primary',
    'data-readonly:bg-background-neutral-subtle data-readonly:text-text-neutral-secondary',
    inputDisabledClasses,
  ],
  {
    variants: {
      size: inputSizeClasses,
    },
    defaultVariants: {
      size: 'lg',
    },
  },
)

export type InputVariants = VariantProps<typeof inputVariants>

/** The native input inside the wrapper. */
export const inputControlClass = [
  'h-full min-w-0 flex-1 bg-transparent outline-none [&::-webkit-search-cancel-button]:appearance-none placeholder:text-text-neutral-tertiary disabled:cursor-not-allowed disabled:placeholder:text-text-neutral-disabled',
  // type="file": the browser's "Choose file" button, as plain medium text before the file name
  'file:mr-8 file:h-full file:cursor-pointer file:border-0 file:bg-transparent file:p-0 file:text-sm file:font-medium file:text-text-neutral-primary disabled:file:cursor-not-allowed disabled:file:text-text-neutral-disabled',
]

/** The clear (×) button. ::after gives it a hit area of at least 24px. */
export const inputClearButtonClass = 'relative flex shrink-0 cursor-pointer items-center justify-center rounded-xxs text-icon-neutral-secondary outline-none after:absolute after:-inset-4 hover:text-icon-neutral-primary focus-visible:shadow-focus-ring'

/** 16px icons at sm, 20px at md, 24px at lg. */
export const inputIconSize = { sm: 16, md: 20, lg: 24 } as const

/** The leading icon is tertiary while empty, secondary once filled, error when invalid. */
export function inputLeadingIconClass(state: { disabled?: boolean, invalid?: boolean, filled?: boolean }) {
  if (state.disabled) return 'text-icon-neutral-disabled'
  if (state.invalid) return 'text-icon-error-primary'
  return state.filled ? 'text-icon-neutral-secondary' : 'text-icon-neutral-tertiary group-focus-within/input:text-icon-neutral-secondary'
}

export function inputTrailingIconClass(disabled?: boolean) {
  return disabled ? 'text-icon-neutral-disabled' : 'text-icon-neutral-primary'
}
