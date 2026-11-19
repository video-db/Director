import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'
import { floatingAnimationClasses, floatingPanelClasses, listItemClasses } from '@/lib/floating'

// Menu rows and panels, from the shared floating styles (lib/floating.ts). Context Menu uses the same.
export const menuItemClasses = listItemClasses
// Long menus scroll inside the space left on screen; each panel adds its primitive's max-height and origin.
export const menuContentClasses = [floatingPanelClasses, 'flex min-w-220 flex-col gap-2 overflow-y-auto p-4', floatingAnimationClasses]

/** Destructive item, e.g. Delete: error text and a subtle error highlight. */
export const menuItemDestructiveClasses = 'text-text-error-primary data-highlighted:bg-background-error-subtle'
/** A destructive item's leading icon, disabled with the row. */
export const menuItemDestructiveIconClasses = 'text-icon-error-primary group-data-disabled/item:text-icon-neutral-disabled'
/** The item's label; typeahead reads it rather than the icon's ligature name. */
export const menuItemLabelClasses = 'min-w-0 flex-1 truncate'
/** Wraps the trailing check of a checkbox or radio item. */
export const menuItemIndicatorClasses = 'flex'
export const menuItemCheckClasses = 'text-icon-neutral-secondary'
/** A submenu trigger stays highlighted while its submenu is open. */
export const menuSubTriggerClasses = 'data-[state=open]:bg-background-neutral-hover'
export const menuSubTriggerChevronClasses = 'text-icon-neutral-tertiary'

/** MenuButton: a bordered trigger with a label and a chevron that turns while the menu is open. */
export const menuButtonVariants = cva(
  [
    'group/menu-button inline-flex cursor-pointer items-center gap-4 rounded-xs border px-12 text-sm font-medium whitespace-nowrap outline-none transition-colors duration-150',
    'border-border-neutral-primary bg-background-neutral-primary text-text-neutral-primary',
    'not-disabled:hover:border-border-neutral-hover not-disabled:hover:bg-background-neutral-hover',
    'data-[state=open]:border-border-neutral-hover data-[state=open]:bg-background-neutral-secondary',
    'focus-visible:shadow-focus-ring',
    'disabled:cursor-not-allowed disabled:text-text-neutral-disabled',
  ],
  {
    variants: {
      size: {
        sm: 'h-control-sm',
        md: 'h-control-md',
      },
    },
    defaultVariants: {
      size: 'sm',
    },
  },
)
export type MenuButtonVariants = VariantProps<typeof menuButtonVariants>
/** 16px leading icon with 8px to the label (gap 4 + mr-4); 4px between the label and the chevron. */
export const menuButtonIconClasses = 'mr-4 text-icon-neutral-primary group-disabled/menu-button:text-icon-neutral-disabled'
export const menuButtonChevronClasses = 'text-icon-neutral-primary transition-transform duration-150 group-data-[state=open]/menu-button:rotate-180 group-disabled/menu-button:text-icon-neutral-disabled'
