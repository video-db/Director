export type DurationLabelEmphasis = 'scrim' | 'solid'
export type DurationLabelSize = 'sm' | 'md'

export const durationLabelClasses = 'inline-flex w-fit shrink-0 items-center rounded-xxs font-medium text-text-neutral-inverse-primary tabular-nums'
/** scrim: half-opaque black for use on media. solid: opaque black. */
export const durationLabelEmphases: Record<DurationLabelEmphasis, string> = {
  scrim: 'bg-background-overlay-scrim',
  solid: 'bg-background-neutral-inverse-primary',
}
export const durationLabelSizes: Record<DurationLabelSize, string> = {
  sm: 'h-22 px-8 text-xs',
  md: 'h-28 px-12 text-sm',
}
