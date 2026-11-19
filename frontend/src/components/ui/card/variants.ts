import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

// Parts are spaced by --card-spacing: the gap between them, the card's top and bottom padding and each
// part's side padding, so any mix of header, content and footer keeps the same space around and between them.
// size sets it (md 20, sm 16); set it yourself, e.g. [--card-spacing:--spacing(24)], for another value.
// Edge-to-edge content cancels it with -mx-(--card-spacing).
export const cardVariants = cva(
  'group/card relative flex flex-col gap-(--card-spacing) rounded-md border border-border-neutral-primary py-(--card-spacing) text-text-neutral-primary',
  {
    variants: {
      size: {
        md: '[--card-spacing:--spacing(20)]',
        sm: '[--card-spacing:--spacing(16)]',
      },
      variant: {
        outline: 'bg-background-neutral-primary',
        // As cards appear in the console (Agent Card, Collection Card)
        muted: 'bg-background-neutral-subtle',
        elevated: 'bg-background-neutral-primary shadow-sm',
      },
      // For the stretched-link pattern: a link in the title covers the card. The ring follows focus
      // on the title link only, so a focused CardAction button keeps just its own ring.
      interactive: {
        false: '',
        true: [
          'transition-colors duration-150 hover:border-border-neutral-hover',
          'has-[[data-slot=card-title]:focus-visible]:shadow-focus-ring has-[[data-slot=card-title]_:focus-visible]:shadow-focus-ring',
        ],
      },
    },
    compoundVariants: [
      { variant: 'outline', interactive: true, class: 'hover:bg-background-neutral-hover' },
      { variant: 'muted', interactive: true, class: 'hover:bg-background-neutral-secondary' },
      { variant: 'elevated', interactive: true, class: 'hover:bg-background-neutral-hover' },
    ],
    defaultVariants: {
      size: 'md',
      variant: 'outline',
      interactive: false,
    },
  },
)

export type CardVariants = VariantProps<typeof cardVariants>

// Title and description stack; a CardAction sits top-right, spanning both rows.
export const cardHeaderClasses = [
  'grid auto-rows-min items-start gap-x-12 gap-y-4 px-(--card-spacing)',
  'has-data-[slot=card-action]:grid-cols-[1fr_auto]',
]

// A heading (h3 by default).
// A small card's title steps down to Text sm.
export const cardTitleClasses = 'text-md font-semibold text-text-neutral-primary group-data-[size=sm]/card:text-sm'

export const cardDescriptionClasses = 'text-sm text-text-neutral-tertiary'

// Top-right of the header, e.g. a "View usage" button or a ⋮ menu.
// It sits above a stretched title link, so it stays clickable on interactive cards.
export const cardActionClasses = 'relative z-10 col-start-2 row-span-2 row-start-1 flex items-center gap-8 self-start justify-self-end'

export const cardContentClasses = 'px-(--card-spacing)'

// inline: actions in line with the content. band: a grey strip across the bottom of the card, like DialogFooter.
// layout: "start" left-aligns the items; "actions" puts them on the right; "split" pushes the first item left.
export type CardFooterVariant = 'inline' | 'band'
export type CardFooterLayout = 'start' | 'actions' | 'split'
export const cardFooterClasses = 'flex items-center gap-12 px-(--card-spacing)'
export const cardFooterLayouts: Record<CardFooterLayout, string> = {
  start: 'justify-start',
  actions: 'justify-end',
  split: 'justify-between',
}
// The band cancels the card's bottom padding so it reaches the edge, and follows its corners.
export const cardFooterBandClasses = '-mb-(--card-spacing) min-h-64 rounded-b-[inherit] border-t border-border-neutral-primary bg-background-neutral-secondary py-12'
