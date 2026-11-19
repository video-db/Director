// The toast and the stack. Colours per status come from Alert's statusStyles; neutral (the default) and
// loading use the grey box, loading with a spinner in the icon's place.
export type ToastStatus = 'neutral' | 'success' | 'info' | 'warning' | 'error' | 'loading'
export const toastNeutralBoxClasses = 'bg-background-neutral-subtle border-border-neutral-primary'
export const toastClasses = 'flex w-full max-w-420 items-center gap-8 rounded-xs border py-4 pr-4 pl-12 shadow-md'
export const toastMessageClasses = 'min-w-0 flex-1 text-sm font-medium text-text-neutral-primary'

export type ToasterPosition = 'bottom-right' | 'bottom-center' | 'top-center'
export const toasterClasses = 'pointer-events-none fixed z-100 flex w-[calc(100%-32px)] max-w-420 flex-col gap-8 rounded-xs outline-none focus-visible:shadow-focus-ring'
export const toasterPositions: Record<ToasterPosition, string> = {
  'bottom-right': 'right-16 bottom-16',
  'bottom-center': 'bottom-16 left-1/2 -translate-x-1/2',
  'top-center': 'top-16 left-1/2 -translate-x-1/2',
}
/** Enter and exit transitions of a toast in the stack. */
export const toastTransition = {
  enterFrom: 'opacity-0 translate-y-8',
  enterActive: 'transition duration-200',
  leaveActive: 'transition duration-150',
  leaveTo: 'opacity-0 scale-95',
}
