// The panel, overlay, header row and footer come from Dialog (dialog/variants.ts).

// sm: 500 wide, as Dialog sm, with the text left-aligned and an icon to its left.
// xs: 320 wide, centred, with the icon above the text and Cancel and Confirm sharing the footer.
export type ConfirmationDialogSize = 'xs' | 'sm'
export const confirmationSizes: Record<ConfirmationDialogSize, string> = { xs: 'max-w-320', sm: 'max-w-500' }

/** Simple variant: the icon and the heading and detail, above the footer. */
export const confirmationBodyClasses = 'flex gap-16 p-20'
export const confirmationBodyXsClasses = 'flex-col items-center text-center'
export const confirmationTextClasses = 'flex min-w-0 flex-1 flex-col gap-12'
export const confirmationTitleClasses = 'text-h6 font-semibold'
export const confirmationDescriptionClasses = 'text-sm text-text-neutral-secondary'
/** The icon tile; red when the dialog is destructive. */
export const confirmationMediaClasses = 'flex size-48 shrink-0 items-center justify-center rounded-sm'
export const confirmationMediaTones = {
  neutral: 'bg-background-neutral-secondary text-icon-neutral-primary',
  destructive: 'bg-background-error-subtle text-icon-error-primary',
}
/** xs: Cancel and Confirm split the footer in two equal halves. */
export const confirmationFooterXsClasses = 'grid grid-cols-2'
/** Typed variant: the warning Alert and the field, under the Dialog header row. */
export const confirmationTypedBodyClasses = 'flex flex-col gap-20 p-20'
/** Typed variant: the confirm button runs the width of the footer. */
export const confirmationTypedConfirmClasses = 'w-full'
