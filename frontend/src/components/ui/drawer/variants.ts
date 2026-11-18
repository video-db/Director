// Position, inner-edge border and a 40px slide with a fade, per side. Top and bottom round their inner
// corners with the Dialog's radius.
export const drawerSideClasses = {
  right: 'inset-y-0 right-0 h-full w-3/4 border-l sm:max-w-384 data-[state=open]:slide-in-from-right-40 data-[state=closed]:slide-out-to-right-40',
  left: 'inset-y-0 left-0 h-full w-3/4 border-r sm:max-w-384 data-[state=open]:slide-in-from-left-40 data-[state=closed]:slide-out-to-left-40',
  top: 'inset-x-0 top-0 h-auto rounded-b-lg border-b data-[state=open]:slide-in-from-top-40 data-[state=closed]:slide-out-to-top-40',
  bottom: 'inset-x-0 bottom-0 h-auto rounded-t-lg border-t data-[state=open]:slide-in-from-bottom-40 data-[state=closed]:slide-out-to-bottom-40',
} as const

/** The veil behind the drawer, lighter than the Dialog scrim. */
export const drawerOverlayClasses = 'fixed inset-0 z-50 bg-background-overlay-veil data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0'
/** The panel, before its side's classes. */
export const drawerContentClasses = [
  'fixed z-50 flex flex-col gap-16 border-border-neutral-primary bg-background-neutral-primary text-sm text-text-neutral-primary shadow-lg outline-none',
  'duration-200 ease-in-out data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0',
]
/** The × button: a tertiary 32px Icon Button in the top-right corner. */
export const drawerCloseButtonClasses = 'absolute top-12 right-12 size-control-xs'
export const drawerHeaderClasses = 'flex flex-col gap-2 p-16'
export const drawerFooterClasses = 'mt-auto flex flex-col gap-8 p-16'
export const drawerTitleClasses = 'text-md font-medium text-text-neutral-primary'
export const drawerDescriptionClasses = 'text-sm text-text-neutral-tertiary'
