// Message Scroller: the scrolling chat thread and its Scroll to latest button.
export const messageScrollerClasses = 'relative flex min-h-0 flex-col'
export const messageScrollerViewportClasses = 'min-h-0 flex-1 overflow-y-auto rounded-[inherit] outline-none focus-visible:shadow-focus-ring'
// Centred 8px above the bottom edge, over the messages.
export const messageScrollerButtonClasses = 'absolute bottom-8 left-1/2 -translate-x-1/2 shadow-sm'
// The button fades in and out.
export const messageScrollerButtonTransition = {
  enterActive: 'transition-opacity duration-150',
  enterFrom: 'opacity-0',
  leaveActive: 'transition-opacity duration-150',
  leaveTo: 'opacity-0',
}
