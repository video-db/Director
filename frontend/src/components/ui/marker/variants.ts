import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

// An inline note in a conversation: a status, a system note, a bordered row or a labelled separator.
export const markerVariants = cva(
  [
    'group/marker relative flex min-h-16 w-full items-center gap-8 text-left text-sm text-text-neutral-tertiary',
    '[a&]:underline [a&]:underline-offset-4 [a&]:hover:text-text-neutral-primary',
    '[button&]:cursor-pointer [button&]:hover:text-text-neutral-primary',
    '[a&]:rounded-xxs [button&]:rounded-xxs outline-none focus-visible:shadow-focus-ring',
  ],
  {
    variants: {
      variant: {
        default: '',
        // The divider lines are decorative pseudo-elements, so the label is read as plain text
        separator: 'before:mr-4 before:h-px before:min-w-0 before:flex-1 before:bg-border-neutral-primary after:ml-4 after:h-px after:min-w-0 after:flex-1 after:bg-border-neutral-primary',
        border: 'border-b border-border-neutral-primary pb-8',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export type MarkerVariants = VariantProps<typeof markerVariants>

// The text. In a separator it doesn't grow, so it sits centred between the lines.
export const markerContentClasses = [
  'min-w-0 wrap-break-word group-data-[variant=separator]/marker:flex-none group-data-[variant=separator]/marker:text-center',
  '*:[a]:underline *:[a]:underline-offset-4 *:[a]:hover:text-text-neutral-primary',
]
/** The shimmer utility from tokens.css, for text still streaming in */
export const markerContentShimmerClasses = 'shimmer'

// Decorative: hidden from screen readers, so MarkerContent carries the meaning.
export const markerIconClasses = 'flex size-16 shrink-0 items-center justify-center text-icon-neutral-tertiary'
