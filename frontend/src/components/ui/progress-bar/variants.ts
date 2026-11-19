export type ProgressBarSize = 'sm' | 'md'
export type ProgressBarColour = 'brand' | 'success' | 'error'

export const progressBarClasses = 'flex w-full items-center gap-12'
export const progressBarTrackClasses = 'relative min-w-0 flex-1 overflow-hidden rounded-full bg-background-neutral-tertiary'
export const progressBarTrackSizes: Record<ProgressBarSize, string> = { sm: 'h-4', md: 'h-8' }
export const progressBarFillClasses = 'h-full rounded-full transition-[width] duration-300'
export const progressBarFills: Record<ProgressBarColour, string> = {
  brand: 'bg-background-brand-primary',
  success: 'bg-background-success-bold',
  error: 'bg-background-error-bold',
}
// showLabel: the label above the bar, with the percentage at the end of its row.
export const progressBarLabelledClasses = 'flex w-full flex-col gap-8'
export const progressBarLabelRowClasses = 'flex items-center justify-between gap-12 text-sm'
export const progressBarLabelClasses = 'min-w-0 truncate font-medium text-text-neutral-primary'
export const progressBarLabelValueClasses = 'shrink-0 text-text-neutral-secondary tabular-nums'
export const progressBarValueClasses = 'w-40 shrink-0 text-right text-sm font-medium text-text-neutral-secondary tabular-nums'

/** The value as a whole percentage between 0 and 100. */
export const progressBarPercent = (value: number) => Math.min(100, Math.max(0, Math.round(value)))
