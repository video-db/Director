// Bars carry data-state="visible" | "hidden" (as Reka UI marks them; the React bar sets it too) and fade
// in and out with it.
export const scrollAreaClasses = 'relative'

export const scrollAreaViewportClasses = 'size-full rounded-[inherit] outline-none transition-shadow duration-150 focus-visible:shadow-focus-ring'

export const scrollBarClasses = [
  'z-10 flex touch-none p-2 select-none',
  'data-[state=visible]:animate-in data-[state=visible]:fade-in-0 data-[state=hidden]:animate-out data-[state=hidden]:fade-out-0',
]
export const scrollBarOrientationClasses = {
  vertical: 'h-full w-12',
  horizontal: 'h-12 flex-col',
} as const

// 8px thumb; the ::before keeps a 44px touch target around it
export const scrollBarThumbClasses = [
  'relative flex-1 rounded-full bg-background-neutral-tertiary transition-colors duration-150 hover:bg-background-neutral-control active:bg-background-neutral-control',
  'before:absolute before:top-1/2 before:left-1/2 before:size-full before:min-h-44 before:min-w-44 before:-translate-1/2',
]

// React: with type="always" a bar shows even when nothing overflows. Reka UI then fills the track with
// the thumb; Base UI sizes it at its 16px minimum, so the React thumb fills its bar while the bar's
// direction has no overflow (Base UI marks overflow with data-has-overflow-x / -y on the bar).
export const scrollBarThumbFillClasses = [
  '[[data-orientation=vertical]:not([data-has-overflow-y])>&]:h-full!',
  '[[data-orientation=horizontal]:not([data-has-overflow-x])>&]:w-full!',
]
