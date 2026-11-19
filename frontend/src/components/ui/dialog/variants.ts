// Shared with ConfirmationDialog.
export type DialogSize = 'sm' | 'lg' | 'xl'
export const dialogSizes: Record<DialogSize, string> = { sm: 'max-w-500', lg: 'max-w-620', xl: 'max-w-720' }
/** Title row: a long title wraps and the close button stays at the top. Add min-h-64 pb-12 without tabs. */
export const headerRowClasses = 'flex shrink-0 items-start gap-12 px-20 pt-12'
/** py-6 centres a one-line title (28px) on the 40px close button. */
export const headerTitleClasses = 'min-w-0 flex-1 py-6 text-h6 font-semibold break-words text-text-neutral-primary'
export const overlayClasses = 'fixed inset-0 z-50 bg-background-overlay-scrim data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0'
export const panelClasses = [
  'fixed top-1/2 left-1/2 z-50 flex max-h-[calc(100dvh-32px)] w-[calc(100%-32px)] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden',
  'rounded-lg border border-border-neutral-primary bg-background-neutral-primary text-text-neutral-primary outline-none',
  'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
  'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
]

export const dialogHeaderClasses = 'flex shrink-0 flex-col gap-12'
/** Added to the title row when there are no tabs under it. */
export const headerRowNoTabsClasses = 'min-h-64 pb-12'
export const headerTabsClasses = 'pl-12'
export const dialogBodyClasses = 'flex min-h-0 flex-1 flex-col gap-20 overflow-y-auto border-t border-border-neutral-primary px-20 py-32'
// actions: buttons on the right, wrapping when they don't fit. split: the first item left; below 640px
// the items stack full width, first item last.
export type DialogFooterLayout = 'actions' | 'split'
export const dialogFooterClasses = 'flex min-h-64 shrink-0 gap-12 border-t border-border-neutral-primary bg-background-neutral-secondary px-20 py-12'
export const dialogFooterLayouts: Record<DialogFooterLayout, string> = {
  actions: 'flex-wrap items-center justify-end',
  split: 'flex-col-reverse *:w-full sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:*:w-auto',
}
