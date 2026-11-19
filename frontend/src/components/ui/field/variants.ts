// vertical: label, description, control, then helper or error text below.
// horizontal: label and description on the left, the control on the right (a Switch, say), message below.
export type FieldOrientation = 'vertical' | 'horizontal'
export const fieldOrientations: Record<FieldOrientation, string> = {
  vertical: 'flex w-full flex-col gap-8',
  horizontal: 'grid w-full grid-cols-[1fr_auto] items-center gap-x-12 gap-y-4',
}
/** Kept for anything that styles a field directly; the vertical layout. */
export const fieldClass = fieldOrientations.vertical
/** horizontal: the control's cell, right of the label (and of the description, when there is one). */
export const fieldControlHorizontalClass = 'col-start-2 row-start-1 flex items-center'
/** With a description: the control spans both rows and is centred on the label's 20px line. */
export const fieldControlHorizontalTallClass = 'row-span-2 h-20 self-start'
/** horizontal: the message runs under both columns. */
export const fieldMessageHorizontalClass = 'col-span-2'

/** The label turns error red with an error, and greys out when disabled. */
export function fieldLabelClass(disabled?: boolean, invalid?: boolean) {
  return ['text-sm font-medium', disabled ? 'text-text-neutral-disabled' : invalid ? 'text-text-error-primary' : 'text-text-neutral-primary']
}
/** required: the asterisk after the label; screen readers hear "(required)" instead. */
export function fieldRequiredClass(disabled?: boolean) {
  return ['ml-4', disabled ? 'text-text-neutral-disabled' : 'text-text-error-primary']
}
/** The label with something at its end, such as a Badge (the trailing slot). */
export const fieldLabelRowClass = 'flex items-center justify-between gap-8'

/** Between the label and the control, e.g. a password rule. */
export const fieldDescriptionClass = 'text-sm text-text-neutral-tertiary'

/** The message stays in the DOM (visually hidden while empty), so its alert is live before an error appears. */
export function fieldMessageClass(error?: string, helper?: string) {
  return ['text-xs font-medium', error ? 'text-text-error-primary' : 'text-text-neutral-tertiary', !(error || helper) && 'sr-only']
}

// FieldSet: a fieldset with a legend and an optional description, around related fields. A legend isn't a
// flex item, so the set's gap doesn't reach it: it keeps 16 below itself, and a description pulls up to 4 under it.
export const fieldSetClass = 'flex min-w-0 flex-col gap-16'
export const fieldSetLegendClass = 'mb-16 text-md font-medium text-text-neutral-primary'
export const fieldSetDescriptionClass = '-mt-12 text-sm text-text-neutral-tertiary'

/** FieldGroup: fields or sets stacked 24 apart. */
export const fieldGroupClass = 'flex flex-col gap-24'

/** FieldSeparator: a 1px line between groups of fields. */
export const fieldSeparatorClass = 'h-px w-full shrink-0 bg-border-neutral-primary'
