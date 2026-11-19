// Tooltip content. Each framework adds its primitive's transform origin, e.g.
// origin-(--reka-tooltip-content-transform-origin).
export const tooltipContentClasses = [
  'z-50 flex w-fit max-w-240 items-center gap-8 rounded-xs bg-background-neutral-inverse-primary px-8 py-4',
  'text-xs font-medium break-words text-text-neutral-inverse-primary',
  'animate-in fade-in-0 zoom-in-95',
  'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
]
/** The 10 × 5 arrow. */
export const tooltipArrowClasses = 'fill-background-neutral-inverse-primary'
