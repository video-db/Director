export type SegmentedControlSize = 'sm' | 'md'

/** The container: md 40px, sm 36px, with 4px of padding around the segments. */
export function segmentedControlClasses(size: SegmentedControlSize = 'md') {
  return ['inline-flex items-center gap-2 rounded-xs bg-background-neutral-secondary p-4', size === 'sm' ? 'h-control-sm' : 'h-control-md']
}

/** A segment: data-state="on" while selected, data-disabled while disabled. md 32px, sm 28px. */
export function segmentedControlItemClasses(size: SegmentedControlSize = 'md') {
  return [
    'flex flex-1 cursor-pointer items-center justify-center gap-4 rounded-xs px-12 text-sm font-medium whitespace-nowrap',
    size === 'sm' ? 'h-28' : 'h-32',
    'text-text-neutral-tertiary outline-none transition-[color,background-color,box-shadow] duration-150',
    'not-data-disabled:hover:bg-background-neutral-tertiary not-data-disabled:hover:text-text-neutral-primary',
    // While held down, an unselected segment takes the selected fill, so the press shows before release.
    'not-data-disabled:data-[state=off]:active:bg-background-neutral-primary',
    'data-[state=on]:bg-background-neutral-primary data-[state=on]:text-text-neutral-primary data-[state=on]:shadow-xxs data-[state=on]:hover:bg-background-neutral-primary',
    'focus-visible:shadow-focus-ring',
    'data-disabled:cursor-not-allowed data-disabled:text-text-neutral-disabled',
  ]
}

/** Segment icons are 16px. */
export const segmentedControlIconSize = 16
