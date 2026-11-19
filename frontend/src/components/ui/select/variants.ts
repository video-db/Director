import type { VariantProps } from 'class-variance-authority'
import { cva } from 'class-variance-authority'
import { inputDisabledClasses, inputSizeClasses } from '@/components/ui/input'
import { floatingAnimationClasses, floatingPanelClasses } from '@/lib/floating'

// The trigger has Input's field look, sizes and disabled state. It is the focused element itself and
// marks errors with aria-invalid, so its hover, focus and invalid classes key off those.
export const selectTriggerVariants = cva(
  [
    'group/select flex w-full cursor-pointer items-center gap-8 rounded-xs border border-border-neutral-field bg-background-neutral-primary',
    'text-left text-sm text-text-neutral-primary outline-none transition-[border-color,box-shadow] duration-150',
    'data-placeholder:text-text-neutral-tertiary',
    // Hover only in the plain resting state, so open, focus, error and disabled keep their borders
    'not-data-disabled:not-aria-invalid:not-data-[state=open]:not-focus-visible:hover:border-border-neutral-field-hover',
    'data-[state=open]:border-border-brand-primary',
    'focus-visible:border-border-brand-primary focus-visible:shadow-focus-ring',
    'aria-invalid:border-border-error-primary',
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
export type SelectTriggerVariants = VariantProps<typeof selectTriggerVariants>

/** The leading icon before the value. */
export const selectLeadingIconClasses = 'text-icon-neutral-secondary'
/** The chevron turns and takes the brand colour while the list is open. */
export const selectChevronClasses = 'text-icon-neutral-secondary transition-transform duration-150 group-data-[state=open]/select:rotate-180 group-data-[state=open]/select:text-icon-brand-primary group-data-disabled/select:text-icon-neutral-disabled'
/** The value inside the trigger: it takes the free space and truncates. */
export const selectValueWrapperClasses = 'min-w-0 flex-1 truncate'

// The list panel, styled like Dropdown Menu. Each framework adds its primitive's max-height, min-width
// (the trigger's width) and transform origin.
export const selectContentClasses = [floatingPanelClasses, 'relative overflow-hidden', floatingAnimationClasses]
/** The scrolling list inside the panel. */
export const selectViewportClasses = 'flex flex-col gap-2 p-4'
/** An item's label, and the trailing check on the selected item. */
export const selectItemTextClasses = 'min-w-0 flex-1 truncate'
export const selectItemIndicatorClasses = 'ml-auto flex'
export const selectItemCheckClasses = 'text-icon-neutral-secondary'
