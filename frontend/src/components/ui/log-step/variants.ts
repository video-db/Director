export type LogStepStatus = 'running' | 'done' | 'failed'

export const logStepClasses = 'flex flex-col rounded-xs'

/** The row: a plain div, or the collapsible trigger when the step has detail. */
export const logStepRowClasses = 'group/log flex min-h-control-sm w-full items-center gap-8 rounded-xs px-12 py-8 text-left outline-none transition-colors duration-150'
/** Added to the row when it is a button (the step has detail). */
export const logStepRowExpandableClasses = 'cursor-pointer hover:bg-background-neutral-hover focus-visible:shadow-focus-ring'

/** The 20px box holding the spinner or status icon. */
export const logStepStatusClasses = 'flex size-20 shrink-0 items-center justify-center'
export const logStepStatusIconClasses = {
  done: 'text-icon-success-primary',
  failed: 'text-icon-error-primary',
} as const

export const logStepLabelClasses = 'min-w-0 flex-1 text-sm font-medium text-text-neutral-primary'
export const logStepChevronClasses = 'text-icon-neutral-tertiary transition-transform duration-150 group-data-[state=open]/log:rotate-180'
/** Inside the collapsible content, so the height animation doesn't jump by the padding. */
// pl-40 lines the detail up with the label: 12 of row padding, the 20px status box and the 8px gap.
export const logStepDetailClasses = 'pr-12 pb-8 pl-40 text-sm text-text-neutral-secondary'
