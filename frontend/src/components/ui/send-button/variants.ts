import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

// idle (nothing to send yet) → ready → processing (sent, waiting), or a Stop button while processing
// when stoppable; or disabled.
export const sendButtonVariants = cva(
  'flex shrink-0 items-center justify-center rounded-full outline-none transition-colors duration-150 focus-visible:shadow-focus-ring',
  {
    variants: {
      size: {
        sm: 'size-control-sm',
        md: 'size-control-md',
        lg: 'size-control-lg',
      },
      state: {
        idle: 'cursor-default bg-background-neutral-disabled text-icon-neutral-inverse-primary',
        ready: 'cursor-pointer bg-background-brand-primary text-icon-brand-inverse hover:bg-background-brand-primary-hover active:bg-background-brand-primary-pressed',
        processing: 'cursor-wait bg-background-neutral-tertiary text-icon-neutral-secondary',
        stop: 'cursor-pointer bg-background-neutral-inverse-primary text-icon-neutral-inverse-primary hover:bg-background-neutral-inverse-secondary',
        disabled: 'cursor-not-allowed bg-background-neutral-disabled text-icon-neutral-disabled',
      },
    },
    defaultVariants: {
      size: 'md',
      state: 'idle',
    },
  },
)

export type SendButtonVariants = VariantProps<typeof sendButtonVariants>
export type SendButtonState = NonNullable<SendButtonVariants['state']>

/** disabled wins over processing, processing over ready. A stoppable button shows stop while processing. */
export function sendButtonState(o: { ready?: boolean, processing?: boolean, stoppable?: boolean, disabled?: boolean }): SendButtonState {
  return o.disabled ? 'disabled' : o.processing ? (o.stoppable ? 'stop' : 'processing') : o.ready ? 'ready' : 'idle'
}

/**
 * While it is a Stop button, only pressing the button itself stops: a click, or Enter or Space with the button
 * focused. Enter in the form's field also "clicks" the submit button (implicit submission); that one is ignored.
 */
export function isOwnPress(event: { detail: number }, button: Element) {
  return event.detail > 0 || document.activeElement === button
}

/** Arrow (and stop icon) size per button size, and the spinner that replaces it while processing. */
export const sendButtonIconSize = { sm: 20, md: 24, lg: 24 } as const
export const sendButtonSpinnerSize = { sm: 'sm', md: 'md', lg: 'md' } as const
