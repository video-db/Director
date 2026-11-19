export type DividerOrientation = 'horizontal' | 'vertical'
export type DividerEmphasis = 'subtle' | 'strong'

export const dividerClasses = 'flex items-center gap-8'
export const dividerOrientationClasses: Record<DividerOrientation, string> = {
  horizontal: 'w-full',
  vertical: 'h-full min-h-20 flex-col self-stretch',
}

/** One 1px line; with a label there is one on each side of it. */
export const dividerLineClasses = (orientation: DividerOrientation, emphasis: DividerEmphasis) => [
  'flex-1',
  orientation === 'horizontal' ? 'h-px' : 'w-px',
  emphasis === 'strong' ? 'bg-border-neutral-hover' : 'bg-border-neutral-primary',
]

export const dividerLabelClasses = 'shrink-0 text-xs font-medium text-text-neutral-tertiary'
