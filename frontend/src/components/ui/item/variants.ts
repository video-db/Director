import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'

export const itemVariants = cva(
  [
    'group/item flex w-full items-center rounded-sm border text-left text-sm text-text-neutral-primary outline-none transition-colors duration-150',
    // Rendered as a link or button (as="a", as="button" or as-child around NuxtLink)
    '[a&]:cursor-pointer [button&]:cursor-pointer focus-visible:shadow-focus-ring',
  ],
  {
    variants: {
      variant: {
        default: 'border-transparent bg-transparent [a&]:hover:bg-background-neutral-hover [button&]:hover:bg-background-neutral-hover',
        outline: 'border-border-neutral-primary [a&]:hover:border-border-neutral-hover [a&]:hover:bg-background-neutral-hover [button&]:hover:border-border-neutral-hover [button&]:hover:bg-background-neutral-hover',
        muted: 'border-transparent bg-background-neutral-subtle [a&]:hover:bg-background-neutral-secondary [button&]:hover:bg-background-neutral-secondary',
      },
      size: {
        sm: 'gap-12 p-12',
        md: 'gap-12 p-16',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  },
)

export const itemMediaVariants = cva(
  // With a description, media aligns to the top of the text instead of the middle.
  'flex shrink-0 items-center justify-center group-has-data-[slot=item-description]/item:self-start',
  {
    variants: {
      variant: {
        // Avatars, icons or anything else, as is
        default: '',
        icon: 'size-40 rounded-xs bg-background-neutral-secondary text-icon-neutral-secondary',
        image: 'size-40 overflow-hidden rounded-xs bg-background-neutral-secondary [&_img]:size-full [&_img]:object-cover',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export type ItemVariants = VariantProps<typeof itemVariants>
export type ItemMediaVariants = VariantProps<typeof itemMediaVariants>

/** The list item an Item is wrapped in inside an ItemGroup. */
export const itemListItemClasses = 'flex'

export const itemGroupClasses = 'flex w-full flex-col'

// Takes the free space; a second ItemContent (e.g. a size or date column) only takes what it needs.
export const itemContentClasses = 'flex min-w-0 flex-1 flex-col gap-4 [&+[data-slot=item-content]]:flex-none'

export const itemTitleClasses = 'flex min-w-0 items-center gap-8 text-sm font-medium text-text-neutral-primary'

// Clamped to two lines.
export const itemDescriptionClasses = 'line-clamp-2 text-xs font-medium text-text-neutral-tertiary'

export const itemActionsClasses = 'flex shrink-0 items-center gap-8'

export const itemSeparatorClasses = 'h-px w-full shrink-0 bg-border-neutral-primary'
